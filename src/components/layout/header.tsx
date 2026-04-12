import { Bell, User, LogOut } from 'lucide-react'
import type { UserRole } from '@/lib/types'

interface HeaderBarProps {
  role: UserRole
  userName: string
  onLogout: () => void
}

export function HeaderBar({ role, userName, onLogout }: HeaderBarProps) {
  return (
    <header className="flex items-center justify-between h-14 px-6 border-b bg-card">
      <div className="flex items-center gap-4">
        <h2 className="text-sm font-medium text-muted-foreground">
          {role === 'admin' ? '甲方管理视角' : role === 'vendor_admin' ? '乙方管理视角' : '乙方开发视角'}
        </h2>
      </div>
      <div className="flex items-center gap-3">
        <button className="relative p-2 rounded-lg hover:bg-accent transition-colors" title="通知">
          <Bell className="w-4 h-4 text-muted-foreground" />
          <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-status-danger" />
        </button>
        <div className="flex items-center gap-2 pl-3 border-l">
          <div className="w-7 h-7 rounded-full bg-primary flex items-center justify-center">
            <User className="w-4 h-4 text-primary-foreground" />
          </div>
          <span className="text-sm">{userName}</span>
        </div>
        <button
          onClick={onLogout}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-accent transition-colors text-xs text-muted-foreground"
          title="退出登录"
        >
          <LogOut className="w-3.5 h-3.5" />
          退出
        </button>
      </div>
    </header>
  )
}
