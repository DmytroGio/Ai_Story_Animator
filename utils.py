import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import shutil

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_story_animator.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class ProjectManager:
    """Управление проектами и историей генераций"""

    def __init__(self, base_dir="outputs"):
        self.base_dir = Path(base_dir)
        self.projects_dir = self.base_dir / "projects"
        self.history_file = self.base_dir / "history.json"

        # Создание структуры папок
        self.projects_dir.mkdir(parents=True, exist_ok=True)

        # Загрузка истории
        self.history = self._load_history()

    def _load_history(self) -> List[Dict]:
        """Загружает историю генераций"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Ошибка загрузки истории: {e}")
                return []
        return []

    def _save_history(self):
        """Сохраняет историю генераций"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Ошибка сохранения истории: {e}")

    def create_project(self, story_idea: str, parameters: Dict) -> str:
        """Создаёт новый проект"""
        project_id = f"project_{int(datetime.now().timestamp())}"
        project_dir = self.projects_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        # Сохраняем метаданные
        metadata = {
            "project_id": project_id,
            "story_idea": story_idea,
            "parameters": parameters,
            "created_at": datetime.now().isoformat(),
            "status": "created"
        }

        metadata_file = project_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Создан проект: {project_id}")
        return project_id

    def update_project(self, project_id: str, data: Dict):
        """Обновляет данные проекта"""
        project_dir = self.projects_dir / project_id
        metadata_file = project_dir / "metadata.json"

        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            metadata.update(data)
            metadata['updated_at'] = datetime.now().isoformat()

            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

    def add_to_history(self, project_data: Dict):
        """Добавляет проект в историю"""
        self.history.insert(0, project_data)  # Новые сверху

        # Ограничиваем историю 50 записями
        if len(self.history) > 50:
            self.history = self.history[:50]

        self._save_history()

    def get_history(self, limit: int = 10) -> List[Dict]:
        """Возвращает последние записи истории"""
        return self.history[:limit]

    def get_project_info(self, project_id: str) -> Optional[Dict]:
        """Получает информацию о проекте"""
        project_dir = self.projects_dir / project_id
        metadata_file = project_dir / "metadata.json"

        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def delete_old_projects(self, days: int = 30):
        """Удаляет старые проекты"""
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)

        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir():
                metadata_file = project_dir / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)

                    created_at = datetime.fromisoformat(metadata.get('created_at'))
                    if created_at.timestamp() < cutoff_time:
                        shutil.rmtree(project_dir)
                        logger.info(f"Удалён старый проект: {project_dir.name}")


class StylePresets:
    """Предустановленные стили для генерации"""

    STYLES = {
        "cinematic": {
            "name": "Cinematic",
            "description": "Hollywood movie style with dramatic lighting",
            "sd_suffix": "cinematic lighting, film grain, dramatic composition, high quality, 8k, professional photography",
            "color_grade": "warm",
            "examples": ["epic landscape", "dramatic portrait", "action scene"]
        },
        "anime": {
            "name": "Anime",
            "description": "Japanese animation style",
            "sd_suffix": "anime style, vibrant colors, detailed, studio ghibli inspired, makoto shinkai, high quality illustration",
            "color_grade": "cool",
            "examples": ["magical girl", "mecha battle", "slice of life"]
        },
        "cartoon": {
            "name": "Cartoon",
            "description": "Western animation style",
            "sd_suffix": "cartoon style, bold colors, clean lines, pixar style, disney style, detailed illustration",
            "color_grade": "warm",
            "examples": ["funny character", "adventure", "family friendly"]
        },
        "realistic": {
            "name": "Realistic",
            "description": "Photorealistic imagery",
            "sd_suffix": "photorealistic, ultra detailed, professional photography, 8k resolution, sharp focus",
            "color_grade": "vintage",
            "examples": ["nature photography", "portrait", "architecture"]
        },
        "cyberpunk": {
            "name": "Cyberpunk",
            "description": "Futuristic neon-lit cityscapes",
            "sd_suffix": "cyberpunk style, neon lights, futuristic, dystopian, blade runner inspired, high tech low life, detailed",
            "color_grade": "cyberpunk",
            "examples": ["neon city", "hacker", "android"]
        },
        "fantasy": {
            "name": "Fantasy",
            "description": "Epic fantasy worlds and magic",
            "sd_suffix": "fantasy art, magical, epic, dungeons and dragons style, detailed concept art, dramatic lighting",
            "color_grade": "warm",
            "examples": ["dragon", "wizard", "enchanted forest"]
        },
        "horror": {
            "name": "Horror",
            "description": "Dark and atmospheric horror",
            "sd_suffix": "horror style, dark atmosphere, creepy, ominous, detailed, dramatic shadows, eerie",
            "color_grade": "cool",
            "examples": ["haunted house", "monster", "nightmare"]
        },
        "sci-fi": {
            "name": "Sci-Fi",
            "description": "Science fiction and space exploration",
            "sd_suffix": "sci-fi style, futuristic, space opera, detailed spaceship, alien world, cinematic lighting",
            "color_grade": "cool",
            "examples": ["spaceship", "alien planet", "robot"]
        }
    }

    @classmethod
    def get_style(cls, style_name: str) -> Dict:
        """Получает предустановку стиля"""
        return cls.STYLES.get(style_name, cls.STYLES["cinematic"])

    @classmethod
    def get_all_styles(cls) -> Dict:
        """Возвращает все стили"""
        return cls.STYLES

    @classmethod
    def get_style_names(cls) -> List[str]:
        """Возвращает список названий стилей"""
        return list(cls.STYLES.keys())


