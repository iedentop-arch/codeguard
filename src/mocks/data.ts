import type { Vendor, PullRequest, MonthlyScore, ExamQuestion, SpecDocument, Delivery, ChecklistItem, QualityGate } from '../lib/types'

export const vendors: Vendor[] = [
  { id: 1, name: '智联科技', vendorType: 'A', status: 'active', memberCount: 6, githubOrg: 'zhilian-tech', currentGrade: 'A', currentScore: 93.6, contractStart: '2025-09-01', contractEnd: '2026-08-31', onboardingStatus: 'completed' },
  { id: 2, name: '云端数据', vendorType: 'B', status: 'active', memberCount: 8, githubOrg: 'yunduan-data', currentGrade: 'B', currentScore: 88.2, contractStart: '2025-10-01', contractEnd: '2026-09-30', onboardingStatus: 'completed' },
  { id: 3, name: '星辰智能', vendorType: 'C', status: 'active', memberCount: 10, githubOrg: 'xingchen-ai', currentGrade: 'A', currentScore: 91.0, contractStart: '2025-08-01', contractEnd: '2026-07-31', onboardingStatus: 'completed' },
  { id: 4, name: '万象数字', vendorType: 'D', status: 'warning', memberCount: 12, githubOrg: 'wanxiang-digital', currentGrade: 'C', currentScore: 68.5, contractStart: '2025-07-01', contractEnd: '2026-06-30', onboardingStatus: 'completed' },
  { id: 5, name: '极光网络', vendorType: 'B', status: 'suspended', memberCount: 5, githubOrg: 'jiguang-net', currentGrade: 'D', currentScore: 52.3, contractStart: '2025-06-01', contractEnd: '2026-05-31', onboardingStatus: 'completed' },
]

