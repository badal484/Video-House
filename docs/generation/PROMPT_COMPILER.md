# Structured Prompt Compilation Engine
**Project:** Universal AI Video Production Studio  
**Department:** 15_ai_generation  
**Document:** PROMPT_COMPILER.md  
**Version:** 1.0.0  

---

## 1. Architectural Purpose

Unstructured natural language prompts fail frequently in production because different AI models expect completely different syntax, token weightings, and camera descriptors.
- **Midjourney**: Expects comma-separated descriptors, `--ar 16:9`, `--v 6.1`, `--style raw`.
- **Runway Gen-3**: Expects structured camera motion brackets `[Camera: Pan Right, Wide Shot, 35mm lens]`, lighting descriptors, and action verbs.
- **Kling 1.5**: Expects natural Chinese/English descriptive sentences detailing subject motion and physical interactions.
- **FLUX.1**: Expects natural English prose describing fine textural details, atmospheric lighting, and accurate spatial arrangements.

The **Prompt Compiler** decomposes a creative shot request into structured dimensions and translates them into provider-tailored prompt payloads while archiving the original creative intent.

---

## 2. Structured Dimension Model

```python
class StructuredPromptDimensions(BaseModel):
    subject: str                      # "Cyberpunk courier"
    character_identity: str           # "Captain Maya Lin, braided dark hair, scar"
    action: str                       # "dashes through neon-lit alleyway in heavy rain"
    environment: str                  # "dense dystopian metropolis, towering skyscrapers"
    composition: str                  # "low angle medium shot, rule of thirds"
    camera_movement: str              # "tracking dolly forward following subject"
    lens: str                         # "anamorphic 35mm lens, shallow depth of field"
    lighting: str                     # "high contrast volumetric neon backlight"
    visual_style: str                 # "photorealistic 35mm film grain, cinematic"
    color_palette: str                # "teal and orange, deep obsidian shadows"
    mood: str                         # "urgent, suspenseful, gritty"
    time_of_day: str                  # "midnight"
    weather: str                      # "torrential rain, wet reflections on asphalt"
```

---

## 3. Provider-Specific Compilation Rules

1. **Runway Compiler**: Injects `[Camera: ...]` and temporal motion cues; strips model parameter flags.
2. **Kling Compiler**: Prioritizes anatomical clarity, clear physical trajectory, and cinematic lighting.
3. **Flux Compiler**: Merges dimensions into cohesive multi-clause prose descriptions with explicit textural details.
4. **Negative Prompt Builder**: Automatically appends quality negatives (`"low quality, blurry, deformed hands, distorted anatomy, extra limbs, watermark, oversaturated"`).
