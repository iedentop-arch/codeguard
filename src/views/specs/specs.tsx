import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { BookOpen, Clock, AlertTriangle, ChevronRight, FileText, Copy, Check, ExternalLink } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { getSpecCategories, getSpecDocuments, getSpecDocumentById, type SpecCategory, type SpecDocument } from '@/lib/api'

// 文档列表项（不含content）
interface SpecListItem {
  id: number
  title: string
  file_path: string | null
  category: string
  vendor_types: string
  read_time: number
  is_required: boolean
  version: string
}

interface SpecsPageProps {
  resetKey?: number  // 用于外部触发重置
}

// 代码块组件（带语法高亮和复制按钮）
function CodeBlock({ language, code }: { language: string; code: string }) {
  const [copied, setCopied] = useState(false)

  // 语言映射（显示更友好的名称）- 支持常用 20+ 种语言
  const langMap: Record<string, string> = {
    // Python 系列
    python: 'Python',
    py: 'Python',
    
    // JavaScript/TypeScript 系列
    javascript: 'JavaScript',
    js: 'JavaScript',
    typescript: 'TypeScript',
    ts: 'TypeScript',
    jsx: 'JSX',
    tsx: 'TSX',
    
    // Web 前端
    html: 'HTML',
    css: 'CSS',
    scss: 'SCSS',
    less: 'Less',
    vue: 'Vue',
    svelte: 'Svelte',
    
    // 数据格式
    json: 'JSON',
    yaml: 'YAML',
    yml: 'YAML',
    xml: 'XML',
    toml: 'TOML',
    ini: 'INI',
    
    // Shell/脚本
    bash: 'Bash',
    shell: 'Shell',
    sh: 'Shell',
    zsh: 'Zsh',
    powershell: 'PowerShell',
    ps1: 'PowerShell',
    
    // 数据库
    sql: 'SQL',
    mysql: 'MySQL',
    postgresql: 'PostgreSQL',
    
    // 编程语言
    java: 'Java',
    go: 'Go',
    golang: 'Go',
    rust: 'Rust',
    c: 'C',
    cpp: 'C++',
    csharp: 'C#',
    cs: 'C#',
    kotlin: 'Kotlin',
    swift: 'Swift',
    objectivec: 'Objective-C',
    objc: 'Objective-C',
    ruby: 'Ruby',
    php: 'PHP',
    perl: 'Perl',
    lua: 'Lua',
    scala: 'Scala',
    groovy: 'Groovy',
    dart: 'Dart',
    r: 'R',
    
    // 标记语言
    markdown: 'Markdown',
    md: 'Markdown',
    latex: 'LaTeX',
    
    // 配置/其他
    dockerfile: 'Dockerfile',
    docker: 'Dockerfile',
    nginx: 'Nginx',
    apache: 'Apache',
    gitignore: 'gitignore',
    
    // AI/ML 相关
    protobuf: 'Protobuf',
    graphql: 'GraphQL',
    gql: 'GraphQL',
    
    // 默认
    text: 'Text',
    plaintext: 'Text',
    '': 'Text',
  }

  // 语言别名映射（用于 SyntaxHighlighter）
  const syntaxLangMap: Record<string, string> = {
    vue: 'html',
    svelte: 'html',
    dockerfile: 'bash',
    docker: 'bash',
    nginx: 'bash',
    gitignore: 'text',
    markdown: 'markdown',
    md: 'markdown',
    jsx: 'javascript',
    tsx: 'typescript',
    mysql: 'sql',
    postgresql: 'sql',
  }

  // 获取显示语言名称
  const displayLang = langMap[language.toLowerCase()] || language || 'Text'
  
  // 获取 SyntaxHighlighter 使用的语言
  const syntaxLang = syntaxLangMap[language.toLowerCase()] || language.toLowerCase() || 'text'

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('复制失败', err)
    }
  }

  // 检测是否包含 ASCII 图表/表格（框线字符或宽列对齐）
  const hasAsciiArt = /[│┌┐└┘├┤┬┴┼─┏┓┗┛┣┫┳┻╋━┃┏┓┗┛┣┫╋]/.test(code)

  return (
    <div className="relative group my-3">
      {/* 语言标签和复制按钮 */}
      <div className="flex items-center justify-between px-4 py-2 bg-slate-800 rounded-t-lg border-b border-slate-600">
        <span className="text-xs font-medium text-slate-300">{displayLang}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 px-2 py-1 text-xs text-slate-400 hover:text-white transition-colors"
          title="复制代码"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3" />
              已复制
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              复制
            </>
          )}
        </button>
      </div>

      {/* 代码内容 */}
      <SyntaxHighlighter
        language={syntaxLang}
        style={vscDarkPlus}
        customStyle={{
          margin: 0,
          borderRadius: '0 0 8px 8px',
          fontSize: '13px',
          lineHeight: hasAsciiArt ? '1.2' : '1.5',
          padding: '16px',
          maxHeight: '600px',
          overflow: 'auto',
          backgroundColor: '#1e1e1e',
          fontFamily: '"Menlo", "Monaco", "Courier New", "Noto Sans Mono CJK SC", "Source Han Sans SC", monospace',
        }}
        showLineNumbers={!hasAsciiArt && code.split('\n').length > 5}
        lineNumberStyle={{
          minWidth: '2.5em',
          paddingRight: '1em',
          color: '#6b7280',
          userSelect: 'none',
        }}
        wrapLines={true}
        wrapLongLines={!hasAsciiArt}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  )
}

