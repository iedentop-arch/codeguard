import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  getPullRequests,
  getPullRequestById,
  approvePullRequest,
  rejectPullRequest,
  addPRComment,
  type PullRequestAPI,
  type QualityGateAPI,
} from '@/lib/api'
import type { PRStatus, QualityGate, GateStatus, PullRequest } from '@/lib/types'
import {
  GitPullRequest,
  Filter,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  ChevronLeft,
  MessageSquare,
  Bot,
  Loader2,
} from 'lucide-react'

// 转换 API 数据到前端格式
function transformPR(apiPR: PullRequestAPI): PullRequest {
  return {
    id: apiPR.id,
    vendorId: apiPR.vendor_id,
    vendorName: apiPR.vendor_name || '未知',
    authorName: apiPR.author_name || '未知',
    githubPrNumber: apiPR.github_pr_number,
    title: apiPR.title,
    branch: apiPR.branch || 'unknown',
    status: apiPR.status as PRStatus,
    linesAdded: apiPR.lines_added,
    linesRemoved: apiPR.lines_removed,
    filesChanged: apiPR.files_changed,
    hasAiCode: apiPR.has_ai_code,
    aiCodeMarked: apiPR.ai_code_marked,
    createdAt: apiPR.created_at,
    gates: apiPR.gates.map(transformGate),
  }
}

function transformGate(apiGate: QualityGateAPI): QualityGate {
  return {
    id: apiGate.id,
    prId: apiGate.pr_id,
    layer: apiGate.layer as 1 | 2 | 3 | 4 | 5 | 6,
    layerName: apiGate.layer_name,
    status: apiGate.status as GateStatus,
    details: apiGate.details || {},
    violationsCount: apiGate.violations_count,
    warningsCount: apiGate.warnings_count,
  }
}

const statusMap: Record<PRStatus, { label: string; variant: 'success' | 'warning' | 'danger' | 'info' | 'secondary' }> = {
  open: { label: '待检查', variant: 'secondary' },
  ci_checking: { label: 'CI检查中', variant: 'info' },
  ci_passed: { label: 'CI通过', variant: 'success' },
  ci_failed: { label: 'CI失败', variant: 'danger' },
  reviewing: { label: '评审中', variant: 'warning' },
  approved: { label: '已批准', variant: 'success' },
  rejected: { label: '已驳回', variant: 'danger' },
  merged: { label: '已合并', variant: 'info' },
}

const gateStatusIcon: Record<GateStatus, typeof CheckCircle2> = {
  passed: CheckCircle2,
  failed: XCircle,
  warning: AlertTriangle,
  skipped: Clock,
  running: Clock,
}

const gateStatusColor: Record<GateStatus, string> = {
  passed: 'text-status-success',
  failed: 'text-status-danger',
  warning: 'text-status-warning',
  skipped: 'text-muted-foreground',
  running: 'text-status-info',
}

const layerColor = ['bg-gate-redline', 'bg-gate-mandatory', 'bg-gate-suggested', 'bg-gate-info', 'bg-gate-info', 'bg-gate-redline']

