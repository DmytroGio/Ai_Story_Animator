# 🎬 AI Story Animator

> Transform your story ideas into cinematic animations powered by AI

An end-to-end AI pipeline that converts text prompts into professional animated videos using **LM Studio (LLM)**, **ComfyUI (Stable Diffusion)**, and **OpenCV** for video processing.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

---

## ✨ Features

- 🤖 **AI-Powered Storytelling** - LLM generates complete story scenarios with scene descriptions
- 🎨 **8 Artistic Styles** - Cinematic, Anime, Cartoon, Realistic, Cyberpunk, Fantasy, Horror, Sci-Fi
- 🎥 **Cinematic Effects** - Ken Burns zoom & pan, smooth transitions, color grading
- 🌐 **Web Interface** - Beautiful Gradio UI with real-time progress tracking
- 📊 **Project Management** - Automatic saving, history tracking, and metadata
- ⚡ **Optimized Performance** - Efficient SD 1.5 generation (5-15s per image)
- 🎬 **Professional Output** - 24 FPS videos with multiple transition types

---

## 🎯 Demo

**Input:** "A lonely robot discovers a magical garden in a post-apocalyptic city"

**Output:** 
- 4 AI-generated scenes with consistent visual style
- 20-second cinematic video with smooth transitions
- Automatic color grading and camera movement

---

## 🏗️ Architecture

```
User Input (Story Idea)
    ↓
LM Studio (LLM) → Story Scenario Generation
    ↓
ComfyUI (Stable Diffusion) → Image Generation (per scene)
    ↓
VideoCreator (OpenCV) → Cinematic Video Assembly
    ↓
Final MP4 Animation
```

---

## 📋 Requirements

### System Requirements
- **OS:** Windows 10/11, Linux, macOS
- **GPU:** NVIDIA GPU with 6GB+ VRAM (recommended)
- **RAM:** 16GB minimum
- **Storage:** 10GB free space

### Software Dependencies
- **Python 3.10+**
- **LM Studio** - Local LLM inference
- **ComfyUI** - Stable Diffusion interface
- **Git** (for cloning)

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/AI_Story_Animator.git
cd AI_Story_Animator
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install LM Studio

