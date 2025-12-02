import { useState, useCallback } from 'react'
import '../styles/LoginForm.css'

interface LoginFormProps {
  onLogin: (token: string) => void
}

const LoginForm = ({ onLogin }: LoginFormProps) => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    
    // Basic client-side validation
    if (!username.trim()) {
      setError('Username is required')
      return
    }
    if (!password) {
      setError('Password is required')
      return
    }
    
    setIsLoading(true)

    // Simulate loading delay
    await new Promise(resolve => setTimeout(resolve, 800))

    try {
      // Hardcoded credentials for demo
      if (username === 'bank' && password === 'Bank@2025') {
        const mockToken = 'demo_token_' + Date.now()
        localStorage.setItem('auth_token', mockToken)
        localStorage.setItem('username', username)
        onLogin(mockToken)
      } else {
        throw new Error('Invalid credentials')
      }
    } catch (error) {
      setError('Invalid username or password. Demo: username "bank", password "Bank@2025"')
      console.error('Login error:', error)
    } finally {
      setIsLoading(false)
    }
  }, [username, password, onLogin])

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <div className="login-logo">
              <svg width="60" height="60" viewBox="0 0 60 60" fill="none">
                <rect width="60" height="60" rx="15" fill="url(#gradient)" />
                <path d="M30 18L39 24V36L30 42L21 36V24L30 18Z" fill="white" opacity="0.9" />
                <defs>
                  <linearGradient id="gradient" x1="0" y1="0" x2="60" y2="60">
                    <stop offset="0%" stopColor="#3b82f6" />
                    <stop offset="100%" stopColor="#14b8a6" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <h1>UNK029 Bank</h1>
            <p>Sign in to access your AI banking assistant</p>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            <div className="form-group">
              <label htmlFor="username">Username</label>
              <div className="input-wrapper">
                <span className="input-icon">👤</span>
                <input
                  id="username"
                  type="text"
                  placeholder="bank"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  autoComplete="username"
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <div className="input-wrapper">
                <span className="input-icon">🔒</span>
                <input
                  id="password"
                  type="password"
                  placeholder="Bank@2025"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                />
              </div>
            </div>

            {error && (
              <div className="error-message">
                ⚠️ {error}
              </div>
            )}

            <button 
              type="submit" 
              className="login-button"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <span className="spinner"></span>
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </button>

          </form>
        </div>
      </div>
    </div>
  )
}

export default LoginForm
