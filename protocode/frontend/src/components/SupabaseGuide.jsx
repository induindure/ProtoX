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
    <details style={{
      border: '1px solid var(--border)',
      borderRadius: '6px',
      background: 'var(--surface2)',
      padding: '0.6rem 0.9rem',
    }}>
      <summary style={{ cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem' }}>
        How do I get my Supabase database URL?
      </summary>

      <ol style={{
        margin: '0.75rem 0 0',
        paddingLeft: '1.2rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.6rem',
        fontSize: '0.83rem',
        lineHeight: 1.5,
      }}>
        {steps.map((s, i) => (
          <li key={i}>
            <div style={{ fontWeight: 700 }}>{s.title}</div>
            <div style={{ color: 'var(--text-muted)' }}>{s.body}</div>
          </li>
        ))}
      </ol>

      <div style={{ marginTop: '0.75rem', fontSize: '0.8rem' }}>
        It should look like this:
        <pre style={{
          margin: '0.35rem 0 0',
          padding: '0.5rem 0.7rem',
          background: '#fff',
          border: '1px solid var(--border)',
          borderRadius: '5px',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.75rem',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-all',
        }}>
{`postgresql://postgres.<project-ref>:<your-password>@aws-1-<region>.pooler.supabase.com:5432/postgres`}
        </pre>
      </div>
    </details>
  )
}