import { useCallback, useEffect, useState } from 'react'

import { api } from './api/client'
import ChatPage from './features/chat/ChatPage'
import LoginForm from './features/login/LoginForm'

type Session =
  { status: 'checking' } | { status: 'out' } | { status: 'in'; username: string; isNew: boolean }

function App() {
  const [session, setSession] = useState<Session>({ status: 'checking' })

  useEffect(() => {
    api
      .me()
      .then((me) => setSession({ status: 'in', username: me.username, isNew: false }))
      .catch(() => setSession({ status: 'out' }))
  }, [])

  const logout = useCallback(() => {
    api.logout().catch(() => undefined)
    setSession({ status: 'out' })
  }, [])

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