export const examQuestions: ExamQuestion[] = [
  {
    id: 1, category: 'compliance_redline', ruleId: 'AD-1.1', severity: 'CRITICAL',
    questionType: 'judgment',
    questionText: '在营销文案中使用"最好的奶粉"这一表述是否合规？',
    codeSnippet: '最好的奶粉，宝宝更聪明',
    options: ['合规', '不合规'], correctAnswer: '不合规',
    explanation: '违反广告法，使用绝对化用语"最好的"属于AD-1.1红线规则'
  },
  {
    id: 2, category: 'code_redline', ruleId: 'ARCH-1', severity: 'CRITICAL',
    questionType: 'judgment',
    questionText: 'Controller层直接调用Infrastructure层的数据库操作，是否违反架构规范？',
    codeSnippet: '# controller.py\nclass UserController:\n    def get_user(self, id):\n        return db.query(User).get(id)',
    options: ['合规', '不合规'], correctAnswer: '不合规',
    explanation: '违反四层架构规范，Controller层不能直接访问Infrastructure层，必须通过Service层'
  },
  {
    id: 3, category: 'compliance_redline', ruleId: 'IF-2.1', severity: 'CRITICAL',
    questionType: 'judgment',
    questionText: '婴儿配方奶粉宣传"接近母乳"是否合规？',
    codeSnippet: '配方接近母乳，给宝宝天然呵护',
    options: ['合规', '不合规'], correctAnswer: '不合规',
    explanation: '违反IF-2.1规则，禁止使用"接近母乳""替代母乳"等暗示性表述'
  },
  {
    id: 4, category: 'process_redline', ruleId: 'PROC-1', severity: 'CRITICAL',
    questionType: 'judgment',
    questionText: 'AI生成的代码未标记AI生成标记，直接提交PR，是否合规？',
    codeSnippet: '# 未添加 AI-Generated 标记的代码\nasync def process_order(order_id: str):\n    ...',
    options: ['合规', '不合规'], correctAnswer: '不合规',
    explanation: '违反PROC-1规则，AI生成的代码必须标记，未标记等同于学术不端'
  },
  {
    id: 5, category: 'code_redline', ruleId: 'SEC-1', severity: 'CRITICAL',
    questionType: 'judgment',
    questionText: '代码中硬编码了数据库连接字符串，是否违反红线规则？',
    codeSnippet: 'DB_URL = "postgresql://admin:password123@db.internal:5432/prod"',
    options: ['合规', '不合规'], correctAnswer: '不合规',
    explanation: '违反SEC-1红线规则，禁止硬编码凭据、令牌、密码等敏感信息'
  },
  {
    id: 6, category: 'compliance_redline', ruleId: 'AD-3.1', severity: 'CRITICAL',
    questionType: 'judgment',
    questionText: '营养品宣传"增强免疫力，预防疾病"是否合规？',
    codeSnippet: '每日一粒，增强免疫力，预防感冒',
    options: ['合规', '不合规'], correctAnswer: '不合规',
    explanation: '违反AD-3.1规则，禁止对食品做医疗效果宣传（治疗/预防/增强免疫）'
  },
  {
    id: 7, category: 'code_redline', ruleId: 'CODE-1', severity: 'CRITICAL',
    questionType: 'judgment',
    questionText: '提交的代码包含TODO和pass占位符，未实现完整功能，是否合规？',
    codeSnippet: 'def calculate_discount(price, level):\n    # TODO: implement later\n    pass',
    options: ['合规', '不合规'], correctAnswer: '不合规',
    explanation: '违反CODE-1红线规则，提交的代码必须完整可运行，禁止占位符'
  },
  {
    id: 8, category: 'process_redline', ruleId: 'PROC-2', severity: 'CRITICAL',
    questionType: 'judgment',
    questionText: 'PR未经Code Review直接合并到main分支，是否合规？',
    codeSnippet: 'git push origin main  # 直接推送',
    options: ['合规', '不合规'], correctAnswer: '不合规',
    explanation: '违反PROC-2规则，所有代码必须经过Code Review才能合并，禁止自动合并'
  },
  {
    id: 9, category: 'code_redline', ruleId: 'API-1', severity: 'WARNING',
    questionType: 'judgment',
    questionText: 'API响应格式不统一，有的返回{code, data, message}，有的直接返回数据，是否合规？',
    codeSnippet: '# 接口A\n{"code": 0, "data": {...}, "message": "ok"}\n# 接口B\n{...}',
    options: ['合规', '不合规'], correctAnswer: '不合规',
    explanation: '违反API设计规范，所有接口必须统一返回{code, data, message}格式'
  },
  {
    id: 10, category: 'code_redline', ruleId: 'TEST-1', severity: 'WARNING',
    questionType: 'judgment',
    questionText: '新增的Service方法没有编写单元测试，是否合规？',
    codeSnippet: 'class OrderService:\n    def create_order(self, data):\n        # 无对应测试\n        ...',
    options: ['合规', '不合规'], correctAnswer: '不合规',
    explanation: '违反TEST-1规则，新增Service方法必须至少编写1个单元测试'
  },
]

