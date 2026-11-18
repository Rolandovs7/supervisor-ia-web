import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import {
  Activity,
  ArrowRight,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  ShieldCheck,
} from 'lucide-react'

import { useAuth } from '../context/AuthContext'
import { errorMessage } from '../lib/api'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'

const CURRENT_YEAR = new Date().getFullYear()

export function Login() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)

    if (!email.trim() || !password.trim()) {
      setError('Ingresa tu correo y contraseña para continuar.')
      return
    }

    setLoading(true)
    try {
      await login(email.trim(), password)
      navigate('/dashboard', { replace: true })
    } catch (cause) {
      setError(errorMessage(cause, 'No pudimos iniciar sesión. Revisa tus credenciales.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-[1.1fr_1fr]">
      <section className="relative hidden overflow-hidden bg-[#070c17] p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="grid-backdrop absolute inset-0 opacity-60" />
        <div className="absolute -left-32 top-1/3 h-96 w-96 rounded-full bg-accent-500/20 blur-[120px]" />
        <div className="absolute -right-20 bottom-0 h-80 w-80 rounded-full bg-emerald-500/10 blur-[110px]" />

        <div className="relative z-10 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-accent-400 to-accent-600 shadow-lg shadow-accent-500/30">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm font-extrabold tracking-tight">
              SUPERVISOR <span className="text-accent-400">IA</span>
            </p>
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">
              Safety operations platform
            </p>
          </div>
        </div>

        <div className="relative z-10 max-w-lg">
          <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1.5 text-[11px] font-bold text-emerald-300">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
            MONITOREO EN TIEMPO REAL
          </div>
          <h2 className="text-4xl font-extrabold leading-[1.15] tracking-tight xl:text-5xl">
            Obras más seguras,
            <br />
            <span className="bg-gradient-to-r from-accent-400 to-emerald-300 bg-clip-text text-transparent">
              decisiones más rápidas.
            </span>
          </h2>
          <p className="mt-6 text-sm leading-relaxed text-slate-400">
            Detección automática de personas con YOLOv8, alertas instantáneas y trazabilidad
            completa de cada evento en tu obra.
          </p>

          <div className="mt-10 grid gap-3 sm:grid-cols-2">
            {[
              { icon: Activity, label: 'Detección YOLOv8' },
              { icon: ShieldCheck, label: 'Alertas automáticas' },
            ].map(({ icon: Icon, label }) => (
              <div
                key={label}
                className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3"
              >
                <Icon className="h-4 w-4 text-accent-400" />
                <span className="text-xs font-semibold text-slate-300">{label}</span>
              </div>
            ))}
          </div>
        </div>

        <p className="relative z-10 text-[11px] text-slate-600">
          © {CURRENT_YEAR} Supervisor IA · Industrial safety intelligence
        </p>
      </section>

      <section className="flex items-center justify-center bg-slate-100 px-5 py-10 dark:bg-canvas sm:px-10">
        <div className="w-full max-w-md">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-accent-400 to-accent-600">
              <ShieldCheck className="h-5 w-5 text-white" />
            </div>
            <p className="text-base font-extrabold text-slate-900 dark:text-white">
              SUPERVISOR <span className="text-accent-500">IA</span>
            </p>
          </div>

          <div className="surface animate-fade-up rounded-2xl p-7 sm:p-9">
            <div className="mb-8">
              <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-accent-500">
                Acceso a la plataforma
              </p>
              <h1 className="mt-2 text-2xl font-extrabold tracking-tight text-slate-900 dark:text-white">
                Bienvenido de nuevo
              </h1>
              <p className="muted mt-2 text-sm">
                Ingresa tus credenciales para acceder al centro de operaciones.
              </p>
            </div>

            {error && (
              <div className="mb-5 flex items-start gap-2.5 rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm font-medium text-rose-600 dark:text-rose-300">
                <span className="mt-0.5">!</span>
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              <Input
                label="Correo electrónico"
                type="email"
                autoComplete="email"
                placeholder="supervisor@empresa.com"
                icon={<Mail className="h-4 w-4" />}
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                disabled={loading}
              />
              <Input
                label="Contraseña"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                placeholder="••••••••"
                icon={<LockKeyhole className="h-4 w-4" />}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                disabled={loading}
                trailing={
                  <button
                    type="button"
                    onClick={() => setShowPassword((value) => !value)}
                    aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                    className="rounded-lg p-2 text-slate-400 transition hover:text-slate-700 dark:hover:text-white"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                }
              />

              <Button
                type="submit"
                size="lg"
                loading={loading}
                className="w-full"
                rightIcon={!loading ? <ArrowRight className="h-4 w-4" /> : undefined}
              >
                {loading ? 'Verificando…' : 'Iniciar sesión'}
              </Button>
            </form>

            <p className="muted mt-7 text-center text-[11px] leading-relaxed">
              Acceso restringido a personal autorizado. Todas las sesiones son auditadas.
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}
