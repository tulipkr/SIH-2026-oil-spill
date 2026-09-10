from datetime import datetime, timezone
import concurrent.futures
from typing import Dict, Any, Callable

from backend.src.schemas import (
    RunResult, RunMode, StageStatus, OverallStatus,
    PipelineStages, PipelineResults, StageMeta,
    PreprocessingOutput, SegmentationOutput, GeometryExtractionOutput,
    DriftBacktrackingOutput, AISRankingOutput
)
from backend.src.run_manager import RunManager
from backend.src.module_adapters import (
    ishita_adapter,
    tulip_adapter,
    shazmeen_adapter,
    sara_adapter
)


class Orchestrator:
    def __init__(self, config_path: str = "backend/configs/config.yaml"):
        self.run_manager = RunManager(config_path)
        self.timeout = self.run_manager.config.get("run_timeout_seconds", 600)

    def _execute_stage_with_timeout(self, func: Callable, *args, **kwargs) -> Any:
        """Executes a stage function with a strict timeout to prevent indefinite hangs."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            return future.result(timeout=self.timeout)

    def run_pipeline(self, scene_id: str, run_mode: RunMode = RunMode.LIVE) -> RunResult:
        """Sequential orchestrator with schema validation gates and partial failure handling."""
        if not self.run_manager.is_scene_valid(scene_id):
            raise ValueError(f"Unknown scene_id '{scene_id}'. Rejecting run request.")

        run_id = self.run_manager.create_run(scene_id)
        started_at = datetime.now(timezone.utc).isoformat()

        # Initialize tracking state
        stages_meta = {
            "sar_preprocessing": StageMeta(status=StageStatus.SKIPPED),
            "segmentation": StageMeta(status=StageStatus.SKIPPED),
            "geometry_extraction": StageMeta(status=StageStatus.SKIPPED),
            "drift_backtracking": StageMeta(status=StageStatus.SKIPPED),
            "ais_ranking": StageMeta(status=StageStatus.SKIPPED),
        }
        results = PipelineResults()
        failed_stage = None
        overall_status = OverallStatus.SUCCESS

        # Pipeline execution steps definition
        pipeline_steps = [
            ("sar_preprocessing", self._run_preprocessing),
            ("segmentation", self._run_segmentation),
            ("geometry_extraction", self._run_geometry_extraction),
            ("drift_backtracking", self._run_drift_backtracking),
            ("ais_ranking", self._run_ais_ranking),
        ]

        skip_remaining = False
        skip_reason = None

        for stage_name, stage_func in pipeline_steps:
            if skip_remaining:
                stages_meta[stage_name] = StageMeta(
                    status=StageStatus.SKIPPED,
                    error=skip_reason or "Skipped due to upstream output condition."
                )
                continue

            try:
                # Execute stage logic with timeout guard
                meta, data, should_skip_next, reason = self._execute_stage_with_timeout(
                    stage_func, scene_id, run_id
                )
                stages_meta[stage_name] = meta

                # Attach stage results to aggregated payload
                self._attach_results(stage_name, data, results)

                if should_skip_next:
                    skip_remaining = True
                    skip_reason = reason

            except Exception as e:
                # Stage failure or schema validation error caught here
                failed_stage = stage_name
                stages_meta[stage_name] = StageMeta(
                    status=StageStatus.FAILED,
                    error=f"Stage '{stage_name}' failed: {str(e)}"
                )
                overall_status = OverallStatus.FAILED if stage_name == "sar_preprocessing" else OverallStatus.PARTIAL
                break

        completed_at = datetime.now(timezone.utc).isoformat()

        # Build final aggregated result record
        run_result = RunResult(
            run_id=run_id,
            scene_id=scene_id,
            run_mode=run_mode,
            started_at_utc=started_at,
            completed_at_utc=completed_at,
            overall_status=overall_status,
            stages=PipelineStages(**stages_meta),
            failed_stage=failed_stage,
            results=results
        )

        # Save aggregated result artifact to disk
        self.run_manager.save_json(run_id, "run_result.json", run_result.model_dump())
        return run_result

    def _attach_results(self, stage_name: str, data: Dict[str, Any], results: PipelineResults):
        """Passes through raw stage output fields into aggregated results without modification."""
        if stage_name == "geometry_extraction":
            results.spill_geometry_geojson = data.get("spill_geometry_geojson")
            results.spill_summary = data.get("spill_summary")
        elif stage_name == "drift_backtracking":
            results.source_estimate = data.get("source_estimate")
        elif stage_name == "ais_ranking":
            results.candidate_ranking = data.get("candidate_ranking")
            results.normalized_ais_tracks = data.get("normalized_ais_tracks")

    # Individual Stage Runners & Schema Validation Gates

    def _run_preprocessing(self, scene_id: str, run_id: str):
        raw_output = ishita_adapter.run_sar_preprocessing(scene_id)
        validated = PreprocessingOutput(**raw_output)  # Schema Gate
        path = self.run_manager.save_json(run_id, "stageA_manifest.json", validated.model_dump())
        return StageMeta(status=StageStatus.SUCCESS, output_path=path), validated.model_dump(), False, None

    def _run_segmentation(self, scene_id: str, run_id: str):
        raw_output = tulip_adapter.run_segmentation(scene_id)
        validated = SegmentationOutput(**raw_output)  # Schema Gate
        path = self.run_manager.save_json(run_id, "tulip_result.json", validated.model_dump())
        return StageMeta(status=StageStatus.SUCCESS, output_path=path), validated.model_dump(), False, None

    def _run_geometry_extraction(self, scene_id: str, run_id: str):
        raw_output = ishita_adapter.run_geometry_extraction(scene_id)
        validated = GeometryExtractionOutput(**raw_output)  # Schema Gate
        geom_path = self.run_manager.save_json(run_id, "spill_geometry.geojson", validated.spill_geometry_geojson)
        summary_path = self.run_manager.save_json(run_id, "spill_summary.json", validated.spill_summary)

        meta = StageMeta(
            status=StageStatus.SUCCESS,
            output_paths={"spill_geometry_geojson": geom_path, "spill_summary": summary_path}
        )

        skip_next = validated.no_oil_detected
        reason = "Skipped downstream stages because no oil was detected in geometry extraction." if skip_next else None
        return meta, validated.model_dump(), skip_next, reason

    def _run_drift_backtracking(self, scene_id: str, run_id: str):
        raw_output = shazmeen_adapter.run_drift_backtracking(scene_id)
        validated = DriftBacktrackingOutput(**raw_output)  # Schema Gate
        path = self.run_manager.save_json(run_id, "source_estimate.json", validated.model_dump())

        skip_next = not validated.backtracking_valid
        reason = "Skipped AIS ranking because drift backtracking produced invalid source trajectory." if skip_next else None
        return StageMeta(status=StageStatus.SUCCESS, output_path=path), validated.model_dump(), skip_next, reason

    def _run_ais_ranking(self, scene_id: str, run_id: str):
        raw_output = sara_adapter.run_ais_ranking(scene_id)
        validated = AISRankingOutput(**raw_output)  # Schema Gate
        ranking_path = self.run_manager.save_json(run_id, "candidate_ranking.json", validated.candidate_ranking)
        tracks_path = self.run_manager.save_json(run_id, "normalized_ais_tracks.geojson", validated.normalized_ais_tracks)

        meta = StageMeta(
            status=StageStatus.SUCCESS,
            output_paths={"candidate_ranking": ranking_path, "normalized_ais_tracks": tracks_path}
        )
        return meta, validated.model_dump(), False, None