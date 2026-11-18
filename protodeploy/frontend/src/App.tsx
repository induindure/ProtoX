import { useEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";
import GithubTokenGuide from "./components/GithubTokenGuide";
import Header, { Hero, CheckIcon } from "./protox/Header";
import { deployProject, getBuildStatus, getBackendStatus, type DeployResult } from "./api";
import RenderGuide from "./components/RenderGuide";

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [repo, setRepo] = useState("");
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<DeployResult | null>(null);
    const [build, setBuild] = useState("starting");
  const [backendLive, setBackendLive] = useState(false);
  const [copied, setCopied] = useState(false);
  const timer = useRef<number | null>(null);
  const backendTimer = useRef<number | null>(null);

  const stopTimers = () => {
    if (timer.current) clearInterval(timer.current);
    if (backendTimer.current) clearInterval(backendTimer.current);
    timer.current = null;
    backendTimer.current = null;
  };

  useEffect(() => stopTimers, []);

  const startPolling = (owner: string, name: string, backendUrl: string) => {
    timer.current = window.setInterval(async () => {
      try {
        const s = await getBuildStatus(owner, name);
        setBuild(s.conclusion ?? s.status);
        if (s.conclusion && timer.current) clearInterval(timer.current);
      } catch { /* try again next tick */ }
    }, 5000);

    backendTimer.current = window.setInterval(async () => {
      try {
        const b = await getBackendStatus(backendUrl);
        if (b.live) {
          setBackendLive(true);
          if (backendTimer.current) clearInterval(backendTimer.current);
        }
      } catch { /* try again next tick */ }
    }, 8000);
  };

  const handleDeploy = async () => {
    if (!file) return;
    stopTimers();
    setLoading(true);
    setError("");
    setResult(null);
    setBuild("starting");
    setBackendLive(false);
    setCopied(false);
    try {
      const r = await deployProject(file, token, repo);
      setResult(r);
      startPolling(r.owner, r.repo, r.backend_url);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const buildDone = build === "success";
  const buildFailed = ["failure", "cancelled", "timed_out"].includes(build);
  const fileSize = file ? `${(file.size / 1024 / 1024).toFixed(1)} MB` : "";

  type StepState = "todo" | "active" | "done" | "error";
  const DOT: Record<StepState, CSSProperties> = {
    todo: { border: "1px solid var(--border)", color: "var(--faint)" },
    active: { background: "var(--accent-soft)", color: "var(--accent-text)" },
    done: { background: "var(--ok-soft)", color: "var(--ok)" },
    error: { background: "var(--err-soft)", color: "var(--err)" },
  };
  const buildState: StepState = !result ? "todo" : buildDone ? "done" : buildFailed ? "error" : "active";
  const steps: { title: string; state: StepState; body: ReactNode }[] = [
    {
      title: "Push to GitHub",
      state: result ? "done" : loading ? "active" : "todo",
      body: result
        ? <a href={result.repo_url} target="_blank" rel="noreferrer" style={{ wordBreak: "break-all", color: "var(--accent-text)" }}>{result.repo_url}</a>
        : loading ? "Uploading your project…" : "Creates the repository and uploads your code.",
    },
    {
      title: "Build the frontend",
      state: buildState,
      body: result
        ? <>Status: {build.replace("_", " ")} · <a href={result.actions_url} target="_blank" rel="noreferrer" style={{ color: "var(--accent-text)" }}>build logs ↗</a></>
        : "GitHub Actions builds and publishes it to GitHub Pages.",
    },
        {
      title: "Backend on Render",
      state: !result ? "todo" : backendLive ? "done" : "active",
      body: !result
        ? "You confirm it on Render with one click."
        : backendLive
          ? <>Live at <a href={result.backend_url} target="_blank" rel="noreferrer" style={{ wordBreak: "break-all", color: "var(--accent-text)" }}>{result.backend_url}</a></>
          : <>Click <b>Deploy backend on Render</b> below. This ticks by itself once {result.backend_url} is live.</>,
    },
  ];
  const allDone = !!result && buildDone && backendLive;
  const phase = allDone
    ? { cls: "px-badge-ok", label: "Live" }
    : buildFailed
      ? { cls: "px-badge-err", label: "Build failed" }
      : result || loading
        ? { cls: "px-badge-accent", label: "In progress" }
        : { cls: "px-badge-neutral", label: "Not started" };

  const apiName = result ? result.backend_url.replace("https://", "").split(".")[0] : "";

  const handleCopy = async () => {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result.frontend_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { /* clipboard blocked */ }
  };

  return (
    <div className="px-page">
      <Header current={5} />

      <Hero step={5} title="Deploy your app" compact>
        GitHub for the code and frontend, Render for the backend.
      </Hero>

      <main className="px-container" style={{ maxWidth: 1180 }}>
        <div className="px-split px-split-even">
          <section className="px-card px-stack" style={{ minWidth: 0 }}>
            <h2 className="px-h2">Settings</h2>
            <div className="px-field">
              <span className="px-label">Project ZIP</span>
              <label
                htmlFor="zip"
                style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6, padding: 22, border: "1.5px dashed var(--border)", borderRadius: 12, background: "var(--surface2)", textAlign: "center", cursor: "pointer" }}
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--accent-text)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" />
                </svg>
                <span style={{ fontWeight: 600 }}>{file ? file.name : "Choose the ZIP from ProtoCode"}</span>
                <span className="px-small px-muted">{file ? `${fileSize} · click to choose a different file` : "Download it from ProtoCode’s code panel"}</span>
              </label>
              <input
                id="zip"
                type="file"
                accept=".zip"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="px-sr-only"
              />
            </div>

            <div className="px-field">
              <label htmlFor="repo" className="px-label">Repository name</label>
              <input id="repo" className="px-input" placeholder="my-app" value={repo} onChange={(e) => setRepo(e.target.value)} />
            </div>

            <div className="px-field">
              <label htmlFor="token" className="px-label">GitHub token</label>
              <input
                id="token"
                type="password"
                className="px-input px-input-mono"
                placeholder="ghp_…"
                autoComplete="off"
                value={token}
                onChange={(e) => setToken(e.target.value)}
              />
              <span className="px-help">Classic token with <strong>repo</strong> and <strong>workflow</strong> scopes.</span>
            </div>

            <GithubTokenGuide />

            <div className="px-alert px-alert-warn">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M12 9v4M12 17h.01M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
              </svg>
              <span>Render’s free plan lets you keep only one app with saved data per account. If you’ve already deployed one, delete it or use a different Render account.</span>
            </div>

            {error && <div className="px-alert px-alert-err" role="alert">{error}</div>}

            <button onClick={handleDeploy} disabled={loading || !file || !repo || !token} className="px-btn px-btn-cta px-btn-lg px-btn-block">
              {loading ? (
                <><span className="px-spinner" /> Deploying…</>
              ) : (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M4.5 16.5c-1.5 1.3-2 5-2 5s3.7-.5 5-2c.7-.8.7-2.1-.1-2.9a2.2 2.2 0 0 0-2.9-.1zM12 15l-3-3a22 22 0 0 1 2-3.9A12.9 12.9 0 0 1 22 2c0 2.7-.8 7.5-6 11a22.4 22.4 0 0 1-4 2z" />
                  </svg>
                  Deploy to GitHub
                </>
              )}
            </button>
          </section>

          <section className="px-card px-stack px-sticky" style={{ minWidth: 0 }} aria-live="polite">
            <div className="px-between">
              <h2 className="px-h2">Live progress</h2>
              <span className={`px-badge ${phase.cls}`}>{phase.label}</span>
            </div>

            <ol className="px-timeline">
              {steps.map((st, i) => (
                <li key={st.title}>
                  <div className="px-timeline-rail">
                    <span className="px-timeline-dot" style={DOT[st.state]}>
                      {st.state === "done" ? <CheckIcon size={14} /> : st.state === "active" ? <span className="px-spinner" style={{ width: 12, height: 12 }} /> : st.state === "error" ? "!" : i + 1}
                    </span>
                  </div>
                  <div className="px-timeline-body" style={{ flex: 1 }}>
                    <p style={{ margin: "3px 0 0", fontWeight: 600, color: st.state === "todo" ? "var(--faint)" : "var(--text)" }}>{st.title}</p>
                    <div className="px-small" style={{ color: "var(--muted)", marginTop: 2 }}>{st.body}</div>
                  </div>
                </li>
              ))}
            </ol>

            {result && (
              <div className="px-stack" style={{ gap: 8, paddingTop: 14, borderTop: "1px solid var(--border)" }}>
                <a href={result.backend_deploy_url} target="_blank" rel="noreferrer" className="px-btn px-btn-cta">Deploy backend on Render ↗</a>
                <RenderGuide apiName={apiName} repo={result.repo} />

                {allDone && (
                  <div style={{ marginTop: 6 }}>
                    <p style={{ margin: "0 0 2px", fontWeight: 700 }}>Share your app</p>
                    <p className="px-small" style={{ margin: "0 0 8px", color: "var(--muted)" }}>Copy this link and send it to the world to share your app</p>
                    <div style={{ position: "relative" }}>
                      <input
                        readOnly
                        value={result.frontend_url}
                        onFocus={(e) => e.target.select()}
                        className="px-input px-input-mono"
                        style={{ width: "100%", paddingRight: 92 }}
                        aria-label="Live site link"
                      />
                      <button
                        type="button"
                        onClick={handleCopy}
                        className="px-btn"
                        style={{ position: "absolute", right: 5, top: "50%", transform: "translateY(-50%)", padding: "4px 12px", minHeight: 0 }}
                      >
                        {copied ? "Copied" : "Copy"}
                      </button>
                    </div>
                  </div>
                )}

                {allDone ? (
                  <a href={result.frontend_url} target="_blank" rel="noreferrer" className="px-btn">Open live site ↗</a>
                ) : (
                  <button type="button" className="px-btn" disabled title="Available after all 3 steps are done">Open live site ↗</button>
                )}
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}