export function SpecsPage({ resetKey = 0 }: SpecsPageProps) {
  const [categories, setCategories] = useState<SpecCategory[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [documents, setDocuments] = useState<SpecListItem[]>([])
  const [selectedDoc, setSelectedDoc] = useState<SpecDocument | null>(null)
  const [allDocuments, setAllDocuments] = useState<SpecListItem[]>([])
  const [filePathToId, setFilePathToId] = useState<Record<string, number>>({})  // 动态映射：file_path -> id
  const [loadingDoc, setLoadingDoc] = useState(false)
  const [loading, setLoading] = useState(true)

  // 当 resetKey 变化时重置到分类列表页
  useEffect(() => {
    setSelectedDoc(null)
    setSelectedCategory(null)
  }, [resetKey])

  useEffect(() => {
    loadCategories()
    loadAllDocuments()
  }, [])

  useEffect(() => {
    if (selectedCategory) {
      loadDocuments(selectedCategory)
    }
  }, [selectedCategory])

  const loadCategories = async () => {
    try {
      const res = await getSpecCategories()
      setCategories(res.data)
    } catch (e) {
      console.error('加载分类失败', e)
    } finally {
      setLoading(false)
    }
  }

  const loadAllDocuments = async () => {
    try {
      const res = await getSpecDocuments({})
      setAllDocuments(res.data)
      // 构建 file_path -> id 动态映射
      const mapping: Record<string, number> = {}
      for (const doc of res.data) {
        if (doc.file_path) {
          // 完整路径映射：02-architecture/system-design-principles.md
          mapping[doc.file_path] = doc.id
          // 纯文件名映射：system-design-principles.md
          const fileName = doc.file_path.split('/').pop()
          if (fileName && fileName !== doc.file_path) {
            mapping[fileName] = doc.id
          }
        }
      }
      setFilePathToId(mapping)
    } catch (e) {
      console.error('加载所有文档失败', e)
    }
  }

  const loadDocuments = async (category: string) => {
    try {
      const res = await getSpecDocuments({ category })
      setDocuments(res.data)
    } catch (e) {
      console.error('加载文档失败', e)
    }
  }

  const loadDocumentDetail = async (docId: number) => {
    setLoadingDoc(true)
    try {
      const res = await getSpecDocumentById(docId)
      setSelectedDoc(res.data)
    } catch (e) {
      console.error('加载文档详情失败', e)
    } finally {
      setLoadingDoc(false)
    }
  }

  // 根据链接路径查找文档并跳转（使用动态 file_path 映射）
  const handleDocLinkClick = useCallback((linkPath: string) => {
    // 提取文件名（如 03-ai-agents/agent-design-principles.md -> agent-design-principles.md）
    const fileName = linkPath.split('/').pop() || linkPath

    // 先用完整路径匹配，再用文件名匹配
    const docId = filePathToId[linkPath] || filePathToId[fileName]
    if (docId) {
      loadDocumentDetail(docId)
      return true
    }

    console.log('未找到文档映射:', linkPath, fileName)
    return false
  }, [filePathToId])

  const getCategoryIcon = (category: string) => {
    const icons: Record<string, string> = {
      overview: '📋',
      general: '📐',
      architecture: '🏗️',
      ai_agents: '🤖',
      skills: '🔧',
      mcp: '🔌',
      sub_agents: '👥',
      compliance: '⚖️',
      templates: '📝',
      delivery: '📦',
      sdlc: '👥',
    }
    return icons[category] || '📄'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full"></div>
      </div>
    )
  }

  // 文档详情视图
  if (selectedDoc) {
    return (
      <div className="space-y-6 animate-fade-in">
        <button
          onClick={() => setSelectedDoc(null)}
          className="text-sm text-muted-foreground hover:text-primary flex items-center gap-1"
        >
          <ChevronRight className="w-4 h-4 rotate-180" />
          返回文档列表
        </button>

        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold">{selectedDoc.title}</h1>
            <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {selectedDoc.read_time} 分钟
              </span>
              <span className="flex items-center gap-1">
                <FileText className="w-4 h-4" />
                {selectedDoc.version}
              </span>
              {selectedDoc.is_required && (
                <span className="flex items-center gap-1 text-orange-500">
                  <AlertTriangle className="w-4 h-4" />
                  必读
                </span>
              )}
            </div>
          </div>
        </div>

        <Card className="overflow-hidden">
          <CardContent className="p-0">
            <div className="spec-content p-6 max-h-[70vh] overflow-y-auto">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  h1: ({ children }) => <h1 className="text-2xl font-bold mb-4 pb-2 border-b">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-xl font-semibold mt-6 mb-3 text-primary/90">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-lg font-medium mt-4 mb-2">{children}</h3>,
                  h4: ({ children }) => <h4 className="text-base font-medium mt-3 mb-2">{children}</h4>,
                  p: ({ children }) => <p className="mb-3 leading-relaxed">{children}</p>,
                  ul: ({ children }) => <ul className="list-disc list-inside mb-3 space-y-1 pl-2">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal list-inside mb-3 space-y-1 pl-2">{children}</ol>,
                  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                  // 代码块 - 使用语法高亮
                  code({ className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '')
                    const language = match ? match[1] : ''
                    const codeString = String(children).replace(/\n$/, '')

                    // 内联代码：无语言标记且内容不含换行
                    // 代码块：有语言标记（className 含 language-xxx），或多行内容（在 <pre> 内）
                    const isInlineCode = !className && !codeString.includes('\n')

                    if (isInlineCode) {
                      // 检测文档路径链接
                      const isDocPath = codeString.match(/\S+\/\S+\.md$/) || codeString.match(/^[a-z0-9_-]+\.md$/)
                      if (isDocPath) {
                        return (
                          <a
                            href="#"
                            onClick={(e) => {
                              e.preventDefault()
                              handleDocLinkClick(codeString)
                            }}
                            className="text-primary hover:underline font-medium cursor-pointer inline-flex items-center gap-1 bg-primary/10 px-1.5 py-0.5 rounded text-sm font-mono"
                          >
                            {children}
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )
                      }
                      return (
                        <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono text-primary" {...props}>
                          {children}
                        </code>
                      )
                    }

                    // 代码块 - 使用语法高亮组件（无论有无语言标记）
                    return <CodeBlock language={language || 'text'} code={codeString} />
                  },
                  pre: ({ children }) => {
                    if (children && typeof children === 'object' && 'type' in children) {
                      return <>{children}</>
                    }
                    return <pre className="bg-muted/80 p-3 rounded-lg overflow-x-auto my-3">{children}</pre>
                  },
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-primary/50 pl-4 py-2 my-3 bg-muted/30 rounded-r italic">
                      {children}
                    </blockquote>
                  ),
                  table: ({ children }) => (
                    <div className="overflow-x-auto my-4">
                      <table className="w-full border-collapse rounded-lg">{children}</table>
                    </div>
                  ),
                  th: ({ children }) => (
                    <th className="border px-3 py-2 bg-muted font-medium text-left">{children}</th>
                  ),
                  td: ({ children }) => <td className="border px-3 py-2">{children}</td>,
                  // 链接处理 - 支持文档内跳转
                  a: ({ href, children }) => {
                    if (!href) return <span>{children}</span>

                    // 检查是否是文档内链接（.md 结尾且不是完整 URL）
                    const isDocLink = href.endsWith('.md') && !href.startsWith('http://') && !href.startsWith('https://')

                    if (isDocLink) {
                      return (
                        <a
                          href="#"
                          onClick={(e) => {
                            e.preventDefault()
                            handleDocLinkClick(href)
                          }}
                          className="text-primary hover:underline font-medium cursor-pointer inline-flex items-center gap-1"
                        >
                          {children}
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )
                    }

                    // 外部链接
                    return (
                      <a
                        href={href}
                        className="text-primary hover:underline font-medium"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {children}
                      </a>
                    )
                  },
                  hr: () => <hr className="my-6 border-t border-border" />,
                  strong: ({ children }) => <strong className="font-semibold text-primary/90">{children}</strong>,
                  em: ({ children }) => <em className="italic">{children}</em>,
                }}
              >
                {selectedDoc.content}
              </ReactMarkdown>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // 文档列表视图
  if (selectedCategory) {
    const categoryInfo = categories.find(c => c.category === selectedCategory)
    return (
      <div className="space-y-6 animate-fade-in">
        <button
          onClick={() => setSelectedCategory(null)}
          className="text-sm text-muted-foreground hover:text-primary flex items-center gap-1"
        >
          <ChevronRight className="w-4 h-4 rotate-180" />
          返回分类列表
        </button>

        <div>
          <h1 className="text-2xl font-bold">{categoryInfo?.name || selectedCategory}</h1>
          <p className="text-sm text-muted-foreground mt-1">
            共 {documents.length} 篇规范文档
          </p>
        </div>

        <div className="space-y-3">
          {documents.map(doc => (
            <Card
              key={doc.id}
              className="hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => loadDocumentDetail(doc.id)}
            >
              <CardContent className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <BookOpen className="w-5 h-5 text-primary" />
                  <div>
                    <h3 className="text-sm font-medium">{doc.title}</h3>
                    <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                      <span>{doc.read_time} 分钟</span>
                      <span>{doc.version}</span>
                      {doc.is_required && (
                        <span className="text-orange-500">必读</span>
                      )}
                    </div>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-muted-foreground" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  // 分类列表视图
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">规范库</h1>
        <p className="text-sm text-muted-foreground mt-1">
          浏览和管理项目开发规范文档 · 共 {categories.reduce((sum, c) => sum + c.count, 0)} 篇
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {categories.map(cat => (
          <Card
            key={cat.category}
            className="hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => setSelectedCategory(cat.category)}
          >
            <CardContent className="p-5">
              <div className="text-2xl mb-3">{getCategoryIcon(cat.category)}</div>
              <h3 className="text-sm font-medium">{cat.name}</h3>
              <p className="text-xs text-muted-foreground mt-1">{cat.count} 篇文档</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}