export const specDocuments: SpecDocument[] = [
  { id: 1, title: 'Python编码风格规范', category: 'general', vendorTypes: ['B', 'D'], readTime: 15, isRequired: true },
  { id: 2, title: 'Vue 3组件开发规范', category: 'general', vendorTypes: ['A', 'D'], readTime: 20, isRequired: true },
  { id: 3, title: 'RESTful API设计指南', category: 'general', vendorTypes: ['A', 'B', 'D'], readTime: 12, isRequired: true },
  { id: 4, title: 'Git工作流与提交规范', category: 'general', vendorTypes: ['A', 'B', 'C', 'D'], readTime: 10, isRequired: true },
  { id: 5, title: 'Code Review方法论', category: 'general', vendorTypes: ['A', 'B', 'C', 'D'], readTime: 15, isRequired: true },
  { id: 6, title: '系统设计原则', category: 'architecture', vendorTypes: ['B', 'D'], readTime: 25, isRequired: true },
  { id: 7, title: '四层架构分层规范', category: 'architecture', vendorTypes: ['B', 'D'], readTime: 20, isRequired: true },
  { id: 8, title: 'LangGraph实现规范', category: 'ai-agents', vendorTypes: ['C', 'D'], readTime: 30, isRequired: true },
  { id: 9, title: 'Agent安全指南', category: 'ai-agents', vendorTypes: ['C', 'D'], readTime: 18, isRequired: true },
  { id: 10, title: 'Prompt工程规范', category: 'ai-agents', vendorTypes: ['C', 'D'], readTime: 22, isRequired: true },
  { id: 11, title: 'Skill开发标准', category: 'skills', vendorTypes: ['C', 'D'], readTime: 15, isRequired: true },
  { id: 12, title: 'MCP服务器标准', category: 'mcp', vendorTypes: ['C', 'D'], readTime: 20, isRequired: true },
  { id: 13, title: '广告法合规检查清单', category: 'compliance', vendorTypes: ['A', 'B', 'C', 'D'], readTime: 12, isRequired: true },
  { id: 14, title: '婴幼儿配方奶粉法规', category: 'compliance', vendorTypes: ['A', 'B', 'C', 'D'], readTime: 10, isRequired: true },
  { id: 15, title: '数据库设计指南', category: 'architecture', vendorTypes: ['B', 'D'], readTime: 18, isRequired: true },
  { id: 16, title: 'DeepAgent编排模式', category: 'ai-agents', vendorTypes: ['C', 'D'], readTime: 25, isRequired: false },
  { id: 17, title: 'RAGFlow集成指南', category: 'ai-agents', vendorTypes: ['C', 'D'], readTime: 20, isRequired: false },
  { id: 18, title: '营养标签规范', category: 'compliance', vendorTypes: ['A', 'B', 'D'], readTime: 8, isRequired: true },
  { id: 19, title: '性能优化指南', category: 'architecture', vendorTypes: ['B', 'D'], readTime: 15, isRequired: false },
  { id: 20, title: 'CI/CD流水线模板', category: 'templates', vendorTypes: ['A', 'B', 'C', 'D'], readTime: 10, isRequired: true },
  { id: 21, title: '乙方入驻指南', category: 'governance', vendorTypes: ['A', 'B', 'C', 'D'], readTime: 15, isRequired: true },
]

const makeGates = (prId: number): QualityGate[] => [
  { id: prId * 10 + 1, prId, layer: 1, layerName: '红线检查', status: prId % 3 === 0 ? 'failed' : 'passed', details: { security: 'passed', lint: 'passed', typeCheck: prId % 3 === 0 ? 'failed' : 'passed', unitTest: 'passed' }, violationsCount: prId % 3 === 0 ? 1 : 0, warningsCount: 0 },
  { id: prId * 10 + 2, prId, layer: 2, layerName: '必需检查', status: prId === 2 ? 'warning' : 'passed', details: { apiDocs: 'passed', agentPrompts: 'passed', depSecurity: prId === 2 ? 'warning' : 'passed' }, violationsCount: 0, warningsCount: prId === 2 ? 1 : 0 },
  { id: prId * 10 + 3, prId, layer: 3, layerName: 'AI辅助检查', status: 'passed', details: { architecture: 'passed', complexity: 'passed', duplication: 'passed' }, violationsCount: 0, warningsCount: 0 },
  { id: prId * 10 + 4, prId, layer: 4, layerName: '指标采集', status: 'passed', details: { ruffScore: 'passed', mypyScore: 'passed', coverage: 'passed' }, violationsCount: 0, warningsCount: 0 },
  { id: prId * 10 + 5, prId, layer: 5, layerName: '文档验证', status: prId === 4 ? 'warning' : 'passed', details: { apiDocs: 'passed', agentDefs: prId === 4 ? 'warning' : 'passed', adr: 'passed' }, violationsCount: 0, warningsCount: prId === 4 ? 1 : 0 },
  { id: prId * 10 + 6, prId, layer: 6, layerName: '合规审查', status: prId === 3 ? 'failed' : 'passed', details: { contentScan: prId === 3 ? 'failed' : 'passed', legalCheck: 'passed' }, violationsCount: prId === 3 ? 2 : 0, warningsCount: 0 },
]

