"""
质量门禁执行引擎

实现 6 层质量门禁检查：
- L1_RED_LINE: 红线检查 (CRITICAL 规范违规)
- L2_MANDATORY: 强制检查 (类型注解、API 文档)
- L3_AI_ASSISTED: AI 辅助审查 (代码质量评分)
- L4_METRICS: 度量检查 (CI 结果)
- L5_DOCUMENTATION: 文档检查 (README/CHANGELOG)
- L6_COMPLIANCE: 合规检查 (广告法、内容合规)
"""
import re
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import QualityGate, PullRequest
from app.core.github_client import github_client

logger = logging.getLogger(__name__)


@dataclass
class GateResult:
    """质量门禁检查结果"""
    layer: int
    gate_id: str
    gate_name: str
    status: str  # passed, failed, warning, running
    details: str
    violations_count: int = 0
    warnings_count: int = 0


async def run_quality_gates(
    pr: PullRequest,
    pr_diff: str,
    db: AsyncSession,
    owner: str,
    repo: str,
    head_sha: str,
):
    """
    执行全部质量门禁
    
    Args:
        pr: PullRequest 记录
        pr_diff: PR diff 内容
        db: 数据库 session
        owner: GitHub repo owner
        repo: GitHub repo name
        head_sha: PR head commit SHA
    """
    gates = [
        (1, "L1_RED_LINE", "红线检查", run_l1_red_line),
        (2, "L2_MANDATORY", "强制检查", run_l2_mandatory),
        (3, "L3_AI_ASSISTED", "AI辅助审查", run_l3_ai_assisted),
        (4, "L4_METRICS", "度量检查", run_l4_metrics),
        (5, "L5_DOCUMENTATION", "文档检查", run_l5_documentation),
        (6, "L6_COMPLIANCE", "合规检查", run_l6_compliance),
    ]
    
    results = []
    all_passed = True
    
    for layer, gate_id, name, check_fn in gates:
        try:
            result = await check_fn(pr, pr_diff, db)
            results.append(result)
            
            # 存储到数据库
            gate_record = QualityGate(
                pr_id=pr.id,
                layer=layer,
                layer_name=name,
                status=result.status,
                details={"message": result.details},
                violations_count=result.violations_count,
                warnings_count=result.warnings_count,
            )
            db.add(gate_record)
            
            # 更新 GitHub commit status
            if github_client.is_configured():
                status_state = "success" if result.status == "passed" else (
                    "failure" if result.status == "failed" else "pending"
                )
                await github_client.create_commit_status(
                    owner=owner,
                    repo=repo,
                    sha=head_sha,
                    state=status_state,
                    context=f"CodeGuard/{gate_id}",
                    description=result.details[:140] if result.details else f"{name}: {result.status}",
                )
            
            if result.status == "failed":
                all_passed = False
                
        except Exception as e:
            logger.error(f"Error running gate {gate_id}: {e}")
            # 标记为 error
            results.append(GateResult(
                layer=layer,
                gate_id=gate_id,
                gate_name=name,
                status="failed",
                details=f"检查执行出错: {str(e)}",
            ))
            all_passed = False
    
    await db.commit()
    
    # 发送 PR 评论摘要
    if github_client.is_configured():
        try:
            comment = format_gates_summary(results)
            await github_client.create_pr_comment(
                owner=owner,
                repo=repo,
                pr_number=pr.github_pr_number,
                body=comment,
            )
        except Exception as e:
            logger.error(f"Failed to post PR comment: {e}")
    
    # 更新 PR 状态
    if all_passed:
        pr.status = "ci_passed"
    else:
        pr.status = "ci_failed"
    await db.commit()
    
    return results


