import Link from "next/link";

import { fetchCalls } from "../../lib/api";

export default async function CallsPage() {
  const calls = await fetchCalls();
  return (
    <main className="container">
      <h1>Past Calls</h1>
      <div className="card">
        {calls.length === 0 ? (
          <p>No calls yet.</p>
        ) : (
          <ul>
            {calls.map((c) => (
              <li key={c.id} style={{ marginBottom: 10 }}>
                <Link href={`/calls/${c.id}`}>{c.filename}</Link> - {c.language} -{" "}
                {new Date(c.created_at).toLocaleString()}
              </li>
            ))}
          </ul>
        )}
      </div>
      <Link href="/">Back to upload</Link>
    </main>
  );
}
