# src/github_client.py

import requests  # 导入requests库用于HTTP请求
from datetime import datetime  # 导入日期处理模块
import os  # 导入os模块用于文件和目录操作
from logger import LOG  # 导入日志模块

class GitHubClient:
    def __init__(self, token):
        self.token = token  # GitHub API令牌
        self.headers = {'Authorization': f'token {self.token}'}  # 设置HTTP头部认证信息

    def fetch_updates(self, repo, since=None, until=None):
        # 获取指定仓库的更新，可以指定开始和结束日期
        updates = {
            'commits': self.fetch_commits(repo, since, until),  # 获取提交记录
            'issues': self.fetch_issues(repo, since, until),  # 获取问题
            'pull_requests': self.fetch_pull_requests(repo, since, until)  # 获取拉取请求
        }
        return updates

    def fetch_commits(self, repo, since=None, until=None):
        LOG.debug(f"准备获取 {repo} 的 Commits")
        url = f'https://api.github.com/repos/{repo}/commits'  # 构建获取提交的API URL
        params = {}
        if since:
            params['since'] = since  # 如果指定了开始日期，添加到参数中
        if until:
            params['until'] = until  # 如果指定了结束日期，添加到参数中

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()  # 检查请求是否成功
            return response.json()  # 返回JSON格式的数据
        except Exception as e:
            LOG.error(f"从 {repo} 获取 Commits 失败：{str(e)}")
            LOG.error(f"响应详情：{response.text if 'response' in locals() else '无响应数据可用'}")
            return []  # Handle failure case

    def fetch_issues(self, repo, since=None, until=None):
        LOG.debug(f"准备获取 {repo} 的 Issues")
        url = f'https://api.github.com/repos/{repo}/issues'  # 构建获取问题的API URL
        params = {'state': 'all'}
        if since:
            params['since'] = since
        # GitHub API doesn't support 'until' for issues, we'll filter it later

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            issues = response.json()
            if until:
                until_date = datetime.fromisoformat(until.rstrip('Z'))
                issues = [issue for issue in issues if datetime.fromisoformat(issue['created_at'].rstrip('Z')) <= until_date]
            return issues
        except Exception as e:
            LOG.error(f"从 {repo} 获取 Issues 失败：{str(e)}")
            LOG.error(f"响应详情：{response.text if 'response' in locals() else '无响应数据可用'}")
            return []

    def fetch_pull_requests(self, repo, since=None, until=None):
        LOG.debug(f"准备获取 {repo} 的 Pull Requests")
        url = f'https://api.github.com/repos/{repo}/pulls'  # 构建获取拉取请求的API URL
        params = {'state': 'all'}
        if since:
            params['since'] = since
        # GitHub API doesn't support 'until' for PRs, we'll filter it later

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()  # 确保成功响应
            prs = response.json()
            if until:
                until_date = datetime.fromisoformat(until.rstrip('Z'))
                prs = [pr for pr in prs if datetime.fromisoformat(pr['created_at'].rstrip('Z')) <= until_date]
            return prs
        except Exception as e:
            LOG.error(f"从 {repo} 获取 Pull Requests 失败：{str(e)}")
            LOG.error(f"响应详情：{response.text if 'response' in locals() else '无响应数据可用'}")
            return []

    def export_progress_by_date_range(self, repo, since, until):
        LOG.debug(f"准备获取 {repo} 从 {since} 到 {until} 的进展")
        
        updates = self.fetch_updates(repo, since=since, until=until)  # 获取指定日期范围内的更新
        
        repo_dir = os.path.join('daily_progress', repo.replace("/", "_"))  # 构建目录路径
        os.makedirs(repo_dir, exist_ok=True)  # 确保目录存在
        
        # 更新文件名以包含日期范围
        date_str = f"{since.split('T')[0]}_to_{until.split('T')[0]}"
        file_path = os.path.join(repo_dir, f'{date_str}.md')  # 构建文件路径
        
        with open(file_path, 'w') as file:
            file.write(f"# Progress for {repo} ({since} to {until})\n\n")
            
            file.write("\n## Commits\n")
            for commit in updates['commits']:
                file.write(f"- {commit['commit']['message'][:50]}... ({commit['sha'][:7]})\n")
            
            file.write(f"\n## Issues\n")
            for issue in updates['issues']:
                file.write(f"- {issue['title']} #{issue['number']} ({issue['state']})\n")
            
            file.write(f"\n## Pull Requests\n")
            for pr in updates['pull_requests']:
                file.write(f"- {pr['title']} #{pr['number']} ({pr['state']})\n")
        
        LOG.info(f"[{repo}]项目进展文件生成： {file_path}")  # 记录日志
        return file_path