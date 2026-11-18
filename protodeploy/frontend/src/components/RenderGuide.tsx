import type { ReactNode } from "react";

const C = ({ children }: { children: ReactNode }) => (
  <code className="px-mono" style={{ padding: "1px 6px", borderRadius: 6, background: "var(--surface)", border: "1px solid var(--border)" }}>{children}</code>
);

export default function RenderGuide({ apiName, repo }: { apiName: string; repo: string }) {
  const steps: { title: string; body: ReactNode }[] = [
    {
      title: "Open Render",
      body: <>Click <b>Deploy backend on Render</b>. Sign in to Render with GitHub if it asks.</>,
    },
    {
      title: "Name the Blueprint",
      body: <>Enter any <b>Blueprint name</b> (for example <C>{repo}</C>). The name does not matter.</>,
    },
    {
      title: "Deploy the Blueprint",
      body: <>Click <b>Deploy Blueprint</b>. Leave the other settings as they are.</>,
    },
    {
      title: "Wait for Render",
      body: (
        <>
          Render creates a database (name starts with <C>{apiName}-db</C>) and a web service
          (name starts with <C>{apiName}</C>). Wait till you see a tick before each. This can take a few minutes.
        </>
      ),
    },
    {
      title: "Come back here",
      body: <>Return to this page. Step 3 ticks by itself once your backend is live.</>,
    },
  ];

  return (
    <details className="px-details">
      <summary>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-text)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <circle cx="12" cy="12" r="10" /><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3M12 17h.01" />
        </svg>
        How do I deploy the backend on Render?
      </summary>

      <div className="px-details-body">
        <ol className="px-timeline">
          {steps.map((s, i) => (
            <li key={i}>
              <div className="px-timeline-rail">
                <span className="px-timeline-dot" style={{ background: "var(--accent-soft)", color: "var(--accent-text)" }}>{i + 1}</span>
              </div>
              <div className="px-timeline-body">
                <p style={{ margin: "3px 0 2px", fontWeight: 700 }}>{s.title}</p>
                <p className="px-small" style={{ margin: 0, color: "var(--muted)" }}>{s.body}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </details>
  );
}