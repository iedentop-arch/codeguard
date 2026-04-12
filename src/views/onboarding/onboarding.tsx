import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { specDocuments, examQuestions } from '@/mocks/data'
import type { VendorType, ExamQuestion } from '@/lib/types'
import {
  BookOpen,
  CheckCircle2,
  Circle,
  Clock,
  Award,
  ChevronRight,
  PlayCircle,
  AlertTriangle,
  FileText,
} from 'lucide-react'

const steps = [
  { label: '完善信息', icon: FileText },
  { label: '规范学习', icon: BookOpen },
  { label: '在线考试', icon: PlayCircle },
  { label: '获取认证', icon: Award },
]

export function OnboardingPage() {
  const [currentStep, setCurrentStep] = useState(1)
  const [vendorType] = useState<VendorType>('B')
  const [readSpecs, setReadSpecs] = useState<Set<number>>(new Set([1, 4, 5]))
  const [examState, setExamState] = useState<'idle' | 'taking' | 'result'>('idle')
  const [examAnswers, setExamAnswers] = useState<Record<number, string>>({})
  const [examSubmitted, setExamSubmitted] = useState(false)
  const [timeLeft, setTimeLeft] = useState(600)

  const filteredSpecs = specDocuments.filter(s => s.vendorTypes.includes(vendorType))
  const requiredSpecs = filteredSpecs.filter(s => s.isRequired)
  const readRequired = requiredSpecs.filter(s => readSpecs.has(s.id)).length
  const canTakeExam = readRequired >= requiredSpecs.length - 1 // Allow with 1 unread

  if (examState === 'taking') {
    return <ExamTaking questions={examQuestions} answers={examAnswers} setAnswers={setExamAnswers} timeLeft={timeLeft} setTimeLeft={setTimeLeft} onFinish={() => { setExamSubmitted(true); setExamState('result') }} />
  }

  if (examState === 'result') {
    const correct = examQuestions.filter(q => examAnswers[q.id] === q.correctAnswer).length
    const passed = correct >= 8
    return (
      <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
        <Card>
          <CardContent className="p-8 text-center">
            {passed ? (
              <>
                <div className="w-20 h-20 rounded-full bg-status-success/10 flex items-center justify-center mx-auto mb-4">
                  <Award className="w-10 h-10 text-status-success" />
                </div>
                <h2 className="text-2xl font-bold text-status-success">恭喜通过！</h2>
                <p className="text-muted-foreground mt-2">你的考试成绩：<span className="text-2xl font-bold">{correct * 10}</span> 分</p>
                <p className="text-sm text-muted-foreground mt-1">认证编号：CG-{Date.now().toString(36).toUpperCase()}</p>
                <Button className="mt-6" onClick={() => setCurrentStep(3)}>查看认证</Button>
              </>
            ) : (
              <>
                <div className="w-20 h-20 rounded-full bg-status-danger/10 flex items-center justify-center mx-auto mb-4">
                  <AlertTriangle className="w-10 h-10 text-status-danger" />
                </div>
                <h2 className="text-2xl font-bold text-status-danger">未通过</h2>
                <p className="text-muted-foreground mt-2">你的考试成绩：<span className="text-2xl font-bold">{correct * 10}</span> 分（需80分及格）</p>
                <p className="text-sm text-muted-foreground mt-1">你还有1次考试机会</p>
                <Button variant="warning" className="mt-6" onClick={() => { setExamAnswers({}); setExamState('taking'); setTimeLeft(600) }}>重新考试</Button>
              </>
            )}
          </CardContent>
        </Card>

        {/* Answer review */}
        <Card>
          <CardHeader>
            <CardTitle>答题回顾</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {examQuestions.map((q, i) => {
              const isCorrect = examAnswers[q.id] === q.correctAnswer
              return (
                <div key={q.id} className="border rounded-lg p-4">
                  <div className="flex items-start gap-2">
                    {isCorrect ? (
                      <CheckCircle2 className="w-4 h-4 text-status-success mt-0.5 flex-shrink-0" />
                    ) : (
                      <XIcon className="w-4 h-4 text-status-danger mt-0.5 flex-shrink-0" />
                    )}
                    <div className="flex-1">
                      <p className="text-sm font-medium">{i + 1}. {q.questionText}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        你的答案：{examAnswers[q.id] || '未作答'} · 正确答案：{q.correctAnswer}
                      </p>
                      <p className="text-xs text-status-info mt-1">{q.explanation}</p>
                    </div>
                  </div>
                </div>
              )
            })}
          </CardContent>
        </Card>
      </div>
    )
  }

  if (currentStep === 3) {
    return (
      <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">
        <Card>
          <CardContent className="p-8 text-center">
            <div className="w-24 h-24 rounded-2xl bg-primary/5 flex items-center justify-center mx-auto mb-6 border-2 border-primary/20">
              <Award className="w-12 h-12 text-primary" />
            </div>
            <h2 className="text-2xl font-bold">认证完成</h2>
            <p className="text-muted-foreground mt-2">你已完成所有入驻步骤，可以开始提交代码</p>
            <div className="mt-6 p-4 rounded-lg bg-accent text-sm">
              <p>认证编号：CG-2026-0410-001</p>
              <p>认证类型：{vendorType}类乙方开发</p>
              <p>生效日期：2026-04-10</p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">入驻中心</h1>
        <p className="text-sm text-muted-foreground mt-1">完成入驻流程后即可获得代码提交权限</p>
      </div>

      {/* Stepper */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            {steps.map((step, i) => {
              const Icon = step.icon
              const isCompleted = i < currentStep
              const isCurrent = i === currentStep
              return (
                <div key={i} className="flex items-center flex-1">
                  <div className="flex flex-col items-center">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
                      isCompleted ? 'bg-status-success text-primary-foreground' :
                      isCurrent ? 'bg-primary text-primary-foreground' :
                      'bg-accent text-muted-foreground'
                    }`}>
                      {isCompleted ? <CheckCircle2 className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
                    </div>
                    <span className={`text-xs mt-2 ${isCurrent ? 'font-medium text-primary' : 'text-muted-foreground'}`}>
                      {step.label}
                    </span>
                  </div>
                  {i < steps.length - 1 && (
                    <div className={`flex-1 h-0.5 mx-3 rounded-full ${isCompleted ? 'bg-status-success' : 'bg-accent'}`} />
                  )}
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Step Content */}
      {currentStep === 1 && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="w-5 h-5" /> 规范学习
                <Badge variant="info">{readSpecs.size}/{filteredSpecs.length} 已读</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {filteredSpecs.map(spec => {
                const isRead = readSpecs.has(spec.id)
                return (
                  <div
                    key={spec.id}
                    className={`flex items-center justify-between p-3 rounded-lg border transition-colors ${
                      isRead ? 'bg-status-success/5 border-status-success/20' : 'hover:bg-accent'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {isRead ? (
                        <CheckCircle2 className="w-4 h-4 text-status-success" />
                      ) : (
                        <Circle className="w-4 h-4 text-muted-foreground" />
                      )}
                      <div>
                        <p className="text-sm font-medium">{spec.title}</p>
                        <p className="text-xs text-muted-foreground">
                          {spec.isRequired ? '必读' : '选读'} · 约{spec.readTime}分钟
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {!isRead && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setReadSpecs(prev => new Set([...prev, spec.id]))}
                        >
                          标记已读
                        </Button>
                      )}
                      <ChevronRight className="w-4 h-4 text-muted-foreground" />
                    </div>
                  </div>
                )
              })}
            </CardContent>
          </Card>
          <div className="flex justify-end">
            <Button
              onClick={() => setCurrentStep(2)}
              disabled={!canTakeExam}
              className="gap-2"
            >
              进入考试 <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}

      {currentStep === 2 && (
        <Card>
          <CardContent className="p-8 text-center">
            <PlayCircle className="w-16 h-16 text-primary mx-auto mb-4" />
            <h2 className="text-xl font-bold">在线合规考试</h2>
            <p className="text-muted-foreground mt-2">考试规则</p>
            <div className="mt-4 space-y-2 text-sm text-muted-foreground">
              <p>共 {examQuestions.length} 道判断题</p>
              <p>考试时间 {10} 分钟</p>
              <p>80 分及格，最多 2 次机会</p>
              <p>覆盖 12 条 CRITICAL 红线规则</p>
            </div>
            <Button size="lg" className="mt-6 gap-2" onClick={() => setExamState('taking')}>
              开始考试 <ChevronRight className="w-4 h-4" />
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function ExamTaking({ questions, answers, setAnswers, timeLeft, setTimeLeft, onFinish }: {
  questions: ExamQuestion[]
  answers: Record<number, string>
  setAnswers: (a: Record<number, string>) => void
  timeLeft: number
  setTimeLeft: (t: number) => void
  onFinish: () => void
}) {
  const [currentQ, setCurrentQ] = useState(0)
  const q = questions[currentQ]
  const mins = Math.floor(timeLeft / 60)
  const secs = timeLeft % 60
  const allAnswered = questions.every(q => answers[q.id])

  // Simple timer
  useState(() => {
    const timer = setInterval(() => {
      setTimeLeft(Math.max(0, timeLeft - 1))
    }, 1000)
    return () => clearInterval(timer)
  })

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      {/* Timer & Progress */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Badge variant={timeLeft < 120 ? 'danger' : 'default'}>
            <Clock className="w-3 h-3 mr-1" />
            {mins}:{secs.toString().padStart(2, '0')}
          </Badge>
          <span className="text-sm text-muted-foreground">
            {currentQ + 1} / {questions.length}
          </span>
        </div>
        <Button
          variant="default"
          disabled={!allAnswered}
          onClick={onFinish}
        >
          提交考试
        </Button>
      </div>

      {/* Question navigation */}
      <div className="flex gap-1">
        {questions.map((_, i) => (
          <button
            key={i}
            onClick={() => setCurrentQ(i)}
            className={`w-8 h-8 rounded text-xs font-medium transition-colors ${
              i === currentQ ? 'bg-primary text-primary-foreground' :
              answers[questions[i].id] ? 'bg-status-success/20 text-status-success' :
              'bg-accent text-muted-foreground'
            }`}
          >
            {i + 1}
          </button>
        ))}
      </div>

      {/* Question */}
      <Card>
        <CardContent className="p-6 space-y-5">
          <div>
            <Badge variant={q.severity === 'CRITICAL' ? 'danger' : 'warning'} className="mb-3">
              {q.severity} · {q.ruleId}
            </Badge>
            <h3 className="text-lg font-medium">{q.questionText}</h3>
          </div>

          {q.codeSnippet && (
            <pre className="p-4 rounded-lg bg-foreground/5 text-sm font-mono overflow-x-auto">
              {q.codeSnippet}
            </pre>
          )}

          <div className="space-y-2">
            {q.options.map(opt => (
              <button
                key={opt}
                onClick={() => setAnswers({ ...answers, [q.id]: opt })}
                className={`w-full p-4 rounded-lg border text-left text-sm transition-all ${
                  answers[q.id] === opt
                    ? 'border-primary bg-primary/5 ring-2 ring-primary/20'
                    : 'hover:bg-accent'
                }`}
              >
                {opt}
              </button>
            ))}
          </div>

          <div className="flex justify-between pt-2">
            <Button variant="outline" disabled={currentQ === 0} onClick={() => setCurrentQ(currentQ - 1)}>
              上一题
            </Button>
            <Button variant="outline" disabled={currentQ === questions.length - 1} onClick={() => setCurrentQ(currentQ + 1)}>
              下一题
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function XIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M18 6L6 18M6 6l12 12" />
    </svg>
  )
}
