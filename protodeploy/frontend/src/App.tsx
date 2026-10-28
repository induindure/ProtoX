import { useEffect, useRef, useState } from "react";
import { deployProject, getBuildStatus, type DeployResult } from "./api";

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

  const link = "text-blue-600 underline break-all";

  return (
    <div className="mx-auto max-w-xl space-y-4 p-6">
      <h1 className="text-2xl font-bold">ProtoDeploy</h1>
      <p className="text-sm text-gray-600">
        Upload the ZIP from ProtoCode. We push it to GitHub and deploy it.
      </p>

      <input
        type="file"
        accept=".zip"
        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        className="block w-full rounded border p-2"
      />
      <input
        className="w-full rounded border p-2"
        placeholder="Repository name"
        value={repo}
        onChange={(e) => setRepo(e.target.value)}
      />
      <input
        type="password"
        className="w-full rounded border p-2"
        placeholder="GitHub token (classic, scopes: repo + workflow)"
        value={token}
        onChange={(e) => setToken(e.target.value)}
      />

      <button
        onClick={handleDeploy}
        disabled={loading || !file || !repo || !token}
        className="rounded bg-black px-4 py-2 text-white disabled:opacity-50"
      >
        {loading ? "Deploying..." : "Deploy to GitHub"}
      </button>

      {error && <p className="text-red-600">{error}</p>}

      {result && (
        <div className="space-y-2 rounded border p-4">
          <p>Detected: <b>{result.stack.frontend}</b> + <b>{result.stack.backend}</b></p>
          <p>Frontend build: <b>{build}</b></p>
          <p>Repo: <a className={link} href={result.repo_url} target="_blank">{result.repo_url}</a></p>
          <p>Live frontend: <a className={link} href={result.frontend_url} target="_blank">{result.frontend_url}</a></p>
          <p>Backend: <a className={link} href={result.backend_deploy_url} target="_blank">Deploy on Render (one click)</a></p>
          <p>Build logs: <a className={link} href={result.actions_url} target="_blank">{result.actions_url}</a></p>
        </div>
      )}
    </div>
  );
}