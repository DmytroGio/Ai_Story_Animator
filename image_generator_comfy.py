import requests
import json
import os
import time
import urllib.request
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class ComfyUIGenerator:
    def __init__(self, server_address="127.0.0.1:8188"):
        self.server_address = server_address
        self.base_url = f"http://{server_address}"

        # Save folder
        self.output_dir = Path("outputs/images")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Connection check
        self._check_connection()

        print("✅ ComfyUI Generator initialized")
        print(f"🌐 Server: {self.base_url}")
        print(f"📁 Images will be saved to: {self.output_dir}")

    def _check_connection(self):
        """Check connection to ComfyUI"""
        try:
            response = requests.get(f"{self.base_url}/system_stats", timeout=5)
            if response.status_code == 200:
                print("✅ ComfyUI server is available")
                return True
            else:
                raise ConnectionError("ComfyUI is not responding")
        except Exception as e:
            raise ConnectionError(
                f"❌ Failed to connect to ComfyUI at {self.base_url}\n"
                f"Make sure ComfyUI is running!\n"
                f"Error: {e}"
            )

    def create_workflow(self, prompt, negative_prompt="", width=1024, height=1024,
                        steps=20, cfg=8, seed=None):
        """
        Creates workflow for image generation
        Structure corresponds to your sdxl_basic.json
        """
        if seed is None:
            seed = int(time.time() * 1000) % 2 ** 32

        workflow = {
            "1": {
                "inputs": {
                    "ckpt_name": "v1-5-pruned-emaonly.safetensors"
                },
                "class_type": "CheckpointLoaderSimple"
            },
            "2": {
                "inputs": {
                    "text": prompt,
                    "clip": ["1", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "3": {
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage"
            },
            "4": {
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "denoise": 1,
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["7", 0],
                    "latent_image": ["3", 0]
                },
                "class_type": "KSampler"
            },
            "5": {
                "inputs": {
                    "samples": ["4", 0],
                    "vae": ["1", 2]
                },
                "class_type": "VAEDecode"
            },
            "6": {
                "inputs": {
                    "filename_prefix": "AI_Story",
                    "images": ["5", 0]
                },
                "class_type": "SaveImage"
            },
            "7": {
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["1", 1]
                },
                "class_type": "CLIPTextEncode"
            }
        }

        return workflow

    def queue_prompt(self, workflow):
        """Sends workflow for generation"""
        p = {"prompt": workflow}
        data = json.dumps(p).encode('utf-8')

        try:
            req = urllib.request.Request(f"{self.base_url}/prompt", data=data)
            req.add_header('Content-Type', 'application/json')
            response = urllib.request.urlopen(req)
            return json.loads(response.read())
        except Exception as e:
            print(f"❌ Error sending prompt: {e}")
            return None

    def get_image(self, filename, subfolder, folder_type):
        """Gets generated image"""
        try:
            data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
            url_values = urllib.parse.urlencode(data)
            url = f"{self.base_url}/view?{url_values}"

            response = urllib.request.urlopen(url)
            return response.read()
        except Exception as e:
            print(f"❌ Error getting image: {e}")
            return None

    def get_history(self, prompt_id):
        """Gets prompt execution history"""
        try:
            response = urllib.request.urlopen(f"{self.base_url}/history/{prompt_id}")
            return json.loads(response.read())
        except Exception as e:
            return {}

    def wait_for_completion(self, prompt_id, timeout=300):
        """Waits for generation to complete"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            history = self.get_history(prompt_id)

            if prompt_id in history:
                status = history[prompt_id].get('status', {})

                # Check completion
                if status.get('completed', False):
                    return history[prompt_id]

                # Check errors
                if 'error' in status:
                    raise Exception(f"Generation error: {status['error']}")

            time.sleep(1)

        raise TimeoutError(f"Generation did not complete within {timeout} seconds")

    def generate_image(self, prompt, negative_prompt="blurry, low quality, distorted",
                       width=1024, height=1024, steps=20, cfg=8, seed=None, filename=None):
        """
        Generates image through ComfyUI
        """
        print(f"\n🎨 Generating image through ComfyUI...")
        print(f"📝 Prompt: {prompt[:80]}...")

        # Create workflow
        workflow = self.create_workflow(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            steps=steps,
            cfg=cfg,
            seed=seed
        )

        # Send for generation
        result = self.queue_prompt(workflow)

        if not result:
            return None

        prompt_id = result['prompt_id']
        print(f"🆔 Prompt ID: {prompt_id}")
        print("⏳ Waiting for generation...")

        try:
            # Wait for completion
            history = self.wait_for_completion(prompt_id)

            # Get result
            for node_id in history['outputs']:
                node_output = history['outputs'][node_id]

                if 'images' in node_output:
                    for image in node_output['images']:
                        image_data = self.get_image(
                            image['filename'],
                            image.get('subfolder', ''),
                            image.get('type', 'output')
                        )

                        if image_data:
                            # Save image
                            if filename is None:
                                filename = f"comfy_gen_{int(time.time())}.png"

                            filepath = self.output_dir / filename

                            with open(filepath, 'wb') as f:
                                f.write(image_data)

                            print(f"✅ Image saved: {filepath}")
                            return filepath

            print("❌ Image not found in results")
            return None

        except Exception as e:
            print(f"❌ Error during generation: {e}")
            return None

    def generate_scene_images(self, prompts_data, style="cinematic", project_name="story",
                              width=512, height=512, steps=20, cfg=7):
        """
        Generates images for all scenes
        """
        print(f"\n🎬 Starting generation of {len(prompts_data)} images through ComfyUI...")
        print(f"🎨 Style: {style}")
        print(f"📐 Resolution: {width}x{height}")
        print(f"⚙️  Steps: {steps}, CFG: {cfg}")

        generated_images = []

        # Use one seed for all images (for consistency)
        base_seed = int(time.time() * 1000) % 2 ** 32

        for idx, prompt_info in enumerate(prompts_data, 1):
            print(f"\n{'=' * 60}")
            print(f"Scene {idx}/{len(prompts_data)}")
            print(f"{'=' * 60}")

            prompt = prompt_info.get("prompt", "")
            negative_prompt = prompt_info.get("negative_prompt",
                                              "blurry, low quality, distorted, deformed, ugly, bad anatomy")

            filename = f"{project_name}_scene_{idx:02d}.png"

            # Use different seeds for variety, but close for consistency
            scene_seed = base_seed + idx

            filepath = self.generate_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                steps=steps,
                cfg=cfg,
                seed=scene_seed,
                filename=filename
            )

            if filepath:
                generated_images.append({
                    "scene_number": idx,
                    "filepath": str(filepath),
                    "prompt": prompt
                })

                print(f"✅ Scene {idx} ready")
            else:
                print(f"❌ Error generating scene {idx}")

        print(f"\n{'=' * 60}")
        print(f"✅ Generation complete!")
        print(f"📊 Successful: {len(generated_images)}/{len(prompts_data)}")
        print(f"{'=' * 60}\n")

        return generated_images


# Testing
if __name__ == "__main__":
    print("🧪 Testing ComfyUI generator...\n")

    try:
        # Initialization
        generator = ComfyUIGenerator()

        # Test prompt
        test_prompt = (
            "A lonely robot standing in a post-apocalyptic city ruins, "
            "dramatic sunset, cinematic lighting, highly detailed, masterpiece, 8k"
        )

        test_negative = "blurry, low quality, distorted, ugly, bad anatomy"

        # Generation
        filepath = generator.generate_image(
            prompt=test_prompt,
            negative_prompt=test_negative,
            width=1024,
            height=1024,
            steps=20,
            cfg=8,
            filename="test_comfy.png"
        )

        if filepath:
            print(f"\n✅ TEST PASSED!")
            print(f"📁 Image: {filepath}")
            print(f"\n💡 Also check ComfyUI/output/ - there will be a copy there too")
        else:
            print("\n❌ Generation failed")

    except ConnectionError as e:
        print(f"\n{e}")
        print("\n💡 Start ComfyUI: run_nvidia_gpu.bat")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
