# AI ANIMATION WORKFLOWS & MOTION TRANSFER SPECIFICATION
**Department:** 10_animation_2d  
**Topic:** Motion Retargeting, Facial Animation Puppetry, and Selective In-Betweening  

---

## 1. Reference Motion Transfer Workflow

```
[ Driving Reference Video / Motion Data ]
                    │
                    ▼
     [ Pose & Motion Vector Extractor ]
     • 2D Body joints (OpenPose / MediaPipe)
     • Facial landmarks & head pose
                    │
                    ▼
    [ Motion Retargeting & Anatomical Fit ]
    • Normalizes limb lengths to target character head-ratio
    • Clamps impossible joint angles
                    │
                    ▼
    [ Skeletal Bone Animation Track ]
    • Keyframes generated on 2s or 3s
    • Easing curve interpolation applied
                    │
                    ▼
    [ Character Puppet Evaluation ]
    • Renders character sprites at mapped bone positions
```

---

## 2. Facial Animation & Dialogue Lip-Sync

In 2D animation, facial performance comprises three decoupled layers:
1. **Head Orientation:** Yaw (rotation around Y), Pitch (nodding X), Roll (tilt Z).
2. **Eye Expression:** Eyelid aperture $[0.0, 1.0]$, pupil gaze $(x, y)$, eyebrow curvature.
3. **Mouth Visemes (Phoneme Shapes):**
   - `REST`: Neutral closed mouth.
   - `AI_A`: Wide open mouth (vowels A, I).
   - `E_EE`: Stretched horizontal smile (vowel E).
   - `O_OH`: Rounded open circle (vowel O).
   - `U_OO`: Pursed small circle (vowel U, W).
   - `M_B_P`: Compressed closed lips (bilabial consonants M, B, P).
   - `F_V`: Lower lip tucked under upper teeth (labiodental F, V).
   - `L_TH`: Tongue tip touching upper teeth (alveolar/dental L, TH).

The system maps Whisper speech word boundaries to corresponding mouth visemes, automatically switching mouth shapes in sync with dialogue audio.

