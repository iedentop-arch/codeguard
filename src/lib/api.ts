/**
 * API 服务层 - 对接后端 FastAPI
 */

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1'

// Token 存储
let authToken: string | null = null

export function setToken(token: string | null) {
  authToken = token
  if (token) {
    localStorage.setItem('auth_token', token)
  } else {
    localStorage.removeItem('auth_token')
  }
}

export function getToken(): string | null {
  if (!authToken) {
    authToken = localStorage.getItem('auth_token')
  }
  return authToken
}

export function clearToken() {
  authToken = null
  localStorage.removeItem('auth_token')
}

// 基础请求函数
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken()
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

// ========== 认证 API ==========

export interface LoginResponse {
  code: number
  message: string
  data: {
    access_token: string
    token_type: string
  }
}

export interface UserInfo {
  id: number
  email: string
  name: string
  role: string
  is_active: boolean
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const formData = new URLSearchParams()
  formData.append('username', email)
  formData.append('password', password)

  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '登录失败' }))
    throw new Error(error.detail || '邮箱或密码错误')
  }

  return response.json()
}

export async function getCurrentUser(): Promise<{ code: number; data: UserInfo }> {
  return request('/auth/me')
}

export async function logout(): Promise<void> {
  await request('/auth/logout', { method: 'POST' })
  clearToken()
}

// ========== 乙方管理 API ==========

export interface Vendor {
  id: number
  name: string
  vendor_type: 'A' | 'B' | 'C' | 'D'
  status: 'pending' | 'active' | 'warning' | 'suspended' | 'exited'
  contact_name: string
  contact_email: string
  contract_start: string
  contract_end: string
  github_org: string
  current_grade: 'A' | 'B' | 'C' | 'D' | null
  current_score: number | null
}

export async function getVendors(): Promise<{ code: number; data: Vendor[] }> {
  return request('/vendors')
}

// ========== PR 审查 API ==========

export interface QualityGateAPI {
  id: number
  pr_id: number
  layer: number
  layer_name: string
  status: 'passed' | 'failed' | 'warning' | 'skipped' | 'running'
  details: Record<string, 'passed' | 'failed' | 'warning' | 'skipped' | 'running'> | null
  violations_count: number
  warnings_count: number
  checked_at: string
}

export interface PullRequestAPI {
  id: number
  vendor_id: number
  vendor_name: string | null
  author_name: string | null
  title: string
  github_pr_number: number
  github_pr_url: string | null
  branch: string | null
  status: string
  lines_added: number
  lines_removed: number
  files_changed: number
  has_ai_code: boolean
  ai_code_marked: boolean
  created_at: string
  merged_at: string | null
  gates: QualityGateAPI[]
}

export interface PRListResponseAPI {
  items: PullRequestAPI[]
  total: number
}

export async function getPullRequests(params?: {
  vendor_id?: number
  status?: string
  page?: number
  page_size?: number
}): Promise<{ code: number; data: PRListResponseAPI }> {
  const query = new URLSearchParams()
  if (params?.vendor_id) query.append('vendor_id', String(params.vendor_id))
  if (params?.status) query.append('status', params.status)
  if (params?.page) query.append('page', String(params.page))
  if (params?.page_size) query.append('page_size', String(params.page_size))
  const queryString = query.toString() ? `?${query}` : ''
  return request(`/reviews/prs${queryString}`)
}

export async function getPullRequestById(prId: number): Promise<{ code: number; data: PullRequestAPI }> {
  return request(`/reviews/prs/${prId}`)
}

export async function approvePullRequest(prId: number, comment?: string): Promise<{ code: number; message: string }> {
  return request(`/reviews/prs/${prId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ comment }),
  })
}

export async function rejectPullRequest(prId: number, reason: string): Promise<{ code: number; message: string }> {
  return request(`/reviews/prs/${prId}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  })
}

export async function addPRComment(prId: number, comment: string): Promise<{ code: number; message: string }> {
  return request(`/reviews/prs/${prId}/comment`, {
    method: 'POST',
    body: JSON.stringify({ comment }),
  })
}

// ========== SLA 指标 API ==========

export interface MonthlyScore {
  id: number
  vendor_id: number
  month: string
  critical_violations_score: number
  warning_trend_score: number
  code_quality_score: number
  compliance_rate_score: number
  pr_efficiency_score: number
  ai_mark_rate_score: number
  ci_success_score: number
  total_score: number
  grade: 'A' | 'B' | 'C' | 'D'
}

export async function getMonthlyScores(vendorId?: number): Promise<{ code: number; data: MonthlyScore[] }> {
  const query = vendorId ? `?vendor_id=${vendorId}` : ''
  return request(`/metrics${query}`)
}

// ========== 规范文档 API ==========

export interface SpecDocument {
  id: number
  title: string
  file_path: string | null
  category: string
  vendor_types: string
  content: string
  read_time: number
  is_required: boolean
  version: string
}

export interface SpecCategory {
  category: string
  name: string
  count: number
}

export async function getSpecDocuments(params?: {
  category?: string
}): Promise<{ code: number; data: SpecDocument[] }> {
  const query = params?.category ? `?category=${params.category}` : ''
  return request(`/specs${query}`)
}

export async function getSpecDocumentById(id: number): Promise<{ code: number; data: SpecDocument }> {
  return request(`/specs/${id}`)
}

export async function getSpecCategories(): Promise<{ code: number; data: SpecCategory[] }> {
  return request('/specs/categories')
}