1. Download from [https://lmstudio.ai/](https://lmstudio.ai/)
2. Install and launch
3. Download a model (recommended: **Mistral-7B-Instruct** or **Llama 3.2**)
4. Start **Local Server** on port `1234`

### 5. Install ComfyUI

**Option A: Portable (Windows)**
1. Download from [ComfyUI Releases](https://github.com/comfyanonymous/ComfyUI/releases)
2. Extract to a folder
3. Download **SD 1.5** model: [v1-5-pruned-emaonly.safetensors](https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors)
4. Place in `ComfyUI/models/checkpoints/`
5. Run `run_nvidia_gpu.bat`

**Option B: Git Clone**
```bash
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
pip install -r requirements.txt
python main.py
```

ComfyUI should run on `http://localhost:8188`

### 6. Configure Environment

Create `.env` file:

```env
# LM Studio
LM_STUDIO_URL=http://localhost:1234/v1
LM_STUDIO_API_KEY=lm-studio

# ComfyUI
COMFY_SERVER=127.0.0.1:8188
COMFY_MODEL=v1-5-pruned-emaonly.safetensors

# Generation Settings
DEFAULT_TEMPERATURE=0.8
MAX_TOKENS=1500
SD_WIDTH=512
SD_HEIGHT=512
SD_NUM_INFERENCE_STEPS=15
SD_GUIDANCE_SCALE=7.0
```

---

## 🎮 Usage

### Web Interface (Recommended)

1. **Start all services:**
   ```bash
   # Terminal 1: LM Studio
   # Open LM Studio → Local Server → Start Server
   
   # Terminal 2: ComfyUI
   cd ComfyUI
   run_nvidia_gpu.bat  # or python main.py
   
   # Terminal 3: AI Story Animator
   cd AI_Story_Animator
   python main.py
   ```

2. **Open browser:** `http://127.0.0.1:7860`

3. **Create animation:**
   - Enter your story idea
   - Choose number of scenes (3-5 recommended)
   - Select art style and color palette
   - Click "🚀 Create Animation"
   - Wait 2-5 minutes
   - Download your video!

### Command Line

```python
from full_pipeline import AIStoryAnimator

animator = AIStoryAnimator()

result = animator.create_story_animation(
    story_idea="A dragon befriends a lonely knight",
    num_scenes=4,
    style='fantasy',
    color_grade='warm',
    scene_duration=4.0
)

print(f"Video saved: {result['video_path']}")
```

---

## 🎨 Art Styles

| Style | Description | Best For |
|-------|-------------|----------|
| **Cinematic** | Hollywood movie aesthetic | Dramatic scenes, landscapes |
| **Anime** | Japanese animation style | Character-focused stories |
| **Cartoon** | Western animation | Fun, family-friendly content |
| **Realistic** | Photorealistic imagery | Documentary-style narratives |
| **Cyberpunk** | Neon-lit futuristic cities | Sci-fi dystopian themes |
| **Fantasy** | Epic magical worlds | Dragons, wizards, adventure |
| **Horror** | Dark atmospheric scenes | Creepy, suspenseful stories |
| **Sci-Fi** | Space exploration & tech | Spaceships, alien worlds |

---

## 📊 Configuration

### Video Settings

```python
# In main.py or full_pipeline.py
video_creator = VideoCreator(
    fps=24,                    # Frames per second (24 for cinematic)
    transition_duration=1.0    # Transition length in seconds
)

# Generation parameters
scene_duration=4.0             # How long each scene is shown
use_ken_burns=True            # Enable camera movement
transition_type='zoom_blur'   # 'crossfade', 'zoom_blur', 'wipe_left'
```

### Image Quality

```python
# In image_generator_comfy.py
width=512                      # Image width (512-1024)
height=512                     # Image height (512-1024)
steps=15                       # SD steps (10-30, higher = better quality)
cfg=7.0                       # Guidance scale (5-15)
```

---

## 📁 Project Structure

```
AI_Story_Animator/
├── main.py                    # Gradio web interface
├── full_pipeline.py           # Complete automation pipeline
├── llm_generator.py           # LLM story generation
├── image_generator_comfy.py   # ComfyUI integration
├── video_creator.py           # Video assembly with effects
├── utils.py                   # Helper functions & presets
├── requirements.txt           # Python dependencies
├── .env                       # Configuration (create this)
├── outputs/
│   ├── images/               # Generated scene images
│   ├── videos/               # Final animations
│   └── projects/             # Project metadata & history
└── README.md
```

---

## 🔧 Troubleshooting

### LM Studio Connection Error
```
❌ LM Studio connection error
```
**Solution:**
- Ensure LM Studio is running
- Check Local Server is started on port 1234
- Verify model is loaded

### ComfyUI Not Responding
```
❌ ComfyUI connection error
```
**Solution:**
- Restart ComfyUI
- Check `http://localhost:8188` opens in browser
- Ensure model is in `ComfyUI/models/checkpoints/`

### GPU Memory Error
```
💾 GPU memory error
```
**Solution:**
- Reduce image resolution (512x512 or 480x480)
- Lower SD steps to 10-12
- Close other GPU applications
- Use smaller batch sizes

### Slow Generation
- Use **SD 1.5** instead of SDXL (3-4x faster)
- Reduce number of scenes
- Lower steps to 12-15
- Decrease resolution to 512x512

---

## 🎓 Examples

### Example 1: Fantasy Adventure
```python
story_idea = "A young wizard discovers an ancient spellbook in a forgotten library"
style = "fantasy"
num_scenes = 5
```

### Example 2: Sci-Fi Exploration
```python
story_idea = "An astronaut finds evidence of alien life on a distant moon"
style = "sci-fi"
num_scenes = 4
```

### Example 3: Anime Drama
```python
story_idea = "A magical girl faces her greatest challenge during a thunderstorm"
style = "anime"
num_scenes = 3
```

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **LM Studio** - Local LLM inference
- **ComfyUI** - Stable Diffusion interface
- **Stability AI** - Stable Diffusion models
- **Gradio** - Web interface framework
- **OpenCV** - Video processing

---

## 📧 Contact

**Your Name**  
- GitHub: [@DmytroGio](https://github.com/DmytroGio)
---

## ⭐ Star History

If you find this project useful, please consider giving it a star! ⭐

---

**Made with ❤️ and AI**
