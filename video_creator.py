import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict
import random


class VideoCreator:
    def __init__(self, fps=24, transition_duration=1.0):
        """
        Initialize video creator with advanced effects

        Args:
            fps (int): Frames per second (24-30 for cinematic feel)
            transition_duration (float): Transition duration in seconds
        """
        self.fps = fps
        self.transition_duration = transition_duration
        self.transition_frames = int(fps * transition_duration)

        # Save folder
        self.output_dir = Path("outputs/videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print("✅ VideoCreator initialized")
        print(f"🎬 FPS: {self.fps}")
        print(f"⏱️  Transition duration: {self.transition_duration}s")
        print(f"📁 Videos will be saved to: {self.output_dir}")

    def load_image(self, image_path):
        """Loads and checks image"""
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Failed to load image: {image_path}")
        return img

    def resize_to_match(self, images, target_size=None):
        """
        Resizes all images to same size
        """
        if not images:
            return images

        if target_size is None:
            target_height, target_width = images[0].shape[:2]
        else:
            target_width, target_height = target_size

        print(f"📐 Target resolution: {target_width}x{target_height}")

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
        Ken Burns effect - slow zoom and pan

        Args:
            img: Source image
            num_frames: Number of frames
            zoom_direction: 'in' (zoom in) or 'out' (zoom out)
            zoom_amount: Zoom factor (1.0-1.5)
            pan_direction: None, 'left', 'right', 'up', 'down'
        """
        height, width = img.shape[:2]
        frames = []

        for i in range(num_frames):
            t = i / (num_frames - 1) if num_frames > 1 else 0

            # Smooth interpolation (ease-in-out)
            t_smooth = t * t * (3 - 2 * t)

            # Calculate zoom
            if zoom_direction == 'in':
                scale = 1.0 + (zoom_amount - 1.0) * t_smooth
            else:  # out
                scale = zoom_amount - (zoom_amount - 1.0) * t_smooth

            # New dimensions
            new_width = int(width * scale)
            new_height = int(height * scale)

            # Resize image
            resized = cv2.resize(img, (new_width, new_height),
                                 interpolation=cv2.INTER_LANCZOS4)

            # Calculate pan offset
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
                # Center
                pan_x = (new_width - width) // 2
                pan_y = (new_height - height) // 2

            # Crop frame
            cropped = resized[pan_y:pan_y + height, pan_x:pan_x + width]

            # Size check
            if cropped.shape[:2] != (height, width):
                cropped = cv2.resize(cropped, (width, height))

            frames.append(cropped)

        return frames

    def apply_parallax_effect(self, img, num_frames, depth_map=None):
        """
        Parallax effect - depth simulation
        """
        height, width = img.shape[:2]
        frames = []

        # Simple depth map (center closer, edges farther)
        if depth_map is None:
            y, x = np.ogrid[:height, :width]
            center_y, center_x = height // 2, width // 2
            depth_map = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
            depth_map = 1 - (depth_map / depth_map.max())

        for i in range(num_frames):
            t = i / (num_frames - 1) if num_frames > 1 else 0
            t_smooth = t * t * (3 - 2 * t)

            # Offset based on depth
            shift_amount = 10 * t_smooth

            # Create displacement map
            map_x = np.zeros((height, width), dtype=np.float32)
            map_y = np.zeros((height, width), dtype=np.float32)

            for y in range(height):
                for x in range(width):
                    offset = depth_map[y, x] * shift_amount
                    map_x[y, x] = x + offset
                    map_y[y, x] = y

            # Apply remap
            frame = cv2.remap(img, map_x, map_y, cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_REFLECT)
            frames.append(frame)

        return frames

    def apply_cinematic_color_grade(self, img, style='warm'):
        """
        Applies cinematic color grading

        Args:
            style: 'warm', 'cool', 'vintage', 'cyberpunk'
        """
        img_float = img.astype(np.float32) / 255.0

        if style == 'warm':
            # Warm tones (orange/yellow)
            img_float[:, :, 0] *= 0.9  # Less blue
            img_float[:, :, 1] *= 1.05  # More green
            img_float[:, :, 2] *= 1.1  # More red

        elif style == 'cool':
            # Cool tones (blue/cyan)
            img_float[:, :, 0] *= 1.2  # More blue
            img_float[:, :, 1] *= 1.0
            img_float[:, :, 2] *= 0.9  # Less red

        elif style == 'vintage':
            # Vintage look (faded colors)
            img_float = img_float * 0.8 + 0.2
            img_float[:, :, 1] *= 0.95

        elif style == 'cyberpunk':
            # Cyberpunk (neon, contrast)
            img_float = np.power(img_float, 1.2)
            img_float[:, :, 0] *= 1.3
            img_float[:, :, 2] *= 1.2

        # Slight vignette
        height, width = img.shape[:2]
        y, x = np.ogrid[:height, :width]
        center_y, center_x = height // 2, width // 2

        vignette = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
        vignette = 1 - (vignette / vignette.max()) * 0.3

        for c in range(3):
            img_float[:, :, c] *= vignette

        # Back to uint8
        img_float = np.clip(img_float, 0, 1)
        return (img_float * 255).astype(np.uint8)

    def create_dynamic_transition(self, img1, img2, num_frames, transition_type='crossfade'):
        """
        Advanced transitions between frames

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

                # Blur first image
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
        Creates cinematic video with effects
        """
        print(f"\n🎬 Creating cinematic video from {len(image_paths)} images...")
        print(f"⏱️  Scene duration: {scene_duration}s")
        print(f"🎨 Ken Burns: {'✅' if use_ken_burns else '❌'}")
        print(f"🌈 Color Grade: {color_style if use_color_grade else '❌'}")
        print(f"🔄 Transitions: {transition_type}")

        # Loading images
        images = []
        for i, path in enumerate(image_paths, 1):
            print(f"📸 Loading {i}/{len(image_paths)}: {Path(path).name}")
            img = self.load_image(path)

            # Color grading
            if use_color_grade:
                img = self.apply_cinematic_color_grade(img, style=color_style)

            images.append(img)

        # Resize to match
        images = self.resize_to_match(images)

        # Prepare video
        height, width = images[0].shape[:2]
        output_path = self.output_dir / output_filename

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(
            str(output_path), fourcc, self.fps, (width, height)
        )

        total_frames = 0
        scene_frames = int(self.fps * scene_duration)

        # Random directions for Ken Burns
        kb_directions = [
            ('in', 'left'),
            ('in', 'right'),
            ('out', None),
            ('in', 'up'),
            ('in', 'down')
        ]

        print(f"\n🎞️  Generating frames with effects...")

        for i, img in enumerate(images):
            print(f"  🎬 Scene {i + 1}:")

            # Ken Burns effect
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

            # Write scene frames
            for frame in scene_frames_list:
                video_writer.write(frame)
                total_frames += 1

            # Transition
            if i < len(images) - 1:
                print(f"    - Transition {i + 1}→{i + 2}: {transition_type}")
                transition_frames = self.create_dynamic_transition(
                    img, images[i + 1], self.transition_frames, transition_type
                )

                for frame in transition_frames:
                    video_writer.write(frame)
                    total_frames += 1

        video_writer.release()

        duration = total_frames / self.fps

        print(f"\n{'=' * 60}")
        print(f"✅ Cinematic video created!")
        print(f"{'=' * 60}")
        print(f"📁 File: {output_path}")
        print(f"📊 Statistics:")
        print(f"  - Resolution: {width}x{height}")
        print(f"  - Frames: {total_frames}")
        print(f"  - Duration: {duration:.2f}s")
        print(f"  - FPS: {self.fps}")
        print(f"{'=' * 60}\n")

        return output_path


# Testing
if __name__ == "__main__":
    print("🎥 Testing cinematic VideoCreator...\n")

    # Initialization (increased FPS for smoothness)
    video_creator = VideoCreator(fps=24, transition_duration=1.0)

    images_dir = Path("outputs/images")

    if not images_dir.exists():
        print("❌ Folder outputs/images not found")
    else:
        image_files = sorted(images_dir.glob("mars_temple_scene_*.png"))

        if not image_files:
            print("❌ Images not found")
        else:
            print(f"✅ Found {len(image_files)} images\n")

            # Create cinematic video
            video_path = video_creator.create_video(
                image_paths=image_files,
                output_filename="cinematic_animation.mp4",
                scene_duration=4.0,
                use_ken_burns=True,
                use_color_grade=True,
                color_style='warm',  # 'warm', 'cool', 'vintage', 'cyberpunk'
                transition_type='zoom_blur'  # 'crossfade', 'zoom_blur', 'wipe_left'
            )

            print(f"🎉 Done!")
            print(f"📺 Open: {video_path}")
