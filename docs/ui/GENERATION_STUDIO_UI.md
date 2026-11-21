# Generation Studio UI Specification: Multimodal AI Router

## 1. Unified Multimodal Generation Interface

The **Generation Studio Interface** provides a single, provider-agnostic dashboard for text, image, video, voice, and music generation:

### Core Controls:
1. **Modality Selector:**
   - Text-to-Video
   - Image-to-Video
   - Video-to-Video
   - Text-to-Image
   - Voice Dubbing / Speech
   - Procedural Music & Sound Effects

2. **Multi-Dimensional Prompt Compiler:**
   - Dedicated structured input fields for:
     - **Subject:** Detailed physical description.
     - **Action:** Movement and dynamics.
     - **Camera:** Framing, focal length, angle, and camera movement.
     - **Lighting:** Key, fill, rim, color temperature, and atmospheric haze.
     - **Mood / Style:** Cinematic, photographic, anime, 3D render.
   - Live compiler preview showing target dialect (e.g. Runway bracketed tags vs Kling motion tags vs FLUX prose).

3. **Provider & Model Selector:**
   - Dynamic dropdown filtered by capability: Runway Gen-3 Alpha, Kling 1.5, Wan2.1, FLUX.1 Dev, ElevenLabs, Mock Local Provider.

4. **Generation Parameters:**
   - Aspect ratio (16:9, 9:16, 1:1, 2.39:1).
   - Resolution (720p, 1080p, 4K).
   - Duration (5s, 10s).
   - Seed value and sampling steps.

5. **Financial Firewall & Cost Safety:**
   - Real-time estimated cost indicator.
   - Warning banner if cost exceeds per-shot budget cap ($1.00) requiring explicit human approval.
   - "Generate" and "Cancel" controls with live job queue progress.
