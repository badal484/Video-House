"""
Unified Temporal Event Graph for Multimodal Video Reverse Engineering.
Represents video as an interconnected temporal graph of:
- Nodes: Video, Scene, Shot, Frame, AudioSegment, TextElement, GraphicElement, Transition, NarrativeEvent.
- Edges: CONTAINS, PRECEDES, OVERLAPS, SYNCHRONIZED_WITH, SUPPORTS_NARRATIVE.
Supports temporal indexing, spatial relationships, cross-modal synchronization, and search queries.
"""
from dataclasses import asdict, dataclass, field
from enum import Enum
import json
import logging
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from core.assets.intelligence_models import (
    EvidenceRecord,
    TimecodeRange
)

logger = logging.getLogger("studio.intelligence.event_graph")

class GraphNodeType(str, Enum):
    VIDEO = "VIDEO"
    SCENE = "SCENE"
    SHOT = "SHOT"
    FRAME = "FRAME"
    AUDIO_EVENT = "AUDIO_EVENT"
    MUSIC_SEGMENT = "MUSIC_SEGMENT"
    TRANSCRIPT_SEGMENT = "TRANSCRIPT_SEGMENT"
    TEXT_ELEMENT = "TEXT_ELEMENT"
    GRAPHIC_ELEMENT = "GRAPHIC_ELEMENT"
    TRANSITION = "TRANSITION"
    NARRATIVE_EVENT = "NARRATIVE_EVENT"

class GraphEdgeType(str, Enum):
    CONTAINS = "CONTAINS"
    PRECEDES = "PRECEDES"
    OVERLAPS = "OVERLAPS"
    SYNCHRONIZED_WITH = "SYNCHRONIZED_WITH"
    SUPPORTS_NARRATIVE = "SUPPORTS_NARRATIVE"

@dataclass
class EventGraphNode:
    node_id: str
    node_type: GraphNodeType
    label: str
    start_seconds: float
    end_seconds: float
    attributes: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    evidence_provider: str = "deterministic"

    @property
    def duration_seconds(self) -> float:
        return max(0.0, self.end_seconds - self.start_seconds)

    def overlaps_with(self, other_start: float, other_end: float) -> bool:
        return max(self.start_seconds, other_start) < min(self.end_seconds, other_end)

@dataclass
class EventGraphEdge:
    source_id: str
    target_id: str
    edge_type: GraphEdgeType
    weight: float = 1.0
    attributes: Dict[str, Any] = field(default_factory=dict)

def _clean_graph_val(v: Any) -> Any:
    if isinstance(v, dict):
        return {k: _clean_graph_val(val) for k, val in v.items()}
    elif isinstance(v, list):
        return [_clean_graph_val(val) for val in v]
    elif hasattr(v, "item"):
        return v.item()
    elif hasattr(v, "value"):
        return v.value
    return v

