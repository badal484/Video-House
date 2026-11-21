# Speaker Diarization and Alignment Specification

## 1. Objectives & Pipeline Stages
Speaker Diarization segments audio into homogeneous temporal intervals and groups them by speaker identity ("Speaker 0", "Speaker 1").

```
Audio Stream ────► [VAD Segmentation] ────► [Speaker Embedding Extractor]
                                                    │
                                                    ▼
                                           [Agglomerative Clustering]
                                                    │
                                                    ▼
                                           [Overlap Resolution]
                                                    │
                                                    ▼
                                           [Speaker-Segment Map]
```

## 2. Algorithm Details
1. **Embedding Extraction:** Audio chunks are encoded into 192-dimensional d-vectors using an ECAPA-TDNN neural network.
2. **Cosine Similarity Clustering:** Spectral clustering with PLDA or agglomerative hierarchical clustering with thresholding separates unique vocal profiles.
3. **Word-to-Speaker Assignment:** For each word boundary $[t_{start}, t_{end}]$, the engine intersects word intervals with speaker segments. If multiple speakers overlap, the segment with maximum acoustic energy in that speaker's frequency centroid is selected.

## 3. Active Speaker Visual Alignment
When video stream is available:
- Face tracking tracks bounding boxes $B_i(t)$.
- Mouth movement optic flow or landmark distance $D(lip_{upper}, lip_{lower})$ correlates with audio energy envelopes $E(t)$.
- The correlation peak confirms on-screen speaker identity, distinguishing between primary characters and background crowds.
