import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { vendors, monthlyScores } from '@/mocks/data'
import {
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  Shield,
} from 'lucide-react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar,
} from 'recharts'
import type { SLAGrade } from '@/lib/types'

const gradeColor: Record<SLAGrade, string> = {
  A: 'text-grade-a',
  B: 'text-grade-b',
  C: 'text-grade-c',
  D: 'text-grade-d',
}

const gradeBg: Record<SLAGrade, string> = {
  A: 'bg-grade-a/10 border-grade-a/20',
  B: 'bg-grade-b/10 border-grade-b/20',
  C: 'bg-grade-c/10 border-grade-c/20',
  D: 'bg-grade-d/10 border-grade-d/20',
}

export function DashboardPage() {
  const activeVendors = vendors.filter(v => v.status === 'active' || v.status === 'warning')
  const latestScores = vendors.map(v => {
    const scores = monthlyScores.filter(s => s.vendorId === v.id)
    return scores[scores.length - 1]
  }).filter(Boolean)

  const kpis = [
    { label: '活跃乙方', value: activeVendors.length, suffix: '家', icon: Shield, color: 'text-primary' },
    { label: 'CRITICAL违规', value: latestScores.reduce((s, sc) => s + (sc?.criticalViolations || 0), 0), suffix: '次', icon: AlertTriangle, color: 'text-status-danger' },
    { label: 'CI平均成功率', value: Math.round(latestScores.reduce((s, sc) => s + (sc?.ciSuccessRate || 0), 0) / latestScores.length), suffix: '%', icon: TrendingUp, color: 'text-status-success' },
    { label: '平均SLA评分', value: (latestScores.reduce((s, sc) => s + (sc?.totalScore || 0), 0) / latestScores.length).toFixed(1), suffix: '分', icon: CheckCircle2, color: 'text-primary-glow' },
  ]

  // Trend data for line chart
  const trendData = ['2026-01', '2026-02', '2026-03'].map(period => {
    const entry: Record<string, string | number> = { period }
    vendors.forEach(v => {
      const score = monthlyScores.find(s => s.vendorId === v.id && s.period === period)
      entry[v.name] = score?.totalScore || 0
    })
    return entry
  })

  const vendorColors = ['#3182CE', '#38A169', '#9F7AEA', '#D69E2E', '#E53E3E']

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">SLA总览看板</h1>
        <p className="text-sm text-muted-foreground mt-1">乙方代码质量与服务水平实时监控</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi) => {
          const Icon = kpi.icon
          return (
            <Card key={kpi.label}>
              <CardContent className="p-5">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">{kpi.label}</p>
                    <p className="text-3xl font-bold mt-1">
                      {kpi.value}<span className="text-base font-normal text-muted-foreground ml-0.5">{kpi.suffix}</span>
                    </p>
                  </div>
                  <div className={`p-2.5 rounded-lg bg-accent ${kpi.color}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Trend Chart */}
      <Card>
        <CardHeader>
          <CardTitle>SLA评分趋势</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="period" tick={{ fontSize: 12 }} stroke="hsl(var(--muted-foreground))" />
                <YAxis domain={[40, 100]} tick={{ fontSize: 12 }} stroke="hsl(var(--muted-foreground))" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                />
                {vendors.map((v, i) => (
                  <Line
                    key={v.id}
                    type="monotone"
                    dataKey={v.name}
                    stroke={vendorColors[i]}
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Vendor Scorecards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {vendors.map((vendor) => {
          const scores = monthlyScores.filter(s => s.vendorId === vendor.id)
          const latest = scores[scores.length - 1]
          if (!latest) return null

          const dimensions = [
            { label: 'CRITICAL违规', value: latest.criticalViolations, target: '=0', pct: latest.criticalViolations === 0 ? 100 : 0 },
            { label: '代码质量', value: latest.codeQualityScore, target: '≥90', pct: latest.codeQualityScore },
            { label: '合规通过率', value: latest.compliancePassRate, target: '≥95%', pct: latest.compliancePassRate },
            { label: 'PR评审效率', value: latest.prAvgReviewRounds, target: '≤2轮', pct: Math.max(0, 100 - (latest.prAvgReviewRounds - 1.5) * 25) },
            { label: 'AI标记率', value: latest.aiCodeMarkingRate, target: '100%', pct: latest.aiCodeMarkingRate },
            { label: 'CI成功率', value: latest.ciSuccessRate, target: '≥95%', pct: latest.ciSuccessRate },
          ]

          return (
            <Card key={vendor.id} className={`border-l-4 ${gradeBg[vendor.currentGrade]}`}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base">{vendor.name}</CardTitle>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {vendor.vendorType}类 · {vendor.memberCount}人 · {vendor.githubOrg}
                    </p>
                  </div>
                  <div className={`text-3xl font-bold ${gradeColor[vendor.currentGrade]}`}>
                    {vendor.currentGrade}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {dimensions.map((dim) => (
                  <div key={dim.label} className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">{dim.label}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-1.5 rounded-full bg-accent overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${Math.min(100, dim.pct)}%`,
                            backgroundColor: dim.pct >= 90 ? 'hsl(var(--grade-a))' : dim.pct >= 70 ? 'hsl(var(--grade-c))' : 'hsl(var(--grade-d))',
                          }}
                        />
                      </div>
                      <span className="w-12 text-right font-mono text-xs">
                        {typeof dim.value === 'number' ? (dim.label.includes('率') || dim.label.includes('质量') ? `${dim.value}%` : dim.value) : dim.value}
                      </span>
                    </div>
                  </div>
                ))}
                <div className="flex items-center justify-between pt-2 border-t">
                  <span className="text-sm font-medium">综合评分</span>
                  <span className={`text-xl font-bold ${gradeColor[vendor.currentGrade]}`}>
                    {latest.totalScore}
                  </span>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
