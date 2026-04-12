"""
导入规范文档数据脚本
从参考项目 20260408220853 导入所有规范文档到数据库
"""
import asyncio
import os
import re
from pathlib import Path
from datetime import datetime

from sqlalchemy import select
from app.core.database import async_session_maker
from app.models.models import SpecDocument


# 规范文档目录
SPEC_BASE_DIR = "/Users/eden-f/code-work/Qoder-w/20260408220853/dairy-coding-standards"

# 分类映射
CATEGORY_MAP = {
    "00-overview": "overview",
    "01-general": "general",
    "02-architecture": "architecture",
    "03-ai-agents": "ai_agents",
    "04-skills": "skills",
    "05-mcp": "mcp",
    "06-sub-agents": "sub_agents",
    "07-compliance": "compliance",
    "08-templates": "templates",
    "11-delivery": "delivery",
    "sdlc-prompts": "sdlc",
}

# 文档分类显示名称
CATEGORY_NAMES = {
    "overview": "总览与入驻",
    "general": "通用编码规范",
    "architecture": "架构设计规范",
    "ai_agents": "AI Agent规范",
    "skills": "Skill开发规范",
    "mcp": "MCP开发规范",
    "sub_agents": "子代理规范",
    "compliance": "合规法规",
    "templates": "模板与工具",
    "delivery": "交付验收",
    "sdlc": "SDLC角色提示词",
}

# 乙方类型映射（A=前端, B=后端, C=AI Agent, D=全栈）
VENDOR_TYPE_MAP = {
    "overview": "D",      # 所有类型都需要
    "general": "D",       # 所有类型都需要
    "architecture": "D",  # 所有类型都需要
    "ai_agents": "C",     # AI Agent类型
    "skills": "C",        # AI Agent类型
    "mcp": "C",           # AI Agent类型
    "sub_agents": "C",    # AI Agent类型
    "compliance": "D",    # 所有类型都需要（合规）
    "templates": "D",     # 所有类型
    "delivery": "D",      # 所有类型
    "sdlc": "D",          # 所有类型
}


def parse_markdown_title(content: str, filename: str) -> str:
    """从Markdown内容中提取标题"""
    # 尝试从第一个 # 标题提取
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        title = match.group(1).strip()
        # 清理版本号等后缀
        title = re.sub(r'\s*v\d+\.\d+', '', title)
        return title[:200]  # 限制长度

    # 从文件名生成标题
    name = filename.replace('.md', '').replace('-', ' ').replace('_', ' ')
    return name.title()[:200]


def estimate_read_time(content: str) -> int:
    """估算阅读时间（分钟）"""
    # 平均阅读速度：约 300 字/分钟
    char_count = len(content)
    # 粗略估计：每500字符约1分钟
    return max(5, min(60, char_count // 500))


def get_document_version(content: str) -> str:
    """提取版本号"""
    match = re.search(r'VERSION:\s*v(\d+\.\d+)', content)
    if match:
        return f"v{match.group(1)}"
    match = re.search(r'v(\d+\.\d+)', content)
    if match:
        return f"v{match.group(1)}"
    return "v1.0"


def determine_required(content: str) -> bool:
    """判断是否必读"""
    # CRITICAL 或合规相关都是必读
    if 'CRITICAL' in content.upper():
        return True
    if 'compliance' in content.lower() or '合规' in content:
        return True
    if 'onboarding' in content.lower() or '入驻' in content:
        return True
    return False


async def import_spec_documents():
    """导入所有规范文档"""
    spec_dir = Path(SPEC_BASE_DIR)

    documents = []

    # 扫描所有 .md 文件
    for md_file in spec_dir.rglob("*.md"):
        # 跳过 README
        if md_file.name in ["README.md"]:
            continue

        try:
            content = md_file.read_text(encoding='utf-8')

            # 获取分类
            relative_path = md_file.relative_to(spec_dir)
            parts = relative_path.parts
            category_key = parts[0] if len(parts) > 1 else "overview"
            category = CATEGORY_MAP.get(category_key, "overview")

            # 构建 file_path（如 02-architecture/system-design-principles.md）
            file_path = str(relative_path)

            # 解析文档信息
            title = parse_markdown_title(content, md_file.name)
            version = get_document_version(content)
            read_time = estimate_read_time(content)
            is_required = determine_required(content)
            vendor_types = VENDOR_TYPE_MAP.get(category, "D")

            doc = {
                "title": title,
                "file_path": file_path,
                "category": category,
                "vendor_types": vendor_types,
                "content": content,
                "read_time": read_time,
                "is_required": is_required,
                "version": version,
            }
            documents.append(doc)
            print(f"解析: {title} ({CATEGORY_NAMES.get(category, category)}) [{file_path}] - {read_time}分钟")

        except Exception as e:
            print(f"跳过文件 {md_file}: {e}")

    # 导入到数据库
    async with async_session_maker() as session:
        imported_count = 0
        updated_count = 0

        for doc_data in documents:
            # 检查是否已存在（按标题）
            result = await session.execute(
                select(SpecDocument).where(SpecDocument.title == doc_data["title"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"更新: {doc_data['title']} [{doc_data['file_path']}]")
                existing.content = doc_data["content"]
                existing.version = doc_data["version"]
                existing.read_time = doc_data["read_time"]
                existing.is_required = doc_data["is_required"]
                existing.file_path = doc_data["file_path"]
                updated_count += 1
            else:
                # 创建新文档
                spec_doc = SpecDocument(
                    title=doc_data["title"],
                    file_path=doc_data["file_path"],
                    category=doc_data["category"],
                    vendor_types=doc_data["vendor_types"],
                    content=doc_data["content"],
                    read_time=doc_data["read_time"],
                    is_required=doc_data["is_required"],
                    version=doc_data["version"],
                    is_deleted=False,
                )
                session.add(spec_doc)
                imported_count += 1
                print(f"导入: {doc_data['title']} [{doc_data['file_path']}]")

        await session.commit()
        print(f"\n完成！新增 {imported_count} 篇，更新 {updated_count} 篇")


async def show_statistics():
    """显示导入统计"""
    print("\n=== 规范文档统计 ===")
    categories = {}

    spec_dir = Path(SPEC_BASE_DIR)
    for md_file in spec_dir.rglob("*.md"):
        if md_file.name in ["README.md"]:
            continue

        relative_path = md_file.relative_to(spec_dir)
        parts = relative_path.parts
        category_key = parts[0] if parts else "general"
        category = CATEGORY_MAP.get(category_key, "general")

        if category not in categories:
            categories[category] = {"name": CATEGORY_NAMES.get(category, category), "count": 0}
        categories[category]["count"] += 1

    total = 0
    for cat_key, cat_info in sorted(categories.items()):
        print(f"  {cat_info['name']}: {cat_info['count']} 篇")
        total += cat_info['count']

    print(f"\n总计: {total} 篇规范文档")


if __name__ == "__main__":
    print("开始导入规范文档...")
    asyncio.run(show_statistics())
    asyncio.run(import_spec_documents())