import { Line, LineChart, ResponsiveContainer, XAxis, YAxis, Tooltip, Area, AreaChart } from "recharts";
import type { SentimentPoint } from "../lib/types";

interface SentimentChartProps {
  data: SentimentPoint[];
}

function formatTimestamp(ts: string): string {
  try {
    const date = new Date(ts);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return ts;
  }
}

function CustomTooltip({ active, payload }: any) {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const score = payload[0].value;
    const sentiment = score > 0.3 ? "Positive" : score < -0.3 ? "Negative" : "Neutral";
    return (
      <div style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-sm)",
        padding: "0.5rem 0.75rem",
        boxShadow: "var(--shadow-md)",
        fontSize: 13,
      }}>
        <div style={{ fontWeight: 600, marginBottom: 2 }}>{formatTimestamp(data.timestamp)}</div>
        <div style={{ color: score > 0 ? "var(--success)" : score < 0 ? "var(--danger)" : "var(--text-secondary)" }}>
          Score: {score.toFixed(2)} ({sentiment})
        </div>
      </div>
    );
  }
  return null;
}

export function SentimentChartComponent({ data }: SentimentChartProps) {
  if (!data || data.length === 0) {
    return (
      <div>
        <h4>Sentiment Timeline</h4>
        <p style={{ color: "var(--text-tertiary)", fontSize: 14, textAlign: "center", padding: "2rem 0" }}>
          No sentiment data available yet.
        </p>
      </div>
    );
  }

  return (
    <div>
      <h4>Sentiment Timeline</h4>
      <div style={{ height: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="sentimentGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.15} />
                <stop offset="95%" stopColor="var(--accent)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="timestamp"
              tickFormatter={formatTimestamp}
              tick={{ fontSize: 11, fill: "var(--text-tertiary)" }}
              axisLine={{ stroke: "var(--border)" }}
              tickLine={false}
            />
            <YAxis
              domain={[-1, 1]}
              tick={{ fontSize: 11, fill: "var(--text-tertiary)" }}
              axisLine={false}
              tickLine={false}
              ticks={[-1, -0.5, 0, 0.5, 1]}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="score"
              stroke="var(--accent)"
              strokeWidth={2}
              fill="url(#sentimentGradient)"
              dot={false}
              activeDot={{ r: 4, fill: "var(--accent)", stroke: "var(--surface)", strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
