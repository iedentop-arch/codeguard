import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { deliveries, checklistItems } from '@/mocks/data'
import {
  Package,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  XCircle,
  Clock,
  Bot,
  Upload,
  FileText,
} from 'lucide-react'

const deliveryStatusMap: Record<string, { label: string; variant: 'info' | 'warning' | 'success' | 'danger' }> = {
  submitted: { label: '已提交', variant: 'info' },
  under_review: { label: '审核中', variant: 'warning' },
  accepted: { label: '已验收', variant: 'success' },
  rejected: { label: '已驳回', variant: 'danger' },
}

const itemStatusIcon = {
  accepted: CheckCircle2,
  rejected: XCircle,
  pending: Clock,
}

const itemStatusColor = {
  accepted: 'text-status-success',
  rejected: 'text-status-danger',
  pending: 'text-muted-foreground',
}

export function DeliverablesPage() {
  const [selectedDelivery, setSelectedDelivery] = useState<number | null>(1)
  const [expandedDimensions, setExpandedDimensions] = useState<Set<string>>(new Set(['代码质量', '合规检查']))
  const [itemStates, setItemStates] = useState<Record<number, 'accepted' | 'rejected' | 'pending'>>(
    Object.fromEntries(checklistItems.map(item => [item.id, item.status]))
  )
  const [showSubmitForm, setShowSubmitForm] = useState(false)

  const delivery = deliveries.find(d => d.id === selectedDelivery)
  const items = selectedDelivery ? checklistItems : []

  const dimensions = [...new Set(items.map(i => i.dimension))]
  const dimStats = dimensions.map(dim => {
    const dimItems = items.filter(i => i.dimension === dim)
    const accepted = dimItems.filter(i => itemStates[i.id] === 'accepted').length
    const rejected = dimItems.filter(i => itemStates[i.id] === 'rejected').length
    return { name: dim, total: dimItems.length, accepted, rejected, pending: dimItems.length - accepted - rejected }
  })

  const totalAccepted = items.filter(i => itemStates[i.id] === 'accepted').length
  const totalItems = items.length

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">交付管理</h1>
          <p className="text-sm text-muted-foreground mt-1">管理项目交付物及验收流程</p>
        </div>
        <Button className="gap-2" onClick={() => setShowSubmitForm(!showSubmitForm)}>
          <Upload className="w-4 h-4" /> 提交交付物
        </Button>
      </div>

      {/* Submit Form */}
      {showSubmitForm && (
        <Card>
          <CardHeader>
            <CardTitle>提交交付物</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1.5">版本号</label>
              <input className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring" placeholder="v1.0.0" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5">交付说明</label>
              <textarea className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring min-h-[80px] resize-none" placeholder="描述本次交付的内容..." />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5">附件</label>
              <div className="border-2 border-dashed rounded-lg p-8 text-center hover:bg-accent/50 transition-colors cursor-pointer">
                <Upload className="w-8 h-8 mx-auto text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground">点击或拖拽上传文件</p>
              </div>
            </div>
            <div className="flex gap-3">
              <Button>提交</Button>
              <Button variant="outline" onClick={() => setShowSubmitForm(false)}>取消</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Deliveries list + Checklist */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Delivery list */}
        <div className="space-y-3">
          {deliveries.map(d => {
            const st = deliveryStatusMap[d.status]
            return (
              <Card
                key={d.id}
                className={`cursor-pointer transition-all ${selectedDelivery === d.id ? 'ring-2 ring-primary' : 'hover:shadow-md'}`}
                onClick={() => setSelectedDelivery(d.id)}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <Badge variant={st.variant}>{st.label}</Badge>
                    <span className="text-xs text-muted-foreground">{d.submittedAt.split('T')[0]}</span>
                  </div>
                  <h3 className="text-sm font-medium">{d.projectName}</h3>
                  <p className="text-xs text-muted-foreground mt-1">{d.vendorName} · {d.version}</p>
                  <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{d.description}</p>
                </CardContent>
              </Card>
            )
          })}
        </div>

        {/* Right: Checklist */}
        <div className="lg:col-span-2">
          {delivery ? (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>验收清单</CardTitle>
                    <p className="text-sm text-muted-foreground mt-1">
                      {delivery.projectName} · {delivery.version}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold">{totalAccepted}/{totalItems}</p>
                    <p className="text-xs text-muted-foreground">已通过</p>
                  </div>
                </div>
                {/* Progress bar */}
                <div className="flex gap-0.5 mt-3">
                  {items.map(item => (
                    <div
                      key={item.id}
                      className={`h-2 flex-1 rounded-full ${
                        itemStates[item.id] === 'accepted' ? 'bg-status-success' :
                        itemStates[item.id] === 'rejected' ? 'bg-status-danger' :
                        'bg-accent'
                      }`}
                    />
                  ))}
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {dimensions.map(dim => {
                  const stats = dimStats.find(d => d.name === dim)!
                  const isExpanded = expandedDimensions.has(dim)
                  const dimItems = items.filter(i => i.dimension === dim)

                  return (
                    <div key={dim} className="border rounded-lg">
                      <button
                        className="w-full flex items-center justify-between p-4 hover:bg-accent/50 transition-colors"
                        onClick={() => {
                          const next = new Set(expandedDimensions)
                          isExpanded ? next.delete(dim) : next.add(dim)
                          setExpandedDimensions(next)
                        }}
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-medium">{dim}</span>
                          <div className="flex items-center gap-1.5">
                            {stats.accepted > 0 && <Badge variant="success" className="text-[10px] px-1.5 py-0">{stats.accepted}通过</Badge>}
                            {stats.rejected > 0 && <Badge variant="danger" className="text-[10px] px-1.5 py-0">{stats.rejected}不通过</Badge>}
                            {stats.pending > 0 && <Badge variant="secondary" className="text-[10px] px-1.5 py-0">{stats.pending}待审</Badge>}
                          </div>
                        </div>
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>
                      {isExpanded && (
                        <div className="px-4 pb-4 space-y-2">
                          {dimItems.map(item => {
                            const Icon = itemStatusIcon[itemStates[item.id]]
                            const color = itemStatusColor[itemStates[item.id]]
                            return (
                              <div key={item.id} className="flex items-start gap-3 p-3 rounded-lg bg-accent/30">
                                <Icon className={`w-4 h-4 mt-0.5 flex-shrink-0 ${color}`} />
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2">
                                    <span className="text-xs font-mono text-muted-foreground">{item.itemNumber}</span>
                                    <span className="text-sm">{item.description}</span>
                                    {item.autoFilled && (
                                      <span className="flex items-center gap-0.5 text-[10px] text-status-info">
                                        <Bot className="w-3 h-3" /> CI
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-xs text-muted-foreground mt-0.5">标准：{item.acceptanceCriteria}</p>
                                  {itemStates[item.id] === 'pending' && (
                                    <div className="flex items-center gap-2 mt-2">
                                      <Button size="sm" variant="success" className="h-7 text-xs" onClick={() => setItemStates({ ...itemStates, [item.id]: 'accepted' })}>
                                        通过
                                      </Button>
                                      <Button size="sm" variant="destructive" className="h-7 text-xs" onClick={() => setItemStates({ ...itemStates, [item.id]: 'rejected' })}>
                                        不通过
                                      </Button>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      )}
                    </div>
                  )
                })}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="p-8 text-center text-muted-foreground">
                <Package className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>请选择一个交付物查看验收清单</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