class ErrorHandler:
    """Централизованная обработка ошибок"""

    @staticmethod
    def handle_llm_error(error: Exception) -> str:
        """Обработка ошибок LLM"""
        error_msg = str(error)

        if "Connection" in error_msg or "connection" in error_msg:
            return (
                "❌ LM Studio connection error\n\n"
                "Please check:\n"
                "1. LM Studio is running\n"
                "2. Local Server is started (http://localhost:1234)\n"
                "3. Model is loaded\n\n"
                f"Technical details: {error_msg}"
            )
        elif "timeout" in error_msg.lower():
            return (
                "⏱️ LLM request timed out\n\n"
                "The model took too long to respond. Try:\n"
                "1. Reducing the number of scenes\n"
                "2. Simplifying your story idea\n"
                "3. Restarting LM Studio\n\n"
                f"Technical details: {error_msg}"
            )
        else:
            return f"❌ LLM Error: {error_msg}"

    @staticmethod
    def handle_comfy_error(error: Exception) -> str:
        """Обработка ошибок ComfyUI"""
        error_msg = str(error)

        if "Connection" in error_msg or "connection" in error_msg:
            return (
                "❌ ComfyUI connection error\n\n"
                "Please check:\n"
                "1. ComfyUI is running (http://localhost:8188)\n"
                "2. The model is loaded correctly\n"
                "3. No other errors in ComfyUI console\n\n"
                f"Technical details: {error_msg}"
            )
        elif "CUDA" in error_msg or "memory" in error_msg.lower():
            return (
                "💾 GPU memory error\n\n"
                "Try:\n"
                "1. Reduce image resolution (512x512 or lower)\n"
                "2. Reduce number of steps\n"
                "3. Close other GPU applications\n"
                "4. Restart ComfyUI\n\n"
                f"Technical details: {error_msg}"
            )
        else:
            return f"❌ ComfyUI Error: {error_msg}"

    @staticmethod
    def handle_video_error(error: Exception) -> str:
        """Обработка ошибок создания видео"""
        error_msg = str(error)

        if "codec" in error_msg.lower():
            return (
                "🎥 Video codec error\n\n"
                "Try installing ffmpeg:\n"
                "https://ffmpeg.org/download.html\n\n"
                f"Technical details: {error_msg}"
            )
        else:
            return f"❌ Video Error: {error_msg}"


def format_duration(seconds: float) -> str:
    """Форматирует длительность в читаемый вид"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def estimate_generation_time(num_scenes: int, image_time: float = 10) -> str:
    """Оценивает время генерации"""
    total_time = (num_scenes * image_time) + 30  # +30s для LLM и видео
    return format_duration(total_time)


# Инициализация при импорте
project_manager = ProjectManager()