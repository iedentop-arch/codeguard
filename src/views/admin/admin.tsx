import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { vendors } from '@/mocks/data'
import type { Vendor, VendorStatus, SLAGrade } from '@/lib/types'
import {
  Users,
  Plus,
  Search,
  MoreHorizontal,
  Edit2,
  Trash2,
  ExternalLink,
} from 'lucide-react'

const statusMap: Record<VendorStatus, { label: string; variant: 'success' | 'warning' | 'danger' | 'secondary' | 'info' }> = {
  active: { label: '活跃', variant: 'success' },
  pending: { label: '待激活', variant: 'secondary' },
  warning: { label: '预警', variant: 'warning' },
  suspended: { label: '暂停', variant: 'danger' },
  exited: { label: '已退出', variant: 'secondary' },
}

const gradeColor: Record<SLAGrade, string> = {
  A: 'text-grade-a',
  B: 'text-grade-b',
  C: 'text-grade-c',
  D: 'text-grade-d',
}

const typeLabels: Record<string, string> = {
  A: '前端',
  B: '后端',
  C: 'AI Agent',
  D: '全栈',
}

export function AdminPage() {
  const [search, setSearch] = useState('')
  const [showAddForm, setShowAddForm] = useState(false)

  const filtered = vendors.filter(v =>
    v.name.includes(search) || v.githubOrg.includes(search)
  )

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">乙方管理</h1>
          <p className="text-sm text-muted-foreground mt-1">管理乙方团队信息、合同及权限</p>
        </div>
        <Button className="gap-2" onClick={() => setShowAddForm(!showAddForm)}>
          <Plus className="w-4 h-4" /> 新增乙方
        </Button>
      </div>

      {/* Add Form */}
      {showAddForm && (
        <Card>
          <CardHeader>
            <CardTitle>新增乙方</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1.5">乙方名称</label>
                <input className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring" placeholder="公司名称" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1.5">乙方类型</label>
                <select className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring">
                  <option value="A">A - 前端</option>
                  <option value="B">B - 后端</option>
                  <option value="C">C - AI Agent</option>
                  <option value="D">D - 全栈</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1.5">GitHub组织</label>
                <input className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring" placeholder="github-org" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1.5">联系人</label>
                <input className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring" placeholder="联系人姓名" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1.5">合同开始</label>
                <input type="date" className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1.5">合同结束</label>
                <input type="date" className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring" />
              </div>
            </div>
            <div className="flex gap-3">
              <Button>创建</Button>
              <Button variant="outline" onClick={() => setShowAddForm(false)}>取消</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="搜索乙方名称或GitHub组织..."
          className="w-full pl-10 pr-4 py-2.5 rounded-lg border bg-card text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>

      {/* Vendor Table */}
      <Card>
        <CardContent className="p-0">
          <table className="w-full">
            <thead>
              <tr className="border-b text-sm text-muted-foreground">
                <th className="text-left p-4 font-medium">乙方</th>
                <th className="text-left p-4 font-medium">类型</th>
                <th className="text-left p-4 font-medium">人数</th>
                <th className="text-center p-4 font-medium">SLA等级</th>
                <th className="text-center p-4 font-medium">评分</th>
                <th className="text-center p-4 font-medium">状态</th>
                <th className="text-left p-4 font-medium">合同周期</th>
                <th className="text-right p-4 font-medium">操作</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(vendor => {
                const st = statusMap[vendor.status]
                return (
                  <tr key={vendor.id} className="border-b last:border-0 hover:bg-accent/30 transition-colors">
                    <td className="p-4">
                      <div>
                        <p className="text-sm font-medium">{vendor.name}</p>
                        <p className="text-xs text-muted-foreground">{vendor.githubOrg}</p>
                      </div>
                    </td>
                    <td className="p-4">
                      <Badge variant="outline">{vendor.vendorType} - {typeLabels[vendor.vendorType]}</Badge>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-1.5">
                        <Users className="w-3.5 h-3.5 text-muted-foreground" />
                        <span className="text-sm">{vendor.memberCount}</span>
                      </div>
                    </td>
                    <td className="p-4 text-center">
                      <span className={`text-xl font-bold ${gradeColor[vendor.currentGrade]}`}>
                        {vendor.currentGrade}
                      </span>
                    </td>
                    <td className="p-4 text-center">
                      <span className="text-sm font-mono">{vendor.currentScore}</span>
                    </td>
                    <td className="p-4 text-center">
                      <Badge variant={st.variant}>{st.label}</Badge>
                    </td>
                    <td className="p-4">
                      <p className="text-xs text-muted-foreground">
                        {vendor.contractStart} ~ {vendor.contractEnd}
                      </p>
                    </td>
                    <td className="p-4 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button className="p-1.5 rounded hover:bg-accent transition-colors" title="编辑">
                          <Edit2 className="w-3.5 h-3.5 text-muted-foreground" />
                        </button>
                        <button className="p-1.5 rounded hover:bg-accent transition-colors" title="GitHub">
                          <ExternalLink className="w-3.5 h-3.5 text-muted-foreground" />
                        </button>
                        <button className="p-1.5 rounded hover:bg-accent transition-colors" title="删除">
                          <Trash2 className="w-3.5 h-3.5 text-muted-foreground" />
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: '活跃乙方', value: vendors.filter(v => v.status === 'active').length, color: 'text-status-success' },
          { label: '预警乙方', value: vendors.filter(v => v.status === 'warning').length, color: 'text-status-warning' },
          { label: '暂停乙方', value: vendors.filter(v => v.status === 'suspended').length, color: 'text-status-danger' },
          { label: 'A级占比', value: `${Math.round(vendors.filter(v => v.currentGrade === 'A').length / vendors.length * 100)}%`, color: 'text-grade-a' },
        ].map(stat => (
          <Card key={stat.label}>
            <CardContent className="p-4 text-center">
              <p className="text-xs text-muted-foreground">{stat.label}</p>
              <p className={`text-2xl font-bold mt-1 ${stat.color}`}>{stat.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
