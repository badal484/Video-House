# Audio Production Known Limitations & Future Work
**Project:** Universal AI Video Production Studio  
**Department:** 14_audio_production  
**Document:** AUDIO_KNOWN_LIMITATIONS.md  
**Version:** 1.0.0  

---

## 1. Known Architectural Limitations

1. **Non-Real-Time DAW UI**: Department 14 is architected as an automated, headless production engine rather than an interactive graphical DAW like Ableton Live or Logic Pro. Interactive UI playback relies on streaming preview renders via WebAudio in Department 01.
2. **Third-Party Plugin Architecture**: Running 64-bit Intel x86 VST3 plugins on Apple Silicon requires Rosetta 2 translation, which can introduce latency. Native ARM64 VST3/AU plugins run at full native speed.
3. **Heavy Stem Separation on CPU**: While 4-stem Demucs runs smoothly on GPU, batch separation of 2-hour multi-channel audio on CPU alone requires chunked background queue scheduling.
4. **Extreme Pitch-Shifting Range**: High quality pitch-shifting is optimal within $\pm 12$ semitones; shifts beyond $\pm 18$ semitones may introduce harmonic dispersion artifacts.

---

## 2. Future Roadmap

1. **Dolby Atmos / ADM BWF Export**: Authoring spatialize bed + object audio conformant to Dolby Atmos cinema and consumer streaming delivery profiles.
2. **Automated AI Foley Matcher**: Computer-vision driven video tracking in Department 03 matching footsteps and object impacts to physical movement in video frames.
3. **Real-time WebAudio Graph Mirroring**: Direct translation of `AudioSession` DAGs into client-side Web Audio API nodes for sub-10ms browser timeline playback.