export const pullRequests: PullRequest[] = [
  { id: 1, vendorId: 1, vendorName: '智联科技', authorName: '张伟', githubPrNumber: 142, title: 'feat(marketing): 添加新品推广页面组件', branch: 'feature/new-promo-page', status: 'reviewing', linesAdded: 234, linesRemoved: 12, filesChanged: 8, hasAiCode: true, aiCodeMarked: true, createdAt: '2026-04-08T10:30:00', gates: makeGates(1) },
  { id: 2, vendorId: 2, vendorName: '云端数据', authorName: '李明', githubPrNumber: 89, title: 'fix(api): 修复订单查询接口分页参数校验', branch: 'fix/order-pagination', status: 'ci_passed', linesAdded: 45, linesRemoved: 18, filesChanged: 3, hasAiCode: true, aiCodeMarked: true, createdAt: '2026-04-09T14:20:00', gates: makeGates(2) },
  { id: 3, vendorId: 4, vendorName: '万象数字', authorName: '王磊', githubPrNumber: 256, title: 'feat(agent): 添加育儿问答Agent节点', branch: 'feature/parenting-agent', status: 'ci_failed', linesAdded: 567, linesRemoved: 23, filesChanged: 15, hasAiCode: true, aiCodeMarked: false, createdAt: '2026-04-09T16:45:00', gates: makeGates(3) },
  { id: 4, vendorId: 3, vendorName: '星辰智能', authorName: '陈静', githubPrNumber: 178, title: 'refactor(rag): 优化RAGFlow检索策略', branch: 'refactor/rag-retrieval', status: 'approved', linesAdded: 189, linesRemoved: 156, filesChanged: 7, hasAiCode: false, aiCodeMarked: true, createdAt: '2026-04-07T09:15:00', gates: makeGates(4) },
  { id: 5, vendorId: 2, vendorName: '云端数据', authorName: '刘洋', githubPrNumber: 92, title: 'feat(service): 实现SLA评分计算引擎', branch: 'feature/sla-engine', status: 'merged', linesAdded: 342, linesRemoved: 0, filesChanged: 12, hasAiCode: true, aiCodeMarked: true, createdAt: '2026-04-05T11:00:00', gates: makeGates(5) },
]

