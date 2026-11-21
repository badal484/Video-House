# COMPOSITING GRAPH SCHEMA SPECIFICATION
**Department:** 13_vfx_compositing  
**Document Version:** 1.0.0  

---

## 1. Data Model Overview

The compositing node graph is defined as a Directed Acyclic Graph:
$$G = (V, E)$$
Where:
- $V = \{N_1, N_2, \dots, N_k\}$ represents the set of processing nodes.
- $E = \{e_1, e_2, \dots, e_m\}$ represents directed data connections between an output port of an upstream node and an input port of a downstream node.

---

## 2. Port Data Types

```python
class PortDataType(str, Enum):
    IMAGE_RGBA = "IMAGE_RGBA"           # 4-channel 8-bit or 32-bit float image
    IMAGE_RGB = "IMAGE_RGB"             # 3-channel image without alpha
    MASK_ALPHA = "MASK_ALPHA"           # Single-channel grayscale mask (0.0 to 1.0)
    TRANSFORM_MATRIX = "TRANSFORM_MATRIX" # 3x3 affine or homography matrix
    TRACK_DATA = "TRACK_DATA"           # Time-series point coordinate dictionary
    SCALAR = "SCALAR"                   # Floating-point numerical value
```

---

## 3. Node Types & Standard Ports

| Node Type | Category | Inputs | Outputs | Description |
|---|---|---|---|---|
| `MEDIA_INPUT` | Generator | None | `output` (IMAGE_RGBA) | Loads source footage, image, or derivative asset |
| `CHROMA_KEY` | Matting | `source` (IMAGE_RGBA), `garbage_matte` (MASK_ALPHA, opt) | `output` (IMAGE_RGBA), `matte` (MASK_ALPHA) | Green/blue screen extraction with despill |
| `MERGE` | Composite | `background` (IMAGE_RGBA), `foreground` (IMAGE_RGBA), `mask` (MASK_ALPHA, opt) | `output` (IMAGE_RGBA) | Layer blending (OVER, ADD, MULTIPLY, SCREEN) |
| `PLANAR_WARP` | Transform | `source` (IMAGE_RGBA), `track` (TRACK_DATA, opt) | `output` (IMAGE_RGBA) | 4-point perspective corner pin |
| `TRANSFORM` | Transform | `source` (IMAGE_RGBA) | `output` (IMAGE_RGBA) | Scale, rotate, translate, flip |
| `BLUR` | Filter | `source` (IMAGE_RGBA), `mask` (MASK_ALPHA, opt) | `output` (IMAGE_RGBA) | Gaussian blur with kernel size |
| `COLOR_GRADE` | Color | `source` (IMAGE_RGBA) | `output` (IMAGE_RGBA) | Exposure, contrast, saturation, lift/gamma/gain |
| `INPAINT` | Cleanup | `source` (IMAGE_RGBA), `mask` (MASK_ALPHA) | `output` (IMAGE_RGBA) | Wire, logo, or object removal |
| `ATMOSPHERIC` | Effect | `source` (IMAGE_RGBA, opt) | `output` (IMAGE_RGBA) | Procedural fog, dust motes, light wrap |
| `MEDIA_OUTPUT` | Terminal | `source` (IMAGE_RGBA) | None | Terminal node writing image or video |

---

## 4. JSON Representation Example

```json
{
  "graph_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "name": "Screen_Replacement_Shot_01",
  "resolution_w": 1920,
  "resolution_h": 1080,
  "fps": 24.0,
  "nodes": [
    {
      "node_id": "node_plate",
      "node_type": "MEDIA_INPUT",
      "parameters": {"asset_id": "asset-raw-phone-footage"}
    },
    {
      "node_id": "node_screen_ui",
      "node_type": "MEDIA_INPUT",
      "parameters": {"asset_id": "asset-motion-canvas-ui"}
    },
    {
      "node_id": "node_warp",
      "node_type": "PLANAR_WARP",
      "parameters": {
        "corners_dst": [[400, 300], [800, 320], [820, 900], [390, 880]]
      }
    },
    {
      "node_id": "node_merge",
      "node_type": "MERGE",
      "parameters": {"blend_mode": "OVER"}
    },
    {
      "node_id": "node_out",
      "node_type": "MEDIA_OUTPUT",
      "parameters": {"output_path": "output/composite_shot_01.mp4"}
    }
  ],
  "edges": [
    {
      "source_node_id": "node_screen_ui",
      "source_port": "output",
      "target_node_id": "node_warp",
      "target_port": "source"
    },
    {
      "source_node_id": "node_plate",
      "source_port": "output",
      "target_node_id": "node_merge",
      "target_port": "background"
    },
    {
      "source_node_id": "node_warp",
      "source_port": "output",
      "target_node_id": "node_merge",
      "target_port": "foreground"
    },
    {
      "source_node_id": "node_merge",
      "source_port": "output",
      "target_node_id": "node_out",
      "target_port": "source"
    }
  ]
}
```