class TemporalEventGraph:
    def __init__(self, asset_id: UUID, title: str = "Video Event Graph"):
        self.asset_id = asset_id
        self.title = title
        self.nodes: Dict[str, EventGraphNode] = {}
        self.edges: List[EventGraphEdge] = []
        self._adjacency: Dict[str, List[EventGraphEdge]] = {}

    def add_node(self, node: EventGraphNode) -> None:
        self.nodes[node.node_id] = node
        if node.node_id not in self._adjacency:
            self._adjacency[node.node_id] = []

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: GraphEdgeType,
        weight: float = 1.0,
        attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        if source_id not in self.nodes or target_id not in self.nodes:
            logger.debug(f"Edge endpoints missing: {source_id} -> {target_id}; adding anyway.")
        edge = EventGraphEdge(
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            weight=weight,
            attributes=attributes or {}
        )
        self.edges.append(edge)
        if source_id not in self._adjacency:
            self._adjacency[source_id] = []
        self._adjacency[source_id].append(edge)

    def query_at_timestamp(self, timestamp_sec: float) -> List[EventGraphNode]:
        """Returns all graph nodes active at a specific point in time."""
        return [
            node for node in self.nodes.values()
            if node.start_seconds <= timestamp_sec <= node.end_seconds
        ]

    def query_overlapping(
        self,
        start_sec: float,
        end_sec: float,
        node_types: Optional[List[GraphNodeType]] = None
    ) -> List[EventGraphNode]:
        """Returns all graph nodes that overlap the given time window, optionally filtered by type."""
        results = []
        for node in self.nodes.values():
            if node_types and node.node_type not in node_types:
                continue
            if node.overlaps_with(start_sec, end_sec):
                results.append(node)
        return sorted(results, key=lambda n: n.start_seconds)

    def query_connected(
        self,
        node_id: str,
        edge_type: Optional[GraphEdgeType] = None
    ) -> List[EventGraphNode]:
        """Returns all nodes immediately reachable from node_id."""
        connected_ids = []
        for edge in self._adjacency.get(node_id, []):
            if edge_type is None or edge.edge_type == edge_type:
                connected_ids.append(edge.target_id)
        return [self.nodes[nid] for nid in connected_ids if nid in self.nodes]

    def search_nodes(self, query: str) -> List[EventGraphNode]:
        """Fuzzy text search over node labels and attributes."""
        q = query.lower()
        matches = []
        for node in self.nodes.values():
            text_corpus = f"{node.label} {json.dumps(node.attributes)}".lower()
            if q in text_corpus:
                matches.append(node)
        return sorted(matches, key=lambda n: n.start_seconds)

    def auto_connect_temporal_edges(self) -> None:
        """
        Computes PRECEDES, OVERLAPS, and SYNCHRONIZED_WITH relationships automatically
        based on timestamps across nodes.
        """
        node_list = list(self.nodes.values())
        # Sort by start time
        node_list.sort(key=lambda n: n.start_seconds)

        for i in range(len(node_list)):
            n1 = node_list[i]
            for j in range(i + 1, min(len(node_list), i + 25)):
                n2 = node_list[j]

                # Precedes check
                if abs(n1.end_seconds - n2.start_seconds) < 0.05 and n1.node_type == n2.node_type:
                    self.add_edge(n1.node_id, n2.node_id, GraphEdgeType.PRECEDES, weight=1.0)

                # Overlaps check (cross-modal e.g. text over shot, audio under shot)
                elif n1.overlaps_with(n2.start_seconds, n2.end_seconds):
                    self.add_edge(n1.node_id, n2.node_id, GraphEdgeType.OVERLAPS, weight=0.8)

                    # Synchronization check: near-simultaneous starts (|t1 - t2| < 0.1s)
                    if abs(n1.start_seconds - n2.start_seconds) < 0.12:
                        self.add_edge(
                            n1.node_id,
                            n2.node_id,
                            GraphEdgeType.SYNCHRONIZED_WITH,
                            weight=1.0,
                            attributes={"delta_ms": round(abs(n1.start_seconds - n2.start_seconds) * 1000.0, 1)}
                        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": str(self.asset_id),
            "title": self.title,
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "nodes": [
                {
                    "node_id": n.node_id,
                    "node_type": n.node_type.value,
                    "label": n.label,
                    "start_seconds": n.start_seconds,
                    "end_seconds": n.end_seconds,
                    "duration_seconds": round(float(n.duration_seconds), 3),
                    "attributes": _clean_graph_val(n.attributes),
                    "confidence": float(n.confidence),
                    "evidence_provider": str(n.evidence_provider)
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {
                    "source_id": str(e.source_id),
                    "target_id": str(e.target_id),
                    "edge_type": e.edge_type.value,
                    "weight": float(e.weight),
                    "attributes": _clean_graph_val(e.attributes)
                }
                for e in self.edges
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemporalEventGraph":
        graph = cls(
            asset_id=UUID(data["asset_id"]),
            title=data.get("title", "Video Event Graph")
        )
        for nd in data.get("nodes", []):
            node = EventGraphNode(
                node_id=nd["node_id"],
                node_type=GraphNodeType(nd["node_type"]),
                label=nd["label"],
                start_seconds=float(nd["start_seconds"]),
                end_seconds=float(nd["end_seconds"]),
                attributes=nd.get("attributes", {}),
                confidence=float(nd.get("confidence", 1.0)),
                evidence_provider=nd.get("evidence_provider", "deterministic")
            )
            graph.add_node(node)

        for ed in data.get("edges", []):
            graph.add_edge(
                source_id=ed["source_id"],
                target_id=ed["target_id"],
                edge_type=GraphEdgeType(ed["edge_type"]),
                weight=float(ed.get("weight", 1.0)),
                attributes=ed.get("attributes", {})
            )
        return graph

