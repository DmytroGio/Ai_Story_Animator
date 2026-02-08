from llm_generator import LLMGenerator
from image_generator_comfy import ComfyUIGenerator
from video_creator import VideoCreator
import time
from pathlib import Path


class AIStoryAnimator:
    def __init__(self):
        """Инициализация всех компонентов пайплайна"""
        print("🎬 Инициализация AI Story Animator...\n")

        self.llm = LLMGenerator()
        self.image_gen = ComfyUIGenerator()
        self.video_creator = VideoCreator(fps=24, transition_duration=1.0)

        print("\n✅ Все компоненты готовы!\n")

    def create_story_animation(self, story_idea, num_scenes=5,
                               style='cinematic', project_name=None,
                               scene_duration=4.0, color_grade='warm'):
        """
        Полный пайплайн: идея → сценарий → изображения → видео

        Args:
            story_idea (str): Идея истории от пользователя
            num_scenes (int): Количество сцен (3-7 оптимально)
            style (str): Художественный стиль (cinematic, anime, cartoon)
            project_name (str): Название проекта для файлов
            scene_duration (float): Длительность каждой сцены в секундах
            color_grade (str): Цветокоррекция (warm, cool, vintage, cyberpunk)
        """
        start_time = time.time()

        print("=" * 70)
        print("🎬 AI STORY ANIMATOR - ПОЛНЫЙ ПАЙПЛАЙН")
        print("=" * 70)
        print(f"\n💡 Идея: {story_idea}")
        print(f"🎨 Стиль: {style}")
        print(f"🎬 Сцен: {num_scenes}")
        print(f"⏱️  Длительность сцены: {scene_duration}s")
        print(f"🌈 Цветокоррекция: {color_grade}\n")

        # Генерируем название проекта
        if project_name is None:
            project_name = f"story_{int(time.time())}"

        # ==================== ЭТАП 1: LLM ====================
        print("\n" + "=" * 70)
        print("📝 ЭТАП 1/3: Генерация сценария через LLM")
        print("=" * 70 + "\n")

        story_data = self.llm.generate_story_scenes(story_idea, num_scenes=num_scenes)

        if not story_data:
            print("❌ Ошибка генерации сценария")
            return None

        story_title = story_data.get('title', 'Untitled Story')
        scenes = story_data.get('scenes', [])

        print(f"\n✅ Сценарий готов: '{story_title}'")
        print(f"📖 Сцен сгенерировано: {len(scenes)}\n")

        # Показываем сцены
        for scene in scenes:
            print(f"  Сцена {scene['scene_number']}: {scene['description'][:60]}...")

        # ==================== ЭТАП 2: IMAGE GEN ====================
        print("\n" + "=" * 70)
        print("🎨 ЭТАП 2/3: Генерация изображений через ComfyUI")
        print("=" * 70 + "\n")

        # Создаём промпты для SD
        image_prompts = self.llm.generate_image_prompts(story_data, style=style)

        # Генерируем изображения
        generated_images = self.image_gen.generate_scene_images(
            prompts_data=image_prompts,
            style=style,
            project_name=project_name,
            width=512,
            height=512,
            steps=15,
            cfg=7
        )

        if not generated_images:
            print("❌ Ошибка генерации изображений")
            return None

        print(f"\n✅ Изображения готовы: {len(generated_images)}/{num_scenes}")

        # ==================== ЭТАП 3: VIDEO ====================
        print("\n" + "=" * 70)
        print("🎥 ЭТАП 3/3: Создание кинематографического видео")
        print("=" * 70 + "\n")

        # Создаём видео
        video_path = self.video_creator.create_video(
            image_paths=[img['filepath'] for img in generated_images],
            output_filename=f"{project_name}_animation.mp4",
            scene_duration=scene_duration,
            use_ken_burns=True,
            use_color_grade=True,
            color_style=color_grade,
            transition_type='zoom_blur'
        )

        # ==================== РЕЗУЛЬТАТЫ ====================
        end_time = time.time()
        total_time = end_time - start_time

        print("\n" + "=" * 70)
        print("🎉 ПАЙПЛАЙН УСПЕШНО ЗАВЕРШЁН!")
        print("=" * 70)
        print(f"\n📖 История: {story_title}")
        print(f"🎬 Сцен: {len(scenes)}")
        print(f"🖼️  Изображений: {len(generated_images)}")
        print(f"🎥 Видео: {video_path}")
        print(f"⏱️  Общее время: {total_time:.1f}s ({total_time / 60:.1f} мин)")
        print(f"\n📁 Результаты:")
        print(f"  - Изображения: outputs/images/{project_name}_scene_*.png")
        print(f"  - Видео: {video_path}")
        print("=" * 70 + "\n")

        return {
            'title': story_title,
            'scenes': scenes,
            'images': generated_images,
            'video_path': str(video_path),
            'duration': total_time
        }


