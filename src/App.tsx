import { useState, useEffect } from 'react'
import type { UserRole } from '@/lib/types'
import { LoginPage } from '@/views/auth/login'
import { Sidebar } from '@/components/layout/sidebar'
import { HeaderBar } from '@/components/layout/header'
import { DashboardPage } from '@/views/dashboard/dashboard'
import { PRListPage, PRDetailPage } from '@/views/review/review'
import { OnboardingPage } from '@/views/onboarding/onboarding'
import { DeliverablesPage } from '@/views/deliverables/deliverables'
import { AdminPage } from '@/views/admin/admin'
import { SpecsPage } from '@/views/specs/specs'
import { login, getCurrentUser, setToken, getToken, clearToken, type UserInfo } from '@/lib/api'

type Page = 'login' | 'dashboard' | 'reviews' | 'review-detail' | 'onboarding' | 'deliverables' | 'admin' | 'my-prs' | 'specs'

export default function App() {
  const [user, setUser] = useState<UserInfo | null>(null)
  const [role, setRole] = useState<UserRole | null>(null)
  const [page, setPage] = useState<Page>('login')
  const [selectedPRId, setSelectedPRId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [specsResetKey, setSpecsResetKey] = useState(0)  // 用于触发规范库重置

  // 初始化时检查是否有保存的token
  useEffect(() => {
    const token = getToken()
    if (token) {
      getCurrentUser()
        .then(res => {
          setUser(res.data)
          setRole(res.data.role as UserRole)
          setPage('dashboard')
        })
        .catch(() => {
          clearToken()
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const handleLogin = async (email: string, password: string) => {
    const res = await login(email, password)
    setToken(res.data.access_token)

    const userRes = await getCurrentUser()
    setUser(userRes.data)
    setRole(userRes.data.role as UserRole)
    setPage('dashboard')
  }

  const handleLogout = () => {
    clearToken()
    setUser(null)
    setRole(null)
    setPage('login')
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full mx-auto"></div>
          <p className="text-sm text-muted-foreground mt-2">加载中...</p>
        </div>
      </div>
    )
  }

  if (!user || !role || page === 'login') {
    return <LoginPage onLogin={handleLogin} />
  }

  const handleNavigate = (path: string) => {
    setSelectedPRId(null)  // 清除 PR 选择状态
    
    if (path === '/dashboard') setPage('dashboard')
    else if (path === '/reviews') setPage('reviews')
    else if (path === '/deliverables') setPage('deliverables')
    else if (path === '/admin') setPage('admin')
    else if (path === '/onboarding') setPage('onboarding')
    else if (path === '/my-prs') setPage('reviews')
    else if (path === '/specs') {
      // 点击规范库菜单时，更新 resetKey 触发重置
      setSpecsResetKey(prev => prev + 1)
      setPage('specs')
    }
  }

  const renderPage = () => {
    switch (page) {
      case 'dashboard':
        return <DashboardPage />
      case 'reviews':
        if (selectedPRId) {
          return <PRDetailPage prId={selectedPRId} onBack={() => setSelectedPRId(null)} />
        }
        return <PRListPage onSelectPR={(id) => { setSelectedPRId(id); setPage('review-detail') }} />
      case 'review-detail':
        if (selectedPRId) {
          return <PRDetailPage prId={selectedPRId} onBack={() => { setSelectedPRId(null); setPage('reviews') }} />
        }
        return <PRListPage onSelectPR={(id) => { setSelectedPRId(id) }} />
      case 'onboarding':
        return <OnboardingPage />
      case 'deliverables':
        return <DeliverablesPage />
      case 'admin':
        return <AdminPage />
      case 'specs':
        return <SpecsPage resetKey={specsResetKey} />
      default:
        return <DashboardPage />
    }
  }

  const currentPath = page === 'review-detail' ? '/reviews' : `/${page}`

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar role={role} currentPath={currentPath} onNavigate={handleNavigate} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <HeaderBar
          role={role}
          userName={user.name}
          onLogout={handleLogout}
        />
        <main className="flex-1 overflow-y-auto p-6">
          {renderPage()}
        </main>
      </div>
    </div>
  )
}