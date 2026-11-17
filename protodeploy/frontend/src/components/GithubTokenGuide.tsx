import type { ReactNode } from "react";

const C = ({ children }: { children: ReactNode }) => (
  <code className="px-mono" style={{ padding: "1px 6px", borderRadius: 6, background: "var(--surface)", border: "1px solid var(--border)" }}>{children}</code>
);

const steps: { title: string; body: ReactNode }[] = [
  {
    title: "Sign in to GitHub",
    body: <>Go to <b>github.com</b> and sign in.</>,
  },
  {
    title: "Open Settings",
    body: <>Click your <b>profile picture</b> (top right), then <b>Settings</b>.</>,
  },
  {
    title: "Open Developer settings",
    body: <>Scroll to the bottom of the left sidebar and click <b>Developer settings</b> (it is at the end).</>,
  },
  {
    title: "Go to Tokens (classic)",
    body: <>Click <b>Personal access tokens</b>, then <b>Tokens (classic)</b>.</>,
  },
  {
    title: "Generate a new token",
    body: (
      <>
        Click <b>Generate new token</b>, then <b>Generate new token (classic)</b>. GitHub may
        ask for your password or a 2FA code.
      </>
    ),
  },
  {
    title: "Name it and set an expiry",
    body: (
      <>
        <b>Note:</b> type a name for the token. <b>Expiration:</b> pick 7 days (or 30). A short
        expiry is safer.
      </>
    ),
  },
  {
    title: "Tick two scopes",
    body: (
      <>
        Tick <b>repo</b> (the top checkbox, which selects the whole group) and{" "}
        <b>workflow</b>. Nothing else is needed.
      </>
    ),
  },
  {
    title: "Generate and copy the token",
    body: (
      <>
        Scroll down and click <b>Generate token</b>. Copy the token right away (it starts with{" "}
        <C>ghp_</C>). GitHub shows it only once. If you lose it, delete it and make a new one.
      </>
    ),
  },
  {
    title: "Paste it into ProtoDeploy",
    body: <>Paste the token into the GitHub token field above, then deploy.</>,
  },
  {
    title: "Delete it when you are done",
    body: (
      <>
        After your deploy works, go back to <b>Tokens (classic)</b> and click <b>Delete</b> on
        the token so it cannot be misused.
      </>
    ),
  },
];

export default function GithubTokenGuide() {
  return (
    <details className="px-details">
      <summary>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-text)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <circle cx="12" cy="12" r="10" /><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3M12 17h.01" />
        </svg>
        How do I get a GitHub token?
      </summary>

      <div className="px-details-body">
        <div className="px-alert px-alert-info" style={{ marginBottom: 14 }}>
          <span>
            <strong>Shortcut:</strong> this link opens GitHub’s form with the name and both scopes filled in. Check they’re ticked before generating.
            <a
            href="https://github.com/settings/tokens/new?scopes=repo,workflow&description=ProtoDeploy"
            target="_blank"
            rel="noreferrer"
            style={{ fontWeight: 700, display: "block", marginTop: 6 }}>
              Create token ↗
            </a>
          </span>
        </div>

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
