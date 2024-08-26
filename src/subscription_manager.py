# src/subscription_manager.py

import json
from logger import LOG

class SubscriptionManager:
    def __init__(self, subscriptions_file):
        self.subscriptions_file = subscriptions_file
        self.subscriptions = self.load_subscriptions()
    
    def load_subscriptions(self):
        try:
            with open(self.subscriptions_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            LOG.warning(f"订阅文件 {self.subscriptions_file} 不存在，创建新文件。")
            return []
        except json.JSONDecodeError:
            LOG.error(f"订阅文件 {self.subscriptions_file} 格式错误，使用空列表。")
            return []
    
    def save_subscriptions(self):
        with open(self.subscriptions_file, 'w') as f:
            json.dump(self.subscriptions, f, indent=4)
    
    def list_subscriptions(self):
        return self.subscriptions
    
    def add_subscription(self, repo):
        if repo not in self.subscriptions:
            self.subscriptions.append(repo)
            self.save_subscriptions()
            LOG.info(f"添加新订阅: {repo}")
        else:
            LOG.info(f"订阅 {repo} 已存在")
    
    def remove_subscription(self, repo):
        if repo in self.subscriptions:
            self.subscriptions.remove(repo)
            self.save_subscriptions()
            LOG.info(f"删除订阅: {repo}")
        else:
            LOG.warning(f"尝试删除不存在的订阅: {repo}")