export function PRListPage({ onSelectPR }: { onSelectPR: (id: number) => void }) {
  const [filterStatus, setFilterStatus] = useState<PRStatus | 'all'>('all')
  const [pullRequests, setPullRequests] = useState<PullRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchPRs() {
      try {
        setLoading(true)
        const response = await getPullRequests({
          status: filterStatus === 'all' ? undefined : filterStatus,
        })
        const transformed = response.data.items.map(transformPR)
        setPullRequests(transformed)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : '加载失败')
        setPullRequests([])
      } finally {
        setLoading(false)
      }
    }
    fetchPRs()
  }, [filterStatus])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-8 text-status-danger">
        <p>{error}</p>
        <Button variant="outline" className="mt-4" onClick={() => setFilterStatus('all')}>
          重试
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">代码审查</h1>
          <p className="text-sm text-muted-foreground mt-1">审查乙方提交的Pull Request及质量门禁结果</p>
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-muted-foreground" />
          {(['all', 'reviewing', 'ci_failed', 'ci_passed', 'merged'] as const).map(s => (
            <Button
              key={s}
              variant={filterStatus === s ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilterStatus(s)}
            >
              {s === 'all' ? '全部' : statusMap[s].label}
            </Button>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        {pullRequests.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              暂无符合条件的 Pull Request
            </CardContent>
          </Card>
        ) : (
          pullRequests.map(pr => {
            const gateSummary = pr.gates.reduce(
              (acc, g) => ({
                passed: acc.passed + (g.status === 'passed' ? 1 : 0),
                failed: acc.failed + (g.status === 'failed' ? 1 : 0),
                warning: acc.warning + (g.status === 'warning' ? 1 : 0),
              }),
              { passed: 0, failed: 0, warning: 0 }
            )
            const st = statusMap[pr.status]

            return (
              <Card
                key={pr.id}
                className="hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => onSelectPR(pr.id)}
              >
                <CardContent className="p-5">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3">
                        <GitPullRequest className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                        <h3 className="text-sm font-medium truncate">{pr.title}</h3>
                        <Badge variant={st.variant}>{st.label}</Badge>
                      </div>
                      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                        <span>#{pr.githubPrNumber}</span>
                        <span>{pr.vendorName}</span>
                        <span>{pr.authorName}</span>
                        <span>+{pr.linesAdded} -{pr.linesRemoved}</span>
                        <span>{pr.filesChanged} files</span>
                        {pr.hasAiCode && (
                          <span className="flex items-center gap-1">
                            <Bot className="w-3 h-3" />
                            {pr.aiCodeMarked ? 'AI已标记' : 'AI未标记'}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-1 ml-4">
                      {pr.gates.map((g) => {
                        const Icon = gateStatusIcon[g.status]
                        return (
                          <div key={g.layer} className="w-6 h-6 rounded flex items-center justify-center" title={`${g.layerName}: ${g.status}`}>
                            <Icon className={`w-3.5 h-3.5 ${gateStatusColor[g.status]}`} />
                          </div>
                        )
                      })}
                    </div>
                  </div>
                  {/* Gate bar */}
                  <div className="flex gap-0.5 mt-3">
                    {pr.gates.map((g, i) => (
                      <div
                        key={g.layer}
                        className={`h-1.5 flex-1 rounded-full ${layerColor[i]} opacity-${g.status === 'passed' ? '100' : g.status === 'failed' ? '100' : '60'}`}
                        style={{ opacity: g.status === 'passed' ? 1 : g.status === 'failed' ? 1 : 0.5 }}
                        title={`L${g.layer}: ${g.layerName} - ${g.status}`}
                      />
                    ))}
                  </div>
                </CardContent>
              </Card>
            )
          })
        )}
      </div>
    </div>
  )
}

export function PRDetailPage({ prId, onBack }: { prId: number; onBack: () => void }) {
  const [pr, setPr] = useState<PullRequest | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [comment, setComment] = useState('')
  const [actionLoading, setActionLoading] = useState(false)

  useEffect(() => {
    async function fetchPR() {
      try {
        setLoading(true)
        const response = await getPullRequestById(prId)
        setPr(transformPR(response.data))
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : '加载失败')
      } finally {
        setLoading(false)
      }
    }
    fetchPR()
  }, [prId])

  const handleApprove = async () => {
    if (!pr || actionLoading) return
    try {
      setActionLoading(true)
      await approvePullRequest(pr.id, comment)
      // 更新状态
      setPr({ ...pr, status: 'approved' })
      setComment('')
    } catch (err) {
      alert('批准失败: ' + (err instanceof Error ? err.message : '未知错误'))
    } finally {
      setActionLoading(false)
    }
  }

  const handleReject = async () => {
    if (!pr || actionLoading || !comment.trim()) {
      alert('请填写驳回原因')
      return
    }
    try {
      setActionLoading(true)
      await rejectPullRequest(pr.id, comment)
      setPr({ ...pr, status: 'rejected' })
      setComment('')
    } catch (err) {
      alert('驳回失败: ' + (err instanceof Error ? err.message : '未知错误'))
    } finally {
      setActionLoading(false)
    }
  }

  const handleComment = async () => {
    if (!pr || actionLoading || !comment.trim()) {
      alert('请填写评论内容')
      return
    }
    try {
      setActionLoading(true)
      await addPRComment(pr.id, comment)
      setComment('')
      alert('评论已添加')
    } catch (err) {
      alert('评论失败: ' + (err instanceof Error ? err.message : '未知错误'))
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error || !pr) {
    return (
      <div className="text-center py-8 text-status-danger">
        <p>{error || 'PR不存在'}</p>
        <Button variant="outline" className="mt-4" onClick={onBack}>
          返回列表
        </Button>
      </div>
    )
  }

  const st = statusMap[pr.status]

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <button onClick={onBack} className="p-1.5 rounded-lg hover:bg-accent transition-colors">
          <ChevronLeft className="w-5 h-5" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold">{pr.title}</h1>
            <Badge variant={st.variant}>{st.label}</Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            #{pr.githubPrNumber} · {pr.vendorName} · {pr.authorName} · {pr.branch}
          </p>
        </div>
      </div>

      {/* PR Info */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: '新增行数', value: `+${pr.linesAdded}` },
          { label: '删除行数', value: `-${pr.linesRemoved}` },
          { label: '变更文件', value: pr.filesChanged },
          { label: 'AI代码', value: pr.hasAiCode ? (pr.aiCodeMarked ? '已标记' : '未标记') : '无' },
        ].map(item => (
          <Card key={item.label}>
            <CardContent className="p-4 text-center">
              <p className="text-xs text-muted-foreground">{item.label}</p>
              <p className="text-lg font-semibold mt-1">{item.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quality Gates - 6 Layer Visualization */}
      <Card>
        <CardHeader>
          <CardTitle>六层质量门禁</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {pr.gates.length === 0 ? (
            <p className="text-center text-muted-foreground py-4">暂无质量门禁数据</p>
          ) : (
            pr.gates.map((gate) => {
              const Icon = gateStatusIcon[gate.status]
              return (
                <div key={gate.layer} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-primary-foreground ${layerColor[gate.layer - 1]}`}>
                        L{gate.layer}
                      </span>
                      <span className="font-medium text-sm">{gate.layerName}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Icon className={`w-4 h-4 ${gateStatusColor[gate.status]}`} />
                      <Badge variant={gate.status === 'passed' ? 'success' : gate.status === 'failed' ? 'danger' : 'warning'}>
                        {gate.status === 'passed' ? '通过' : gate.status === 'failed' ? '失败' : '警告'}
                      </Badge>
                    </div>
                  </div>
                  {gate.details && Object.keys(gate.details).length > 0 && (
                    <div className="grid grid-cols-3 gap-2 ml-10">
                      {Object.entries(gate.details).map(([key, value]) => {
                        const SubIcon = gateStatusIcon[value as GateStatus]
                        return (
                          <div key={key} className="flex items-center gap-2 text-xs">
                            <SubIcon className={`w-3.5 h-3.5 ${gateStatusColor[value as GateStatus]}`} />
                            <span className="text-muted-foreground">{key}</span>
                          </div>
                        )
                      })}
                    </div>
                  )}
                  {gate.violationsCount > 0 && (
                    <p className="text-xs text-status-danger mt-2 ml-10">{gate.violationsCount} 个违规项</p>
                  )}
                  {gate.warningsCount > 0 && (
                    <p className="text-xs text-status-warning mt-2 ml-10">{gate.warningsCount} 个警告项</p>
                  )}
                </div>
              )
            })
          )}
        </CardContent>
      </Card>

      {/* Review Action */}
      {(pr.status === 'ci_passed' || pr.status === 'reviewing') && (
        <Card>
          <CardHeader>
            <CardTitle>评审操作</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1.5">评审意见</label>
              <textarea
                value={comment}
                onChange={e => setComment(e.target.value)}
                placeholder="请输入评审意见（驳回时必填）..."
                className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring min-h-[80px] resize-none"
              />
            </div>
            <div className="flex items-center gap-3">
              <Button variant="success" className="gap-2" onClick={handleApprove} disabled={actionLoading}>
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                批准合并
              </Button>
              <Button variant="destructive" className="gap-2" onClick={handleReject} disabled={actionLoading}>
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />}
                驳回修改
              </Button>
              <Button variant="outline" className="gap-2" onClick={handleComment} disabled={actionLoading}>
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <MessageSquare className="w-4 h-4" />}
                仅评论
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}