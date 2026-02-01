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

        # Папка для сохранения
        self.output_dir = Path("outputs/images")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Проверка подключения
        self._check_connection()

        print("✅ ComfyUI Generator инициализирован")
        print(f"🌐 Сервер: {self.base_url}")
        print(f"📁 Изображения будут сохранены в: {self.output_dir}")

    def _check_connection(self):
        """Проверка подключения к ComfyUI"""
        try:
            response = requests.get(f"{self.base_url}/system_stats", timeout=5)
            if response.status_code == 200:
                print("✅ ComfyUI сервер доступен")
                return True
            else:
                raise ConnectionError("ComfyUI не отвечает")
        except Exception as e:
            raise ConnectionError(
                f"❌ Не удалось подключиться к ComfyUI на {self.base_url}\n"
                f"Убедитесь, что ComfyUI запущен!\n"
                f"Ошибка: {e}"
            )

    def create_workflow(self, prompt, negative_prompt="", width=1024, height=1024,
                        steps=20, cfg=8, seed=None):
        """
        Создаёт workflow для генерации изображения
        Структура соответствует вашему sdxl_basic.json
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
        """Отправляет workflow на генерацию"""
        p = {"prompt": workflow}
        data = json.dumps(p).encode('utf-8')

        try:
            req = urllib.request.Request(f"{self.base_url}/prompt", data=data)
            req.add_header('Content-Type', 'application/json')
            response = urllib.request.urlopen(req)
            return json.loads(response.read())
        except Exception as e:
            print(f"❌ Ошибка отправки промпта: {e}")
            return None

    def get_image(self, filename, subfolder, folder_type):
        """Получает сгенерированное изображение"""
        try:
            data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
            url_values = urllib.parse.urlencode(data)
            url = f"{self.base_url}/view?{url_values}"

            response = urllib.request.urlopen(url)
            return response.read()
        except Exception as e:
            print(f"❌ Ошибка получения изображения: {e}")
            return None

    def get_history(self, prompt_id):
        """Получает историю выполнения промпта"""
        try:
            response = urllib.request.urlopen(f"{self.base_url}/history/{prompt_id}")
            return json.loads(response.read())
        except Exception as e:
            return {}

    def wait_for_completion(self, prompt_id, timeout=300):
        """Ждёт завершения генерации"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            history = self.get_history(prompt_id)

            if prompt_id in history:
                status = history[prompt_id].get('status', {})

                # Проверка завершения
                if status.get('completed', False):
                    return history[prompt_id]

                # Проверка ошибок
                if 'error' in status:
                    raise Exception(f"Ошибка генерации: {status['error']}")

            time.sleep(1)

        raise TimeoutError(f"Генерация не завершилась за {timeout} секунд")

    def generate_image(self, prompt, negative_prompt="blurry, low quality, distorted",
                       width=1024, height=1024, steps=20, cfg=8, seed=None, filename=None):
        """
        Генерирует изображение через ComfyUI
        """
        print(f"\n🎨 Генерация изображения через ComfyUI...")
        print(f"📝 Промпт: {prompt[:80]}...")

        # Создаём workflow
        workflow = self.create_workflow(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            steps=steps,
            cfg=cfg,
            seed=seed
        )

        # Отправляем на генерацию
        result = self.queue_prompt(workflow)

        if not result:
            return None

        prompt_id = result['prompt_id']
        print(f"🆔 Prompt ID: {prompt_id}")
        print("⏳ Ожидание генерации...")

        try:
            # Ждём завершения
            history = self.wait_for_completion(prompt_id)

            # Получаем результат
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
                            # Сохраняем изображение
                            if filename is None:
                                filename = f"comfy_gen_{int(time.time())}.png"

                            filepath = self.output_dir / filename

                            with open(filepath, 'wb') as f:
                                f.write(image_data)

                            print(f"✅ Изображение сохранено: {filepath}")
                            return filepath

            print("❌ Изображение не найдено в результатах")
            return None

        except Exception as e:
            print(f"❌ Ошибка во время генерации: {e}")
            return None

    def generate_scene_images(self, prompts_data, style="cinematic", project_name="story",
                              width=512, height=512, steps=20, cfg=7):
        """
        Генерирует изображения для всех сцен
        """
        print(f"\n🎬 Начало генерации {len(prompts_data)} изображений через ComfyUI...")
        print(f"🎨 Стиль: {style}")
        print(f"📐 Разрешение: {width}x{height}")
        print(f"⚙️  Steps: {steps}, CFG: {cfg}")

        generated_images = []

        # Используем один seed для всех изображений (для consistency)
        base_seed = int(time.time() * 1000) % 2 ** 32

        for idx, prompt_info in enumerate(prompts_data, 1):
            print(f"\n{'=' * 60}")
            print(f"Сцена {idx}/{len(prompts_data)}")
            print(f"{'=' * 60}")

            prompt = prompt_info.get("prompt", "")
            negative_prompt = prompt_info.get("negative_prompt",
                                              "blurry, low quality, distorted, deformed, ugly, bad anatomy")

            filename = f"{project_name}_scene_{idx:02d}.png"

            # Используем разные seeds для разнообразия, но близкие для consistency
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

                print(f"✅ Сцена {idx} готова")
            else:
                print(f"❌ Ошибка генерации сцены {idx}")

        print(f"\n{'=' * 60}")
        print(f"✅ Генерация завершена!")
        print(f"📊 Успешно: {len(generated_images)}/{len(prompts_data)}")
        print(f"{'=' * 60}\n")

        return generated_images


# Тестирование
if __name__ == "__main__":
    print("🧪 Тестирование ComfyUI генератора...\n")

    try:
        # Инициализация
        generator = ComfyUIGenerator()

        # Тестовый промпт
        test_prompt = (
            "A lonely robot standing in a post-apocalyptic city ruins, "
            "dramatic sunset, cinematic lighting, highly detailed, masterpiece, 8k"
        )

        test_negative = "blurry, low quality, distorted, ugly, bad anatomy"

        # Генерация
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
            print(f"\n✅ ТЕСТ ПРОЙДЕН!")
            print(f"📁 Изображение: {filepath}")
            print(f"\n💡 Проверьте также ComfyUI/output/ - там тоже будет копия")
        else:
            print("\n❌ Генерация не удалась")

    except ConnectionError as e:
        print(f"\n{e}")
        print("\n💡 Запустите ComfyUI: run_nvidia_gpu.bat")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback

        traceback.print_exc()