"""
GitHub App API 客户端

实现 GitHub App 认证和 API 调用，用于：
- 获取 PR 详情
- 设置 commit status
- 发表 PR 评论
- 获取 PR diff 内容
"""
import time

import httpx
import jwt

from app.core.config import get_private_key, settings


class GitHubAppClient:
    """GitHub App API 客户端"""

    GITHUB_API_BASE = "https://api.github.com"

    def __init__(self):
        self.app_id = settings.GITHUB_APP_ID
        self._private_key_value = settings.GITHUB_APP_PRIVATE_KEY
        self.installation_id = settings.GITHUB_APP_INSTALLATION_ID
        self._installation_token: str | None = None
        self._token_expires_at: float = 0

    @property
    def private_key(self) -> str:
        """获取私钥（支持文件读取）"""
        return get_private_key()

    def _generate_jwt(self) -> str:
        """
        生成 GitHub App JWT (RS256, 10分钟有效)
        
        GitHub App 使用 JWT 来获取 installation access token
        JWT 需要使用私钥签名，iss=app_id，有效期最长 10 分钟
        """
        if not self.private_key:
            raise ValueError("GITHUB_APP_PRIVATE_KEY not configured")

        now = int(time.time())
        payload = {
            "iat": now - 60,  # issued at (allow 60s clock drift)
            "exp": now + (10 * 60 - 60),  # expires (max 10 min, minus drift)
            "iss": self.app_id,  # issuer = app ID
        }

        token = jwt.encode(payload, self.private_key, algorithm="RS256")
        return token

    async def get_installation_token(self) -> str:
        """
        获取 installation access token
        
        使用 JWT 调用 GitHub API 获取安装令牌，用于后续 API 调用
        令牌有效期 1 小时，这里缓存直到过期
        """
        # 如果已有有效令牌，直接返回
        if self._installation_token and time.time() < self._token_expires_at - 60:
            return self._installation_token

        if not self.installation_id:
            raise ValueError("GITHUB_APP_INSTALLATION_ID not configured")

        jwt_token = self._generate_jwt()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.GITHUB_API_BASE}/app/installations/{self.installation_id}/access_tokens",
                headers={
                    "Authorization": f"Bearer {jwt_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            response.raise_for_status()
            data = response.json()

        self._installation_token = data["token"]
        # 令牌有效期 1 小时
        self._token_expires_at = time.time() + 3600 - 60

        return self._installation_token

    async def _get_headers(self) -> dict:
        """获取认证请求头"""
        token = await self.get_installation_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def get_pr(self, owner: str, repo: str, pr_number: int) -> dict:
        """获取 PR 详情"""
        headers = await self._get_headers()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}",
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

    async def get_pr_files(self, owner: str, repo: str, pr_number: int) -> list:
        """获取 PR 变更文件列表"""
        headers = await self._get_headers()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/files",
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

    async def create_commit_status(
        self,
        owner: str,
        repo: str,
        sha: str,
        state: str,
        context: str,
        description: str,
        target_url: str | None = None,
    ) -> dict:
        """
        设置 commit status
        
        Args:
            state: pending, success, failure, error
            context: 状态检查名称 (如 "CodeGuard/L1-RedLine")
            description: 状态描述
            target_url: 可选的详情链接
        """
        headers = await self._get_headers()

        payload = {
            "state": state,
            "context": context,
            "description": description,
        }
        if target_url:
            payload["target_url"] = target_url

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}/statuses/{sha}",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    async def create_pr_comment(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str,
    ) -> dict:
        """在 PR 上发表评论"""
        headers = await self._get_headers()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{pr_number}/comments",
                headers=headers,
                json={"body": body},
            )
            response.raise_for_status()
            return response.json()

    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """获取 PR diff 内容"""
        headers = await self._get_headers()
        headers["Accept"] = "application/vnd.github.diff"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}",
                headers=headers,
            )
            response.raise_for_status()
            return response.text

    async def get_installations(self) -> list:
        """获取 App 所有安装列表（用于获取 installation_id）"""
        jwt_token = self._generate_jwt()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.GITHUB_API_BASE}/app/installations",
                headers={
                    "Authorization": f"Bearer {jwt_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            response.raise_for_status()
            return response.json()

    def is_configured(self) -> bool:
        """检查 GitHub App 是否已配置"""
        return bool(self.app_id and self.private_key and self.installation_id)


# 全局客户端实例
github_client = GitHubAppClient()
