import { useEffect, useState, type FormEvent } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'

import { login, resendVerification, signup, verifyEmail } from '../../api/auth'
import { getErrorMessage } from '../../api/client'
import { useAuth } from './AuthContext'
import AuthShell from './AuthShell'

type Mode = 'login' | 'signup' | 'verify'

const inputClass =
  'w-full rounded-xl border border-gray-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-teal-400'
const primaryButton =
  'w-full rounded-xl bg-brand-teal text-white font-semibold py-2.5 hover:opacity-90 disabled:opacity-60 transition'
const linkButton = 'font-semibold text-brand-teal hover:underline disabled:opacity-50 disabled:no-underline'

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
        toast('Please verify your email first. We sent you a new code.', { icon: '✉️' })
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
        <div className="text-4xl mb-3">✉️</div>
        <h1 className="text-2xl font-bold text-gray-900">Check your email</h1>
        <p className="text-sm text-gray-600 mt-2">
          We sent a 6-digit code to <span className="font-semibold text-gray-900">{email}</span>.
          It expires in 10 minutes.
        </p>

        <form onSubmit={handleVerify} className="mt-6 space-y-4">
          <div>
            <label htmlFor="code" className="block text-sm font-medium text-gray-700 mb-1">Verification code</label>
            <input
              id="code"
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              autoFocus
              maxLength={6}
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              className="w-full rounded-xl border border-gray-300 px-4 py-3 text-center text-2xl font-bold tracking-[0.5em] focus:outline-none focus:ring-2 focus:ring-teal-400"
              placeholder="••••••"
            />
          </div>

          <button type="submit" disabled={loading || code.length !== 6} className={primaryButton}>
            {loading ? 'Checking…' : 'Verify email'}
          </button>
        </form>

        <div className="text-sm text-gray-500 text-center mt-6 space-y-2">
          <p>
            Didn't get it? Check spam, or{' '}
            <button type="button" onClick={handleResend} disabled={loading || cooldown > 0} className={linkButton}>
              {cooldown > 0 ? `send a new code in ${cooldown}s` : 'send a new code'}
            </button>
          </p>
          <p>
            Wrong email?{' '}
            <button type="button" onClick={() => switchMode('signup')} className={linkButton}>Start over</button>
          </p>
        </div>
      </AuthShell>
    )
  }

  // ---------- screen: log in / sign up ----------
  const isSignup = mode === 'signup'

  return (
    <AuthShell>
      <h1 className="text-2xl font-bold text-gray-900">
        {isSignup ? 'Create your account' : 'Log in to ProtoX'}
      </h1>
      <p className="text-sm text-gray-500 mt-1">
        {isSignup ? 'Your ideas stay private to your account.' : 'Welcome back. Pick up where you left off.'}
      </p>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputClass}
            placeholder="you@example.com"
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <input
            id="password"
            type="password"
            required
            autoComplete={isSignup ? 'new-password' : 'current-password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={inputClass}
            placeholder={isSignup ? 'At least 8 characters' : '••••••••'}
          />
        </div>

        {isSignup && (
          <div>
            <label htmlFor="confirm" className="block text-sm font-medium text-gray-700 mb-1">Confirm password</label>
            <input
              id="confirm"
              type="password"
              required
              autoComplete="new-password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              className={inputClass}
            />
          </div>
        )}

        <button type="submit" disabled={loading} className={primaryButton}>
          {loading ? 'Please wait…' : isSignup ? 'Sign up' : 'Log in'}
        </button>
      </form>

      <p className="text-sm text-gray-500 text-center mt-6">
        {isSignup ? 'Already have an account?' : "Don't have an account?"}{' '}
        <button type="button" onClick={() => switchMode(isSignup ? 'login' : 'signup')} className={linkButton}>
          {isSignup ? 'Log in' : 'Sign up'}
        </button>
      </p>
    </AuthShell>
  )
}