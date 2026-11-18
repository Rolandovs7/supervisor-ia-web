import type { ReactNode } from 'react'

import { cn } from '../../lib/utils'

interface CardProps {
  children: ReactNode
  title?: string
  subtitle?: string
  action?: ReactNode
  className?: string
  bodyClassName?: string
}

export function Card({
  children,
  title,
  subtitle,
  action,
  className,
  bodyClassName,
}: CardProps) {
  const hasHeader = Boolean(title || subtitle || action)

  return (
    <section className={cn('surface rounded-2xl', className)}>
      {hasHeader && (
        <header className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 px-5 py-4 dark:border-slate-800/80 sm:px-6">
          <div>
            {title && (
              <h2 className="text-sm font-bold tracking-wide text-slate-900 dark:text-white">
                {title}
              </h2>
            )}
            {subtitle && <p className="muted mt-1 text-xs">{subtitle}</p>}
          </div>
          {action}
        </header>
      )}
      <div className={cn('p-5 sm:p-6', bodyClassName)}>{children}</div>
    </section>
  )
}
