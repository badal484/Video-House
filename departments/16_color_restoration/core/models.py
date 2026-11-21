"""
Core Domain Models for Department 16: Color Grading, Color Management, Video Restoration & Enhancement.
Defines Pydantic v2 schemas for color spaces, transfer functions, grading node graphs,
LUT metadata, restoration jobs, and quality control reviews.
"""
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class ColorSpace(str, Enum):
    REC709 = "rec709"
    SRGB = "srgb"
    DISPLAY_P3 = "display_p3"
    REC2020 = "rec2020"
    ACESCG = "acescg"
    ACES_CCT = "aces_cct"
    ACES2065_1 = "aces2065_1"
    REC2100_PQ = "rec2100_pq"
    REC2100_HLG = "rec2100_hlg"
    # Camera Log Spaces
    ARRI_LOGC3 = "arri_logc3"
    ARRI_LOGC4 = "arri_logc4"
    SONY_SLOG3 = "sony_slog3"
    CANON_CLOG3 = "canon_clog3"
    RED_LOG3G10 = "red_log3g10"
    BMD_FILM_GEN5 = "bmd_film_gen5"
    PANASONIC_VLOG = "panasonic_vlog"


class TransferFunction(str, Enum):
    LINEAR = "linear"
    SRGB = "srgb"
    BT1886 = "bt1886"
    GAMMA_22 = "gamma_22"
    PQ = "pq"
    HLG = "hlg"
    LOGC3 = "logc3"
    LOGC4 = "logc4"
    SLOG3 = "slog3"
    CLOG3 = "clog3"
    LOG3G10 = "log3g10"
    VLOG = "vlog"


class DataRange(str, Enum):
    FULL = "full"       # 0 - 255 (8-bit) / 0.0 - 1.0 (float)
    VIDEO = "video"     # 16 - 235 (8-bit studio legal)


class ColorProfileMetadata(BaseModel):
    color_space: ColorSpace = ColorSpace.REC709
    transfer_function: TransferFunction = TransferFunction.BT1886
    bit_depth: int = Field(8, ge=8, le=16)
    data_range: DataRange = DataRange.FULL
    white_point: Tuple[float, float] = (0.3127, 0.3290) # D65 default
    primaries: Optional[List[Tuple[float, float]]] = None
    is_hdr: bool = False
    max_cll: Optional[float] = None # Maximum Content Light Level in nits
    max_fall: Optional[float] = None # Maximum Frame-Average Light Level in nits


class GradingNodeType(str, Enum):
    PRIMARY = "primary"
    CURVES = "curves"
    WHEELS = "wheels"
    SECONDARY_QUALIFIER = "secondary_qualifier"
    POWER_WINDOW = "power_window"
    LUT = "lut"
    TONE_MAP = "tone_map"
    CREATIVE_LOOK = "creative_look"


class PrimaryGradingParameters(BaseModel):
    exposure_ev: float = Field(0.0, description="Exposure in EV stops (-4.0 to +4.0)")
    lift: Tuple[float, float, float] = Field((0.0, 0.0, 0.0), description="Shadow offset RGB")
    gamma: Tuple[float, float, float] = Field((1.0, 1.0, 1.0), description="Midtone power RGB")
    gain: Tuple[float, float, float] = Field((1.0, 1.0, 1.0), description="Highlight scale RGB")
    offset: Tuple[float, float, float] = Field((0.0, 0.0, 0.0), description="Uniform offset RGB")
    contrast: float = Field(1.0, ge=0.0, le=3.0, description="Contrast slope")
    pivot: float = Field(0.18, ge=0.0, le=1.0, description="Middle gray pivot point (18%)")
    temperature_k: float = Field(6500.0, description="Color temperature in Kelvin")
    tint: float = Field(0.0, description="Green-Magenta tint (-100.0 to +100.0)")
    saturation: float = Field(1.0, ge=0.0, le=3.0, description="Global color saturation")
    vibrance: float = Field(0.0, description="Selective low-saturation boost (-1.0 to 1.0)")
    highlights: float = Field(0.0, description="Highlight recovery/compression (-1.0 to 1.0)")
    shadows: float = Field(0.0, description="Shadow boost/crush (-1.0 to 1.0)")


class CurvesParameters(BaseModel):
    # Control points as list of (x, y) coordinates normalized [0.0, 1.0]
    master_curve: List[Tuple[float, float]] = Field(default_factory=lambda: [(0.0, 0.0), (1.0, 1.0)])
    red_curve: List[Tuple[float, float]] = Field(default_factory=lambda: [(0.0, 0.0), (1.0, 1.0)])
    green_curve: List[Tuple[float, float]] = Field(default_factory=lambda: [(0.0, 0.0), (1.0, 1.0)])
    blue_curve: List[Tuple[float, float]] = Field(default_factory=lambda: [(0.0, 0.0), (1.0, 1.0)])
    hue_vs_hue: Optional[List[Tuple[float, float]]] = None
    hue_vs_sat: Optional[List[Tuple[float, float]]] = None
    hue_vs_lum: Optional[List[Tuple[float, float]]] = None
    lum_vs_sat: Optional[List[Tuple[float, float]]] = None


