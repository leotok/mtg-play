import { describe, it, expect } from 'vitest'
import { loginSchema, registerSchema } from './auth'

describe('auth schemas', () => {
  describe('loginSchema', () => {
    it('validates correct login data', () => {
      const result = loginSchema.safeParse({
        email: 'test@example.com',
        password: 'password123',
      })
      expect(result.success).toBe(true)
    })

    it('rejects empty email', () => {
      const result = loginSchema.safeParse({
        email: '',
        password: 'password123',
      })
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toBe('Email is required')
      }
    })

    it('rejects invalid email format', () => {
      const result = loginSchema.safeParse({
        email: 'notanemail',
        password: 'password123',
      })
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toBe('Invalid email address')
      }
    })

    it('rejects empty password', () => {
      const result = loginSchema.safeParse({
        email: 'test@example.com',
        password: '',
      })
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toBe('Password is required')
      }
    })
  })

  describe('registerSchema', () => {
    it('validates correct registration data', () => {
      const result = registerSchema.safeParse({
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123',
        confirm_password: 'password123',
      })
      expect(result.success).toBe(true)
    })

    it('rejects short username', () => {
      const result = registerSchema.safeParse({
        username: 'ab',
        email: 'test@example.com',
        password: 'password123',
        confirm_password: 'password123',
      })
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toBe('Username must be at least 3 characters')
      }
    })

    it('rejects long username', () => {
      const result = registerSchema.safeParse({
        username: 'a'.repeat(51),
        email: 'test@example.com',
        password: 'password123',
        confirm_password: 'password123',
      })
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toBe('Username must be less than 50 characters')
      }
    })

    it('rejects username with special characters', () => {
      const result = registerSchema.safeParse({
        username: 'test@user',
        email: 'test@example.com',
        password: 'password123',
        confirm_password: 'password123',
      })
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toBe('Username can only contain letters, numbers, and underscores')
      }
    })

    it('allows username with underscores and numbers', () => {
      const result = registerSchema.safeParse({
        username: 'test_user123',
        email: 'test@example.com',
        password: 'password123',
        confirm_password: 'password123',
      })
      expect(result.success).toBe(true)
    })

    it('rejects mismatched passwords', () => {
      const result = registerSchema.safeParse({
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123',
        confirm_password: 'differentpassword',
      })
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toBe('Passwords do not match')
      }
    })

    it('rejects empty confirm password', () => {
      const result = registerSchema.safeParse({
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123',
        confirm_password: '',
      })
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.error.issues[0].message).toBe('Please confirm your password')
      }
    })
  })
})
