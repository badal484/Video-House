# AI Video Generation Workflows
**Project:** Universal AI Video Production Studio  
**Department:** 15_ai_generation  
**Document:** VIDEO_GENERATION_WORKFLOWS.md  
**Version:** 1.0.0  

---

## 1. Core Video Generation Workflows

Department 15 provides five standardized video production pipelines:

### 1.1 Text-to-Video (T2V)
- Takes structured prompt from Prompt Compiler.
- Submits to Runway Gen-3, Kling, or Wan2.1.
- Generates 5s to 10s video master clip at 24/30 fps.

### 1.2 Image-to-Video (I2V)
- Conditioned on a hero concept image (e.g. from FLUX.1 Pro or approved storyboard frame).
- Preserves the exact initial frame composition while generating downstream temporal motion.

### 1.3 First-Frame & Last-Frame (Interpolative Generation)
- Conditioned on both an opening keyframe image and a concluding keyframe image.
- Model synthesizes the continuous camera motion and scene transformation bridging the two states.

### 1.4 Reference-Guided Video Generation
- Ingests a character turnaround sheet or style reference image.
- Cross-attends to the character reference to preserve facial geometry and costume while following new prompt actions.

### 1.5 Video Extension
- Takes an existing 5-second video clip and generates an extended 5-second continuation maintaining momentum and narrative continuity.
