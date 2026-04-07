import type { Insights } from "../lib/types";

interface InsightsPanelProps {
  insights: Insights | null;
  isLoading: boolean;
}

export function InsightsPanel({ insights, isLoading }: InsightsPanelProps) {
  if (isLoading) {
    return (
      <div>
        <h4>Insights</h4>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div className="skeleton" style={{ height: 64, width: "100%" }} />
          <div className="skeleton" style={{ height: 48, width: "80%" }} />
          <div className="skeleton" style={{ height: 48, width: "90%" }} />
        </div>
      </div>
    );
  }

  if (!insights) {
    return (
      <div>
        <h4>Insights</h4>
        <p style={{ color: "var(--text-tertiary)", fontSize: 14, textAlign: "center", padding: "2rem 0" }}>
          Waiting for analysis to complete...
        </p>
      </div>
    );
  }

  const score = insights.call_score?.total;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      <h4>Insights</h4>

      {score !== undefined && score !== null && (
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          padding: 16,
          background: "var(--surface-hover)",
          borderRadius: "var(--radius-md)",
        }}>
          <div style={{
            width: 56,
            height: 56,
            borderRadius: "50%",
            border: `3px solid ${score >= 70 ? "var(--success)" : score >= 40 ? "var(--warning)" : "var(--danger)"}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 20,
            fontWeight: 700,
            color: score >= 70 ? "var(--success)" : score >= 40 ? "var(--warning)" : "var(--danger)",
            flexShrink: 0,
          }}>
            {score}
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 14 }}>Call Score</div>
            <div style={{ fontSize: 13, color: "var(--text-tertiary)" }}>
              {score >= 70 ? "Strong performance" : score >= 40 ? "Room for improvement" : "Needs attention"}
            </div>
          </div>
        </div>
      )}

      {insights.summary && (
        <div>
          <h4>Summary</h4>
          <p style={{ fontSize: 14, color: "var(--text-secondary)", lineHeight: 1.7 }}>
            {insights.summary}
          </p>
        </div>
      )}

      {insights.key_topics && insights.key_topics.length > 0 && (
        <div>
          <h4>Key Topics</h4>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {insights.key_topics.map((topic, i) => (
              <span key={i} className="badge badge-accent">{topic}</span>
            ))}
          </div>
        </div>
      )}

      {insights.objections && insights.objections.length > 0 && (
        <div>
          <h4>Objections</h4>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {insights.objections.map((obj, i) => (
              <div
                key={i}
                style={{
                  padding: "0.625rem 0.75rem",
                  background: "var(--danger-subtle)",
                  borderRadius: "var(--radius-sm)",
                  fontSize: 14,
                  borderLeft: "3px solid var(--danger)",
                }}
              >
                {obj.text}
              </div>
            ))}
          </div>
        </div>
      )}

      {insights.action_items && insights.action_items.length > 0 && (
        <div>
          <h4>Action Items</h4>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {insights.action_items.map((item, i) => (
              <div
                key={i}
                style={{
                  padding: "0.625rem 0.75rem",
                  background: "var(--accent-subtle)",
                  borderRadius: "var(--radius-sm)",
                  fontSize: 14,
                  borderLeft: "3px solid var(--accent)",
                }}
              >
                {item.text}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
