# Localization Known Limitations & Future Roadmap

## 1. Current Technical Limitations
1. **Local Apple Silicon Lip-Sync Sizing:**
   - Real-time 4K video lip-sync requires high-end CUDA hardware with $>24\text{ GB}$ VRAM. On local Apple Silicon (16GB unified memory), local neural lip-sync is constrained to lower-resolution crops ($256\times256$ to $512\times512$) or must be offloaded to cloud APIs (Sync Labs).
2. **Accented Code-Switching Nuances:**
   - While major Indic code-switched dialects (Hinglish, Tanglish) are supported, rare regional dialects with heavy colloquialisms may require manual transcript review before dubbing.
3. **Extreme Pacing Discrepancies:**
   - In rare scenes where target translations are $>150\%$ the duration of the source speech and video pauses are absent, aggressive semantic summarization is required to fit the time budget.

## 2. Strategic Future Enhancements (Post-v1.0)
- Real-time zero-shot emotional timbre matching during live streaming.
- Fully local quantized LatentSync running on Apple Silicon Neural Engine (ANE) via CoreML.
- Interactive multi-user web subtitle editor with real-time waveform visualization.
