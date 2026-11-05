import type { ReactNode } from "react";

const C = ({ children }: { children: ReactNode }) => (
  <code className="rounded bg-gray-200 px-1">{children}</code>
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
    <details className="rounded border bg-gray-50 p-3">
      <summary className="cursor-pointer text-sm font-semibold">
        How do I get a GitHub token?
      </summary>

      <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm">
        {steps.map((s, i) => (
          <li key={i}>
            <div className="font-bold">{s.title}</div>
            <div className="text-gray-600">{s.body}</div>
          </li>
        ))}
      </ol>

      <p className="mt-3 text-xs">
        Shortcut: this link opens the form with the name and both scopes already filled in
        (check they are ticked before generating):{" "}
        <a
          className="text-blue-600 underline"
          href="https://github.com/settings/tokens/new?scopes=repo,workflow&description=ProtoDeploy"
          target="_blank"
          rel="noreferrer"
        >
          Create token
        </a>
      </p>
    </details>
  );
}