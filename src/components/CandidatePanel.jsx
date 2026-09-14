import React from "react";

function CandidatePanel({ runResult }) {
  const candidateRanking =
    runResult?.results?.candidate_ranking;

  const candidates =
    candidateRanking?.candidates || [];

  return (
    <div
      style={{
        width: "100%",
        boxSizing: "border-box",
        backgroundColor: "#151515",
        borderRadius: "10px",
        padding: "14px",
        marginBottom: "16px",
        border: "1px solid #292929"
      }}
    >

      {/* HEADER */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "12px"
        }}
      >
        <div>

          <h3
            style={{
              margin: 0,
              fontSize: "16px",
              color: "#ffffff"
            }}
          >
            Candidate Vessels
          </h3>

          <p
            style={{
              margin: "3px 0 0",
              fontSize: "11px",
              color: "#888888"
            }}
          >
            AIS attribution results
          </p>

        </div>

        <span
          style={{
            backgroundColor: "#29204a",
            color: "#b9a5ff",
            padding: "4px 8px",
            borderRadius: "15px",
            fontSize: "11px",
            fontWeight: "600"
          }}
        >
          {candidates.length} found
        </span>

      </div>


      {/* NO CANDIDATES */}
      {candidates.length === 0 && (
        <div
          style={{
            padding: "10px",
            backgroundColor: "#1d1d1d",
            borderRadius: "7px",
            color: "#888888",
            fontSize: "12px"
          }}
        >
          No candidate vessels found in search window.
        </div>
      )}


      {/* CANDIDATES */}
      {candidates.map((candidate, index) => (

        <div
          key={
            candidate.mmsi ||
            candidate.vessel_id ||
            index
          }
          style={{
            padding: "10px",
            marginBottom: "7px",
            borderRadius: "8px",
            backgroundColor:
              index === 0
                ? "#211b35"
                : "#1b1b1b",
            border:
              index === 0
                ? "1px solid #493d70"
                : "1px solid #292929"
          }}
        >

          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center"
            }}
          >

            <div
              style={{
                minWidth: 0
              }}
            >

              <div
                style={{
                  fontWeight: "600",
                  fontSize: "13px",
                  color: "#ffffff"
                }}
              >
                #{candidate.rank || index + 1}{" "}
                {candidate.vessel_name ||
                  "Unknown vessel"}
              </div>

              <div
                style={{
                  fontSize: "10px",
                  color: "#888888",
                  marginTop: "3px"
                }}
              >
                {candidate.vessel_id ||
                  "ID not available"}
              </div>

              <div
                style={{
                  fontSize: "10px",
                  color: "#888888"
                }}
              >
                MMSI:{" "}
                {candidate.mmsi ||
                  "Not available"}
              </div>

            </div>


            {/* SCORE */}
            <div
              style={{
                textAlign: "right",
                marginLeft: "8px"
              }}
            >

              <div
                style={{
                  fontSize: "15px",
                  fontWeight: "700",
                  color:
                    index === 0
                      ? "#a78bfa"
                      : "#d1d5db"
                }}
              >
                {candidate.score ?? "N/A"}
              </div>

              <div
                style={{
                  fontSize: "8px",
                  color: "#666666"
                }}
              >
                SCORE
              </div>

            </div>

          </div>


          {/* EVIDENCE */}
          {candidate.evidence && (
            <div
              style={{
                marginTop: "8px",
                paddingTop: "7px",
                borderTop:
                  "1px solid #303030",
                fontSize: "10px",
                color: "#999999",
                lineHeight: "1.4"
              }}
            >
              <strong>Evidence:</strong>{" "}
              {typeof candidate.evidence ===
              "string"
                ? candidate.evidence
                : JSON.stringify(
                    candidate.evidence
                  )}
            </div>
          )}

        </div>

      ))}


      {/* DISCLAIMER */}
      <p
        style={{
          fontSize: "9px",
          color: "#666666",
          margin: "10px 2px 0",
          lineHeight: "1.4"
        }}
      >
        Candidate ranking is an analytical result
        and not a legal determination.
      </p>

    </div>
  );
}

export default CandidatePanel;