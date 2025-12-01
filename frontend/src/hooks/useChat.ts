import { useState, useCallback, useRef, useEffect } from 'react'
import { sendChatMessage, getErrorMessage } from '../utils/api'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  error?: boolean
}

export interface UseChatState {
  messages: ChatMessage[]
  input: string
  isLoading: boolean
  error: string | null
}

export interface UseChatActions {
  setInput: (input: string) => void
  sendMessage: (message?: string) => Promise<void>
  clearMessages: () => void
  removeMessage: (id: string) => void
  resetError: () => void
}

export function useChat(): UseChatState & UseChatActions {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m your AI banking assistant powered by Google Gemini. I can help you with account information, deposits, withdrawals, and answer any banking questions. How may I assist you today?',
      timestamp: new Date()
    }
  ])

  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesRef = useRef(messages)

  useEffect(() => {
    messagesRef.current = messages
  }, [messages])

  const sendMessage = useCallback(async (messageText?: string) => {
    const textToSend = messageText || input

    if (!textToSend.trim() || isLoading) {
      return
    }

    setError(null)

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: textToSend,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await sendChatMessage(textToSend)

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.reply,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      const errorMsg = getErrorMessage(err)
      setError(errorMsg)

      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `⚠️ ${errorMsg}`,
        timestamp: new Date(),
        error: true
      }

      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }, [input, isLoading])

  const clearMessages = useCallback(() => {
    setMessages([
      {
        id: '1',
        role: 'assistant',
        content: 'Hello! I\'m your AI banking assistant powered by Google Gemini. I can help you with account information, deposits, withdrawals, and answer any banking questions. How may I assist you today?',
        timestamp: new Date()
      }
    ])
    setInput('')
    setError(null)
  }, [])

  const removeMessage = useCallback((id: string) => {
    setMessages(prev => prev.filter(msg => msg.id !== id))
  }, [])

  const resetError = useCallback(() => {
    setError(null)
  }, [])

  return {
    // State
    messages,
    input,
    isLoading,
    error,
    // Actions
    setInput,
    sendMessage,
    clearMessages,
    removeMessage,
    resetError
  }
}
