import React from 'react'

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div style={styles.container}>
            <div style={styles.card}>
              <h2 style={styles.title}>⚠️ Something went wrong</h2>
              <p style={styles.message}>{this.state.error?.message}</p>
              <button
                onClick={() => this.setState({ hasError: false, error: null })}
                style={styles.button}
              >
                Try Again
              </button>
            </div>
          </div>
        )
      )
    }

    return this.props.children
  }
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  },
  card: {
    background: 'white',
    padding: '2rem',
    borderRadius: '1rem',
    textAlign: 'center',
    maxWidth: '400px',
    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.2)',
  },
  title: {
    fontSize: '1.5rem',
    fontWeight: '700',
    color: '#1e293b',
    margin: '0 0 1rem 0',
  },
  message: {
    color: '#64748b',
    fontSize: '0.95rem',
    lineHeight: '1.6',
    margin: '0 0 1.5rem 0',
  },
  button: {
    padding: '0.75rem 1.5rem',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    border: 'none',
    borderRadius: '0.5rem',
    fontSize: '0.95rem',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
}
