import requests
import re
from typing import Tuple, Optional
from constants import VERSION, PROJECT_URL, GITHUB_DOMAIN, VERSION_PATTERN

class UpdateChecker:
    @staticmethod
    def check_for_updates() -> Tuple[Optional[str], Optional[str]]:
        """检查GitHub是否有新版本
        返回: (最新版本号, 发布页面URL) 或 (None, None)"""
        try:
            repo = PROJECT_URL.split(GITHUB_DOMAIN)[-1].rstrip("/")
            api_url = f"https://api.github.com/repos/{repo}/releases/latest"
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            
            release_data = response.json()
            latest_version = release_data.get("tag_name", "").lstrip('v')
            if UpdateChecker._is_newer(latest_version, VERSION):
                return latest_version, release_data.get("html_url")
            return None, None
        except Exception as e:
            print(f"更新检查失败: {str(e)}")
            return None, None

    @staticmethod
    def _is_newer(remote_version: str, local_version: str) -> bool:
        """比较版本号，返回远程版本是否更新"""
        def parse_version(ver: str) -> tuple:
            # 提取主版本号、次版本号、修订号和预览标识
            match = re.match(VERSION_PATTERN, ver)
            if not match:
                return (0, 0, 0, 'z')  # 无效版本视为最低
            major, minor, patch = map(int, match.groups()[:3])
            pre = match.group(4) or ''
            return (major, minor, patch, pre)

        rv = parse_version(remote_version)
        lv = parse_version(local_version)

        # 比较主版本号
        if rv[0] > lv[0]:
            return True
        if rv[0] < lv[0]:
            return False

        # 比较次版本号
        if rv[1] > lv[1]:
            return True
        if rv[1] < lv[1]:
            return False

        # 比较修订号
        if rv[2] > lv[2]:
            return True
        if rv[2] < lv[2]:
            return False

        # 比较预览标识：有预览标识的版本较旧
        if not lv[3] and rv[3]:
            return False  # 本地是正式版，远程是预览版
        if lv[3] and not rv[3]:
            return True   # 本地是预览版，远程是正式版
        return rv[3] > lv[3]  # 比较预览标识字母顺序
