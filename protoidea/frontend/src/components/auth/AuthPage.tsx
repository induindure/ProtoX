import { useEffect, useState, type FormEvent } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'

import { login, resendVerification, signup, verifyEmail } from '../../api/auth'
import { getErrorMessage } from '../../api/client'
import { useAuth } from './AuthContext'
import AuthShell from './AuthShell'

type Mode = 'login' | 'signup' | 'verify'

export default function AuthPage() {
  const { signIn } = useAuth()
  const [mode, setMode] = useState<Mode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [cooldown, setCooldown] = useState(0)

  // Countdown for the "Send a new code" button
  useEffect(() => {
    if (cooldown <= 0) return
    const timer = setTimeout(() => setCooldown((c) => c - 1), 1000)
    return () => clearTimeout(timer)
  }, [cooldown])

  const switchMode = (next: Mode) => {
    setMode(next)
    setPassword('')
    setConfirm('')
    setCode('')
  }

  // ---------- log in / sign up ----------
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (mode === 'signup') {
      if (password.length < 8) { toast.error('Password must be at least 8 characters.'); return }
      if (password !== confirm) { toast.error('Passwords do not match.'); return }
    }

    setLoading(true)
    try {
      if (mode === 'login') {
        const user = await login(email, password)
        toast.success('Welcome back!')
        signIn(user)
      } else {
        await signup(email, password)
        setCooldown(60)
        switchMode('verify')
        toast.success('Code sent. Check your email.')
      }
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 403) {
        // Right password, but the email isn't verified yet: send a fresh code
        switchMode('verify')
        toast('Please verify your email first. We sent you a new code.')
        try {
          await resendVerification(email)
          setCooldown(60)
        } catch {
          /* the user can still press "Send a new code" */
        }
      } else {
        toast.error(getErrorMessage(err))
      }
    } finally {
      setLoading(false)
    }
  }

  // ---------- verify the 6-digit code ----------
  const handleVerify = async (e: FormEvent) => {
    e.preventDefault()
    if (!/^\d{6}$/.test(code)) { toast.error('Enter the 6-digit code from the email.'); return }

    setLoading(true)
    try {
      const user = await verifyEmail(email, code)
      toast.success('Email verified. Welcome to ProtoX!')
      signIn(user)
    } catch (err) {
      toast.error(getErrorMessage(err))
      setCode('')
    } finally {
      setLoading(false)
    }
  }

  const handleResend = async () => {
    setLoading(true)
    try {
      await resendVerification(email)
      setCooldown(60)
      setCode('')
      toast.success('A new code is on its way.')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  // ---------- screen: enter code ----------
  if (mode === 'verify') {
    return (
      <AuthShell>
        <div className="px-stack">
          <span className="px-empty-icon" style={{ width: 44, height: 44, borderRadius: 12, margin: 0 }} aria-hidden="true">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="5" width="18" height="14" rx="2" /><path d="M3 7l9 6 9-6" />
            </svg>
          </span>
          <div>
            <h2 className="px-title" style={{ fontSize: 22 }}>Check your email</h2>
            <p className="px-subtitle">
              We sent a 6-digit code to <strong style={{ color: 'var(--text)' }}>{email}</strong>. It expires in 10 minutes.
            </p>
          </div>

          <form onSubmit={handleVerify} className="px-stack">
            <div className="px-field">
              <label htmlFor="code" className="px-label">Verification code</label>
              <input
                id="code"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                autoFocus
                maxLength={6}
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                className="px-input px-input-mono"
                style={{ minHeight: 56, textAlign: 'center', fontSize: 26, fontWeight: 700, letterSpacing: '0.5em' }}
                placeholder="••••••"
              />
            </div>
            <button type="submit" disabled={loading || code.length !== 6} className="px-btn px-btn-cta px-btn-lg px-btn-block">
              {loading ? <><span className="px-spinner" /> Checking…</> : 'Verify email'}
            </button>
          </form>

          <div className="px-small px-muted" style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', gap: 4 }}>
            <p style={{ margin: 0 }}>
              Didn’t get it? Check spam, or{' '}
              <button type="button" onClick={handleResend} disabled={loading || cooldown > 0} className="px-link-btn">
                {cooldown > 0 ? `send a new code in ${cooldown}s` : 'send a new code'}
              </button>
            </p>
            <p style={{ margin: 0 }}>
              Wrong email?{' '}
              <button type="button" onClick={() => switchMode('signup')} className="px-link-btn">Start over</button>
            </p>
          </div>
        </div>
      </AuthShell>
    )
  }

  // ---------- screen: log in / sign up ----------
  const isSignup = mode === 'signup'

  return (
    <AuthShell>
      <div className="px-stack">
        <div>
          <h2 className="px-title" style={{ fontSize: 22 }}>{isSignup ? 'Create your account' : 'Log in'}</h2>
          <p className="px-subtitle">
            {isSignup ? 'Your ideas stay private to your account.' : 'Welcome back. Pick up where you left off.'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="px-stack">
          <div className="px-field">
            <label htmlFor="email" className="px-label">Email</label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="px-input"
              placeholder="you@example.com"
            />
          </div>

          <div className="px-field">
            <label htmlFor="password" className="px-label">Password</label>
            <input
              id="password"
              type="password"
              required
              autoComplete={isSignup ? 'new-password' : 'current-password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="px-input"
              placeholder={isSignup ? 'At least 8 characters' : '••••••••'}
            />
          </div>

          {isSignup && (
            <div className="px-field">
              <label htmlFor="confirm" className="px-label">Confirm password</label>
              <input
                id="confirm"
                type="password"
                required
                autoComplete="new-password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                className="px-input"
              />
            </div>
          )}

          <button type="submit" disabled={loading} className="px-btn px-btn-cta px-btn-lg px-btn-block">
            {loading ? <><span className="px-spinner" /> Please wait…</> : isSignup ? 'Create account' : 'Log in'}
          </button>
        </form>

        <p className="px-small px-muted" style={{ margin: 0, textAlign: 'center' }}>
          {isSignup ? 'Already have an account?' : 'New to ProtoX?'}{' '}
          <button type="button" onClick={() => switchMode(isSignup ? 'login' : 'signup')} className="px-link-btn">
            {isSignup ? 'Log in' : 'Create an account'}
          </button>
        </p>
      </div>
    </AuthShell>
  )
}