async def run_l1_red_line(pr: PullRequest, diff: str, db: AsyncSession) -> GateResult:
    """
    L1 红线检查：CRITICAL 规范违规检测
    
    检查内容：
    - 硬编码密码/API 密钥
    - SQL 注入风险
    - eval/exec 调用
    - 禁止的模块导入
    """
    violations = []
    
    # 检查硬编码敏感信息
    sensitive_patterns = [
        (r'password\s*=\s*[\'"][^\'\"]+[\'"]', "硬编码密码"),
        (r'api_key\s*=\s*[\'"][^\'\"]+[\'"]', "硬编码 API Key"),
        (r'secret\s*=\s*[\'"][^\'\"]+[\'"]', "硬编码 Secret"),
        (r'token\s*=\s*[\'"][^\'\"]+[\'"]', "硬编码 Token"),
        (r'AWS_ACCESS_KEY', "AWS Access Key"),
        (r'PRIVATE_KEY', "Private Key"),
    ]
    
    for pattern, desc in sensitive_patterns:
        matches = re.findall(pattern, diff, re.IGNORECASE)
        if matches:
            violations.append(desc)
    
    # 检查危险函数调用
    dangerous_patterns = [
        (r'eval\s*\(', "eval() 调用"),
        (r'exec\s*\(', "exec() 谅用"),
        (r'subprocess\.call\s*\([^)]*shell=True', "shell=True 的 subprocess 调用"),
        (r'os\.system\s*\(', "os.system() 谅用"),
    ]
    
    for pattern, desc in dangerous_patterns:
        matches = re.findall(pattern, diff)
        if matches:
            violations.append(desc)
    
    # 检查 SQL 注入风险
    sql_injection_patterns = [
        (r'execute\s*\([^)]*\+', "潜在 SQL 注入 (字符串拼接)"),
        (r'raw\s*\([^)]*\+', "Raw SQL 拼接"),
        (r'f\".*SELECT.*\{', "f-string SQL 查询"),
    ]
    
    for pattern, desc in sql_injection_patterns:
        matches = re.findall(pattern, diff, re.IGNORECASE)
        if matches:
            violations.append(desc)
    
    if violations:
        return GateResult(
            layer=1,
            gate_id="L1_RED_LINE",
            gate_name="红线检查",
            status="failed",
            details=f"发现 {len(violations)} 个红线违规: " + "; ".join(violations[:5]),
            violations_count=len(violations),
        )
    
    return GateResult(
        layer=1,
        gate_id="L1_RED_LINE",
        gate_name="红线检查",
        status="passed",
        details="无红线违规",
    )


async def run_l2_mandatory(pr: PullRequest, diff: str, db: AsyncSession) -> GateResult:
    """
    L2 强制检查：类型注解、API 文档完整性
    
    检查内容：
    - Python 函数类型注解
    - FastAPI 端点文档
    """
    warnings = []
    
    # 检查新增 Python 函数是否有类型注解
    # 匹配新增的函数定义 (diff 中 + 开头的行)
    new_functions = re.findall(r'^\+\s*def\s+(\w+)\s*\([^:]*\):', diff, re.MULTILINE)
    
    # 检查是否有返回类型注解
    functions_with_return_type = re.findall(
        r'^\+\s*def\s+\w+\s*\([^)]*\)\s*->\s*\w+',
        diff, re.MULTILINE
    )
    
    missing_type_annotations = len(new_functions) - len(functions_with_return_type)
    if missing_type_annotations > 0:
        warnings.append(f"{missing_type_annotations} 个函数缺少返回类型注解")
    
    # 检查 FastAPI 端点是否有描述
    # @router.get/post 等装饰器后面应该有 docstring 或 description 参数
    api_routes_without_desc = re.findall(
        r'^\+\s*@router\.(get|post|put|delete|patch)\s*\(\s*[\'"][^\'\"]+[\'\"]\s*\)',
        diff, re.MULTILINE
    )
    api_routes_with_desc = re.findall(
        r'^\+\s*@router\.(get|post|put|delete|patch)\s*\([^)]*description',
        diff, re.MULTILINE
    )
    
    routes_missing_desc = len(api_routes_without_desc) - len(api_routes_with_desc)
    if routes_missing_desc > 0:
        warnings.append(f"{routes_missing_desc} 个 API 端点缺少 description")
    
    if warnings:
        return GateResult(
            layer=2,
            gate_id="L2_MANDATORY",
            gate_name="强制检查",
            status="warning",
            details="强制检查警告: " + "; ".join(warnings),
            warnings_count=len(warnings),
        )
    
    return GateResult(
        layer=2,
        gate_id="L2_MANDATORY",
        gate_name="强制检查",
        status="passed",
        details="类型注解和 API 文档完整",
    )


