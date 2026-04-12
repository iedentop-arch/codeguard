import { useState } from 'react'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  FileCheck,
  GitPullRequest,
  Package,
  Users,
  BookOpen,
  Shield,
  ChevronLeft,
  ChevronRight,
  Settings,
  Award,
  BarChart3,
  AlertTriangle,
} from 'lucide-react'
import type { UserRole } from '@/lib/types'

interface SidebarProps {
  role: UserRole
  currentPath: string
  onNavigate: (path: string) => void
}

interface NavItem {
  label: string
  icon: React.ComponentType<{ className?: string }>
  path: string
  badge?: string
  badgeColor?: string
}

interface NavGroup {
  title?: string
  items: NavItem[]
}

// 甲方管理员导航 - 完整权限
const adminNavGroups: NavGroup[] = [
  {
    title: '监控',
    items: [
      { label: '总览看板', icon: LayoutDashboard, path: '/dashboard' },
      { label: 'SLA评分', icon: BarChart3, path: '/sla' },
      { label: '告警中心', icon: AlertTriangle, path: '/alerts', badge: '3', badgeColor: 'bg-status-warning' },
    ],
  },
  {
    title: '审查',
    items: [
      { label: '代码审查', icon: GitPullRequest, path: '/reviews', badge: '5', badgeColor: 'bg-status-info' },
      { label: '交付验收', icon: Package, path: '/deliveries' },
    ],
  },
  {
    title: '管理',
    items: [
      { label: '乙方管理', icon: Users, path: '/vendors' },
      { label: '规范库', icon: BookOpen, path: '/specs' },
      { label: '题库管理', icon: FileCheck, path: '/exam-bank' },
      { label: '系统设置', icon: Settings, path: '/settings' },
    ],
  },
]

// 甲方评审员导航 - 审查权限
const reviewerNavGroups: NavGroup[] = [
  {
    title: '监控',
    items: [
      { label: '总览看板', icon: LayoutDashboard, path: '/dashboard' },
      { label: 'SLA评分', icon: BarChart3, path: '/sla' },
    ],
  },
  {
    title: '审查',
    items: [
      { label: '代码审查', icon: GitPullRequest, path: '/reviews' },
      { label: '交付验收', icon: Package, path: '/deliveries' },
    ],
  },
  {
    items: [
      { label: '规范库', icon: BookOpen, path: '/specs' },
    ],
  },
]

// 乙方管理员导航 - 团队管理权限
const vendorAdminNavGroups: NavGroup[] = [
  {
    title: '入驻',
    items: [
      { label: '入驻中心', icon: Shield, path: '/onboarding' },
      { label: '认证管理', icon: Award, path: '/certifications' },
    ],
  },
  {
    title: '工作',
    items: [
      { label: '我的PR', icon: GitPullRequest, path: '/my-prs' },
      { label: '交付提交', icon: Package, path: '/my-deliveries' },
      { label: 'SLA指标', icon: BarChart3, path: '/my-metrics' },
    ],
  },
  {
    title: '团队',
    items: [
      { label: '成员管理', icon: Users, path: '/my-team' },
    ],
  },
  {
    items: [
      { label: '规范学习', icon: BookOpen, path: '/specs' },
    ],
  },
]

// 乙方开发导航 - 基础权限
const vendorDevNavGroups: NavGroup[] = [
  {
    title: '入驻',
    items: [
      { label: '入驻中心', icon: Shield, path: '/onboarding' },
    ],
  },
  {
    title: '工作',
    items: [
      { label: '我的PR', icon: GitPullRequest, path: '/my-prs' },
      { label: '我的指标', icon: BarChart3, path: '/my-metrics' },
    ],
  },
  {
    items: [
      { label: '规范学习', icon: BookOpen, path: '/specs' },
    ],
  },
]

const roleNavMap: Record<UserRole, NavGroup[]> = {
  admin: adminNavGroups,
  vendor_admin: vendorAdminNavGroups,
  vendor_dev: vendorDevNavGroups,
}

const roleLabels: Record<UserRole, string> = {
  admin: '甲方管理员',
  vendor_admin: '乙方管理员',
  vendor_dev: '乙方开发',
}

export function Sidebar({ role, currentPath, onNavigate }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false)
  const navGroups = roleNavMap[role] || vendorDevNavGroups

  return (
    <aside
      className={cn(
        "flex flex-col h-screen bg-sidebar text-sidebar-foreground transition-all duration-300",
        collapsed ? "w-16" : "w-56"
      )}
    >
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b border-sidebar-accent">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-primary-glow flex items-center justify-center flex-shrink-0">
            <Shield className="w-5 h-5 text-primary-foreground" />
          </div>
          {!collapsed && (
            <div className="min-w-0 animate-fade-in">
              <h1 className="text-sm font-bold text-sidebar-accent-foreground truncate">CodeGuard</h1>
              <p className="text-xs text-sidebar-foreground/60 truncate">乙方代码管理系统</p>
            </div>
          )}
        </div>
      </div>

      {/* Nav groups */}
      <nav className="flex-1 py-2 px-2 overflow-y-auto">
        {navGroups.map((group, gi) => (
          <div key={gi} className="mb-4">
            {group.title && !collapsed && (
              <p className="px-3 mb-1.5 text-xs font-medium text-sidebar-foreground/40 uppercase tracking-wider">
                {group.title}
              </p>
            )}
            <div className="space-y-1">
              {group.items.map((item) => {
                const Icon = item.icon
                const isActive = currentPath === item.path || currentPath.startsWith(item.path + '/')
                return (
                  <button
                    key={item.path}
                    onClick={() => onNavigate(item.path)}
                    className={cn(
                      "flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm transition-all duration-200",
                      isActive
                        ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium shadow-sm"
                        : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground"
                    )}
                  >
                    <Icon className={cn("w-5 h-5 flex-shrink-0", isActive && "text-primary-glow")} />
                    {!collapsed && (
                      <div className="flex items-center justify-between flex-1 min-w-0">
                        <span className="truncate">{item.label}</span>
                        {item.badge && (
                          <span className={cn(
                            "px-1.5 py-0.5 rounded text-xs font-medium text-primary-foreground",
                            item.badgeColor || "bg-status-info"
                          )}>
                            {item.badge}
                          </span>
                        )}
                      </div>
                    )}
                  </button>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Role indicator */}
      <div className="px-2 pb-2">
        {!collapsed && (
          <div className="px-3 py-2 rounded-lg bg-sidebar-accent/30 text-xs text-sidebar-foreground/60 animate-fade-in">
            {roleLabels[role]}
          </div>
        )}
      </div>

      {/* Collapse toggle */}
      <div className="p-2 border-t border-sidebar-accent">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center justify-center w-full p-2 rounded-lg text-sidebar-foreground/60 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>
    </aside>
  )
}