class SecondaryQualifierParameters(BaseModel):
    enabled: bool = True
    # Hue in degrees [0, 360]
    hue_center: float = Field(123.0, ge=0.0, le=360.0)
    hue_width: float = Field(30.0, ge=1.0, le=180.0)
    hue_softness: float = Field(10.0, ge=0.0, le=90.0)
    # Saturation [0.0, 1.0]
    sat_min: float = Field(0.15, ge=0.0, le=1.0)
    sat_max: float = Field(0.85, ge=0.0, le=1.0)
    sat_softness: float = Field(0.1, ge=0.0, le=0.5)
    # Luminance [0.0, 1.0]
    lum_min: float = Field(0.10, ge=0.0, le=1.0)
    lum_max: float = Field(0.90, ge=0.0, le=1.0)
    lum_softness: float = Field(0.1, ge=0.0, le=0.5)
    # Adjustments inside qualifier mask
    gain: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    saturation: float = 1.0
    hue_shift_deg: float = 0.0
    invert_mask: bool = False


class PowerWindowParameters(BaseModel):
    enabled: bool = True
    shape: str = Field("ellipse", description="'ellipse' or 'rectangle'")
    center_x: float = Field(0.5, ge=0.0, le=1.0)
    center_y: float = Field(0.5, ge=0.0, le=1.0)
    radius_x: float = Field(0.25, ge=0.01, le=1.0)
    radius_y: float = Field(0.25, ge=0.01, le=1.0)
    rotation_deg: float = Field(0.0)
    feather: float = Field(0.15, ge=0.0, le=1.0)
    invert: bool = False


class LUTMetadata(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    format: str = Field("cube", description="cube, 3dl, or clf")
    input_color_space: ColorSpace = ColorSpace.REC709
    output_color_space: ColorSpace = ColorSpace.REC709
    size: int = Field(33, description="1D size (e.g. 1024) or 3D cube dimension (e.g. 33)")
    is_3d: bool = True
    is_technical: bool = False
    intensity: float = Field(1.0, ge=0.0, le=1.0)
    description: Optional[str] = None
    author: Optional[str] = None
    license: str = "Proprietary / Studio"


class GradingNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    name: str
    node_type: GradingNodeType
    enabled: bool = True
    primary_params: Optional[PrimaryGradingParameters] = None
    curves_params: Optional[CurvesParameters] = None
    qualifier_params: Optional[SecondaryQualifierParameters] = None
    power_window_params: Optional[PowerWindowParameters] = None
    lut_metadata: Optional[LUTMetadata] = None
    look_preset_name: Optional[str] = None
    opacity: float = Field(1.0, ge=0.0, le=1.0)


class GradingGraph(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    clip_id: Optional[str] = None
    name: str = "Master Grade"
    working_color_space: ColorSpace = ColorSpace.ACESCG
    display_color_space: ColorSpace = ColorSpace.REC709
    nodes: List[GradingNode] = Field(default_factory=list)
    version: int = 1
    description: Optional[str] = None


class RestorationType(str, Enum):
    DENOISE = "denoise"
    DEBLUR = "deblur"
    DEFLICKER = "deflicker"
    DEINTERLACE = "deinterlace"
    STABILIZE = "stabilize"
    SCRATCH_REMOVAL = "scratch_removal"
    LOW_LIGHT_ENHANCE = "low_light_enhance"
    FRAME_INTERPOLATION = "frame_interpolation"
    SUPER_RESOLUTION = "super_resolution"


class RestorationParameters(BaseModel):
    restoration_type: RestorationType
    strength: float = Field(0.5, ge=0.0, le=1.0)
    model_name: Optional[str] = None # e.g. "realesrgan_x4plus", "anime_esrgan"
    scale_factor: float = Field(1.0, ge=1.0, le=4.0)
    tile_size: int = Field(512, ge=128, le=2048)
    temporal_radius: int = Field(2, ge=1, le=5)
    preserve_fine_texture: bool = True
    noise_variance: Optional[float] = None
    psf_kernel_size: Optional[int] = Field(5, ge=3, le=21)


class QualityReviewState(str, Enum):
    UNCHECKED = "UNCHECKED"
    PROCESSING = "PROCESSING"
    PASSED = "PASSED"
    WARNING = "WARNING"
    FAILED = "FAILED"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"


class RestorationJob(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    asset_id: UUID
    restoration_types: List[RestorationType]
    parameters: Dict[str, Any] = Field(default_factory=dict)
    status: str = "PENDING"
    progress: float = 0.0
    output_derivative_id: Optional[UUID] = None
    review_state: QualityReviewState = QualityReviewState.UNCHECKED
    qc_metrics: Dict[str, float] = Field(default_factory=dict) # psnr, ssim, clipping_pct
    notes: Optional[str] = None