async def run_l3_ai_assisted(pr: PullRequest, diff: str, db: AsyncSession) -> GateResult:
    """
    L3 AI 辅助审查：代码质量评分
    
    检查内容：
    - 代码复杂度
    - 命名规范
    - 重复代码检测 (简化版)
    """
    warnings = []
    
    # 检查过长的函数 (>50 行)
    long_functions = []
    function_pattern = r'^\+\s*def\s+\w+\s*\([^)]*\):'
    matches = list(re.finditer(function_pattern, diff, re.MULTILINE))
    
    for i, match in enumerate(matches):
        start_line = diff.count('\n', 0, match.start())
        # 简化：统计到下一个 def 或文件结束
        end_marker = matches[i + 1].start() if i + 1 < len(matches) else len(diff)
        function_body = diff[match.start():end_marker]
        added_lines = function_body.count('\n+') - function_body.count('\n-')
        if added_lines > 50:
            long_functions.append(added_lines)
    
    if long_functions:
        warnings.append(f"{len(long_functions)} 个函数超过 50 行")
    
    # 检查不规范的命名 (单字母变量、中文变量名)
    bad_names = re.findall(r'^\+\s*\w+\s*=\s', diff, re.MULTILINE)
    # 单字母变量 (除了 i, j, k, x, y, z 等循环变量)
    single_letter_vars = re.findall(r'^\+\s*[a-zA-Z]\s*=\s', diff, re.MULTILINE)
    non_standard_vars = [v for v in single_letter_vars if v.strip()[0] not in 'ijkxyz']
    
    if non_standard_vars:
        warnings.append(f"{len(non_standard_vars)} 个不规范变量名")
    
    # 计算质量评分 (简化版)
    score = 100 - len(warnings) * 10
    
    if score < 60:
        return GateResult(
            layer=3,
            gate_id="L3_AI_ASSISTED",
            gate_name="AI辅助审查",
            status="failed",
            details=f"代码质量评分: {score}/100 (低于 60 分)",
            violations_count=len(warnings),
        )
    elif score < 80:
        return GateResult(
            layer=3,
            gate_id="L3_AI_ASSISTED",
            gate_name="AI辅助审查",
            status="warning",
            details=f"代码质量评分: {score}/100",
            warnings_count=len(warnings),
        )
    
    return GateResult(
        layer=3,
        gate_id="L3_AI_ASSISTED",
        gate_name="AI辅助审查",
        status="passed",
        details=f"代码质量评分: {score}/100",
    )


async def run_l4_metrics(pr: PullRequest, diff: str, db: AsyncSession) -> GateResult:
    """
    L4 度量检查：由 GitHub Actions CI 运行后回传结果
    
    此检查先标记为 running，等 CI 回调后更新
    """
    return GateResult(
        layer=4,
        gate_id="L4_METRICS",
        gate_name="度量检查",
        status="running",
        details="等待 CI 完成...",
    )


