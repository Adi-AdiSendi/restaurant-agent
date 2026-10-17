import { useCallback, useEffect, useState } from 'react'

import { api } from './api/client'
import ChatPage from './features/chat/ChatPage'
import LoginForm from './features/login/LoginForm'
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
    return (
      <LoginForm
        onLoggedIn={(r) => setSession({ status: 'in', username: r.username, isNew: r.is_new })}
      />
    )
  }
  return <ChatPage username={session.username} isNew={session.isNew} onLogout={logout} />
}

export default App
