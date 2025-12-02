import { useState, useEffect } from 'react'
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import './App.css'
import BankChat from './components/BankChat'
import AccountManager from './components/AccountManager'
import Dashboard from './components/Dashboard'
import LoginForm from './components/LoginForm'
import Header from './components/Header'
import { ErrorBoundary } from './components/ErrorBoundary'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    const token = localStorage.getItem('auth_token')
    return !!token
  })
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogin = () => {
    setIsAuthenticated(true)
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('username')
    setIsAuthenticated(false)
  }

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isAuthenticated && location.pathname !== '/') {
      navigate('/')
    }
  }, [isAuthenticated, location.pathname, navigate])

  if (!isAuthenticated) {
    return <LoginForm onLogin={handleLogin} />
  }

  return (
    <ErrorBoundary>
      <div className="app">
        <div className="full-page-view">
          <Header onLogout={handleLogout} />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<Navigate to="/ai-assistant" replace />} />
              <Route path="/ai-assistant" element={<BankChat />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/accounts" element={<AccountManager initialTab="manage" />} />
              <Route path="/accounts/create" element={<AccountManager initialTab="create" />} />
              <Route path="*" element={<Navigate to="/ai-assistant" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </ErrorBoundary>
  )
}

export default App