# ==================== ИНТЕРАКТИВНЫЙ РЕЖИМ ====================
def interactive_mode():
    """Интерактивный режим для пользователя"""
    print("\n" + "=" * 70)
    print("🎬 AI STORY ANIMATOR - Интерактивный режим")
    print("=" * 70 + "\n")

    animator = AIStoryAnimator()

    # Получаем идею от пользователя
    print("\n💡 Введите идею для вашей анимированной истории:")
    print("   (Например: 'A robot falls in love with a star')")
    story_idea = input("\n> ")

    if not story_idea.strip():
        story_idea = "A lonely robot discovers a small plant in a post-apocalyptic world"
        print(f"\n✨ Используем пример: {story_idea}")

    # Количество сцен
    print("\n🎬 Сколько сцен создать? (рекомендуется 3-5)")
    try:
        num_scenes = int(input("> ") or "3")
        num_scenes = max(2, min(num_scenes, 10))  # Ограничение 2-10
    except:
        num_scenes = 3
        print(f"✨ Используем по умолчанию: {num_scenes}")

    # Стиль
    print("\n🎨 Выберите стиль:")
    print("   1. Cinematic (кинематографический)")
    print("   2. Anime (аниме)")
    print("   3. Cartoon (мультяшный)")
    print("   4. Realistic (реалистичный)")

    style_choice = input("\n> ") or "1"
    styles = {'1': 'cinematic', '2': 'anime', '3': 'cartoon', '4': 'realistic'}
    style = styles.get(style_choice, 'cinematic')

    # Цветокоррекция
    print("\n🌈 Цветовая палитра:")
    print("   1. Warm (тёплая)")
    print("   2. Cool (холодная)")
    print("   3. Vintage (винтажная)")
    print("   4. Cyberpunk (киберпанк)")

    color_choice = input("\n> ") or "1"
    colors = {'1': 'warm', '2': 'cool', '3': 'vintage', '4': 'cyberpunk'}
    color_grade = colors.get(color_choice, 'warm')

    # Запуск
    print("\n🚀 Запускаем генерацию...\n")

    result = animator.create_story_animation(
        story_idea=story_idea,
        num_scenes=num_scenes,
        style=style,
        color_grade=color_grade,
        scene_duration=4.0
    )

    if result:
        print("\n✅ Готово! Откройте видео:")
        print(f"   {result['video_path']}")


# ==================== БЫСТРЫЕ ТЕСТЫ ====================
def quick_test():
    """Быстрый тест с предустановленными параметрами"""
    animator = AIStoryAnimator()

    test_stories = [
        {
            'idea': 'A space explorer discovers an ancient alien temple on Mars',
            'scenes': 3,
            'style': 'cinematic',
            'color': 'warm'
        },
        {
            'idea': 'A magical cat protects a hidden forest from dark forces',
            'scenes': 4,
            'style': 'anime',
            'color': 'cool'
        },
        {
            'idea': 'A steampunk inventor creates a time machine in Victorian London',
            'scenes': 3,
            'style': 'cinematic',
            'color': 'vintage'
        }
    ]

    print("\n🎬 Доступные тесты:\n")
    for i, story in enumerate(test_stories, 1):
        print(f"{i}. {story['idea']}")
        print(f"   Стиль: {story['style']}, Сцен: {story['scenes']}\n")

    choice = input("Выберите тест (1-3) или Enter для первого: ") or "1"

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(test_stories):
            story = test_stories[idx]
        else:
            story = test_stories[0]
    except:
        story = test_stories[0]

    result = animator.create_story_animation(
        story_idea=story['idea'],
        num_scenes=story['scenes'],
        style=story['style'],
        color_grade=story['color']
    )

    return result


# ==================== MAIN ====================
if __name__ == "__main__":
    import sys

    print("\n" + "=" * 70)
    print("🎬 AI STORY ANIMATOR")
    print("=" * 70)
    print("\nВыберите режим:")
    print("  1. Интерактивный режим (вводите свою идею)")
    print("  2. Быстрый тест (готовые примеры)")
    print("  3. Выход")

    mode = input("\n> ") or "1"

    if mode == "1":
        interactive_mode()
    elif mode == "2":
        quick_test()
    else:
        print("\n👋 До встречи!")
        sys.exit(0)