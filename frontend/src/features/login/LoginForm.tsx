import { useState, type FormEvent } from 'react'

import { api, ApiError } from '../../api/client'
import type { LoginResponse } from '../../api/types'
import styles from './LoginForm.module.css'

interface Props {
  onLoggedIn: (result: LoginResponse) => void
}

const USERNAME = /^[A-Za-z0-9_]{3,20}$/
const PIN = /^[0-9]{4}$/

function LoginForm({ onLoggedIn }: Props) {
  const [username, setUsername] = useState('')
  const [pin, setPin] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!USERNAME.test(username.trim())) {
      setError('Usernames are 3 to 20 letters, numbers or underscores.')
      return
    }
    if (!PIN.test(pin)) {
      setError('Your PIN is exactly 4 digits.')
      return
    }
    setBusy(true)
    setError(null)
    try {
      onLoggedIn(await api.login(username.trim(), pin))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.')
      setBusy(false)
    }
  }

  return (
    <main className={styles.page}>
      <form className={styles.card} onSubmit={(e) => void submit(e)} noValidate>
        <img className={styles.logo} src="/foodics-logo.svg" alt="Foodics" />
        <h1 className={styles.title}>Corner Table</h1>
        <p className={styles.subtitle}>Your ordering assistant that remembers what you like.</p>
        <label className={styles.label}>
          Username
          <input
            className={styles.input}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            autoFocus
          />
        </label>
        <label className={styles.label}>
          4-digit PIN
          <input
            className={styles.input}
            value={pin}
            onChange={(e) => setPin(e.target.value.replace(/\D/g, '').slice(0, 4))}
            inputMode="numeric"
            type="password"
            autoComplete="current-password"
          />
        </label>
        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}
        <button className={styles.button} type="submit" disabled={busy}>
          {busy ? 'Signing in…' : 'Continue'}
        </button>
        <p className={styles.hint}>New name? We will create your profile with this PIN.</p>
      </form>
    </main>
  )
}

export default LoginForm
