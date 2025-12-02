import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import '../styles/AccountManager.css'

interface Account {
  account_no: number
  name: string
  balance: number
}

interface AccountManagerProps {
  initialTab?: 'create' | 'manage'
}

const AccountManager = ({ initialTab = 'manage' }: AccountManagerProps) => {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<'create' | 'manage'>(initialTab)
  const [accounts, setAccounts] = useState<Account[]>([])
  const [selectedAccount, setSelectedAccount] = useState<number | null>(null)
  const [accountDetails, setAccountDetails] = useState<Account | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  // Create account form
  const [newAccountName, setNewAccountName] = useState('')
  const [initialBalance, setInitialBalance] = useState('')
  const [newPassword, setNewPassword] = useState('')

  // Transaction form
  const [transactionType, setTransactionType] = useState<'topup' | 'withdraw'>('topup')
  const [transactionAmount, setTransactionAmount] = useState('')

  useEffect(() => {
    setActiveTab(initialTab)
  }, [initialTab])

  const createAccount = async () => {
    if (!newAccountName.trim()) {
      setError('Please enter an account name')
      setTimeout(() => setError(null), 3000)
      return
    }

    if (!newPassword.trim() || newPassword.length < 8) {
      setError('Password must be at least 8 characters')
      setTimeout(() => setError(null), 3000)
      return
    }

    const hasNumber = /\d/.test(newPassword)
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(newPassword)
    if (!hasNumber || !hasSpecialChar) {
      setError('Password must contain at least 1 number and 1 special character')
      setTimeout(() => setError(null), 3000)
      return
    }

    const balance = parseFloat(initialBalance) || 0
    if (balance < 0) {
      setError('Initial balance cannot be negative')
      setTimeout(() => setError(null), 3000)
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(null)
    
    try {
      const response = await fetch('/api/account', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newAccountName.trim(),
          balance: balance,
          password: newPassword
        })
      })

      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to create account')
      }

      const accountNo = Array.isArray(data.account_no) ? data.account_no[0] : data.account_no
      setAccounts([...accounts, { ...data, account_no: accountNo }])
      setNewAccountName('')
      setInitialBalance('')
      setNewPassword('')
      setSuccess(`✅ Account #${accountNo} created successfully for ${data.name} with balance £${data.balance.toFixed(2)}!`)
      
      setTimeout(() => setSuccess(null), 5000)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error creating account'
      setError(errorMessage)
      setTimeout(() => setError(null), 5000)
    } finally {
      setLoading(false)
    }
  }

  const fetchAccountDetails = async (accountNo: number) => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`/api/account/${accountNo}`)
      if (!response.ok) throw new Error('Failed to fetch account')

      const data = await response.json()
      setAccountDetails(data)
      setSelectedAccount(accountNo)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error fetching account')
    } finally {
      setLoading(false)
    }
  }

  const performTransaction = async () => {
    if (!selectedAccount || !transactionAmount) return

    const amount = parseFloat(transactionAmount)
    if (isNaN(amount) || amount <= 0) {
      setError('Please enter a valid amount greater than 0')
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(null)
    try {
      const endpoint = transactionType === 'topup' 
        ? `/api/account/${selectedAccount}/topup`
        : `/api/account/${selectedAccount}/withdraw`

      const response = await fetch(endpoint, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: amount })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Transaction failed')
      }

      const data = await response.json()
      setAccountDetails({ ...accountDetails!, balance: data.new_balance })
      setTransactionAmount('')
      setSuccess(`✅ ${transactionType === 'topup' ? 'Deposit' : 'Withdrawal'} of £${amount.toFixed(2)} successful! New balance: £${data.new_balance.toFixed(2)}`)
      
      setTimeout(() => setSuccess(null), 5000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error processing transaction')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="account-manager">
      <div className="manager-header">
        <div>
          <h2>Account Management</h2>
          <p>Create, view, and manage your bank accounts</p>
        </div>
        <div className="tab-switcher">
          <button 
            className={`tab-btn ${activeTab === 'manage' ? 'active' : ''}`}
            onClick={() => { setActiveTab('manage'); navigate('/accounts'); }}
          >
            🔍 Manage Accounts
          </button>
          <button 
            className={`tab-btn ${activeTab === 'create' ? 'active' : ''}`}
            onClick={() => { setActiveTab('create'); navigate('/accounts/create'); }}
          >
            ➕ Create Account
          </button>
        </div>
      </div>

      {activeTab === 'create' && (
        <div className="create-account-section">
          <div className="card create-card">
            <div className="card-header">
              <div className="card-icon large">🏦</div>
              <div className="card-title">
                <h3>Open a New Bank Account</h3>
                <p>Start your banking journey with UNK029 Bank</p>
              </div>
            </div>
            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">Account Holder Name *</label>
                <input
                  type="text"
                  placeholder="Enter your full name"
                  value={newAccountName}
                  onChange={(e) => setNewAccountName(e.target.value)}
                  className="form-input large"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Password *</label>
                <input
                  type="password"
                  placeholder="Enter a secure password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="form-input large"
                />
                <span className="form-hint">Min 8 chars, 1 number, 1 special character (!@#$%^&*)</span>
              </div>
              <div className="form-group">
                <label className="form-label">Initial Deposit (£)</label>
                <input
                  type="number"
                  placeholder="0.00"
                  value={initialBalance}
                  onChange={(e) => setInitialBalance(e.target.value)}
                  className="form-input large"
                  min="0"
                  step="0.01"
                />
                <span className="form-hint">Minimum deposit: £0.00</span>
              </div>
              <button 
                onClick={createAccount}
                disabled={loading || !newAccountName || !newPassword}
                className="btn btn-primary btn-large"
              >
                {loading ? (
                  <>⏳ Creating Account...</>
                ) : (
                  <>🚀 Create My Account</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'manage' && (
        <div className="manage-section">
          <div className="manager-grid">
            <div className="card">
              <div className="card-header">
                <div className="card-icon">🔍</div>
                <div className="card-title">
                  <h3>Find Account</h3>
                  <p>Search by account number</p>
                </div>
              </div>
              <div className="form-grid">
                <div className="form-group">
                  <label className="form-label">Account Number</label>
                  <input
                    type="number"
                    placeholder="Enter account number"
                    onChange={(e) => {
                      const value = e.target.value
                      if (value) {
                        setSelectedAccount(parseInt(value))
                        fetchAccountDetails(parseInt(value))
                      }
                    }}
                    className="form-input"
                  />
                </div>
              </div>
            </div>

            <div className="card quick-actions-card">
              <div className="card-header">
                <div className="card-icon">⚡</div>
                <div className="card-title">
                  <h3>Quick Actions</h3>
                  <p>Common banking operations</p>
                </div>
              </div>
              <div className="quick-actions-grid">
                <button className="quick-action-btn" onClick={() => { setActiveTab('create'); navigate('/accounts/create'); }}>
                  <span>➕</span>
                  <span>New Account</span>
                </button>
                <button className="quick-action-btn" onClick={() => navigate('/ai-assistant')}>
                  <span>🤖</span>
                  <span>AI Help</span>
                </button>
              </div>
            </div>
          </div>

          {accountDetails && (
            <div className="account-details-card">
              <div className="details-header">
                <h3>📋 Account Information</h3>
                <span className="account-badge">Active</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Account Number</span>
                <span className="detail-value">#{accountDetails.account_no}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Account Holder</span>
                <span className="detail-value">{accountDetails.name}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Current Balance</span>
                <span className="detail-value balance">£{accountDetails.balance.toFixed(2)}</span>
              </div>
            </div>
          )}

          {selectedAccount && accountDetails && (
            <div className="card transaction-card">
              <div className="card-header">
                <div className="card-icon">💳</div>
                <div className="card-title">
                  <h3>Transactions</h3>
                  <p>Deposit or withdraw funds from Account #{selectedAccount}</p>
                </div>
              </div>
              <div className="form-grid">
                <div className="form-group">
                  <label className="form-label">Transaction Type</label>
                  <div className="transaction-type-selector">
                    <button
                      className={`type-option ${transactionType === 'topup' ? 'active' : ''}`}
                      onClick={() => setTransactionType('topup')}
                    >
                      💰 Deposit
                    </button>
                    <button
                      className={`type-option ${transactionType === 'withdraw' ? 'active' : ''}`}
                      onClick={() => setTransactionType('withdraw')}
                    >
                      💸 Withdraw
                    </button>
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Amount (£)</label>
                  <input
                    type="number"
                    placeholder="0.00"
                    value={transactionAmount}
                    onChange={(e) => setTransactionAmount(e.target.value)}
                    className="form-input"
                    min="0"
                    step="0.01"
                  />
                </div>
                <button 
                  onClick={performTransaction}
                  disabled={loading || !transactionAmount}
                  className={`btn ${transactionType === 'topup' ? 'btn-success' : 'btn-danger'}`}
                >
                  {loading ? '⏳ Processing...' : (transactionType === 'topup' ? '💰 Deposit Funds' : '💸 Withdraw Funds')}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="error-message">
          <span>⚠️</span>
          {error}
        </div>
      )}

      {success && (
        <div className="success-message">
          <span>✅</span>
          {success}
        </div>
      )}
    </div>
  )
}

export default AccountManager
