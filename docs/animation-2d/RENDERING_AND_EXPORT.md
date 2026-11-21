# RENDERING & EXPORT SPECIFICATION
**Department:** 10_animation_2d  
**Topic:** Transparent Alpha Video, Image Sequences, Vector SVG, and NLE Timeline Conformance  

---

## 1. Supported Export Formats

| Format | Codec / Pixel Format | Alpha Support | Target Destination | Use Case |
|---|---|---|---|---|
| **Apple ProRes 4444** | `prores_ks` / `yuva444p10le` | Full 16-bit Alpha | NLE Timeline (V2/V3) | Master video composite overlays |
| **Transparent WebM** | `libvpx-vp9` / `yuva420p` | Full 8-bit Alpha | Web / Stream preview | Lightweight web animation preview |
| **PNG Image Sequence** | `png` / `rgba` | Lossless 8-bit Alpha | Post-production VFX | Frame-by-frame compositing in Part 07 |
| **Vector SVG XML** | Standalone SVG 1.1 | Lossless Vector Alpha | Web / Motion Canvas | Resolution-independent graphic assets |
| **Sprite Sheet** | `png` + JSON Atlas | Lossless 8-bit Alpha | Game Runtimes | 2D game character animation |

---

## 2. NLE Timeline Conformance Pipeline

When an animation scene or character pass finishes rendering:
1. The rendered master is registered in the Central Asset Registry (`AssetRecord` with `MediaType.VIDEO` or `MediaType.ANIMATION`).
2. `TimelineAnimationAdapter` generates an OpenTimelineIO clip.
3. The clip is placed onto the destination timeline:
   - Full scenes (with background) are placed on track `V1` as primary cuts.
   - Transparent character actions or overlays are placed on track `V3` over existing footage.
   - Rational time duration (`RationalTime(frame_count, fps)`) guarantees zero floating-point accumulation drift.

