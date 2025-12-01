import { useState } from 'react'
import './App.css'
import BankChat from './components/BankChat'
import AccountManager from './components/AccountManager'
import Dashboard from './components/Dashboard'
import LoginForm from './components/LoginForm'
import { ErrorBoundary } from './components/ErrorBoundary'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    const token = localStorage.getItem('auth_token')
    return !!token
  })
  const [activeView, setActiveView] = useState<'chat' | 'dashboard' | 'accounts'>('chat')

  const handleLogin = () => {
    setIsAuthenticated(true)
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('username')
    setIsAuthenticated(false)
    setActiveView('chat')
  }

  if (!isAuthenticated) {
    return <LoginForm onLogin={handleLogin} />
  }

  return (
    <ErrorBoundary>
      <div className="app">
        {activeView === 'chat' && <BankChat onNavigate={setActiveView} onLogout={handleLogout} />}
        {activeView === 'dashboard' && (
          <div className="full-page-view">
            <header className="view-header">
              <button className="back-btn" onClick={() => setActiveView('chat')}>
                ← Back to AI Chat
              </button>
              <h2>Dashboard</h2>
              <button className="logout-btn" onClick={handleLogout}>
                🚪 Logout
              </button>
            </header>
            <Dashboard />
          </div>
        )}
        {activeView === 'accounts' && (
          <div className="full-page-view">
            <header className="view-header">
              <button className="back-btn" onClick={() => setActiveView('chat')}>
                ← Back to AI Chat
              </button>
              <h2>Manage Accounts</h2>
              <button className="logout-btn" onClick={handleLogout}>
                🚪 Logout
              </button>
            </header>
            <AccountManager />
          </div>
        )}
      </div>
    </ErrorBoundary>
  )
}

export default App
