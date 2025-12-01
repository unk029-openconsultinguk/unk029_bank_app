import { useState, useRef, useEffect, useCallback } from 'react'
import '../styles/BankChat.css'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  error?: boolean
}

interface BankChatProps {
  onNavigate: (view: 'chat' | 'dashboard' | 'accounts') => void
  onLogout: () => void
}

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

const BankChat = ({ onNavigate, onLogout }: BankChatProps) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m your AI banking assistant powered by Google Gemini. I can help you with account information, deposits, withdrawals, and answer any banking questions. How may I assist you today?',
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // Pre-warm AI agent on component mount
  useEffect(() => {
    const warmUp = async () => {
      try {
        // Send a quick warmup request to initialize Gemini
        await fetch(`${API_BASE_URL}/api/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: 'ping' })
        })
      } catch {
        // Ignore warmup errors
      }
    }
    warmUp()
  }, [])

  const quickPrompts = [
    "What's my account balance?",
    "Deposit £500 to account 1",
    "Withdraw £200 from account 1"
  ]

  const sendMessage = useCallback(async (messageText?: string) => {
    const textToSend = messageText || input
    if (!textToSend.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: textToSend,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 15000) // 15 second timeout

      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ message: textToSend }),
        signal: controller.signal
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Server error' }))
        throw new Error(errorData.message || `Server responded with ${response.status}`)
      }

      const data = await response.json()

      if (!data.reply) {
        throw new Error('Invalid response format')
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.reply,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Chat error:', error)
      const errorMsg = error instanceof Error ? (
        error.name === 'AbortError' 
          ? 'Request timed out. Please try again.' 
          : error.message
      ) : 'Connection error. Please check your connection and try again.'
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `⚠️ ${errorMsg}`,
        timestamp: new Date(),
        error: true
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }, [input, isLoading])

  const handleKeyPress = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }, [sendMessage])

  return (
    <div className="bank-chat">
      {/* Modern Header with Navigation */}
      <div className="chat-header">
        <div className="chat-header-left">
          <div className="chat-avatar-logo">
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none" aria-label="UNK029 Logo">
              <rect width="40" height="40" rx="10" fill="url(#gradient)" />
              <path d="M20 12L26 16V24L20 28L14 24V16L20 12Z" fill="white" opacity="0.9" />
              <defs>
                <linearGradient id="gradient" x1="0" y1="0" x2="40" y2="40">
                  <stop offset="0%" stopColor="#3b82f6" />
                  <stop offset="100%" stopColor="#14b8a6" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <div className="chat-header-info">
            <h1>AI Banking Assistant</h1>
            <p>Powered by Gemini AI</p>
          </div>
        </div>
        <div className="chat-header-nav">
          {/* Navigation buttons without icons - UPDATED */}
          <button 
            className="nav-btn"
            onClick={() => onNavigate('dashboard')}
            title="View Dashboard"
            aria-label="Navigate to Dashboard"
          >
            <span className="nav-btn-label">Dashboard</span>
          </button>
          <button 
            className="nav-btn"
            onClick={() => onNavigate('accounts')}
            title="Manage Accounts"
            aria-label="Navigate to Account Management"
          >
            <span className="nav-btn-label">Accounts</span>
          </button>
          <button 
            className="nav-btn logout-nav-btn"
            onClick={onLogout}
            title="Logout"
            aria-label="Logout from your account"
          >
            <span className="nav-btn-label">Logout</span>
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="messages-container" role="log" aria-live="polite" aria-label="Chat messages">
        <div className="messages-wrapper">
          {messages.map((message) => (
            <div 
              key={message.id} 
              className={`message ${message.role} ${message.error ? 'error' : ''}`}
              role="article"
            >
              <div className="message-avatar">
                {message.role === 'user' ? (
                  <div className="avatar-user" aria-label="Your message">👤</div>
                ) : (
                  <div className="avatar-assistant" aria-label="AI Assistant response">🤖</div>
                )}
              </div>
              <div className="message-content">
                <div className="message-author">
                  {message.role === 'user' ? 'You' : 'AI Assistant'}
                </div>
                <div className="message-bubble">{message.content}</div>
                <div className="message-time">
                  {message.timestamp.toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit',
                    hour12: true
                  })}
                </div>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message assistant loading" role="status" aria-label="AI is thinking">
              <div className="message-avatar">
                <div className="avatar-assistant">🤖</div>
              </div>
              <div className="message-content">
                <div className="message-author">AI Assistant</div>
                <div className="typing-indicator">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="chat-input-container">
        {messages.length === 1 && (
          <div className="chat-hints">
            <p className="hints-label">Try asking:</p>
            {quickPrompts.map((prompt, index) => (
              <button
                key={index}
                className="hint-button"
                onClick={() => sendMessage(prompt)}
                disabled={isLoading}
                aria-label={`Quick prompt: ${prompt}`}
              >
                {prompt}
              </button>
            ))}
          </div>
        )}
        <div className="chat-input-wrapper">
          <textarea
            ref={inputRef}
            className="chat-input"
            placeholder="Ask me anything about your banking needs..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
            rows={1}
            aria-label="Chat message input"
            aria-describedby="input-hint"
          />
          <button 
            className="send-button"
            onClick={() => sendMessage()}
            disabled={isLoading || !input.trim()}
            title="Send message (Enter)"
            aria-label="Send message"
          >
            {isLoading ? (
              <span className="loading-icon" aria-hidden="true">⏳</span>
            ) : (
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path d="M2 10L18 2L10 18L8 11L2 10Z" />
              </svg>
            )}
          </button>
        </div>
        <p className="input-hint" id="input-hint">Press Enter to send • Connected to UNK029 Bank</p>
      </div>
    </div>
  )
}

export default BankChat
