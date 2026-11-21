"""
Compositor Engine Interface
Defines the standard execution contract for local and remote compositing engines.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import numpy as np
from ..core.graph_models import CompositingGraph


class ICompositorEngine(ABC):
    """
    Abstract interface for evaluating and rendering compositing node graphs.
    """

    @abstractmethod
    def evaluate_frame(
        self,
        graph: CompositingGraph,
        frame_index: int = 0,
        inputs: Optional[Dict[str, np.ndarray]] = None,
    ) -> np.ndarray:
        """
        Evaluates the node graph for a single frame and returns the output RGBA array.
        """
        pass

    @abstractmethod
    def render_sequence(
        self,
        graph: CompositingGraph,
        start_frame: int = 0,
        end_frame: Optional[int] = None,
        output_path: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Renders a full frame sequence or video file.
        """
        pass
