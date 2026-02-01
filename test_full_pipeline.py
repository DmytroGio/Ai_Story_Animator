from llm_generator import LLMGenerator
from image_generator_comfy import ComfyUIGenerator


def main():
    print("🎬 Тестирование полного пайплайна: LLM → ComfyUI (ОПТИМИЗИРОВАННЫЙ)\n")

    # Инициализация
    llm = LLMGenerator()
    img_gen = ComfyUIGenerator()

    # Идея истории
    story_idea = "A lone astronaut discovers an ancient alien temple on Mars"

    print(f"💡 Идея: {story_idea}\n")

    # 1. Генерация сценария через LLM
    print("📝 Этап 1: Генерация сценария...\n")
    story_data = llm.generate_story_scenes(story_idea, num_scenes=3)

    if not story_data:
        print("❌ Ошибка генерации сценария")
        return

    # 2. Создание промптов для SD
    print("\n🎨 Этап 2: Создание промптов для изображений...\n")
    image_prompts = llm.generate_image_prompts(story_data, style="cinematic")

    # 3. Генерация изображений через ComfyUI
    print("\n🖼️ Этап 3: Генерация изображений через ComfyUI...\n")

    # ОПТИМИЗИРОВАННЫЕ НАСТРОЙКИ
    generated_images = img_gen.generate_scene_images(
        prompts_data=image_prompts,
        style="cinematic",
        project_name="mars_temple",
        width=512,  # ← Уменьшено для скорости
        height=512,  # ← Уменьшено для скорости
        steps=15,  # ← Меньше шагов = быстрее
        cfg=7  # ← Оптимальное значение
    )

    # Результаты
    print("\n" + "=" * 60)
    print("✅ ПАЙПЛАЙН ЗАВЕРШЁН!")
    print("=" * 60)
    print(f"\n📖 История: {story_data.get('title')}")
    print(f"🎬 Сцен: {len(story_data.get('scenes', []))}")
    print(f"🖼️ Изображений: {len(generated_images)}")
    print(f"\n📁 Результаты в: outputs/images/")

    for img in generated_images:
        print(f"  - {img['filepath']}")

    # Статистика
    print(f"\n⚙️ Настройки генерации:")
    print(f"  Разрешение: 512x512")
    print(f"  Steps: 15")
    print(f"  CFG: 7")


if __name__ == "__main__":
    main()