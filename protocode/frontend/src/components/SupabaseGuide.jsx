const steps = [
  {
    title: 'Open Supabase',
    body: (
      <>Go to <b>supabase.com/dashboard</b> and sign in (GitHub login works).</>
    ),
  },
  {
    title: 'Create a project (or open an existing one)',
    body: (
      <>
        Click <b>New project</b>. Enter a name, choose a region close to you, and set a{' '}
        <b>Database Password</b>. Use a password with only letters and numbers, and no special characters. Save that password somewhere now, because you need it in
        step 5. Click <b>Create new project</b> and wait a minute or two until it finishes
        setting up.
      </>
    ),
  },
  {
    title: 'Click Connect',
    body: (
      <>
        Open your project. In the top bar of the project dashboard, click the{' '}
        <b>Connect</b> button.
      </>
    ),
  },
  {
    title: 'Choose Session pooler',
    body: (
      <>
        In the Connect dialog, select the <b>Session pooler</b> connection string (not Direct
        connection, which needs IPv6 and often fails on home networks). Copy the connection string with
        the copy button.
      </>
    ),
  },
  {
    title: 'Put your password in',
    body: (
      <>
        The copied string has <code>[YOUR-PASSWORD]</code> in it. Replace that whole
        placeholder, brackets included, with the database password from step 2. It is the{' '}
        <b>database password</b>.
      </>
    ),
  },
  {
    title: 'Forgot the password?',
    body: (
      <>
        In Supabase, in your project, go to <b>Database (in the sidebar on the left) → Settings → Database password </b> and click{' '}
        <b>Reset password</b> next to <b>Reset database password</b>. The old password stops working immediately, so update
        the URL anywhere you already used it.
      </>
    ),
  },
  {
    title: 'Paste it into ProtoCode',
    body: <>Paste the final URL into the Database URL field above.</>,
  },
]

export default function SupabaseGuide() {
  return (
    <details className="px-details">
      <summary>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-text)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <circle cx="12" cy="12" r="10" /><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3M12 17h.01" />
        </svg>
        How do I get my Supabase database URL?
      </summary>

      <div className="px-details-body">
        <ol className="px-timeline">
          {steps.map((s, i) => (
            <li key={i}>
              <div className="px-timeline-rail">
                <span className="px-timeline-dot" style={{ background: 'var(--accent-soft)', color: 'var(--accent-text)' }}>{i + 1}</span>
              </div>
              <div className="px-timeline-body">
                <p style={{ margin: '3px 0 2px', fontWeight: 700 }}>{s.title}</p>
                <p className="px-small" style={{ margin: 0, color: 'var(--muted)' }}>{s.body}</p>
              </div>
            </li>
          ))}
        </ol>

        <p className="px-small" style={{ margin: '4px 0 6px', fontWeight: 600 }}>It should look like this:</p>
        <pre className="px-code px-code-wrap" style={{ border: '1px solid var(--border)', borderRadius: 10, padding: '10px 12px', fontSize: 12 }}>
{`postgresql://postgres.<project-ref>:<your-password>@aws-1-<region>.pooler.supabase.com:5432/postgres`}
        </pre>
      </div>
    </details>
  )
}
