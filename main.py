import gradio as gr
from pathlib import Path
import json
import time
from datetime import datetime
from llm_generator import LLMGenerator
from image_generator_comfy import ComfyUIGenerator
from video_creator import VideoCreator

from utils import (
    project_manager,
    StylePresets,
    ErrorHandler,
    estimate_generation_time,
    logger
)

# Global variables for components
llm_gen = None
img_gen = None
video_gen = None


def initialize_components():
    """Lazy initialization of components"""
    global llm_gen, img_gen, video_gen

    if llm_gen is None:
        llm_gen = LLMGenerator()
    if img_gen is None:
        img_gen = ComfyUIGenerator()
    if video_gen is None:
        video_gen = VideoCreator(fps=24, transition_duration=1.0)

    return llm_gen, img_gen, video_gen


def generate_story_animation(
        story_idea,
        num_scenes,
        art_style,
        color_grade,
        scene_duration,
        use_ken_burns,
        transition_type,
        image_width,
        image_height,
        sd_steps,
        sd_cfg,
        progress=gr.Progress()
):
    """
    Main generation function with improved error handling
    """
    try:
        # Logging start
        logger.info(f"Starting generation: {story_idea[:50]}...")
        logger.info(f"Parameters: scenes={num_scenes}, style={art_style}")

        # Create project
        project_id = project_manager.create_project(
            story_idea=story_idea,
            parameters={
                "num_scenes": num_scenes,
                "art_style": art_style,
                "color_grade": color_grade,
                "scene_duration": scene_duration,
                "use_ken_burns": use_ken_burns,
                "transition_type": transition_type,
                "resolution": f"{image_width}x{image_height}"
            }
        )

        # Initialization
        progress(0, desc="🎬 Initializing components...")
        llm, img_gen_inst, video_gen_inst = initialize_components()

        total_steps = num_scenes + 2
        current_step = 0
        status_updates = []

        # Time estimation
        estimated_time = estimate_generation_time(num_scenes)
        status_updates.append(f"⏱️ Estimated time: ~{estimated_time}")

        # ========== STAGE 1: LLM ==========
        try:
            progress(current_step / total_steps, desc="📝 Generating story via LLM...")
            status_updates.append("📝 Generating story scenario...")

            story_data = llm.generate_story_scenes(story_idea, num_scenes=num_scenes)

            if not story_data:
                raise Exception("Story generation failed")

            story_title = story_data.get('title', 'Untitled')
            scenes = story_data.get('scenes', [])

            status_updates.append(f"✅ Story ready: '{story_title}'")
            current_step += 1

            # Update project
            project_manager.update_project(project_id, {
                "story_title": story_title,
                "scenes": scenes,
                "status": "story_generated"
            })

        except Exception as e:
            logger.error(f"LLM error: {e}")
            error_msg = ErrorHandler.handle_llm_error(e)
            return None, None, error_msg, json.dumps({"error": str(e)}, indent=2)

        # ========== STAGE 2: Images ==========
        try:
            image_prompts = llm.generate_image_prompts(story_data, style=art_style)
            generated_images = []
            image_files = []

            for idx, prompt_info in enumerate(image_prompts, 1):
                progress(
                    current_step / total_steps,
                    desc=f"🎨 Generating image {idx}/{num_scenes}..."
                )

                status_updates.append(f"🎨 Generating scene {idx}/{num_scenes}...")

                prompt = prompt_info.get("prompt", "")
                negative_prompt = prompt_info.get("negative_prompt", "")
                filename = f"{project_id}_scene_{idx:02d}.png"

                filepath = img_gen_inst.generate_image(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    width=image_width,
                    height=image_height,
                    steps=sd_steps,
                    cfg=sd_cfg,
                    seed=None,
                    filename=filename
                )

                if filepath:
                    generated_images.append({
                        "scene_number": idx,
                        "filepath": str(filepath),
                        "prompt": prompt
                    })
                    image_files.append(str(filepath))
                    status_updates.append(f"✅ Scene {idx} complete")

                current_step += 1

                # Update project status
                yield (
                    image_files,  # Show images as they are generated
                    None,
                    "\n".join(status_updates),
                    json.dumps({"progress": f"{idx}/{num_scenes}"}, indent=2)
                )

            if not generated_images:
                raise Exception("No images generated")

            project_manager.update_project(project_id, {
                "images": generated_images,
                "status": "images_generated"
            })

        except Exception as e:
            logger.error(f"Image generation error: {e}")
            error_msg = ErrorHandler.handle_comfy_error(e)
            return None, None, error_msg, json.dumps({"error": str(e)}, indent=2)

        # ========== STAGE 3: Video ==========
        try:
            progress(current_step / total_steps, desc="🎥 Creating video...")
            status_updates.append("🎥 Creating cinematic video...")

            video_path = video_gen_inst.create_video(
                image_paths=image_files,
                output_filename=f"{project_id}_animation.mp4",
                scene_duration=scene_duration,
                use_ken_burns=use_ken_burns,
                use_color_grade=True,
                color_style=color_grade,
                transition_type=transition_type
            )

            status_updates.append(f"✅ Video ready: {video_path}")

            # Final project update
            project_manager.update_project(project_id, {
                "video_path": str(video_path),
                "status": "completed"
            })

            # Add to history
            project_manager.add_to_history({
                "project_id": project_id,
                "title": story_title,
                "idea": story_idea,
                "scenes_count": num_scenes,
                "style": art_style,
                "video_path": str(video_path),
                "created_at": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Video creation error: {e}")
            error_msg = ErrorHandler.handle_video_error(e)
            return image_files, None, error_msg, json.dumps({"error": str(e)}, indent=2)

        # ========== Result ==========
        progress(1.0, desc="✅ Complete!")

        result_json = {
            "project_id": project_id,
            "title": story_title,
            "scenes": scenes,
            "images_count": len(generated_images),
            "video_path": str(video_path),
            "timestamp": datetime.now().isoformat()
        }

        status_text = "\n".join(status_updates)
        logger.info(f"Generation completed: {project_id}")

        return (
            image_files,
            str(video_path),
            status_text,
            json.dumps(result_json, indent=2)
        )

    except Exception as e:
        logger.error(f"Critical error: {e}")
        error_msg = f"❌ Critical error: {str(e)}\n\nPlease check the logs."
        return None, None, error_msg, json.dumps({"error": str(e)}, indent=2)


def create_ui():
    """
    Creates Gradio interface
    """
    with gr.Blocks(
            title="AI Story Animator",
            theme=gr.themes.Soft(),
            css="""
            .main-header { text-align: center; margin-bottom: 2rem; }
            .generate-btn { font-size: 1.2rem !important; }
            """
    ) as app:

        # Header
        gr.Markdown(
            """
            # 🎬 AI Story Animator
            ### Transform your ideas into animated stories with AI
            
            Generate cinematic animated videos from text descriptions using LLM + ComfyUI
            """,
            elem_classes="main-header"
        )

        with gr.Row():
            # ========== LEFT COLUMN: Settings ==========
            with gr.Column(scale=1):
                gr.Markdown("## ⚙️ Settings")

                # Story
                with gr.Group():
                    gr.Markdown("### 📝 Story")
                    story_input = gr.Textbox(
                        label="💡 Your Story Idea",
                        placeholder="For example: A lonely robot discovers a magical garden in a post-apocalyptic city...",
                        lines=3,
                        value="A lone astronaut discovers an ancient alien temple on Mars"
                    )

                    num_scenes = gr.Slider(
                        label="🎬 Number of Scenes",
                        minimum=2,
                        maximum=10,
                        step=1,
                        value=4,
                        info="More scenes = longer generation"
                    )

                # Art Style
                with gr.Group():
                    gr.Markdown("### 🎨 Visual Style")

                    art_style = gr.Radio(
                        label="Art Style",
                        choices=[
                            "cinematic",
                            "anime",
                            "cartoon",
                            "realistic"
                        ],
                        value="cinematic",
                        info="Scene visualization style"
                    )

                    color_grade = gr.Radio(
                        label="🌈 Color Palette",
                        choices=[
                            "warm",
                            "cool",
                            "vintage",
                            "cyberpunk"
                        ],
                        value="warm",
                        info="Color grading for video"
                    )

                # Video Settings
                with gr.Group():
                    gr.Markdown("### 🎥 Video Parameters")

                    scene_duration = gr.Slider(
                        label="⏱️ Scene duration (seconds)",
                        minimum=2.0,
                        maximum=8.0,
                        step=0.5,
                        value=4.0
                    )

                    use_ken_burns = gr.Checkbox(
                        label="✨ Ken Burns effect (zoom & pan)",
                        value=True,
                        info="Dynamic camera movement"
                    )

                    transition_type = gr.Radio(
                        label="🔄 Transition Type",
                        choices=[
                            "crossfade",
                            "zoom_blur",
                            "wipe_left"
                        ],
                        value="zoom_blur"
                    )

                # Advanced Settings (hidden)
                with gr.Accordion("🔧 Advanced Settings", open=False):
                    image_width = gr.Slider(
                        label="Image Width",
                        minimum=256,
                        maximum=1024,
                        step=128,
                        value=512
                    )

                    image_height = gr.Slider(
                        label="Image Height",
                        minimum=256,
                        maximum=1024,
                        step=128,
                        value=512
                    )

                    sd_steps = gr.Slider(
                        label="SD Steps (quality)",
                        minimum=10,
                        maximum=30,
                        step=5,
                        value=15,
                        info="More = better quality, but slower"
                    )

                    sd_cfg = gr.Slider(
                        label="CFG Scale",
                        minimum=5.0,
                        maximum=15.0,
                        step=0.5,
                        value=7.0,
                        info="How closely to follow the prompt"
                    )

                # Generate button
                generate_btn = gr.Button(
                    "🚀 Create Animation",
                    variant="primary",
                    size="lg"
                )

            # ========== RIGHT COLUMN: Outputs ==========
            with gr.Column(scale=2):
                gr.Markdown("## 📊 Results")

                # Status
                status_output = gr.Textbox(
                    label="📝 Generation Status",
                    lines=8,
                    max_lines=15,
                    interactive=False
                )

                # Tabs with results
                with gr.Tabs():
                    # Tab: Images
                    with gr.Tab("🖼️ Images"):
                        image_gallery = gr.Gallery(
                            label="Generated Scenes",
                            show_label=True,
                            columns=3,
                            rows=2,
                            height="auto",
                            object_fit="contain"
                        )

                    # Tab: Video
                    with gr.Tab("🎥 Video"):
                        video_output = gr.Video(
                            label="Final Animation",
                            show_label=True,
                            height=500
                        )

                        video_download = gr.File(
                            label="📥 Download Video",
                            interactive=False
                        )

                    # Tab: JSON data
                    with gr.Tab("📋 Data"):
                        json_output = gr.Code(
                            label="Metadata (JSON)",
                            language="json",
                            lines=15
                        )

        # Examples
        gr.Markdown("## 💡 Example Ideas")
        gr.Examples(
            examples=[
                ["A robot gardener tends to the last flowers on Earth", 3, "cinematic", "warm"],
                ["A young witch discovers her powers during a magical thunderstorm", 4, "anime", "cool"],
                ["Time traveler witnesses the birth of the universe", 5, "realistic", "cyberpunk"],
                ["A dragon befriends a lonely knight in an enchanted forest", 4, "cartoon", "vintage"],
            ],
            inputs=[story_input, num_scenes, art_style, color_grade],
        )

        # Footer
        gr.Markdown(
            """
            ---
            **📌 Tip:** For best results, use detailed descriptions and 3-5 scenes.

            **⚡ Generation time:** ~2-5 minutes depending on number of scenes.
            """
        )

        # Button handler
        generate_btn.click(
            fn=generate_story_animation,
            inputs=[
                story_input,
                num_scenes,
                art_style,
                color_grade,
                scene_duration,
                use_ken_burns,
                transition_type,
                image_width,
                image_height,
                sd_steps,
                sd_cfg
            ],
            outputs=[
                image_gallery,
                video_output,
                status_output,
                json_output
            ]
        )

    return app


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🎬 AI Story Animator - Web Interface")
    print("=" * 70 + "\n")

    print("🚀 Launching Gradio interface...")
    print("📍 Make sure these are running:")
    print("   - LM Studio (http://localhost:1234)")
    print("   - ComfyUI (http://localhost:8188)")
    print("\n")

    app = create_ui()

    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,  # Set True for public link
        show_error=True,
        quiet=False
    )
