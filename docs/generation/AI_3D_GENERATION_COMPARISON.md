# AI 3D Generation Models Comparison & Integration
**Project:** Universal AI Video Production Studio  
**Department:** 15_ai_generation & 11_animation_3d  
**Document:** AI_3D_GENERATION_COMPARISON.md  
**Version:** 1.0.0  

---

## 1. 3D Generative AI State of the Art

| Technology / Model | Developer | Modalities | Output Format | Mesh Topology | Texture Resolution | Commercial License | Studio Verdict |
|---|---|---|---|---|---|---|---|
| **Tripo3D (v2.0)** | Tripo AI | Text/Image to 3D | GLTF, USDZ, OBJ | Clean quad retopology | 4K PBR (diffuse, normal, roughness) | Commercial Permitted | **Primary Production 3D Generator** |
| **Meshy-4** | Meshy Inc. | Text/Image to 3D | GLTF, FBX, OBJ | Triangular / Quad | 4K PBR | Commercial Permitted | **Secondary High-Poly 3D Asset** |
| **Hunyuan3D 1.0** | Tencent | Text/Image to 3D | OBJ, GLTF | High poly | 2K Texture | Tencent Open License | **Primary Open Source 3D Model** |
| **TRELLIS (Microsoft)** | Microsoft Research | Structured Latent 3D | GLB / NeRF | Structured Gaussians | Radiance Field / Mesh | MIT | **Rapid Volumetric Prototype** |

---

## 2. Integration Boundary with Department 11 (3D Animation)

Department 15 does not duplicate the 3D scene assembler or Blender USD rendering pipeline established in Department 11 (`11_animation_3d`).
- Department 15 acts as the **generation client & validator**: it submits the prompt or reference image, monitors progress, retrieves the GLTF/USDZ mesh, validates polygonal manifold geometry and non-overlapping UVs, and registers the 3D asset in `core/assets/database.py`.
- Department 11 ingests the validated USD/GLTF asset, positions it in the OpenUSD stage graph, assigns lighting, and executes final multi-pass Cycles rendering.
