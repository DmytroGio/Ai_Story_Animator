from openai import OpenAI
import os
from dotenv import load_dotenv
import json

load_dotenv()


class LLMGenerator:
    def __init__(self):
        self.client = OpenAI(
            base_url=os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1"),
            api_key=os.getenv("LM_STUDIO_API_KEY", "lm-studio")
        )
        self.temperature = float(os.getenv("DEFAULT_TEMPERATURE", "0.8"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "1500"))

    def generate_story_scenes(self, user_idea, num_scenes=5):
        """
        Generates story script with scene descriptions for animation

        Args:
            user_idea (str): Story idea from user
            num_scenes (int): Number of scenes to generate

        Returns:
            list: List of dictionaries with each scene description
        """

        prompt = f"""You are a creative AI that generates visual story scenes for animation.

USER IDEA: {user_idea}

TASK: Create {num_scenes} distinct visual scenes that tell this story. Each scene should be described in detail for image generation.

IMPORTANT RULES:
1. Each scene description must be detailed and visual (describe colors, lighting, mood, composition)
2. Maintain consistency in characters and setting across scenes
3. Create a clear narrative progression from scene 1 to scene {num_scenes}
4. Each description should be 2-3 sentences long
5. Use cinematic and artistic language

FORMAT YOUR RESPONSE AS JSON:
{{
  "title": "Story Title",
  "scenes": [
    {{
      "scene_number": 1,
      "description": "Detailed visual description of scene 1...",
      "mood": "emotional mood (e.g., mysterious, hopeful, dramatic)"
    }},
    ...
  ]
}}

Generate the JSON response now:"""

        try:
            completion = self.client.chat.completions.create(
                model="local-model",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            response_text = completion.choices[0].message.content.strip()

            # Attempt to extract JSON from response
            response_text = self._extract_json(response_text)

            # Parse JSON
            story_data = json.loads(response_text)

            print(f"✅ Script generated: {story_data.get('title', 'Untitled')}")
            print(f"📝 Number of scenes: {len(story_data.get('scenes', []))}")

            return story_data

        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"Model response:\n{response_text}")
            return None
        except Exception as e:
            print(f"❌ Generation error: {e}")
            return None

    def _extract_json(self, text):
        """Extracts JSON from text (removes markdown formatting)"""
        # Remove markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        return text.strip()

    def generate_image_prompts(self, story_data, style="cinematic"):
        """
        Converts scenes to Stable Diffusion prompts
        Uses enhanced style presets
        """
        from utils import StylePresets

        # Get style preset
        style_preset = StylePresets.get_style(style)
        style_suffix = style_preset['sd_suffix']

        prompts = []
        scenes = story_data.get("scenes", [])

        for scene in scenes:
            # Create prompt for Stable Diffusion
            base_description = scene.get("description", "")
            mood = scene.get("mood", "")

            # Form full prompt
            full_prompt = f"{base_description}, {mood} mood, {style_suffix}"

            prompts.append({
                "scene_number": scene.get("scene_number"),
                "prompt": full_prompt,
                "negative_prompt": "blurry, low quality, distorted, deformed, ugly, bad anatomy, watermark, signature, text"
            })

        return prompts


# Testing
if __name__ == "__main__":
    print("🎬 Testing script generator...\n")

    llm = LLMGenerator()

    # Test idea
    test_idea = "A lonely robot discovers a small plant growing in a post-apocalyptic city"

    # Generate script
    story = llm.generate_story_scenes(test_idea, num_scenes=5)

    if story:
        print(f"\n📖 Title: {story.get('title')}\n")

        # Output scenes
        for scene in story.get("scenes", []):
            print(f"Scene {scene['scene_number']}:")
            print(f"  {scene['description']}")
            print(f"  Mood: {scene['mood']}\n")

        # Generate prompts for images
        print("\n🎨 Prompts for Stable Diffusion:\n")
        image_prompts = llm.generate_image_prompts(story, style="cinematic")

        for idx, prompt_data in enumerate(image_prompts, 1):
            print(f"{idx}. {prompt_data['prompt'][:100]}...")
            print()