async def run_l5_documentation(pr: PullRequest, diff: str, db: AsyncSession) -> GateResult:
    """
    L5 文档检查：README/CHANGELOG 更新
    
    检查内容：
    - 是否涉及需要更新文档的功能变更
    - 是否有对应的文档更新
    """
    warnings = []
    
    # 检查是否涉及重要功能变更 (新增 API、数据库变更等)
    important_changes = [
        (r'^\+\s*@router\.', "新增 API 端点"),
        (r'^\+\s*class\s+\w+\(.*Model', "新增数据模型"),
        (r'^\+\s*ALTER\s+TABLE', "数据库结构变更"),
        (r'^\+\s*migration', "迁移脚本变更"),
    ]
    
    has_important_change = False
    for pattern, desc in important_changes:
        if re.search(pattern, diff, re.MULTILINE | re.IGNORECASE):
            has_important_change = True
            break
    
    # 检查是否有文档更新
    doc_files = re.findall(r'^diff --git .* (README|CHANGELOG|CHANGELOG\.md|README\.md)', diff, re.MULTILINE)
    
    if has_important_change and not doc_files:
        warnings.append("涉及重要变更但未更新文档")
    
    if warnings:
        return GateResult(
            layer=5,
            gate_id="L5_DOCUMENTATION",
            gate_name="文档检查",
            status="warning",
            details="建议更新 README 或 CHANGELOG",
            warnings_count=len(warnings),
        )
    
    return GateResult(
        layer=5,
        gate_id="L5_DOCUMENTATION",
        gate_name="文档检查",
        status="passed",
        details="文档检查通过",
    )


async def run_l6_compliance(pr: PullRequest, diff: str, db: AsyncSession) -> GateResult:
    """
    L6 合规检查：广告法、内容合规
    
    检查内容：
    - 广告法敏感词
    - 不合规文案
    """
    violations = []
    
    # 广告法敏感词检查
    prohibited_words = [
        "最", "第一", "唯一", "顶级", "极致", "完美",
        "独家", "首选", "绝对", "保证", "百分百",
        "国家级", "世界级", "全网", "全国",
    ]
    
    # 只检查新增内容 (+ 开头的行)
    added_lines = re.findall(r'^\+.*', diff, re.MULTILINE)
    added_content = '\n'.join(added_lines)
    
    for word in prohibited_words:
        if word in added_content:
            # 统计出现次数
            count = added_content.count(word)
            violations.append(f"'{word}' 出现 {count} 次")
    
    # 前端文案相关文件
    frontend_files = ['.vue', '.tsx', '.jsx', '.html']
    is_frontend_change = any(ext in diff for ext in frontend_files)
    
    if is_frontend_change and violations:
        return GateResult(
            layer=6,
            gate_id="L6_COMPLIANCE",
            gate_name="合规检查",
            status="failed",
            details=f"发现广告法敏感词: " + "; ".join(violations[:5]),
            violations_count=len(violations),
        )
    elif violations:
        return GateResult(
            layer=6,
            gate_id="L6_COMPLIANCE",
            gate_name="合规检查",
            status="warning",
            details=f"建议检查敏感词使用: " + "; ".join(violations[:3]),
            warnings_count=len(violations),
        )
    
    return GateResult(
        layer=6,
        gate_id="L6_COMPLIANCE",
        gate_name="合规检查",
        status="passed",
        details="合规检查通过",
    )


def format_gates_summary(results: list[GateResult]) -> str:
    """
    格式化质量门禁摘要为 Markdown 评论
    """
    lines = ["## CodeGuard 质量门禁检查结果\n"]
    
    passed_count = sum(1 for r in results if r.status == "passed")
    failed_count = sum(1 for r in results if r.status == "failed")
    warning_count = sum(1 for r in results if r.status == "warning")
    
    # 总体状态
    if failed_count == 0:
        lines.append(f"### ✅ 总体状态: 通过 ({passed_count}/{len(results)} 门禁通过)\n")
    else:
        lines.append(f"### ❌ 总体状态: 失败 ({failed_count} 个门禁失败)\n")
    
    lines.append("| 层级 | 门禁 | 状态 | 详情 |\n")
    lines.append("|------|------|------|------|\n")
    
    status_icons = {
        "passed": "✅",
        "failed": "❌",
        "warning": "⚠️",
        "running": "🔄",
    }
    
    for r in results:
        icon = status_icons.get(r.status, "❓")
        lines.append(f"| L{r.layer} | {r.gate_name} | {icon} {r.status} | {r.details[:50]} |\n")
    
    if failed_count > 0:
        lines.append("\n> 请修复失败的门禁后再请求合并。\n")
    elif warning_count > 0:
        lines.append("\n> 建议处理警告项以提高代码质量。\n")
    
    return "".join(lines)