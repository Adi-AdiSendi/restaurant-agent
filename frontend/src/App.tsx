import { useCallback, useEffect, useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router'

import { api } from './api/client'
import LoginForm from './features/login/LoginForm'
import MenuPage from './features/menu/MenuPage'
import RestaurantsPage from './features/restaurants/RestaurantsPage'
import AppShell from './features/shell/AppShell'
import StartupScreen from './features/startup/StartupScreen'
import { useServerReady } from './features/startup/useServerReady'

type Session =
  { status: 'checking' } | { status: 'out' } | { status: 'in'; username: string; isNew: boolean }

function App() {
  const server = useServerReady()
  const [session, setSession] = useState<Session>({ status: 'checking' })

  useEffect(() => {
    if (server.state !== 'ready') return
    api
      .me()
      .then((me) => setSession({ status: 'in', username: me.username, isNew: false }))
      .catch(() => setSession({ status: 'out' }))
  }, [server.state])

  const logout = useCallback(() => {
    api.logout().catch(() => undefined)
    setSession({ status: 'out' })
  }, [])

  if (server.state === 'waking' || server.state === 'down') {
    return <StartupScreen down={server.state === 'down'} onRetry={server.retry} />
  }
  if (session.status === 'checking') return null
  if (session.status === 'out') {
    // Before the router, so a deep link survives logging in.
    return (
      <LoginForm
        onLoggedIn={(r) => setSession({ status: 'in', username: r.username, isNew: r.is_new })}
      />
    )
  }
  const { username, isNew } = session
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell username={username} onLogout={logout} />}>
          <Route index element={<RestaurantsPage />} />
          <Route
            path="r/:slug"
            element={<MenuPage username={username} isNew={isNew} onLogout={logout} />}
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
