import type { AuthUser } from './types'

const TOKEN_KEY = 'supervisor_ia_token'
const USER_KEY = 'supervisor_ia_user'

function read(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function write(key: string, value: string): void {
  try {
    localStorage.setItem(key, value)
  } catch {
    // Storage can be disabled; the in-memory session still works.
  }
}

function remove(key: string): void {
  try {
    localStorage.removeItem(key)
  } catch {
    // Nothing to do.
  }
}

export function getToken(): string | null {
  return read(TOKEN_KEY)
}

export function getStoredUser(): AuthUser | null {
  const raw = read(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as AuthUser
  } catch {
    return null
  }
}

export function saveSession(token: string, user: AuthUser): void {
  write(TOKEN_KEY, token)
  write(USER_KEY, JSON.stringify(user))
}

export function clearSession(): void {
  remove(TOKEN_KEY)
  remove(USER_KEY)
}
