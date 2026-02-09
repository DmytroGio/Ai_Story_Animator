import gradio as gr
from pathlib import Path
import json
import time
from datetime import datetime
from llm_generator import LLMGenerator
from image_generator_comfy import ComfyUIGenerator
from video_creator import VideoCreator

# Глобальные переменные для компонентов
llm_gen = None
img_gen = None
video_gen = None


def initialize_components():
    """Ленивая инициализация компонентов"""
    global llm_gen, img_gen, video_gen

    if llm_gen is None:
        llm_gen = LLMGenerator()
    if img_gen is None:
        img_gen = ComfyUIGenerator()
    if video_gen is None:
        video_gen = VideoCreator(fps=24, transition_duration=1.0)

    return llm_gen, img_gen, video_gen


def generate_story_animation(
        story_idea,
        num_scenes,
        art_style,
        color_grade,
        scene_duration,
        use_ken_burns,
        transition_type,
        image_width,
        image_height,
        sd_steps,
        sd_cfg,
        progress=gr.Progress()
):
    """
    Главная функция генерации с прогресс-баром
    """
    try:
        # Инициализация
        progress(0, desc="🎬 Инициализация компонентов...")
        llm, img_gen_inst, video_gen_inst = initialize_components()

        project_name = f"story_{int(time.time())}"
        total_steps = num_scenes + 2  # сцены + сценарий + видео
        current_step = 0

        # История для отображения
        status_updates = []

        # ========== ЭТАП 1: Генерация сценария ==========
        progress(current_step / total_steps, desc="📝 Генерация сценария через LLM...")
        status_updates.append("📝 Генерация сценария...")

        story_data = llm.generate_story_scenes(story_idea, num_scenes=num_scenes)

        if not story_data:
            return None, None, None, "❌ Ошибка генерации сценария", json.dumps({}, indent=2)

        story_title = story_data.get('title', 'Untitled')
        scenes = story_data.get('scenes', [])

        status_updates.append(f"✅ Сценарий готов: '{story_title}'")
        current_step += 1

        # ========== ЭТАП 2: Генерация изображений ==========
        image_prompts = llm.generate_image_prompts(story_data, style=art_style)
        generated_images = []
        image_files = []

        for idx, prompt_info in enumerate(image_prompts, 1):
            progress(
                current_step / total_steps,
                desc=f"🎨 Генерация изображения {idx}/{num_scenes}..."
            )

            status_updates.append(f"🎨 Генерация сцены {idx}/{num_scenes}...")

            prompt = prompt_info.get("prompt", "")
            negative_prompt = prompt_info.get("negative_prompt", "")
            filename = f"{project_name}_scene_{idx:02d}.png"

            # Генерация изображения
            filepath = img_gen_inst.generate_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=image_width,
                height=image_height,
                steps=sd_steps,
                cfg=sd_cfg,
                seed=None,
                filename=filename
            )

            if filepath:
                generated_images.append({
                    "scene_number": idx,
                    "filepath": str(filepath),
                    "prompt": prompt
                })
                image_files.append(str(filepath))
                status_updates.append(f"✅ Сцена {idx} готова")

            current_step += 1

        if not generated_images:
            return None, None, None, "❌ Ошибка генерации изображений", json.dumps({}, indent=2)

        # ========== ЭТАП 3: Создание видео ==========
        progress(current_step / total_steps, desc="🎥 Создание видео...")
        status_updates.append("🎥 Создание кинематографического видео...")

        video_path = video_gen_inst.create_video(
            image_paths=image_files,
            output_filename=f"{project_name}_animation.mp4",
            scene_duration=scene_duration,
            use_ken_burns=use_ken_burns,
            use_color_grade=True,
            color_style=color_grade,
            transition_type=transition_type
        )

        status_updates.append(f"✅ Видео готово: {video_path}")

        # Результат
        progress(1.0, desc="✅ Готово!")

        result_json = {
            "title": story_title,
            "scenes": scenes,
            "images_count": len(generated_images),
            "video_path": str(video_path),
            "timestamp": datetime.now().isoformat()
        }

        status_text = "\n".join(status_updates)

        return (
            image_files,  # Галерея изображений
            str(video_path),  # Видео
            status_text,  # Статус
            json.dumps(result_json, indent=2)  # JSON данные
        )

    except Exception as e:
        import traceback
        error_msg = f"❌ Ошибка: {str(e)}\n\n{traceback.format_exc()}"
        return None, None, error_msg, json.dumps({"error": str(e)}, indent=2)