export const monthlyScores: MonthlyScore[] = [
  { vendorId: 1, vendorName: '智联科技', period: '2026-01', criticalViolations: 0, warningTrendPct: -12, codeQualityScore: 92, compliancePassRate: 98, prAvgReviewRounds: 1.8, aiCodeMarkingRate: 100, ciSuccessRate: 96, totalScore: 93.6, grade: 'A' },
  { vendorId: 1, vendorName: '智联科技', period: '2026-02', criticalViolations: 0, warningTrendPct: -8, codeQualityScore: 93, compliancePassRate: 99, prAvgReviewRounds: 1.6, aiCodeMarkingRate: 100, ciSuccessRate: 97, totalScore: 94.8, grade: 'A' },
  { vendorId: 1, vendorName: '智联科技', period: '2026-03', criticalViolations: 0, warningTrendPct: -15, codeQualityScore: 94, compliancePassRate: 100, prAvgReviewRounds: 1.5, aiCodeMarkingRate: 100, ciSuccessRate: 98, totalScore: 95.2, grade: 'A' },
  { vendorId: 2, vendorName: '云端数据', period: '2026-01', criticalViolations: 0, warningTrendPct: -5, codeQualityScore: 88, compliancePassRate: 95, prAvgReviewRounds: 2.1, aiCodeMarkingRate: 98, ciSuccessRate: 92, totalScore: 87.5, grade: 'B' },
  { vendorId: 2, vendorName: '云端数据', period: '2026-02', criticalViolations: 0, warningTrendPct: -3, codeQualityScore: 89, compliancePassRate: 96, prAvgReviewRounds: 2.0, aiCodeMarkingRate: 99, ciSuccessRate: 93, totalScore: 88.0, grade: 'B' },
  { vendorId: 2, vendorName: '云端数据', period: '2026-03', criticalViolations: 0, warningTrendPct: -7, codeQualityScore: 90, compliancePassRate: 96, prAvgReviewRounds: 1.9, aiCodeMarkingRate: 100, ciSuccessRate: 94, totalScore: 88.2, grade: 'B' },
  { vendorId: 3, vendorName: '星辰智能', period: '2026-01', criticalViolations: 0, warningTrendPct: -10, codeQualityScore: 90, compliancePassRate: 97, prAvgReviewRounds: 1.7, aiCodeMarkingRate: 100, ciSuccessRate: 95, totalScore: 90.8, grade: 'A' },
  { vendorId: 3, vendorName: '星辰智能', period: '2026-02', criticalViolations: 0, warningTrendPct: -8, codeQualityScore: 91, compliancePassRate: 97, prAvgReviewRounds: 1.6, aiCodeMarkingRate: 100, ciSuccessRate: 96, totalScore: 91.0, grade: 'A' },
  { vendorId: 3, vendorName: '星辰智能', period: '2026-03', criticalViolations: 0, warningTrendPct: -12, codeQualityScore: 92, compliancePassRate: 98, prAvgReviewRounds: 1.5, aiCodeMarkingRate: 100, ciSuccessRate: 97, totalScore: 91.5, grade: 'A' },
  { vendorId: 4, vendorName: '万象数字', period: '2026-01', criticalViolations: 1, warningTrendPct: 5, codeQualityScore: 72, compliancePassRate: 88, prAvgReviewRounds: 3.2, aiCodeMarkingRate: 90, ciSuccessRate: 82, totalScore: 65.3, grade: 'C' },
  { vendorId: 4, vendorName: '万象数字', period: '2026-02', criticalViolations: 2, warningTrendPct: 8, codeQualityScore: 70, compliancePassRate: 85, prAvgReviewRounds: 3.5, aiCodeMarkingRate: 88, ciSuccessRate: 80, totalScore: 60.1, grade: 'C' },
  { vendorId: 4, vendorName: '万象数字', period: '2026-03', criticalViolations: 1, warningTrendPct: 3, codeQualityScore: 74, compliancePassRate: 90, prAvgReviewRounds: 3.0, aiCodeMarkingRate: 92, ciSuccessRate: 84, totalScore: 68.5, grade: 'C' },
  { vendorId: 5, vendorName: '极光网络', period: '2026-01', criticalViolations: 3, warningTrendPct: 15, codeQualityScore: 58, compliancePassRate: 78, prAvgReviewRounds: 4.2, aiCodeMarkingRate: 80, ciSuccessRate: 72, totalScore: 48.2, grade: 'D' },
  { vendorId: 5, vendorName: '极光网络', period: '2026-02', criticalViolations: 2, warningTrendPct: 10, codeQualityScore: 60, compliancePassRate: 82, prAvgReviewRounds: 3.8, aiCodeMarkingRate: 85, ciSuccessRate: 76, totalScore: 52.3, grade: 'D' },
  { vendorId: 5, vendorName: '极光网络', period: '2026-03', criticalViolations: 4, warningTrendPct: 20, codeQualityScore: 55, compliancePassRate: 75, prAvgReviewRounds: 4.5, aiCodeMarkingRate: 78, ciSuccessRate: 70, totalScore: 45.8, grade: 'D' },
]

export const deliveries: Delivery[] = [
  { id: 1, projectId: 1, projectName: '智能营销平台', vendorId: 1, vendorName: '智联科技', version: 'v2.3.0', description: '新品推广模块 + 营销活动管理功能', status: 'under_review', submittedAt: '2026-04-05T10:00:00' },
  { id: 2, projectId: 2, projectName: 'AI育儿助手', vendorId: 3, vendorName: '星辰智能', version: 'v1.1.0', description: 'RAG检索优化 + 合规检查增强', status: 'submitted', submittedAt: '2026-04-08T14:30:00' },
]

