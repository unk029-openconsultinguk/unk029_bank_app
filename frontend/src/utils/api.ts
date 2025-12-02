/**
 * API Utilities for UNK029 Banking Application
 * Provides centralized API communication with error handling
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost'
const REQUEST_TIMEOUT = 10000 // 10 seconds (reduced from 30)
const CHAT_TIMEOUT = 15000 // 15 seconds for chat (allows more time for AI)

export interface ApiError {
  message: string
  status?: number
  code?: string
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

/**
 * Generic fetch wrapper with error handling and optimized headers
 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit & { timeout?: number } = {}
): Promise<Response> {
  const { timeout = REQUEST_TIMEOUT, ...fetchOptions } = options

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers: {
        'Content-Type': 'application/json',
        // Prevent local network permission prompt by being explicit
        'Access-Control-Request-Headers': 'Content-Type',
        ...fetchOptions.headers
      },
      signal: controller.signal,
      // Optimize for faster responses
      mode: 'cors',
      credentials: 'include'
    })
    clearTimeout(timeoutId)
    return response
  } catch (error) {
    clearTimeout(timeoutId)
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error(`Request timeout after ${timeout}ms`)
    }
    throw error
  }
}

/**
 * Send a chat message to the AI agent
 */
export async function sendChatMessage(message: string): Promise<{ reply: string }> {
  if (!message?.trim()) {
    throw new Error('Message cannot be empty')
  }

  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      timeout: CHAT_TIMEOUT, // Use longer timeout for AI responses
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({ message: message.trim() })
    })

    if (!response.ok) {
      let errorMessage = `Server error: ${response.status}`
      try {
        const errorData = await response.json()
        errorMessage = errorData.message || errorData.detail || errorMessage
      } catch {
        // Failed to parse error response
      }
      throw new Error(errorMessage)
    }

    const data: Record<string, unknown> = await response.json()
    
    if (!data.reply && !((data.data as Record<string, unknown>)?.reply)) {
      throw new Error('Invalid response format from server')
    }

    const reply = (data.reply as string) || ((data.data as Record<string, unknown>)?.reply as string) || ''
    return { reply }
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error('Network error: Unable to connect to server')
    }
    throw error
  }
}

/**
 * Get account information
 */
export async function getAccount(accountNo: number): Promise<Record<string, unknown>> {
  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/api/account/${accountNo}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch account: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error('Network error: Unable to connect to server')
    }
    throw error
  }
}

/**
 * Create a new account
 */
export async function createAccount(accountData: Record<string, unknown>): Promise<Record<string, unknown>> {
  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/api/account`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(accountData)
    })

    if (!response.ok) {
      throw new Error(`Failed to create account: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error('Network error: Unable to connect to server')
    }
    throw error
  }
}

/**
 * Extract user-friendly error message
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  if (typeof error === 'string') {
    return error
  }
  return 'An unexpected error occurred'
}

/**
 * Check if API is available
 */
export async function checkApiHealth(): Promise<boolean> {
  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message: 'ping' }),
      timeout: 5000
    })
    return response.ok
  } catch {
    return false
  }
}
