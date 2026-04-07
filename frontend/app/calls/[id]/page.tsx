"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { askQuestion, fetchInsights, streamCall } from "../../../lib/api";

type Segment = { speaker: string; text: string; start_time: number; end_time: number };

export default function CallDashboard() {
  const params = useParams<{ id: string }>();
  const callId = params.id;
  const [segments, setSegments] = useState<Segment[]>([]);
  const [progress, setProgress] = useState(0);
  const [insights, setInsights] = useState<any>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [connection, setConnection] = useState<"connecting" | "connected" | "reconnecting" | "closed">("connecting");

  useEffect(() => {
    if (!callId) return;
    const seqKey = `saleslens:lastSeq:${callId}`;
    let ws: WebSocket | null = null;
    let closedByUnmount = false;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;

    const connect = (isRetry: boolean) => {
      const sinceSeq = Number(window.localStorage.getItem(seqKey) || "0");
      setConnection(isRetry ? "reconnecting" : "connecting");
      ws = streamCall(
        callId,
        async (event) => {
          if (typeof event.seq === "number") {
            window.localStorage.setItem(seqKey, String(event.seq));
          }
          if (event.type === "status") {
            setProgress(event.progress || 0);
          }
          if (event.type === "transcript_segment") {
            setProgress(event.progress || 0);
            if (!event.is_partial) {
              setSegments((s) => {
                const last = s[s.length - 1];
                if (
                  last &&
                  last.start_time === event.segment.start_time &&
                  last.end_time === event.segment.end_time &&
                  last.text === event.segment.text
                ) {
                  return s;
                }
                return [...s, event.segment];
              });
            }
          }
          if (event.type === "completed") {
            setProgress(100);
            const data = await fetchInsights(callId);
            setInsights(data);
          }
        },
        sinceSeq
      );

      ws.onopen = () => setConnection("connected");
      ws.onclose = () => {
        if (closedByUnmount) {
          setConnection("closed");
          return;
        }
        retryTimer = setTimeout(() => connect(true), 1200);
      };
    };

    connect(false);
    return () => {
      closedByUnmount = true;
      if (retryTimer) clearTimeout(retryTimer);
      ws?.close();
    };
  }, [callId]);

  const sentimentChart = useMemo(() => insights?.sentiment_timeline || [], [insights]);

  async function onAsk(e: React.FormEvent) {
    e.preventDefault();
    const out = await askQuestion(callId, question);
    setAnswer(out.answer);
  }

  return (
    <main className="container">
      <h1>Call Dashboard</h1>
      <p style={{ color: "var(--muted)" }}>Progress: {progress}%</p>
      <p style={{ color: "var(--muted)" }}>Stream: {connection}</p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <section className="card">
          <h3>Live Transcript</h3>
          {segments.map((s, i) => (
            <p key={i}>
              <strong>{s.speaker}:</strong> {s.text}
            </p>
          ))}
        </section>

        <section className="card">
          <h3>Insights</h3>
          {!insights ? (
            <p>Waiting for analysis...</p>
          ) : (
            <>
              <p>
                <strong>Call Score:</strong> {insights.call_score?.total ?? "-"}
              </p>
              <h4>Objections</h4>
              <ul>{(insights.objections || []).map((o: any, i: number) => <li key={i}>{o.text}</li>)}</ul>
              <h4>Action Items</h4>
              <ul>{(insights.action_items || []).map((a: any, i: number) => <li key={i}>{a.text}</li>)}</ul>
            </>
          )}
        </section>
      </div>

      <section className="card" style={{ marginTop: 12, height: 260 }}>
        <h3>Sentiment Timeline</h3>
        <ResponsiveContainer width="100%" height="85%">
          <LineChart data={sentimentChart}>
            <XAxis dataKey="timestamp" />
            <YAxis domain={[-1, 1]} />
            <Tooltip />
            <Line type="monotone" dataKey="score" stroke="#3ee1b3" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </section>

      <section className="card" style={{ marginTop: 12 }}>
        <h3>Ask about this call</h3>
        <form onSubmit={onAsk} style={{ display: "flex", gap: 8 }}>
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="When did customer mention pricing?"
            style={{ flex: 1, padding: 10, borderRadius: 8, border: "1px solid #263553", background: "#0d162b", color: "white" }}
          />
          <button className="btn">Ask</button>
        </form>
        {answer && <p style={{ marginTop: 8 }}>{answer}</p>}
      </section>
    </main>
  );
}
