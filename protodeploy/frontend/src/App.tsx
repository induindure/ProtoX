import { useEffect, useRef, useState } from "react";
import { deployProject, getBuildStatus, type DeployResult } from "./api";
import GithubTokenGuide from "./components/GithubTokenGuide";
import Header, { Hero, CheckIcon } from "./protox/Header";

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [repo, setRepo] = useState("");
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<DeployResult | null>(null);
  const [build, setBuild] = useState("starting");
  const timer = useRef<number | null>(null);

  useEffect(() => () => { if (timer.current) clearInterval(timer.current); }, []);

  const startPolling = (owner: string, name: string) => {
    timer.current = window.setInterval(async () => {
      const s = await getBuildStatus(owner, name);
      setBuild(s.conclusion ?? s.status);
      if (s.conclusion && timer.current) clearInterval(timer.current);
    }, 5000);
  };

  const handleDeploy = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    setResult(null);
    setBuild("starting");
    try {
      const r = await deployProject(file, token, repo);
      setResult(r);
      startPolling(r.owner, r.repo);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const buildDone = build === "success";
  const buildFailed = ["failure", "cancelled", "timed_out"].includes(build);
  const fileSize = file ? `${(file.size / 1024 / 1024).toFixed(1)} MB` : "";

  return (
    <div className="px-page">
      <Header current={5} />

      <Hero step={5} title="Deploy your app">
        We push your project to GitHub, publish the frontend on GitHub Pages and set up the backend on Render.
      </Hero>

      <main className="px-container px-container-narrow">
        <div style={{ display: "flex", flexWrap: "wrap", gap: 20, alignItems: "flex-start" }}>
          <section className="px-card px-stack" style={{ flex: "1.2 1 440px", minWidth: 0 }}>
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

          <section className="px-card px-stack" style={{ flex: "1 1 360px", minWidth: 0 }} aria-live="polite">
            <div className="px-between">
              <h2 className="px-h2">Deployment</h2>
              {result && <span className="px-badge px-badge-accent">{result.stack.frontend} + {result.stack.backend}</span>}
            </div>

            {!result ? (
              <p className="px-muted" style={{ margin: 0 }}>
                {loading ? "Pushing your project to GitHub…" : "Fill in the form and deploy. Progress and links will appear here."}
              </p>
            ) : (
              <>
                <ol className="px-timeline">
                  <li>
                    <div className="px-timeline-rail">
                      <span className="px-timeline-dot" style={{ background: "var(--ok-soft)", color: "var(--ok)" }}><CheckIcon size={14} /></span>
                    </div>
                    <div className="px-timeline-body">
                      <p style={{ margin: "3px 0 0", fontWeight: 600 }}>Pushed to GitHub</p>
                      <a href={result.repo_url} target="_blank" rel="noreferrer" className="px-small" style={{ wordBreak: "break-all" }}>{result.repo_url}</a>
                    </div>
                  </li>
                  <li>
                    <div className="px-timeline-rail">
                      <span
                        className="px-timeline-dot"
                        style={{
                          background: buildDone ? "var(--ok-soft)" : buildFailed ? "var(--err-soft)" : "var(--accent-soft)",
                          color: buildDone ? "var(--ok)" : buildFailed ? "var(--err)" : "var(--accent-text)",
                        }}
                      >
                        {buildDone ? <CheckIcon size={14} /> : buildFailed ? "!" : <span className="px-spinner" style={{ width: 12, height: 12 }} />}
                      </span>
                    </div>
                    <div className="px-timeline-body">
                      <p style={{ margin: "3px 0 0", fontWeight: 600 }}>
                        Frontend build <span style={{ fontWeight: 500, color: "var(--muted)" }}>· {build.replace("_", " ")}</span>
                      </p>
                      <a href={result.actions_url} target="_blank" rel="noreferrer" className="px-small">View build logs ↗</a>
                    </div>
                  </li>
                  <li>
                    <div className="px-timeline-rail">
                      <span className="px-timeline-dot" style={{ border: "1px solid var(--border)", color: "var(--faint)" }}>3</span>
                    </div>
                    <div className="px-timeline-body">
                      <p style={{ margin: "3px 0 0", fontWeight: 600 }}>Backend on Render</p>
                      <p className="px-small px-muted" style={{ margin: 0 }}>One click to finish. It will run at {result.backend_url}</p>
                    </div>
                  </li>
                </ol>

                <div className="px-stack" style={{ gap: 8, paddingTop: 14, borderTop: "1px solid var(--border)" }}>
                  <a href={result.frontend_url} target="_blank" rel="noreferrer" className="px-btn">Open live site ↗</a>
                  <a href={result.backend_deploy_url} target="_blank" rel="noreferrer" className="px-btn px-btn-cta">Deploy backend on Render ↗</a>
                </div>
              </>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}
