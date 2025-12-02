import { useNavigate, useLocation } from 'react-router-dom'
import '../styles/Header.css'

interface HeaderProps {
  onLogout: () => void
}

const Header = ({ onLogout }: HeaderProps) => {
  const navigate = useNavigate()
  const location = useLocation()
  const username = localStorage.getItem('username') || 'User'

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('username')
    onLogout()
    navigate('/')
  }

  const isActive = (path: string) => location.pathname === path

  return (
    <header className="app-header">
      <div className="header-left">
        <div className="logo" onClick={() => navigate('/dashboard')} style={{ cursor: 'pointer' }}>
          <div className="logo-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3"/>
            </svg>
          </div>
          <div className="logo-text">
            <span className="logo-name">UNK029</span>
            <span className="logo-tagline">Digital Banking</span>
          </div>
        </div>
      </div>
      
      <div className="header-right">
        <nav className="main-nav">
          <button 
            className={`nav-link ${isActive('/dashboard') ? 'active' : ''}`}
            onClick={() => navigate('/dashboard')}
          >
            <span className="nav-icon">📊</span>
            <span className="nav-text">Dashboard</span>
          </button>
          <button 
            className={`nav-link ${isActive('/accounts') ? 'active' : ''}`}
            onClick={() => navigate('/accounts')}
          >
            <span className="nav-icon">💳</span>
            <span className="nav-text">Accounts</span>
          </button>
        </nav>
        <button className="ai-btn" onClick={() => navigate('/ai-assistant')}>
          <span className="ai-icon">✨</span>
          <span className="ai-btn-text">Ask AI</span>
        </button>
        <div className="user-menu">
          <div className="user-avatar">{username.charAt(0).toUpperCase()}</div>
          <div className="user-info">
            <span className="user-name">{username}</span>
            <span className="user-role">Personal Account</span>
          </div>
          <button className="logout-btn" onClick={handleLogout} title="Logout">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>
            </svg>
            <span className="logout-text">Logout</span>
          </button>
        </div>
      </div>
    </header>
  )
}

export default Header
