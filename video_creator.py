import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict
import random


class VideoCreator:
    def __init__(self, fps=24, transition_duration=1.0):
        """
        Инициализация создателя видео с продвинутыми эффектами

        Args:
            fps (int): Кадров в секунду (24-30 для кинематографичности)
            transition_duration (float): Длительность перехода в секундах
        """
        self.fps = fps
        self.transition_duration = transition_duration
        self.transition_frames = int(fps * transition_duration)

        # Папка для сохранения
        self.output_dir = Path("outputs/videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print("✅ VideoCreator инициализирован")
        print(f"🎬 FPS: {self.fps}")
        print(f"⏱️  Длительность перехода: {self.transition_duration}s")
        print(f"📁 Видео будут сохранены в: {self.output_dir}")

    def load_image(self, image_path):
        """Загружает и проверяет изображение"""
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Не удалось загрузить изображение: {image_path}")
        return img

    def resize_to_match(self, images, target_size=None):
        """
        Приводит все изображения к одному размеру
        """
        if not images:
            return images

        if target_size is None:
            target_height, target_width = images[0].shape[:2]
        else:
            target_width, target_height = target_size

        print(f"📐 Целевое разрешение: {target_width}x{target_height}")

        resized = []
        for img in images:
            if img.shape[:2] != (target_height, target_width):
                img = cv2.resize(img, (target_width, target_height),
                                 interpolation=cv2.INTER_LANCZOS4)
            resized.append(img)

        return resized

    def apply_ken_burns(self, img, num_frames, zoom_direction='in',
                        zoom_amount=1.2, pan_direction=None):
        """
        Эффект Ken Burns - медленный zoom и pan

        Args:
            img: Исходное изображение
            num_frames: Количество кадров
            zoom_direction: 'in' (приближение) или 'out' (удаление)
            zoom_amount: Коэффициент увеличения (1.0-1.5)
            pan_direction: None, 'left', 'right', 'up', 'down'
        """
        height, width = img.shape[:2]
        frames = []

        for i in range(num_frames):
            t = i / (num_frames - 1) if num_frames > 1 else 0

            # Плавная интерполяция (ease-in-out)
            t_smooth = t * t * (3 - 2 * t)

            # Вычисляем zoom
            if zoom_direction == 'in':
                scale = 1.0 + (zoom_amount - 1.0) * t_smooth
            else:  # out
                scale = zoom_amount - (zoom_amount - 1.0) * t_smooth

            # Новые размеры
            new_width = int(width * scale)
            new_height = int(height * scale)

            # Увеличиваем изображение
            resized = cv2.resize(img, (new_width, new_height),
                                 interpolation=cv2.INTER_LANCZOS4)

            # Вычисляем pan offset
            pan_x = 0
            pan_y = 0

            if pan_direction == 'left':
                pan_x = int((new_width - width) * t_smooth)
            elif pan_direction == 'right':
                pan_x = int((new_width - width) * (1 - t_smooth))
            elif pan_direction == 'up':
                pan_y = int((new_height - height) * t_smooth)
            elif pan_direction == 'down':
                pan_y = int((new_height - height) * (1 - t_smooth))
            else:
                # Центрирование
                pan_x = (new_width - width) // 2
                pan_y = (new_height - height) // 2

            # Обрезаем кадр
            cropped = resized[pan_y:pan_y + height, pan_x:pan_x + width]

            # Проверка размера
            if cropped.shape[:2] != (height, width):
                cropped = cv2.resize(cropped, (width, height))

            frames.append(cropped)

        return frames

    def apply_parallax_effect(self, img, num_frames, depth_map=None):
        """
        Эффект параллакса - имитация глубины
        """
        height, width = img.shape[:2]
        frames = []

        # Простой depth map (центр ближе, края дальше)
        if depth_map is None:
            y, x = np.ogrid[:height, :width]
            center_y, center_x = height // 2, width // 2
            depth_map = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
            depth_map = 1 - (depth_map / depth_map.max())

        for i in range(num_frames):
            t = i / (num_frames - 1) if num_frames > 1 else 0
            t_smooth = t * t * (3 - 2 * t)

            # Смещение на основе глубины
            shift_amount = 10 * t_smooth

            # Создаём карту смещения
            map_x = np.zeros((height, width), dtype=np.float32)
            map_y = np.zeros((height, width), dtype=np.float32)

            for y in range(height):
                for x in range(width):
                    offset = depth_map[y, x] * shift_amount
                    map_x[y, x] = x + offset
                    map_y[y, x] = y

            # Применяем remap
            frame = cv2.remap(img, map_x, map_y, cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_REFLECT)
            frames.append(frame)

        return frames

    def apply_cinematic_color_grade(self, img, style='warm'):
        """
        Применяет кинематографическую цветокоррекцию

        Args:
            style: 'warm', 'cool', 'vintage', 'cyberpunk'
        """
        img_float = img.astype(np.float32) / 255.0

        if style == 'warm':
            # Тёплые тона (оранжевый/жёлтый)
            img_float[:, :, 0] *= 0.9  # Меньше синего
            img_float[:, :, 1] *= 1.05  # Больше зелёного
            img_float[:, :, 2] *= 1.1  # Больше красного

        elif style == 'cool':
            # Холодные тона (синий/голубой)
            img_float[:, :, 0] *= 1.2  # Больше синего
            img_float[:, :, 1] *= 1.0
            img_float[:, :, 2] *= 0.9  # Меньше красного

        elif style == 'vintage':
            # Винтажный вид (выцветшие цвета)
            img_float = img_float * 0.8 + 0.2
            img_float[:, :, 1] *= 0.95

        elif style == 'cyberpunk':
            # Киберпанк (неон, контраст)
            img_float = np.power(img_float, 1.2)
            img_float[:, :, 0] *= 1.3
            img_float[:, :, 2] *= 1.2

        # Небольшое виньетирование
        height, width = img.shape[:2]
        y, x = np.ogrid[:height, :width]
        center_y, center_x = height // 2, width // 2

        vignette = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
        vignette = 1 - (vignette / vignette.max()) * 0.3

        for c in range(3):
            img_float[:, :, c] *= vignette

        # Обратно в uint8
        img_float = np.clip(img_float, 0, 1)
        return (img_float * 255).astype(np.uint8)

    def create_dynamic_transition(self, img1, img2, num_frames, transition_type='crossfade'):
        """
        Продвинутые переходы между кадрами

        Types: 'crossfade', 'wipe_left', 'wipe_right', 'zoom_blur', 'rotate'
        """
        frames = []

        if transition_type == 'crossfade':
            for i in range(num_frames):
                t = i / (num_frames - 1) if num_frames > 1 else 1
                alpha = t * t * (3 - 2 * t)  # smooth
                blended = cv2.addWeighted(img1, 1 - alpha, img2, alpha, 0)
                frames.append(blended)

        elif transition_type == 'wipe_left':
            width = img1.shape[1]
            for i in range(num_frames):
                t = i / (num_frames - 1) if num_frames > 1 else 1
                wipe_x = int(width * t)
                frame = img1.copy()
                frame[:, :wipe_x] = img2[:, :wipe_x]
                frames.append(frame)

        elif transition_type == 'zoom_blur':
            for i in range(num_frames):
                t = i / (num_frames - 1) if num_frames > 1 else 1

                # Blur первого изображения
                blur_amount = int(15 * (1 - abs(t - 0.5) * 2))
                if blur_amount > 0 and blur_amount % 2 == 0:
                    blur_amount += 1

                if blur_amount > 0:
                    img1_blur = cv2.GaussianBlur(img1, (blur_amount, blur_amount), 0)
                else:
                    img1_blur = img1

                alpha = t * t * (3 - 2 * t)
                blended = cv2.addWeighted(img1_blur, 1 - alpha, img2, alpha, 0)
                frames.append(blended)

        return frames

    def create_video(self, image_paths, output_filename="story_animation.mp4",
                     scene_duration=4.0, use_ken_burns=True,
                     use_color_grade=True, color_style='warm',
                     transition_type='zoom_blur'):
        """
        Создаёт кинематографическое видео с эффектами
        """
        print(f"\n🎬 Создание кинематографического видео из {len(image_paths)} изображений...")
        print(f"⏱️  Длительность сцены: {scene_duration}s")
        print(f"🎨 Ken Burns: {'✅' if use_ken_burns else '❌'}")
        print(f"🌈 Color Grade: {color_style if use_color_grade else '❌'}")
        print(f"🔄 Переходы: {transition_type}")

        # Загрузка изображений
        images = []
        for i, path in enumerate(image_paths, 1):
            print(f"📸 Загрузка {i}/{len(image_paths)}: {Path(path).name}")
            img = self.load_image(path)

            # Цветокоррекция
            if use_color_grade:
                img = self.apply_cinematic_color_grade(img, style=color_style)

            images.append(img)

        # Приведение к размеру
        images = self.resize_to_match(images)

        # Подготовка видео
        height, width = images[0].shape[:2]
        output_path = self.output_dir / output_filename

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(
            str(output_path), fourcc, self.fps, (width, height)
        )

        total_frames = 0
        scene_frames = int(self.fps * scene_duration)

        # Случайные направления для Ken Burns
        kb_directions = [
            ('in', 'left'),
            ('in', 'right'),
            ('out', None),
            ('in', 'up'),
            ('in', 'down')
        ]

        print(f"\n🎞️  Генерация кадров с эффектами...")

        for i, img in enumerate(images):
            print(f"  🎬 Сцена {i + 1}:")

            # Ken Burns эффект
            if use_ken_burns:
                zoom_dir, pan_dir = random.choice(kb_directions)
                print(f"    - Ken Burns: zoom={zoom_dir}, pan={pan_dir}")
                scene_frames_list = self.apply_ken_burns(
                    img, scene_frames,
                    zoom_direction=zoom_dir,
                    pan_direction=pan_dir,
                    zoom_amount=1.15
                )
            else:
                scene_frames_list = [img] * scene_frames

            # Запись кадров сцены
            for frame in scene_frames_list:
                video_writer.write(frame)
                total_frames += 1

            # Переход
            if i < len(images) - 1:
                print(f"    - Переход {i + 1}→{i + 2}: {transition_type}")
                transition_frames = self.create_dynamic_transition(
                    img, images[i + 1], self.transition_frames, transition_type
                )

                for frame in transition_frames:
                    video_writer.write(frame)
                    total_frames += 1

        video_writer.release()

        duration = total_frames / self.fps

        print(f"\n{'=' * 60}")
        print(f"✅ Кинематографическое видео создано!")
        print(f"{'=' * 60}")
        print(f"📁 Файл: {output_path}")
        print(f"📊 Статистика:")
        print(f"  - Разрешение: {width}x{height}")
        print(f"  - Кадров: {total_frames}")
        print(f"  - Длительность: {duration:.2f}s")
        print(f"  - FPS: {self.fps}")
        print(f"{'=' * 60}\n")

        return output_path


# Тестирование
if __name__ == "__main__":
    print("🎥 Тестирование кинематографического VideoCreator...\n")

    # Инициализация (увеличили FPS для плавности)
    video_creator = VideoCreator(fps=24, transition_duration=1.0)

    images_dir = Path("outputs/images")

    if not images_dir.exists():
        print("❌ Папка outputs/images не найдена")
    else:
        image_files = sorted(images_dir.glob("mars_temple_scene_*.png"))

        if not image_files:
            print("❌ Изображения не найдены")
        else:
            print(f"✅ Найдено {len(image_files)} изображений\n")

            # Создаём кинематографическое видео
            video_path = video_creator.create_video(
                image_paths=image_files,
                output_filename="cinematic_animation.mp4",
                scene_duration=4.0,
                use_ken_burns=True,
                use_color_grade=True,
                color_style='warm',  # 'warm', 'cool', 'vintage', 'cyberpunk'
                transition_type='zoom_blur'  # 'crossfade', 'zoom_blur', 'wipe_left'
            )

            print(f"🎉 Готово!")
            print(f"📺 Откройте: {video_path}")