from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class RunMode(str, Enum):
    LIVE = "live"
    PRECOMPUTED = "precomputed"


class StageStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class OverallStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


# Stage Output Schemas (Validated at module boundaries)

class PreprocessingOutput(BaseModel):
    status: str
    scene_id: str
    preprocessed_image_path: str
    acquisition_timestamp_utc: str
    bounds: List[float]


class SegmentationOutput(BaseModel):
    status: str
    mask_path: str
    probability_map_path: str
    confidence_score: float


class GeometryExtractionOutput(BaseModel):
    status: str
    no_oil_detected: bool = False
    spill_geometry_geojson: Dict[str, Any]  # Unmodified GeoJSON FeatureCollection
    spill_summary: Dict[str, Any]


class DriftBacktrackingOutput(BaseModel):
    status: str
    backtracking_valid: bool = True
    source_estimate: Dict[str, Any]
    uncertainty_bounds: Optional[Dict[str, Any]] = None


class AISRankingOutput(BaseModel):
    status: str
    candidate_ranking: Dict[str, Any]  # Vessel rankings, attribution scores, and disclaimer text
    normalized_ais_tracks: Dict[str, Any]  # GeoJSON FeatureCollection for map tracks


# Aggregated Pipeline Status & Schema Contracts

class StageMeta(BaseModel):
    status: StageStatus
    output_path: Optional[str] = None
    output_paths: Optional[Dict[str, Optional[str]]] = None
    error: Optional[str] = None


class PipelineStages(BaseModel):
    sar_preprocessing: StageMeta
    segmentation: StageMeta
    geometry_extraction: StageMeta
    drift_backtracking: StageMeta
    ais_ranking: StageMeta


class PipelineResults(BaseModel):
    spill_geometry_geojson: Optional[Dict[str, Any]] = None
    spill_summary: Optional[Dict[str, Any]] = None
    source_estimate: Optional[Dict[str, Any]] = None
    candidate_ranking: Optional[Dict[str, Any]] = None
    normalized_ais_tracks: Optional[Dict[str, Any]] = None


class RunResult(BaseModel):
    run_id: str
    scene_id: str
    run_mode: RunMode
    started_at_utc: str
    completed_at_utc: Optional[str] = None
    overall_status: OverallStatus
    stages: PipelineStages
    failed_stage: Optional[str] = None
    results: PipelineResults


# Request / Response Models for FastAPI

class RunPipelineRequest(BaseModel):
    scene_id: str
    run_mode: RunMode = RunMode.LIVE


class RunPipelineResponse(BaseModel):
    run_id: str
    message: str