def create_ui():
    """Создание Gradio интерфейса"""

    with gr.Blocks(
            theme=gr.themes.Soft(
                primary_hue="blue",
                secondary_hue="purple",
            ),
            title="AI Story Animator",
            css="""
        .container {max-width: 1400px; margin: auto;}
        .header {text-align: center; padding: 20px;}
        .gallery-container {min-height: 400px;}
        """
    ) as app:
        # Header
        gr.Markdown(
            """
            # 🎬 AI Story Animator
            ### Превратите вашу идею в кинематографическую анимацию

            **Powered by:** LM Studio (LLM) + ComfyUI (Stable Diffusion) + OpenCV
            """
        )

        with gr.Row():
            # ========== LEFT COLUMN: Inputs ==========
            with gr.Column(scale=1):
                gr.Markdown("## ⚙️ Настройки")

                # Основные параметры
                with gr.Group():
                    gr.Markdown("### 📝 История")
                    story_input = gr.Textbox(
                        label="💡 Идея вашей истории",
                        placeholder="Например: A lonely robot discovers a magical garden in a post-apocalyptic city...",
                        lines=3,
                        value="A lone astronaut discovers an ancient alien temple on Mars"
                    )

                    num_scenes = gr.Slider(
                        label="🎬 Количество сцен",
                        minimum=2,
                        maximum=10,
                        step=1,
                        value=4,
                        info="Больше сцен = дольше генерация"
                    )

                # Художественный стиль
                with gr.Group():
                    gr.Markdown("### 🎨 Визуальный стиль")

                    art_style = gr.Radio(
                        label="Художественный стиль",
                        choices=[
                            "cinematic",
                            "anime",
                            "cartoon",
                            "realistic"
                        ],
                        value="cinematic",
                        info="Стиль визуализации сцен"
                    )

                    color_grade = gr.Radio(
                        label="🌈 Цветовая палитра",
                        choices=[
                            "warm",
                            "cool",
                            "vintage",
                            "cyberpunk"
                        ],
                        value="warm",
                        info="Цветокоррекция для видео"
                    )

                # Настройки видео
                with gr.Group():
                    gr.Markdown("### 🎥 Параметры видео")

                    scene_duration = gr.Slider(
                        label="⏱️ Длительность сцены (сек)",
                        minimum=2.0,
                        maximum=8.0,
                        step=0.5,
                        value=4.0
                    )

                    use_ken_burns = gr.Checkbox(
                        label="✨ Ken Burns эффект (zoom & pan)",
                        value=True,
                        info="Динамическое движение камеры"
                    )

                    transition_type = gr.Radio(
                        label="🔄 Тип перехода",
                        choices=[
                            "crossfade",
                            "zoom_blur",
                            "wipe_left"
                        ],
                        value="zoom_blur"
                    )

                # Продвинутые настройки (скрытые)
                with gr.Accordion("🔧 Продвинутые настройки", open=False):
                    image_width = gr.Slider(
                        label="Ширина изображения",
                        minimum=256,
                        maximum=1024,
                        step=128,
                        value=512
                    )

                    image_height = gr.Slider(
                        label="Высота изображения",
                        minimum=256,
                        maximum=1024,
                        step=128,
                        value=512
                    )

                    sd_steps = gr.Slider(
                        label="SD Steps (качество)",
                        minimum=10,
                        maximum=30,
                        step=5,
                        value=15,
                        info="Больше = лучше качество, но медленнее"
                    )

                    sd_cfg = gr.Slider(
                        label="CFG Scale",
                        minimum=5.0,
                        maximum=15.0,
                        step=0.5,
                        value=7.0,
                        info="Насколько точно следовать промпту"
                    )

                # Кнопка генерации
                generate_btn = gr.Button(
                    "🚀 Создать анимацию",
                    variant="primary",
                    size="lg"
                )

            # ========== RIGHT COLUMN: Outputs ==========
            with gr.Column(scale=2):
                gr.Markdown("## 📊 Результаты")

                # Статус
                status_output = gr.Textbox(
                    label="📝 Статус генерации",
                    lines=8,
                    max_lines=15,
                    interactive=False
                )

                # Вкладки с результатами
                with gr.Tabs():
                    # Вкладка: Изображения
                    with gr.Tab("🖼️ Изображения"):
                        image_gallery = gr.Gallery(
                            label="Сгенерированные сцены",
                            show_label=True,
                            columns=3,
                            rows=2,
                            height="auto",
                            object_fit="contain"
                        )

                    # Вкладка: Видео
                    with gr.Tab("🎥 Видео"):
                        video_output = gr.Video(
                            label="Финальная анимация",
                            show_label=True,
                            height=500
                        )

                        video_download = gr.File(
                            label="📥 Скачать видео",
                            interactive=False
                        )

                    # Вкладка: JSON данные
                    with gr.Tab("📋 Данные"):
                        json_output = gr.Code(
                            label="Метаданные (JSON)",
                            language="json",
                            lines=15
                        )

        # Примеры
        gr.Markdown("## 💡 Примеры идей")
        gr.Examples(
            examples=[
                ["A robot gardener tends to the last flowers on Earth", 3, "cinematic", "warm"],
                ["A young witch discovers her powers during a magical thunderstorm", 4, "anime", "cool"],
                ["Time traveler witnesses the birth of the universe", 5, "realistic", "cyberpunk"],
                ["A dragon befriends a lonely knight in an enchanted forest", 4, "cartoon", "vintage"],
            ],
            inputs=[story_input, num_scenes, art_style, color_grade],
        )

        # Подвал
        gr.Markdown(
            """
            ---
            **📌 Совет:** Для лучших результатов используйте детальные описания и 3-5 сцен.

            **⚡ Время генерации:** ~2-5 минут в зависимости от количества сцен.
            """
        )

        # Обработчик кнопки
        generate_btn.click(
            fn=generate_story_animation,
            inputs=[
                story_input,
                num_scenes,
                art_style,
                color_grade,
                scene_duration,
                use_ken_burns,
                transition_type,
                image_width,
                image_height,
                sd_steps,
                sd_cfg
            ],
            outputs=[
                image_gallery,
                video_output,
                status_output,
                json_output
            ]
        )

    return app


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🎬 AI Story Animator - Web Interface")
    print("=" * 70 + "\n")

    print("🚀 Запуск Gradio интерфейса...")
    print("📍 Убедитесь, что запущены:")
    print("   - LM Studio (http://localhost:1234)")
    print("   - ComfyUI (http://localhost:8188)")
    print("\n")

    app = create_ui()

    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,  # Установите True для публичной ссылки
        show_error=True,
        quiet=False
    )