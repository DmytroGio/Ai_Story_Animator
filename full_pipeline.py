from llm_generator import LLMGenerator
from image_generator_comfy import ComfyUIGenerator
from video_creator import VideoCreator
import time
from pathlib import Path


class AIStoryAnimator:
    def __init__(self):
        """Initialize all pipeline components"""
        print("🎬 Initializing AI Story Animator...\n")

        self.llm = LLMGenerator()
        self.image_gen = ComfyUIGenerator()
        self.video_creator = VideoCreator(fps=24, transition_duration=1.0)

        print("\n✅ All components ready!\n")

    def create_story_animation(self, story_idea, num_scenes=5,
                               style='cinematic', project_name=None,
                               scene_duration=4.0, color_grade='warm'):
        """
        Full pipeline: idea → script → images → video

        Args:
            story_idea (str): Story idea from user
            num_scenes (int): Number of scenes (3-7 optimal)
            style (str): Art style (cinematic, anime, cartoon)
            project_name (str): Project name for files
            scene_duration (float): Duration of each scene in seconds
            color_grade (str): Color grading (warm, cool, vintage, cyberpunk)
        """
        start_time = time.time()

        print("=" * 70)
        print("🎬 AI STORY ANIMATOR - FULL PIPELINE")
        print("=" * 70)
        print(f"\n💡 Idea: {story_idea}")
        print(f"🎨 Style: {style}")
        print(f"🎬 Scenes: {num_scenes}")
        print(f"⏱️  Scene duration: {scene_duration}s")
        print(f"🌈 Color grading: {color_grade}\n")

        # Generate project name
        if project_name is None:
            project_name = f"story_{int(time.time())}"

        # ==================== STAGE 1: LLM ====================
        print("\n" + "=" * 70)
        print("📝 STAGE 1/3: Generating script through LLM")
        print("=" * 70 + "\n")

        story_data = self.llm.generate_story_scenes(story_idea, num_scenes=num_scenes)

        if not story_data:
            print("❌ Script generation error")
            return None

        story_title = story_data.get('title', 'Untitled Story')
        scenes = story_data.get('scenes', [])

        print(f"\n✅ Script ready: '{story_title}'")
        print(f"📖 Scenes generated: {len(scenes)}\n")

        # Display scenes
        for scene in scenes:
            print(f"  Scene {scene['scene_number']}: {scene['description'][:60]}...")

        # ==================== STAGE 2: IMAGE GEN ====================
        print("\n" + "=" * 70)
        print("🎨 STAGE 2/3: Generating images through ComfyUI")
        print("=" * 70 + "\n")

        # Create prompts for SD
        image_prompts = self.llm.generate_image_prompts(story_data, style=style)

        # Generate images
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
            print("❌ Image generation error")
            return None

        print(f"\n✅ Images ready: {len(generated_images)}/{num_scenes}")

        # ==================== STAGE 3: VIDEO ====================
        print("\n" + "=" * 70)
        print("🎥 STAGE 3/3: Creating cinematic video")
        print("=" * 70 + "\n")

        # Create video
        video_path = self.video_creator.create_video(
            image_paths=[img['filepath'] for img in generated_images],
            output_filename=f"{project_name}_animation.mp4",
            scene_duration=scene_duration,
            use_ken_burns=True,
            use_color_grade=True,
            color_style=color_grade,
            transition_type='zoom_blur'
        )

        # ==================== RESULTS ====================
        end_time = time.time()
        total_time = end_time - start_time

        print("\n" + "=" * 70)
        print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(f"\n📖 Story: {story_title}")
        print(f"🎬 Scenes: {len(scenes)}")
        print(f"🖼️  Images: {len(generated_images)}")
        print(f"🎥 Video: {video_path}")
        print(f"⏱️  Total time: {total_time:.1f}s ({total_time / 60:.1f} min)")
        print(f"\n📁 Results:")
        print(f"  - Images: outputs/images/{project_name}_scene_*.png")
        print(f"  - Video: {video_path}")
        print("=" * 70 + "\n")

        return {
            'title': story_title,
            'scenes': scenes,
            'images': generated_images,
            'video_path': str(video_path),
            'duration': total_time
        }


# ==================== INTERACTIVE MODE ====================
def interactive_mode():
    """Interactive mode for user"""
    print("\n" + "=" * 70)
    print("🎬 AI STORY ANIMATOR - Interactive Mode")
    print("=" * 70 + "\n")

    animator = AIStoryAnimator()

    # Get idea from user
    print("\n💡 Enter your idea for an animated story:")
    print("   (For example: 'A robot falls in love with a star')")
    story_idea = input("\n> ")

    if not story_idea.strip():
        story_idea = "A lonely robot discovers a small plant in a post-apocalyptic world"
        print(f"\n✨ Using example: {story_idea}")

    # Number of scenes
    print("\n🎬 How many scenes to create? (recommended 3-5)")
    try:
        num_scenes = int(input("> ") or "3")
        num_scenes = max(2, min(num_scenes, 10))  # Limit 2-10
    except:
        num_scenes = 3
        print(f"✨ Using default: {num_scenes}")

    # Style
    print("\n🎨 Choose style:")
    print("   1. Cinematic")
    print("   2. Anime")
    print("   3. Cartoon")
    print("   4. Realistic")

    style_choice = input("\n> ") or "1"
    styles = {'1': 'cinematic', '2': 'anime', '3': 'cartoon', '4': 'realistic'}
    style = styles.get(style_choice, 'cinematic')

    # Color grading
    print("\n🌈 Color Palette:")
    print("   1. Warm")
    print("   2. Cool")
    print("   3. Vintage")
    print("   4. Cyberpunk")

    color_choice = input("\n> ") or "1"
    colors = {'1': 'warm', '2': 'cool', '3': 'vintage', '4': 'cyberpunk'}
    color_grade = colors.get(color_choice, 'warm')

    # Launch
    print("\n🚀 Starting generation...\n")

    result = animator.create_story_animation(
        story_idea=story_idea,
        num_scenes=num_scenes,
        style=style,
        color_grade=color_grade,
        scene_duration=4.0
    )

    if result:
        print("\n✅ Done! Open video:")
        print(f"   {result['video_path']}")


# ==================== QUICK TESTS ====================
def quick_test():
    """Quick test with preset parameters"""
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

    print("\n🎬 Available tests:\n")
    for i, story in enumerate(test_stories, 1):
        print(f"{i}. {story['idea']}")
        print(f"   Style: {story['style']}, Scenes: {story['scenes']}\n")

    choice = input("Choose test (1-3) or Enter for first: ") or "1"

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
    print("\nChoose mode:")
    print("  1. Interactive mode (enter your own idea)")
    print("  2. Quick test (ready-made examples)")
    print("  3. Exit")

    mode = input("\n> ") or "1"

    if mode == "1":
        interactive_mode()
    elif mode == "2":
        quick_test()
    else:
        print("\n👋 See you later!")
        sys.exit(0)
