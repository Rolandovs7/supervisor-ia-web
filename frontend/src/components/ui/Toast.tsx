import { useEffect, useState } from 'react'
import { CheckCircle2, CircleAlert, X } from 'lucide-react'

import { cn } from '../../lib/utils'

interface ToastProps {
  message: string | null
  tone?: 'success' | 'error'
  onDismiss: () => void
}

export function Toast({ message, tone = 'success', onDismiss }: ToastProps) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    setVisible(Boolean(message))
    if (!message) return
    const timer = setTimeout(() => {
      setVisible(false)
      onDismiss()
    }, 4500)
    return () => clearTimeout(timer)
  }, [message, onDismiss])

  if (!message || !visible) return null

  const Icon = tone === 'error' ? CircleAlert : CheckCircle2

  return (
    <div className="animate-fade-up fixed bottom-6 right-6 z-[60] flex max-w-sm items-start gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-2xl dark:border-slate-700 dark:bg-panel">
      <Icon
        className={cn(
          'mt-0.5 h-5 w-5 shrink-0',
          tone === 'error' ? 'text-rose-500' : 'text-emerald-500',
        )}
      />
      <p className="flex-1 text-sm font-medium text-slate-800 dark:text-slate-100">
        {message}
      </p>
      <button
        type="button"
        onClick={() => {
          setVisible(false)
          onDismiss()
        }}
        aria-label="Cerrar notificación"
        className="text-slate-400 transition hover:text-slate-700 dark:hover:text-white"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}
