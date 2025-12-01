import { useState } from 'react'
import '../styles/Dashboard.css'

interface QuickStat {
  label: string
  value: string
  icon: string
  trend?: string
}

const Dashboard = () => {
  const [stats] = useState<QuickStat[]>([
    { label: 'Total Balance', value: '£0.00', icon: '💰', trend: '+12%' },
    { label: 'Active Accounts', value: '0', icon: '📊', trend: '+2' },
    { label: 'Transactions', value: '0', icon: '💳', trend: '+5' },
    { label: 'AI Queries', value: '0', icon: '🤖', trend: '+8' },
  ])

  const [recentActivity] = useState([
    { type: 'Deposit', amount: '+£500.00', account: 'Account #1', time: '2 hours ago', status: 'completed' },
    { type: 'Withdrawal', amount: '-£200.00', account: 'Account #2', time: '5 hours ago', status: 'completed' },
    { type: 'AI Query', amount: 'Balance Check', account: 'Chat', time: '1 day ago', status: 'info' },
  ])

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h2>Welcome back! 👋</h2>
          <p>Here's what's happening with your accounts today.</p>
        </div>
        <button className="btn-primary">
          <span>➕</span>
          New Account
        </button>
      </div>

      <div className="stats-grid">
        {stats.map((stat, index) => (
          <div key={index} className="stat-card">
            <div className="stat-icon">{stat.icon}</div>
            <div className="stat-content">
              <div className="stat-label">{stat.label}</div>
              <div className="stat-value">{stat.value}</div>
              {stat.trend && (
                <div className="stat-trend positive">
                  ↗ {stat.trend}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="dashboard-grid">
        <div className="card">
          <div className="card-header">
            <h3>Recent Activity</h3>
            <button className="btn-text">View All</button>
          </div>
          <div className="activity-list">
            {recentActivity.map((activity, index) => (
              <div key={index} className="activity-item">
                <div className={`activity-icon ${activity.status}`}>
                  {activity.type === 'Deposit' ? '↓' : activity.type === 'Withdrawal' ? '↑' : '💬'}
                </div>
                <div className="activity-details">
                  <div className="activity-type">{activity.type}</div>
                  <div className="activity-account">{activity.account}</div>
                </div>
                <div className="activity-meta">
                  <div className={`activity-amount ${activity.status}`}>
                    {activity.amount}
                  </div>
                  <div className="activity-time">{activity.time}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Quick Actions</h3>
          </div>
          <div className="quick-actions">
            <button className="action-btn">
              <span className="action-icon">💸</span>
              <span className="action-label">Send Money</span>
            </button>
            <button className="action-btn">
              <span className="action-icon">💰</span>
              <span className="action-label">Deposit</span>
            </button>
            <button className="action-btn">
              <span className="action-icon">📊</span>
              <span className="action-label">View Reports</span>
            </button>
            <button className="action-btn">
              <span className="action-icon">🤖</span>
              <span className="action-label">Ask AI</span>
            </button>
          </div>
        </div>
      </div>

      <div className="card insights-card">
        <div className="card-header">
          <h3>AI Insights</h3>
          <span className="badge">Beta</span>
        </div>
        <div className="insights-content">
          <div className="insight">
            <span className="insight-icon">💡</span>
            <p>Your spending is 15% lower this month. Great job managing your finances!</p>
          </div>
          <div className="insight">
            <span className="insight-icon">📈</span>
            <p>Consider moving £2,000 to a savings account to maximize your interest earnings.</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
