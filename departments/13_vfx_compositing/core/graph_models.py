"""
Compositing Graph Data Models
Defines Directed Acyclic Graph (DAG) structures, nodes, edges, ports, and blend modes
for Department 13: VFX & Compositing.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Set
from uuid import UUID, uuid4


class PortDataType(str, Enum):
    IMAGE_RGBA = "IMAGE_RGBA"
    IMAGE_RGB = "IMAGE_RGB"
    MASK_ALPHA = "MASK_ALPHA"
    TRANSFORM_MATRIX = "TRANSFORM_MATRIX"
    TRACK_DATA = "TRACK_DATA"
    SCALAR = "SCALAR"


class BlendMode(str, Enum):
    OVER = "OVER"
    ADD = "ADD"
    MULTIPLY = "MULTIPLY"
    SCREEN = "SCREEN"
    DIFFERENCE = "DIFFERENCE"
    SUBTRACT = "SUBTRACT"
    MASK = "MASK"


class VFXNodeType(str, Enum):
    MEDIA_INPUT = "MEDIA_INPUT"
    CHROMA_KEY = "CHROMA_KEY"
    MERGE = "MERGE"
    PLANAR_WARP = "PLANAR_WARP"
    FEATURE_TRACK = "FEATURE_TRACK"
    TRANSFORM = "TRANSFORM"
    BLUR = "BLUR"
    COLOR_GRADE = "COLOR_GRADE"
    INPAINT = "INPAINT"
    ATMOSPHERIC = "ATMOSPHERIC"
    CINEMATIC_FX = "CINEMATIC_FX"
    MEDIA_OUTPUT = "MEDIA_OUTPUT"


@dataclass
class NodePort:
    port_id: str
    data_type: PortDataType
    name: str
    is_input: bool = True
    default_value: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "port_id": self.port_id,
            "data_type": self.data_type.value,
            "name": self.name,
            "is_input": self.is_input,
            "default_value": self.default_value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NodePort":
        return cls(
            port_id=data["port_id"],
            data_type=PortDataType(data["data_type"]),
            name=data["name"],
            is_input=data.get("is_input", True),
            default_value=data.get("default_value"),
        )


@dataclass
class VFXNode:
    node_id: str
    node_type: VFXNodeType
    name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    inputs: List[NodePort] = field(default_factory=list)
    outputs: List[NodePort] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "name": self.name,
            "parameters": self.parameters,
            "inputs": [p.to_dict() for p in self.inputs],
            "outputs": [p.to_dict() for p in self.outputs],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VFXNode":
        return cls(
            node_id=data["node_id"],
            node_type=VFXNodeType(data["node_type"]),
            name=data.get("name", data["node_id"]),
            parameters=data.get("parameters", {}),
            inputs=[NodePort.from_dict(p) for p in data.get("inputs", [])],
            outputs=[NodePort.from_dict(p) for p in data.get("outputs", [])],
        )


@dataclass
class GraphEdge:
    edge_id: str
    source_node_id: str
    source_port: str
    target_node_id: str
    target_port: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_node_id": self.source_node_id,
            "source_port": self.source_port,
            "target_node_id": self.target_node_id,
            "target_port": self.target_port,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraphEdge":
        return cls(
            edge_id=data.get("edge_id", str(uuid4())),
            source_node_id=data["source_node_id"],
            source_port=data["source_port"],
            target_node_id=data["target_node_id"],
            target_port=data["target_port"],
        )


@dataclass
class CompositingGraph:
    graph_id: str
    project_id: str
    name: str
    resolution_w: int = 1920
    resolution_h: int = 1080
    fps: float = 24.0
    duration_frames: int = 24
    nodes: List[VFXNode] = field(default_factory=list)
    edges: List[GraphEdge] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_node(self, node: VFXNode) -> None:
        if any(n.node_id == node.node_id for n in self.nodes):
            raise ValueError(f"Node with id {node.node_id} already exists in graph.")
        self.nodes.append(node)

    def add_edge(self, source_node_id: str, source_port: str, target_node_id: str, target_port: str) -> GraphEdge:
        if not any(n.node_id == source_node_id for n in self.nodes):
            raise ValueError(f"Source node {source_node_id} does not exist.")
        if not any(n.node_id == target_node_id for n in self.nodes):
            raise ValueError(f"Target node {target_node_id} does not exist.")
        edge = GraphEdge(
            edge_id=str(uuid4()),
            source_node_id=source_node_id,
            source_port=source_port,
            target_node_id=target_node_id,
            target_port=target_port,
        )
        self.edges.append(edge)
        # Validate that graph remains acyclic
        self.topological_sort()
        return edge

    def get_node(self, node_id: str) -> Optional[VFXNode]:
        for n in self.nodes:
            if n.node_id == node_id:
                return n
        return None

    def topological_sort(self) -> List[VFXNode]:
        """
        Returns nodes in topological dependency order (sources to terminals).
        Raises ValueError if cycle is detected.
        """
        in_degree: Dict[str, int] = {n.node_id: 0 for n in self.nodes}
        adjacency: Dict[str, List[str]] = {n.node_id: [] for n in self.nodes}

        for edge in self.edges:
            adjacency[edge.source_node_id].append(edge.target_node_id)
            in_degree[edge.target_node_id] = in_degree.get(edge.target_node_id, 0) + 1

        queue: List[str] = [n_id for n_id, deg in in_degree.items() if deg == 0]
        sorted_nodes: List[VFXNode] = []

        while queue:
            curr_id = queue.pop(0)
            node = self.get_node(curr_id)
            if node:
                sorted_nodes.append(node)
            for neighbor in adjacency[curr_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_nodes) != len(self.nodes):
            raise ValueError("Cycle detected in CompositingGraph dependency structure.")
        return sorted_nodes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "project_id": self.project_id,
            "name": self.name,
            "resolution_w": self.resolution_w,
            "resolution_h": self.resolution_h,
            "fps": self.fps,
            "duration_frames": self.duration_frames,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompositingGraph":
        return cls(
            graph_id=data.get("graph_id", str(uuid4())),
            project_id=data.get("project_id", ""),
            name=data.get("name", "Untitled_Graph"),
            resolution_w=data.get("resolution_w", 1920),
            resolution_h=data.get("resolution_h", 1080),
            fps=data.get("fps", 24.0),
            duration_frames=data.get("duration_frames", 24),
            nodes=[VFXNode.from_dict(n) for n in data.get("nodes", [])],
            edges=[GraphEdge.from_dict(e) for e in data.get("edges", [])],
            metadata=data.get("metadata", {}),
        )

