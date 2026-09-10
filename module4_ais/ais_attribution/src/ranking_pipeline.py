import json
import logging
from pathlib import Path

import pandas as pd

from search_window import calculate_search_window, load_config
from ingest_ais import clean_ais_data
from trajectory_reconstruction import (
    preprocess_ais_data,
    reconstruct_trajectories
)
from spatial_filter import filter_by_bbox
from temporal_filter import filter_by_time
from closest_approach import calculate_closest_approach
from temporal_compatibility import check_temporal_compatibility
from drift_compatibility import calculate_drift_compatibility
from ais_completeness import (
    calculate_completeness_for_trajectories
)
from scoring import (
    calculate_composite_score,
    create_evidence_summary
)

logger = logging.getLogger(__name__)


DISCLAIMER = (
    "This output is a decision-support ranking based on heuristic "
    "AIS compatibility signals. It is not a probability, does not "
    "establish causation or legal responsibility, and must not be "
    "treated as legal determination."
)


def rank_candidates(candidate_scores, top_k=10):
    """
    Rank vessels by heuristic composite score.

    Ties at the top-k cutoff are all retained.
    """

    if not candidate_scores:
        return pd.DataFrame()

    ranking_df = pd.DataFrame(candidate_scores)

    ranking_df = ranking_df.sort_values(
        by="composite_score",
        ascending=False
    ).reset_index(drop=True)

    ranking_df["rank"] = (
        ranking_df["composite_score"]
        .rank(
            method="min",
            ascending=False
        )
        .astype(int)
    )

    if len(ranking_df) > top_k:

        cutoff_score = ranking_df.iloc[
            top_k - 1
        ]["composite_score"]

        ranking_df = ranking_df[
            ranking_df["composite_score"]
            >= cutoff_score
        ].copy()

    return ranking_df.reset_index(drop=True)


def save_candidate_ranking(
    ranked_candidates,
    output_path="outputs/candidate_ranking.json"
):
    """
    Save final candidate ranking as JSON.
    """

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    candidates = []

    for _, row in ranked_candidates.iterrows():

        candidate = {
            "rank": int(row["rank"]),
            "MMSI": int(row["MMSI"]),
            "vessel_name": row.get(
                "vessel_name",
                None
            ),
            "closest_approach_km": (
                float(row["closest_approach_km"])
                if pd.notna(
                    row.get("closest_approach_km")
                )
                else None
            ),
            "closest_approach_time": row.get(
                "closest_approach_time",
                None
            ),
            "temporal_compatible": bool(
                row["temporal_compatible"]
            ),
            "trajectory_drift_compatibility_score": (
                float(
                    row[
                        "trajectory_drift_compatibility_score"
                    ]
                )
                if pd.notna(
                    row.get(
                        "trajectory_drift_compatibility_score"
                    )
                )
                else None
            ),
            "ais_completeness_score": (
                float(
                    row["ais_completeness_score"]
                )
                if pd.notna(
                    row.get(
                        "ais_completeness_score"
                    )
                )
                else None
            ),
            "composite_score": float(
                row["composite_score"]
            ),
            "score_type": (
                "heuristic_composite_score"
            ),
            "evidence_summary": row.get(
                "evidence_summary",
                None
            ),
            "disclaimer": DISCLAIMER
        }

        candidates.append(candidate)

    output_data = {
        "score_type": "heuristic_composite_score",
        "candidates": candidates,
        "disclaimer": DISCLAIMER
    }

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output_data,
            file,
            indent=4,
            ensure_ascii=False
        )

    return output_path