export const checklistItems: ChecklistItem[] = [
  { id: 1, dimension: '项目初始化', dimensionIndex: 1, itemNumber: '1.1', description: '项目结构符合四层架构规范', acceptanceCriteria: '目录结构包含controller/service/infrastructure/model层', status: 'accepted', autoFilled: true, reviewerNotes: '' },
  { id: 2, dimension: '项目初始化', dimensionIndex: 1, itemNumber: '1.2', description: 'pre-commit hooks已配置', acceptanceCriteria: '包含black/ruff/mypy配置', status: 'accepted', autoFilled: true, reviewerNotes: '' },
  { id: 3, dimension: '项目初始化', dimensionIndex: 1, itemNumber: '1.3', description: '.cursorrules文件已创建', acceptanceCriteria: '包含项目编码规则', status: 'pending', autoFilled: false, reviewerNotes: '' },
  { id: 4, dimension: '代码质量', dimensionIndex: 2, itemNumber: '2.1', description: 'Ruff检查全部通过', acceptanceCriteria: '无E/F/W级别错误', status: 'accepted', autoFilled: true, reviewerNotes: '' },
  { id: 5, dimension: '代码质量', dimensionIndex: 2, itemNumber: '2.2', description: 'MyPy类型检查通过', acceptanceCriteria: 'strict模式无错误', status: 'accepted', autoFilled: true, reviewerNotes: '' },
  { id: 6, dimension: '代码质量', dimensionIndex: 2, itemNumber: '2.3', description: 'Black格式化已应用', acceptanceCriteria: '所有Python文件格式一致', status: 'accepted', autoFilled: true, reviewerNotes: '' },
  { id: 7, dimension: '架构合规', dimensionIndex: 3, itemNumber: '3.1', description: '无跨层调用', acceptanceCriteria: 'Controller不直接访问Infrastructure', status: 'accepted', autoFilled: true, reviewerNotes: '' },
  { id: 8, dimension: '架构合规', dimensionIndex: 3, itemNumber: '3.2', description: '无循环依赖', acceptanceCriteria: '模块依赖关系为DAG', status: 'pending', autoFilled: false, reviewerNotes: '' },
  { id: 9, dimension: '合规检查', dimensionIndex: 6, itemNumber: '6.1', description: '营销内容通过合规扫描', acceptanceCriteria: '无广告法违规项', status: 'rejected', autoFilled: true, reviewerNotes: '发现1处绝对化用语需修改' },
  { id: 10, dimension: '合规检查', dimensionIndex: 6, itemNumber: '6.2', description: 'AI生成代码已标记', acceptanceCriteria: 'AI代码标记率100%', status: 'accepted', autoFilled: true, reviewerNotes: '' },
  { id: 11, dimension: '测试', dimensionIndex: 8, itemNumber: '8.1', description: '测试覆盖率达标', acceptanceCriteria: '核心模块≥60%', status: 'accepted', autoFilled: true, reviewerNotes: '当前覆盖率72%' },
  { id: 12, dimension: '测试', dimensionIndex: 8, itemNumber: '8.2', description: '新增API有集成测试', acceptanceCriteria: '每个新接口≥1个测试', status: 'pending', autoFilled: false, reviewerNotes: '' },
  { id: 13, dimension: '文档', dimensionIndex: 9, itemNumber: '9.1', description: 'API文档100%覆盖', acceptanceCriteria: 'OpenAPI/Swagger文档完整', status: 'pending', autoFilled: false, reviewerNotes: '' },
  { id: 14, dimension: '文档', dimensionIndex: 9, itemNumber: '9.2', description: 'Agent定义文档完整', acceptanceCriteria: '包含输入/输出/Prompt说明', status: 'accepted', autoFilled: false, reviewerNotes: '' },
  { id: 15, dimension: '安全', dimensionIndex: 7, itemNumber: '7.1', description: '无硬编码凭据', acceptanceCriteria: 'Bandit扫描无HIGH级别问题', status: 'accepted', autoFilled: true, reviewerNotes: '' },
  { id: 16, dimension: '安全', dimensionIndex: 7, itemNumber: '7.2', description: '依赖安全检查通过', acceptanceCriteria: 'pip-audit无已知漏洞', status: 'accepted', autoFilled: true, reviewerNotes: '' },
  { id: 17, dimension: '交付清单', dimensionIndex: 10, itemNumber: '10.1', description: '代码已合并到main分支', acceptanceCriteria: '所有PR已合并', status: 'accepted', autoFilled: false, reviewerNotes: '' },
  { id: 18, dimension: '交付清单', dimensionIndex: 10, itemNumber: '10.2', description: '部署文档已提供', acceptanceCriteria: '包含部署步骤和配置说明', status: 'pending', autoFilled: false, reviewerNotes: '' },
]
