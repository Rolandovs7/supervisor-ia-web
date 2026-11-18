import { API_BASE_URL } from './api'

export function buildWsUrl(token: string): string {
  let url: URL
  try {
    url = new URL(API_BASE_URL, window.location.origin)
  } catch {
    url = new URL(window.location.origin)
  }
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  url.pathname = '/ws/alertas'
  url.search = ''
  url.hash = ''
  url.searchParams.set('token', token)
  return url.toString()
}
