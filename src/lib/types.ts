export type VendorType = 'A' | 'B' | 'C' | 'D'
export type SLAGrade = 'A' | 'B' | 'C' | 'D'
export type VendorStatus = 'pending' | 'active' | 'warning' | 'suspended' | 'exited'
export type UserRole = 'admin' | 'vendor_admin' | 'vendor_dev'
export type PRStatus = 'open' | 'ci_checking' | 'ci_passed' | 'ci_failed' | 'reviewing' | 'approved' | 'rejected' | 'merged'
export type GateLayer = 1 | 2 | 3 | 4 | 5 | 6
export type GateStatus = 'passed' | 'failed' | 'warning' | 'skipped' | 'running'
export type DeliveryStatus = 'submitted' | 'under_review' | 'accepted' | 'rejected'

export interface Vendor {
  id: number
  name: string
  vendorType: VendorType
  status: VendorStatus
  memberCount: number
  githubOrg: string
  currentGrade: SLAGrade
  currentScore: number
  contractStart: string
  contractEnd: string
  onboardingStatus: 'not_started' | 'in_progress' | 'completed'
}

export interface VendorMember {
  id: number
  vendorId: number
  name: string
  email: string
  role: string
  status: 'pending' | 'active' | 'suspended'
  examScore: number | null
  certificationId: string | null
}

export interface QualityGate {
  id: number
  prId: number
  layer: GateLayer
  layerName: string
  status: GateStatus
  details: Record<string, GateStatus>
  violationsCount: number
  warningsCount: number
}

export interface PullRequest {
  id: number
  vendorId: number
  vendorName: string
  authorName: string
  githubPrNumber: number
  title: string
  branch: string
  status: PRStatus
  linesAdded: number
  linesRemoved: number
  filesChanged: number
  hasAiCode: boolean
  aiCodeMarked: boolean
  createdAt: string
  gates: QualityGate[]
}

export interface MonthlyScore {
  vendorId: number
  vendorName: string
  period: string
  criticalViolations: number
  warningTrendPct: number
  codeQualityScore: number
  compliancePassRate: number
  prAvgReviewRounds: number
  aiCodeMarkingRate: number
  ciSuccessRate: number
  totalScore: number
  grade: SLAGrade
}

export interface ExamQuestion {
  id: number
  category: string
  ruleId: string
  severity: 'CRITICAL' | 'WARNING' | 'INFO'
  questionType: 'judgment' | 'scenario'
  questionText: string
  codeSnippet: string | null
  options: string[]
  correctAnswer: string
  explanation: string
}

export interface SpecDocument {
  id: number
  title: string
  category: string
  vendorTypes: VendorType[]
  readTime: number
  isRequired: boolean
}

export interface Delivery {
  id: number
  projectId: number
  projectName: string
  vendorId: number
  vendorName: string
  version: string
  description: string
  status: DeliveryStatus
  submittedAt: string
}

export interface ChecklistItem {
  id: number
  dimension: string
  dimensionIndex: number
  itemNumber: string
  description: string
  acceptanceCriteria: string
  status: 'pending' | 'accepted' | 'rejected'
  autoFilled: boolean
  reviewerNotes: string
}
