const API = import.meta.env.VITE_API_URL ?? "http://localhost:8004";

export interface DeployResult {
  owner: string;
  repo: string;
  stack: { frontend: string; backend: string };
  repo_url: string;
  frontend_url: string;
  backend_deploy_url: string;
  backend_url: string;
  actions_url: string;
}

export async function deployProject(
  file: File,
  token: string,
  repoName: string
): Promise<DeployResult> {
  const form = new FormData();
  form.append("file", file);
  form.append("github_token", token);
  form.append("repo_name", repoName);

  const res = await fetch(`${API}/api/protodeploy/deploy`, {
    method: "POST",
    body: form,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail ?? "Deployment failed");
  return data;
}

export async function getBuildStatus(owner: string, repo: string) {
  const res = await fetch(
    `${API}/api/protodeploy/status?owner=${owner}&repo=${repo}`
  );
  return res.json() as Promise<{ status: string; conclusion: string | null }>;
}