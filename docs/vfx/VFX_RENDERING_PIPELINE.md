# VFX RENDERING PIPELINE & COLOR CONFORMANCE
**Department:** 13_vfx_compositing  
**Topic:** Render Execution, OpenColorIO ACEScg, Alpha Channels, and Output Formats  

---

## 1. Topological Graph Execution

Compositing graphs are executed strictly in topological order. A Kahn's algorithm or depth-first search ensures every input port receives evaluated data before a node runs.

```python
def topological_sort(nodes: List[Node], edges: List[Edge]) -> List[Node]:
    in_degree = {n.node_id: 0 for n in nodes}
    adjacency = {n.node_id: [] for n in nodes}
    for e in edges:
        adjacency[e.source_node_id].append(e.target_node_id)
        in_degree[e.target_node_id] += 1
    
    queue = [n_id for n_id, deg in in_degree.items() if deg == 0]
    sorted_nodes = []
    while queue:
        curr_id = queue.pop(0)
        sorted_nodes.append(next(n for n in nodes if n.node_id == curr_id))
        for neighbor in adjacency[curr_id]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    return sorted_nodes
```

---

## 2. Color Space & Radiance Math

### 2.1 The Need for Linear Space
Display color spaces (sRGB / Rec.709) use a non-linear power curve ($\gamma \approx 2.2$) to maximize perceptual bit depth. However, physical light addition is linear:
$$I_{total} = I_1 + I_2$$
Performing additive merges (glows, light wraps, motion blur) in non-linear sRGB creates muddy, desaturated edges. The studio compositor transforms all 8-bit inputs into linear floating-point arrays before blending:
$$C_{linear} = \begin{cases} \frac{C_{sRGB}}{12.92} & C_{sRGB} \le 0.04045 \\ \left(\frac{C_{sRGB} + 0.055}{1.055}\right)^{2.4} & C_{sRGB} > 0.04045 \end{cases}$$

### 2.2 Premultiplied Compositing Equation
All merge operations standardly evaluate:
$$\text{Color}_{out} = \text{Color}_{fg} + \text{Color}_{bg} \times (1.0 - \alpha_{fg})$$
$$\alpha_{out} = \alpha_{fg} + \alpha_{bg} \times (1.0 - \alpha_{fg})$$

---

## 3. Output Media Conformance

1. **Master Renders:**
   - Apple ProRes 4444 (`prores_ks -profile:v 4`) with alpha channel for downstream NLE layering.
   - High-bitrate H.264 / H.265 Rec.709 MP4 for web and client review previews.
2. **Intermediate Frame Caches:**
   - Saved in temporary storage with immediate cleanup upon job completion to preserve the ~41GB local disk quota.

