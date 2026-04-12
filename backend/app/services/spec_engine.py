"""
规范引擎

解析spec-index.md YAML结构，根据供应商类型裁剪规范列表。
"""
import re
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class SpecModule:
    """规范模块"""
    file_path: str
    status: str
    version: str
    summary: List[str]
    top_priority: List[str]
    category: str


@dataclass
class SpecProfile:
    """规范配置"""
    name: str
    description: str
    enable: List[str]
    optional: List[str]


@dataclass
class CriticalRule:
    """CRITICAL红线规则"""
    module: str
    rule_id: str
    severity: str
    description: str


class SpecEngine:
    """规范引擎"""

    # 供应商类型对应的规范裁剪规则
    VENDOR_TYPE_SPEC_MAP = {
        "A": {  # 前端供应商
            "categories": ["general", "compliance"],
            "modules": [
                "01-general/vue-style-guide.md",
                "01-general/api-design-guide.md",
                "01-general/git-workflow.md",
                "01-general/code-review-guide.md",
                "07-compliance/content-compliance-checklist.md",
                "07-compliance/advertising-law.md",
            ]
        },
        "B": {  # 后端供应商
            "categories": ["general", "architecture", "compliance"],
            "modules": [
                "01-general/python-style-guide.md",
                "01-general/api-design-guide.md",
                "01-general/git-workflow.md",
                "01-general/code-review-guide.md",
                "02-architecture/system-design-principles.md",
                "02-architecture/layering-guide.md",
                "02-architecture/database-design-guide.md",
                "07-compliance/content-compliance-checklist.md",
                "07-compliance/advertising-law.md",
                "07-compliance/infant-formula-rules.md",
                "07-compliance/compliance-tiered-policy.md",
            ]
        },
        "C": {  # AI Agent供应商
            "categories": ["general", "architecture", "ai_agents", "compliance"],
            "modules": [
                "01-general/python-style-guide.md",
                "01-general/api-design-guide.md",
                "01-general/git-workflow.md",
                "01-general/code-review-guide.md",
                "02-architecture/layering-guide.md",
                "03-ai-agents/agent-design-principles.md",
                "03-ai-agents/langgraph-rules.md",
                "03-ai-agents/agent-security-guide.md",
                "03-ai-agents/prompt-engineering-guide.md",
                "07-compliance/advertising-law.md",
                "07-compliance/infant-formula-rules.md",
                "07-compliance/content-compliance-checklist.md",
                "07-compliance/compliance-tiered-policy.md",
            ]
        },
        "D": {  # 全栈供应商
            "categories": ["overview", "general", "architecture", "ai_agents", "skills", "mcp", "sub_agents", "compliance"],
            "modules": []  # 全部规范
        }
    }

    # 统一红线 (所有供应商必须遵守)
    CRITICAL_RED_LINES = [
        {"id": "RED_LINE_1", "desc": "生成完整可运行代码"},
        {"id": "RED_LINE_2", "desc": "验证所有 API 是否存在"},
        {"id": "RED_LINE_3", "desc": "严格类型注解"},
        {"id": "RED_LINE_4", "desc": "禁止硬编码密钥"},
        {"id": "RED_LINE_5", "desc": "禁用绝对化用语"},
        {"id": "RED_LINE_6", "desc": "禁止虚假宣传"},
        {"id": "RED_LINE_7", "desc": "禁止母乳替代宣称"},
        {"id": "RED_LINE_8", "desc": "禁止医疗效果宣称"},
        {"id": "RED_LINE_9", "desc": "营销内容过合规检查"},
        {"id": "RED_LINE_10", "desc": "AI代码必须标记"},
        {"id": "RED_LINE_11", "desc": "未经CR不允许合并"},
        {"id": "RED_LINE_12", "desc": "CRITICAL合规不通过不允许上线"},
    ]

    # 目录到类别的映射
    DIR_TO_CATEGORY = {
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
    }

    @classmethod
    def parse_spec_index(cls, spec_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        解析spec-index.md获取规范结构

        Args:
            spec_dir: 规范目录路径，默认使用环境变量或默认路径

        Returns:
            规范结构字典 {modules, profiles, dependencies, global}
        """
        # 确定规范目录
        if spec_dir:
            spec_path = Path(spec_dir)
        else:
            # 尝试从环境变量或默认位置查找
            default_paths = [
                Path(os.environ.get("SPEC_DIR", "")),
                Path("/Users/eden-f/code-work/Qoder-w/20260408220853/dairy-coding-standards"),
            ]
            for p in default_paths:
                if p and p.exists():
                    spec_path = p
                    break
            else:
                logger.warning("Spec directory not found, using empty structure")
                return {"modules": {}, "profiles": {}, "dependencies": {}, "global": {}}

        index_file = spec_path / "spec-index.md"
        if not index_file.exists():
            logger.warning(f"spec-index.md not found at {spec_path}")
            return {"modules": {}, "profiles": {}, "dependencies": {}, "global": {}}

        # 解析YAML内容 (简单解析，不依赖yaml库)
        content = index_file.read_text(encoding="utf-8")
        return cls._parse_yaml_content(content)

    @classmethod
    def _parse_yaml_content(cls, content: str) -> Dict[str, Any]:
        """
        解析spec-index.md的YAML内容

        简化解析器，处理关键结构
        """
        result = {
            "modules": {},
            "profiles": {},
            "dependencies": {},
            "global": {"enabled_modules": []}
        }

        # 解析GLOBAL.ENABLE_MODULES
        global_match = re.search(r"GLOBAL:\s*\n\s*DEFAULT_PROFILE:\s*(\S+)\s*\n\s*ENABLE_MODULES:\s*\n((?:\s+[\w\-./]+:\s*(?:ENABLED|DISABLED)\s*\n)+)", content)
        if global_match:
            enabled_block = global_match.group(2)
            enabled_modules = re.findall(r"([\w\-./]+):\s*ENABLED", enabled_block)
            result["global"]["enabled_modules"] = enabled_modules

        # 解析MODULE区块
        module_pattern = r"MODULE:\s*([\w\-./]+\.md)\s*\n\s*STATUS:\s*(ENABLED|DISABLED)\s*\n\s*VERSION:\s*(\S+)\s*\n\s*SUMMARY:\s*\n((?:\s+-\s+.+\s*\n)+)\s*TOP_PRIORITY:\s*\n((?:\s+-\s+.+\s*\n)+)"
        for match in re.finditer(module_pattern, content):
            file_path = match.group(1)
            status = match.group(2)
            version = match.group(3)
            summary_lines = re.findall(r"-\s*(.+)", match.group(4))
            priority_lines = re.findall(r"-\s*(.+)", match.group(5))

            # 从文件路径提取类别
            dir_name = file_path.split("/")[0]
            category = cls.DIR_TO_CATEGORY.get(dir_name, dir_name)

            result["modules"][file_path] = SpecModule(
                file_path=file_path,
                status=status,
                version=version,
                summary=summary_lines,
                top_priority=priority_lines,
                category=category
            )

        # 解析PROFILE区块
        profile_pattern = r"PROFILE:\s*(\S+)\s*\n\s*DESCRIPTION:\s*(.+)\s*\n\s*ENABLE:\s*\n((?:\s+-\s+.+\s*\n)+)\s*OPTIONAL:\s*\n((?:\s+-\s+.+\s*\n)+)"
        for match in re.finditer(profile_pattern, content):
            name = match.group(1)
            description = match.group(2).strip()
            enable_list = re.findall(r"-\s*([\w\-./]+\.md)", match.group(3))
            optional_list = re.findall(r"-\s*([\w\-./]+\.md)", match.group(4))

            result["profiles"][name] = SpecProfile(
                name=name,
                description=description,
                enable=enable_list,
                optional=optional_list
            )

        # 解析DEPENDENCIES
        dep_pattern = r"([\w\-./]+\.md)::RULE_\d+\s*->\s*([\w\-./]+\.md)(?:::RULE_\d+)?\s*\n\s*note:\s*(.+)"
        for match in re.finditer(dep_pattern, content):
            source = match.group(1)
            target = match.group(2)
            note = match.group(3).strip()
            if source not in result["dependencies"]:
                result["dependencies"][source] = []
            result["dependencies"][source].append({"target": target, "note": note})

        return result

    @classmethod
    def get_vendor_specs(cls, vendor_type: str, spec_index: Optional[Dict] = None) -> List[SpecModule]:
        """
        根据供应商类型返回需学习的规范列表

        Args:
            vendor_type: 供应商类型 A/B/C/D
            spec_index: 规范索引数据，默认自动解析

        Returns:
            规范模块列表
        """
        if spec_index is None:
            spec_index = cls.parse_spec_index()

        vendor_config = cls.VENDOR_TYPE_SPEC_MAP.get(vendor_type, cls.VENDOR_TYPE_SPEC_MAP["D"])
        modules = []

        # D类型获取全部规范
        if vendor_type == "D":
            for module in spec_index["modules"].values():
                if module.status == "ENABLED":
                    modules.append(module)
        else:
            # 其他类型按配置过滤
            allowed_modules = vendor_config.get("modules", [])
            allowed_categories = vendor_config.get("categories", [])

            for file_path, module in spec_index["modules"].items():
                # 检查模块是否在允许列表
                if file_path in allowed_modules:
                    modules.append(module)
                # 检查类别是否在允许类别
                elif module.category in allowed_categories and module.status == "ENABLED":
                    modules.append(module)

        # 所有类型都需要overview类别的规范 (vendor-onboarding等)
        for file_path, module in spec_index["modules"].items():
            if module.category == "overview" and module.status == "ENABLED":
                if module not in modules:
                    modules.append(module)

        return modules

    @classmethod
    def get_critical_rules(cls, spec_index: Optional[Dict] = None) -> List[CriticalRule]:
        """
        提取所有CRITICAL规则

        Args:
            spec_index: 规范索引数据

        Returns:
            CRITICAL规则列表
        """
        # 使用预定义的12条红线
        rules = []
        for red_line in cls.CRITICAL_RED_LINES:
            rules.append(CriticalRule(
                module="overview",
                rule_id=red_line["id"],
                severity="CRITICAL",
                description=red_line["desc"]
            ))

        if spec_index:
            # 从模块TOP_PRIORITY提取CRITICAL规则
            for file_path, module in spec_index["modules"].items():
                for item in module.top_priority:
                    if "CRITICAL" in item:
                        # 解析规则ID和描述
                        match = re.search(r"RULE\s*(\d+):\s*(.+)\s*\((CRITICAL)\)", item)
                        if match:
                            rules.append(CriticalRule(
                                module=file_path,
                                rule_id=f"RULE_{match.group(1)}",
                                severity="CRITICAL",
                                description=match.group(2).strip()
                            ))

        return rules

    @classmethod
    def get_profile_specs(cls, profile_name: str, spec_index: Optional[Dict] = None) -> List[SpecModule]:
        """
        根据PROFILE名称获取规范列表

        Args:
            profile_name: PROFILE名称 (ai-agent, skill-mcp, web-fullstack, library)
            spec_index: 规范索引数据

        Returns:
            规范模块列表
        """
        if spec_index is None:
            spec_index = cls.parse_spec_index()

        profile = spec_index["profiles"].get(profile_name)
        if not profile:
            logger.warning(f"Profile {profile_name} not found")
            return []

        modules = []
        # 获取ENABLE规范
        for file_path in profile.enable:
            module = spec_index["modules"].get(file_path)
            if module:
                modules.append(module)

        # 获取OPTIONAL规范 (标记为可选)
        for file_path in profile.optional:
            module = spec_index["modules"].get(file_path)
            if module:
                # 创建副本，标记为可选
                modules.append(SpecModule(
                    file_path=module.file_path,
                    status=module.status,
                    version=module.version,
                    summary=module.summary,
                    top_priority=module.top_priority,
                    category=module.category
                ))

        return modules

    @classmethod
    def get_module_dependencies(cls, module_path: str, spec_index: Optional[Dict] = None) -> List[Dict]:
        """
        获取模块的依赖关系

        Args:
            module_path: 模块路径
            spec_index: 规范索引数据

        Returns:
            依赖列表 [{"target": str, "note": str}]
        """
        if spec_index is None:
            spec_index = cls.parse_spec_index()

        return spec_index["dependencies"].get(module_path, [])

    @classmethod
    def vendor_type_to_profile(cls, vendor_type: str) -> str:
        """
        将供应商类型映射到PROFILE名称

        Args:
            vendor_type: A/B/C/D

        Returns:
            PROFILE名称
        """
        mapping = {
            "A": "web-fullstack",  # 前端 -> 全栈 (包含vue规范)
            "B": "ai-agent",       # 后端 -> AI Agent (包含Python和架构)
            "C": "ai-agent",       # AI Agent供应商 -> ai-agent profile
            "D": "ai-agent",       # 全栈 -> 使用最完整的profile
        }
        return mapping.get(vendor_type, "ai-agent")

    @classmethod
    def get_spec_count_by_vendor_type(cls, vendor_type: str) -> Dict[str, int]:
        """
        获取供应商类型对应的规范统计

        Args:
            vendor_type: A/B/C/D

        Returns:
            统计字典 {total, required, optional, critical}
        """
        specs = cls.get_vendor_specs(vendor_type)
        critical_rules = cls.get_critical_rules()

        return {
            "total": len(specs),
            "required": len([s for s in specs if s.status == "ENABLED"]),
            "optional": 0,  # 简化处理
            "critical": len(critical_rules),
            "categories": list(set(s.category for s in specs))
        }