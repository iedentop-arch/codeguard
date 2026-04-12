import { useState } from 'react'
import { Shield, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface LoginPageProps {
  onLogin: (email: string, password: string) => Promise<void>
}

export function LoginPage({ onLogin }: LoginPageProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      await onLogin(email, password)
    } catch (err) {
      setError(err instanceof Error ? err.message : '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background"
      style={{ backgroundImage: 'url(/images/hero-bg.png)', backgroundSize: 'cover', backgroundPosition: 'center' }}>
      <div className="w-full max-w-md p-8 rounded-2xl border border-primary-foreground/10 bg-primary-foreground/5 backdrop-blur-sm animate-fade-in">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-xl bg-primary mx-auto flex items-center justify-center mb-4 shadow-lg">
            <Shield className="w-8 h-8 text-primary-foreground" />
          </div>
          <h1 className="text-2xl font-bold text-primary-foreground">CodeGuard</h1>
          <p className="text-sm text-primary-foreground/60 mt-1">乙方代码管理系统</p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-destructive/10 border border-destructive/20 flex items-center gap-2 text-destructive">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-primary-foreground/80 mb-1.5">邮箱</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="your@company.com"
              required
              className="w-full px-4 py-2.5 rounded-lg border border-primary-foreground/10 bg-primary-foreground/5 text-primary-foreground placeholder:text-primary-foreground/30 focus:outline-none focus:ring-2 focus:ring-primary-glow"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-primary-foreground/80 mb-1.5">密码</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full px-4 py-2.5 rounded-lg border border-primary-foreground/10 bg-primary-foreground/5 text-primary-foreground placeholder:text-primary-foreground/30 focus:outline-none focus:ring-2 focus:ring-primary-glow"
            />
          </div>
          <Button type="submit" className="w-full h-11 text-base" size="lg" disabled={loading}>
            {loading ? (
              <span className="flex items-center gap-2">
                <div className="animate-spin w-4 h-4 border-2 border-current border-t-transparent rounded-full"></div>
                登录中...
              </span>
            ) : '登录'}
          </Button>

          <div className="text-xs text-center text-primary-foreground/40 mt-4 space-y-2">
            <p>测试账户：</p>
            <div className="space-y-1">
              <p><code className="text-primary-foreground/60">admin@codeguard.com</code> / <code className="text-primary-foreground/60">admin123</code> (管理员)</p>
              <p><code className="text-primary-foreground/60">dev@company-a.com</code> / <code className="text-primary-foreground/60">dev123</code> (开发)</p>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}