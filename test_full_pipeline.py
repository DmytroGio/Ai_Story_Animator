from llm_generator import LLMGenerator
from image_generator_comfy import ComfyUIGenerator


def main():
    print("🎬 Testing full pipeline: LLM → ComfyUI (OPTIMIZED)\n")

    # Initialization
    llm = LLMGenerator()
    img_gen = ComfyUIGenerator()

    # Story idea
    story_idea = "A lone astronaut discovers an ancient alien temple on Mars"

    print(f"💡 Idea: {story_idea}\n")

    # 1. Generate script through LLM
    print("📝 Stage 1: Generating script...\n")
    story_data = llm.generate_story_scenes(story_idea, num_scenes=3)

    if not story_data:
        print("❌ Script generation error")
        return

    # 2. Create prompts for SD
    print("\n🎨 Stage 2: Creating prompts for images...\n")
    image_prompts = llm.generate_image_prompts(story_data, style="cinematic")

    # 3. Generate images through ComfyUI
    print("\n🖼️ Stage 3: Generating images through ComfyUI...\n")

    # OPTIMIZED SETTINGS
    generated_images = img_gen.generate_scene_images(
        prompts_data=image_prompts,
        style="cinematic",
        project_name="mars_temple",
        width=512,  # ← Reduced for speed
        height=512,  # ← Reduced for speed
        steps=15,  # ← Fewer steps = faster
        cfg=7  # ← Optimal value
    )

    # Results
    print("\n" + "=" * 60)
    print("✅ PIPELINE COMPLETED!")
    print("=" * 60)
    print(f"\n📖 Story: {story_data.get('title')}")
    print(f"🎬 Scenes: {len(story_data.get('scenes', []))}")
    print(f"🖼️ Images: {len(generated_images)}")
    print(f"\n📁 Results in: outputs/images/")

    for img in generated_images:
        print(f"  - {img['filepath']}")

    # Statistics
    print(f"\n⚙️ Generation settings:")
    print(f"  Resolution: 512x512")
    print(f"  Steps: 15")
    print(f"  CFG: 7")


if __name__ == "__main__":
    main()
