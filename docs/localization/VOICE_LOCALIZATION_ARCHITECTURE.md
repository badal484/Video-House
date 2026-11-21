# Voice Localization Architecture Specification

## 1. Voice Assignment & Casting Engine
The `VoiceAssignmentManager` bridges speaker diarization clusters with neural voice profiles.
1. **Acoustic Profiling:**
   - Ingests audio segments belonging to each speaker cluster.
   - Computes acoustic features: fundamental frequency $F_0$ (pitch), pitch variance, spectral centroid (timbre brightness), and speech cadence.
   - Estimates speaker age bracket and gender presentation.
2. **Voice Profile Library Matching:**
   - Matches speaker acoustic features against available voice profiles (ElevenLabs cloned voices, Kokoro open-source presets, studio voice talent roster).
   - Preserves gender, age, and emotional persona in target languages.
3. **Dynamic Multi-Actor Casting:**
   - Manages multi-speaker projects where each character is assigned an independent target voice profile.
   - Ensures distinct voice separation so dialogue exchanges remain clear and unmistakable to the listener.

## 2. Biometric Consent & Authorization Flow
Before any voice profile can be cloned or synthesized:
- The system queries `ConsentManager` for an active `BiometricConsentRecord`.
- Verifies that `actor_name`, `authorized_until`, and `permitted_territories` cover the current production.
- If unauthorized, synthesis is halted with a clear `ConsentAuthorizationException`.
