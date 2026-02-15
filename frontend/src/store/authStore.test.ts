import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from './authStore'

describe('authStore', () => {
  beforeEach(() => {
    localStorage.clear()
    useAuthStore.getState().logout()
  })

  it('initializes with no user', () => {
    const { user, token, isAuthenticated } = useAuthStore.getState()
    expect(user).toBe(null)
    expect(token).toBe(null)
    expect(isAuthenticated).toBe(false)
  })

  it('login sets user and token', () => {
    const { login } = useAuthStore.getState()
    
    const testUser = { id: '1', email: 'test@example.com', username: 'testuser' }
    login('test-token', testUser)

    const { user, token, isAuthenticated } = useAuthStore.getState()
    expect(user).toEqual(testUser)
    expect(token).toBe('test-token')
    expect(isAuthenticated).toBe(true)
  })

  it('login saves token to localStorage', () => {
    const { login } = useAuthStore.getState()
    
    login('test-token', { id: '1', email: 'test@example.com', username: 'testuser' })

    expect(localStorage.getItem('token')).toBe('test-token')
  })

  it('logout clears user and token', () => {
    const { login, logout } = useAuthStore.getState()
    
    login('test-token', { id: '1', email: 'test@example.com', username: 'testuser' })
    logout()

    const { user, token, isAuthenticated } = useAuthStore.getState()
    expect(user).toBe(null)
    expect(token).toBe(null)
    expect(isAuthenticated).toBe(false)
  })

  it('logout removes token from localStorage', () => {
    const { login, logout } = useAuthStore.getState()
    
    login('test-token', { id: '1', email: 'test@example.com', username: 'testuser' })
    logout()

    expect(localStorage.getItem('token')).toBe(null)
  })

  it('setUser updates user without changing token', () => {
    const { login, setUser } = useAuthStore.getState()
    
    login('test-token', { id: '1', email: 'test@example.com', username: 'testuser' })
    setUser({ id: '1', email: 'updated@example.com', username: 'updateduser' })

    const { user, token, isAuthenticated } = useAuthStore.getState()
    expect(user?.username).toBe('updateduser')
    expect(user?.email).toBe('updated@example.com')
    expect(token).toBe('test-token')
    expect(isAuthenticated).toBe(true)
  })
})
