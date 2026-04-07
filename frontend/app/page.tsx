"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { uploadCall } from "../lib/api";

export default function HomePage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      const data = await uploadCall(file);
      router.push(`/calls/${data.call_id}`);
    } catch {
      setError("Failed to upload call.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="container">
      <h1>SalesLens</h1>
      <p style={{ color: "var(--muted)" }}>Upload a sales call to start real-time intelligence.</p>
      <form className="card" onSubmit={onSubmit}>
        <input
          type="file"
          accept=".mp3,.wav,audio/*"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          required
        />
        <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
          <button className="btn" disabled={loading}>
            {loading ? "Uploading..." : "Upload and Analyze"}
          </button>
          <a className="btn" href="/calls">
            View Call History
          </a>
        </div>
        {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
      </form>
    </main>
  );
}
