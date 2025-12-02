import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import '../styles/Dashboard.css'

interface Account {
  account_no: number
  name: string
  balance: number
}

const Dashboard = () => {
  const navigate = useNavigate()
  const [isLoaded, setIsLoaded] = useState(false)
  const [accounts, setAccounts] = useState<Account[]>([])
  const [totalBalance, setTotalBalance] = useState(0)
  const username = localStorage.getItem('username') || 'User'
  
  const currentDate = new Date().toLocaleDateString('en-GB', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })

  useEffect(() => {
    setIsLoaded(true)
    // Fetch accounts from API
    const fetchAccounts = async () => {
      try {
        const response = await fetch('/api/account/')
        if (response.ok) {
          const data = await response.json()
          setAccounts(data)
          const total = data.reduce((sum: number, acc: Account) => sum + acc.balance, 0)
          setTotalBalance(total)
        }
      } catch (error) {
        console.error('Failed to fetch accounts:', error)
      }
    }
    fetchAccounts()
  }, [])

  const handleQuickAction = (action: string) => {
    switch (action) {
      case 'deposit':
      case 'withdraw':
      case 'view':
        navigate('/accounts')
        break
      case 'ai':
        navigate('/ai-assistant')
        break
      case 'create':
        navigate('/accounts/create')
        break
    }
  }

  return (
    <div className={`dashboard ${isLoaded ? 'loaded' : ''}`}>
      {/* Welcome Section */}
      <div className="welcome-section">
        <div className="welcome-content">
          <p className="welcome-date">{currentDate}</p>
          <h1 className="welcome-title">Welcome back, {username}!</h1>
          <p className="welcome-subtitle">Here's an overview of your financial status</p>
        </div>
        <button className="create-account-btn" onClick={() => navigate('/accounts/create')}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 5v14M5 12h14"/>
          </svg>
          Open New Account
        </button>
      </div>

      {/* Balance Overview Cards */}
      <div className="balance-cards">
        <div className="balance-card primary" onClick={() => navigate('/accounts')}>
          <div className="balance-card-header">
            <span className="balance-label">Total Balance</span>
            <div className="balance-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
              </svg>
            </div>
          </div>
          <div className="balance-amount">£{totalBalance.toLocaleString('en-GB', { minimumFractionDigits: 2 })}</div>
          <div className="balance-footer">
            <span className="balance-change positive">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M23 6l-9.5 9.5-5-5L1 18"/>
              </svg>
              Click to view accounts
            </span>
          </div>
        </div>

        <div className="balance-card secondary" onClick={() => navigate('/accounts')}>
          <div className="balance-card-header">
            <span className="balance-label">Active Accounts</span>
            <div className="balance-icon accounts">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="1" y="4" width="22" height="16" rx="2" ry="2"/>
                <line x1="1" y1="10" x2="23" y2="10"/>
              </svg>
            </div>
          </div>
          <div className="balance-amount">{accounts.length}</div>
          <div className="balance-footer">
            <span className="balance-info">Manage your accounts</span>
          </div>
        </div>

        <div className="balance-card ai-card" onClick={() => navigate('/ai-assistant')}>
          <div className="balance-card-header">
            <span className="balance-label">AI Assistant</span>
            <div className="balance-icon ai">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2a10 10 0 0 1 10 10 10 10 0 0 1-10 10A10 10 0 0 1 2 12 10 10 0 0 1 12 2z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
            </div>
          </div>
          <div className="ai-status">
            <span className="status-dot"></span>
            Online & Ready
          </div>
          <div className="balance-footer">
            <span className="balance-info">Ask anything about banking</span>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="dashboard-grid">
        {/* Quick Actions */}
        <div className="dashboard-card">
          <div className="card-header">
            <h3>Quick Actions</h3>
          </div>
          <div className="quick-actions-list">
            <button className="quick-action" onClick={() => handleQuickAction('deposit')}>
              <div className="action-icon deposit">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 19V5M5 12l7-7 7 7"/>
                </svg>
              </div>
              <div className="action-info">
                <span className="action-title">Deposit</span>
                <span className="action-desc">Add funds to account</span>
              </div>
              <svg className="action-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 18l6-6-6-6"/>
              </svg>
            </button>

            <button className="quick-action" onClick={() => handleQuickAction('withdraw')}>
              <div className="action-icon withdraw">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 5v14M19 12l-7 7-7-7"/>
                </svg>
              </div>
              <div className="action-info">
                <span className="action-title">Withdraw</span>
                <span className="action-desc">Withdraw from account</span>
              </div>
              <svg className="action-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 18l6-6-6-6"/>
              </svg>
            </button>

            <button className="quick-action" onClick={() => handleQuickAction('view')}>
              <div className="action-icon view">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
              </div>
              <div className="action-info">
                <span className="action-title">View Accounts</span>
                <span className="action-desc">Check balances & details</span>
              </div>
              <svg className="action-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 18l6-6-6-6"/>
              </svg>
            </button>

            <button className="quick-action highlight" onClick={() => handleQuickAction('ai')}>
              <div className="action-icon ai">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
              </div>
              <div className="action-info">
                <span className="action-title">AI Banking Assistant</span>
                <span className="action-desc">Get instant help with AI</span>
              </div>
              <svg className="action-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 18l6-6-6-6"/>
              </svg>
            </button>
          </div>
        </div>

        {/* AI Features Card */}
        <div className="dashboard-card ai-features">
          <div className="card-header">
            <h3>AI-Powered Features</h3>
            <span className="badge">Powered by Gemini</span>
          </div>
          <div className="ai-features-list">
            <div className="ai-feature">
              <div className="feature-icon">💬</div>
              <div className="feature-content">
                <h4>Natural Language Banking</h4>
                <p>Ask questions like "What's my balance?" or "Deposit £100"</p>
              </div>
            </div>
            <div className="ai-feature">
              <div className="feature-icon">🔍</div>
              <div className="feature-content">
                <h4>Smart Account Lookup</h4>
                <p>Find account details instantly by asking the AI</p>
              </div>
            </div>
            <div className="ai-feature">
              <div className="feature-icon">💡</div>
              <div className="feature-content">
                <h4>Financial Insights</h4>
                <p>Get personalized tips and recommendations</p>
              </div>
            </div>
          </div>
          <button className="try-ai-btn" onClick={() => navigate('/ai-assistant')}>
            Try AI Assistant
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </button>
        </div>
      </div>

      {/* Getting Started Section */}
      {accounts.length === 0 && (
        <div className="getting-started">
          <div className="getting-started-content">
            <div className="getting-started-icon">🏦</div>
            <h2>Get Started with UNK029 Banking</h2>
            <p>Create your first account to start managing your finances with AI-powered assistance</p>
            <div className="getting-started-actions">
              <button className="primary-btn" onClick={() => navigate('/accounts/create')}>
                Create Your First Account
              </button>
              <button className="secondary-btn" onClick={() => navigate('/ai-assistant')}>
                Chat with AI Assistant
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
