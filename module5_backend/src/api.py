from fastapi import FastAPI, HTTPException
from backend.src.schemas import (
    RunPipelineRequest,
    RunPipelineResponse,
    RunResult
)
from backend.src.orchestrator import Orchestrator
from backend.src.run_manager import RunManager

app = FastAPI(
    title="Oil Spill Detection & Tracking Pipeline API",
    description="Backend orchestration service for Smart India Hackathon pipeline.",
    version="1.0.0"
)

orchestrator = Orchestrator()
run_manager = RunManager()


@app.get("/health")
def health_check():
    """Health check endpoint required by frontend/monitoring."""
    return {"status": "ok"}


@app.post("/pipeline/run", response_model=RunPipelineResponse)
def trigger_pipeline_run(request: RunPipelineRequest):
    """Triggers a pipeline run for a given scene_id and run_mode."""
    if not run_manager.is_scene_valid(request.scene_id):
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scene_id '{request.scene_id}'. Scene not found in config."
        )

    # Execute orchestrator pipeline run
    try:
        run_result = orchestrator.run_pipeline(
            scene_id=request.scene_id,
            run_mode=request.run_mode
        )
        return RunPipelineResponse(
            run_id=run_result.run_id,
            message=f"Pipeline execution finished with overall_status: {run_result.overall_status.value}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution encountered an unhandled error: {str(e)}"
        )


@app.get("/pipeline/status/{run_id}")
def get_pipeline_status(run_id: str):
    """Returns stage status breakdown and overall execution status for a run_id."""
    if not run_manager.run_exists(run_id):
        raise HTTPException(
            status_code=404,
            detail=f"Run ID '{run_id}' not found."
        )

    result_data = run_manager.load_json(run_id, "run_result.json")
    if not result_data:
        raise HTTPException(
            status_code=404,
            detail=f"run_result.json for run_id '{run_id}' is missing."
        )

    # Return status portion of run_result.json
    return {
        "run_id": result_data.get("run_id"),
        "scene_id": result_data.get("scene_id"),
        "overall_status": result_data.get("overall_status"),
        "failed_stage": result_data.get("failed_stage"),
        "stages": result_data.get("stages")
    }


@app.get("/results/{run_id}", response_model=RunResult)
def get_pipeline_results(run_id: str):
    """Fetches full aggregated pipeline results and raw GeoJSON/JSON payloads."""
    if not run_manager.run_exists(run_id):
        raise HTTPException(
            status_code=404,
            detail=f"Run ID '{run_id}' not found."
        )

    result_data = run_manager.load_json(run_id, "run_result.json")
    if not result_data:
        raise HTTPException(
            status_code=404,
            detail=f"run_result.json for run_id '{run_id}' is missing."
        )

    return result_data