def run_pipeline(
    source_estimate_path=(
        "data/source_estimate/"
        "source_estimate.json"
    ),
    ais_input_path=(
        "data/synthetic/"
        "synthetic_ais.csv"
    ),
    top_k=10
):
    """
    Run the complete AIS attribution pipeline.

    Returns:
        Ranked candidate DataFrame.
    """

    logger.info("Starting AIS attribution pipeline.")

    # --------------------------------------------------
    # 1. Load configuration
    # --------------------------------------------------

    config = load_config(
        "config/config.yaml"
    )

    # --------------------------------------------------
    # 2. Load source estimate
    # --------------------------------------------------

    with open(
        source_estimate_path,
        "r",
        encoding="utf-8"
    ) as file:

        source_estimate = json.load(file)

    # --------------------------------------------------
    # 3. Validate source estimate / short-circuit
    # --------------------------------------------------

    if not source_estimate.get(
        "backtracking_valid",
        False
    ):

        logger.warning(
            "Pipeline short-circuited: "
            "backtracking_valid=false"
        )

        return pd.DataFrame()

    if source_estimate.get(
        "no_oil_detected",
        False
    ):

        logger.warning(
            "Pipeline short-circuited: "
            "no_oil_detected=true"
        )

        return pd.DataFrame()

    # --------------------------------------------------
    # 4. Calculate search window
    # --------------------------------------------------

    search_window = calculate_search_window(
        source_estimate,
        config
    )

    # --------------------------------------------------
    # 5. Load AIS
    # --------------------------------------------------

    ais_df = pd.read_csv(
        ais_input_path
    )

    logger.info(
        f"AIS records loaded: {len(ais_df)}"
    )

    # --------------------------------------------------
    # 6. Clean AIS
    # --------------------------------------------------

    cleaned_df, _ = clean_ais_data(
        ais_df
    )

    # --------------------------------------------------
    # 7. Preprocess AIS
    # --------------------------------------------------

    processed_df = preprocess_ais_data(
        cleaned_df,
        expected_interval_minutes=6
    )

    # --------------------------------------------------
    # 8. Normalize timestamp
    # --------------------------------------------------

    processed_df["timestamp"] = pd.to_datetime(
        processed_df["timestamp"],
        utc=True,
        errors="coerce"
    )

    # --------------------------------------------------
    # 9. Spatial filtering
    # --------------------------------------------------

    spatial_filtered = filter_by_bbox(
        processed_df,
        search_window["bbox"]
    )

    # --------------------------------------------------
    # 10. Temporal filtering
    # --------------------------------------------------

    filtered_df = filter_by_time(
        spatial_filtered,
        search_window["time_window"]
    )

    logger.info(
        f"Combined filtering: "
        f"{len(processed_df)} → "
        f"{len(filtered_df)} records"
    )

    # --------------------------------------------------
    # 11. Reconstruct trajectories
    # --------------------------------------------------

    trajectories = reconstruct_trajectories(
        filtered_df
    )

    if not trajectories:

        logger.warning(
            "No AIS trajectories found."
        )

        empty_df = pd.DataFrame()

        save_candidate_ranking(
            empty_df
        )

        return empty_df

    # --------------------------------------------------
    # 12. AIS completeness
    # --------------------------------------------------

    completeness_results = (
        calculate_completeness_for_trajectories(
            trajectories,
            expected_interval_minutes=6
        )
    )

    # --------------------------------------------------
    # 13. Score each vessel
    # --------------------------------------------------

    candidate_scores = []

    for mmsi, vessel_df in trajectories.items():

        # Closest approach
        
        closest = calculate_closest_approach(
            vessel_df,
            search_window[
                "probable_source_region"
            ]
            if "probable_source_region"
            in search_window
            else source_estimate[
                "probable_source_region"
            ]
        )

        closest_distance = (
            closest["closest_approach_km"]
        )

        closest_time = (
            closest["closest_approach_time"]
        )

        # Temporal compatibility
        temporal_result = (
            check_temporal_compatibility(
                vessel_df,
                search_window["time_window"]
            )
        )

        temporal_compatible = (
            temporal_result[
                "temporal_compatible"
            ]
        )

        # Drift compatibility
        drift_direction = source_estimate.get(
            "drift_direction_degrees"
        )

        drift_score = (
            calculate_drift_compatibility(
                vessel_df,
                drift_direction
            )
        )

        # AIS completeness
        completeness_score = (
            completeness_results.get(
                mmsi
            )
        )

        # Composite score
        composite_score = (
            calculate_composite_score(
                closest_distance,
                temporal_compatible,
                drift_score
            )
        )

        # Vessel name
        if "vessel_name" in vessel_df.columns:
            vessel_name = (
                vessel_df["vessel_name"]
                .dropna()
                .iloc[0]
                if not vessel_df["vessel_name"]
                .dropna()
                .empty
                else None
            )
        else:
            vessel_name = None

        # Evidence
        evidence_summary = (
            create_evidence_summary(
                closest_distance,
                closest_time,
                temporal_compatible,
                drift_score,
                completeness_score
            )
        )

        candidate_scores.append(
            {
                "MMSI": mmsi,
                "vessel_name": vessel_name,
                "closest_approach_km": (
                    closest_distance
                ),
                "closest_approach_time": (
                    str(closest_time)
                    if closest_time is not None
                    else None
                ),
                "temporal_compatible": (
                    temporal_compatible
                ),
                "trajectory_drift_compatibility_score": (
                    drift_score
                ),
                "ais_completeness_score": (
                    completeness_score
                ),
                "composite_score": (
                    composite_score
                ),
                "evidence_summary": (
                    evidence_summary
                )
            }
        )

    # --------------------------------------------------
    # 14. Rank candidates
    # --------------------------------------------------

    ranked_candidates = rank_candidates(
        candidate_scores,
        top_k=top_k
    )

    # --------------------------------------------------
    # 15. Save candidate ranking
    # --------------------------------------------------

    save_candidate_ranking(
        ranked_candidates
    )

    logger.info(
        "AIS attribution pipeline completed."
    )

    return ranked_candidates


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO
    )

    ranked = run_pipeline()

    print("\nPipeline completed.")

    print(
        f"Ranked candidates: "
        f"{len(ranked)}"
    )

    if not ranked.empty:

        print("\nTop candidates:")

        print(
            ranked[
                [
                    "rank",
                    "MMSI",
                    "composite_score"
                ]
            ].to_string(
                index=False
            )
        )

    else:

        print(
            "No candidates available."
        )