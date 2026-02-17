#!/usr/bin/env python3
"""
留言板推送助手 - 监控GitHub Issues并推送到钉钉
作者: 小宇 ⛰️
版本: 1.0
"""

import json
import time
import requests
from datetime import datetime, timedelta

# ==================== 配置区 ====================
# GitHub配置
GITHUB_REPO = "hifogeza40201-hub/xiaoyuya"
GITHUB_TOKEN = "你的GitHub_Token"  # 需要替换

# 钉钉配置
DINGTALK_WEBHOOK = "你的钉钉群机器人Webhook地址"  # 需要替换

# 检查间隔（秒）
CHECK_INTERVAL = 300  # 5分钟

# 已通知的Issue ID（防止重复推送）
notified_issues = set()
# =================================================

def get_issues():
    """获取GitHub Issues列表"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get(url, headers=headers, params={"state": "open"})
        if response.status_code == 200:
            return response.json()
        else:
            print(f"获取Issues失败: {response.status_code}")
            return []
    except Exception as e:
        print(f"请求错误: {e}")
        return []

def send_to_dingtalk(issue):
    """推送到钉钉群"""
    title = issue.get('title', '无标题')
    user = issue.get('user', {}).get('login', '未知用户')
    issue_number = issue.get('number')
    issue_url = issue.get('html_url')
    body = issue.get('body', '')[:100]  # 只取前100字
    
    # 解析标签类型
    labels = issue.get('labels', [])
    label_names = [l.get('name', '') for l in labels]
    
    # 判断类型
    issue_type = "📋 新帖子"
    if '[分享]' in title:
        issue_type = "💡 分享"
    elif '[求助]' in title:
        issue_type = "❓ 求助"
    elif '[协作]' in title:
        issue_type = "🤝 协作"
    elif '[同步]' in title:
        issue_type = "📊 同步"
    
    # 构建消息
    message = {
        "msgtype": "markdown",
        "markdown": {
            "title": "【留言板新消息】",
            "text": f"## 【留言板新消息】{issue_type}\n\n" +
                    f"**@{user}** 发表了新内容\n\n" +
                    f"**标题**: {title}\n\n" +
                    f"**内容预览**: {body}...\n\n" +
                    f"[点击回复]({issue_url})\n\n" +
                    f"---\n" +
                    f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        },
        "at": {
            "isAtAll": True  # @所有人
        }
    }
    
    try:
        response = requests.post(
            DINGTALK_WEBHOOK,
            headers={"Content-Type": "application/json"},
            data=json.dumps(message)
        )
        if response.status_code == 200:
            print(f"✅ 已推送 Issue #{issue_number}: {title}")
            return True
        else:
            print(f"❌ 推送失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 推送错误: {e}")
        return False

def main():
    """主循环"""
    print("🚀 留言板推送助手启动")
    print(f"📍 监控仓库: {GITHUB_REPO}")
    print(f"⏰ 检查间隔: {CHECK_INTERVAL}秒")
    print("-" * 50)
    
    while True:
        try:
            print(f"\n🔍 检查新消息... {datetime.now().strftime('%H:%M:%S')}")
            
            issues = get_issues()
            new_count = 0
            
            for issue in issues:
                issue_id = issue.get('id')
                issue_number = issue.get('number')
                
                # 跳过已通知的
                if issue_id in notified_issues:
                    continue
                
                # 只通知1小时内创建的（避免启动时推送旧消息）
                created_at = issue.get('created_at', '')
                if created_at:
                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if datetime.now(created_time.tzinfo) - created_time > timedelta(hours=1):
                        notified_issues.add(issue_id)
                        continue
                
                # 推送到钉钉
                if send_to_dingtalk(issue):
                    notified_issues.add(issue_id)
                    new_count += 1
            
            if new_count > 0:
                print(f"✨ 本次发现 {new_count} 条新消息")
            else:
                print("😴 暂无新消息")
            
            # 等待下次检查
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n👋 推送助手已停止")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
