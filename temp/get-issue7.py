import urllib.request
import json
import os

token = os.environ.get('GITHUB_TOKEN')
headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'xiaoyu-bot'
}

url = 'https://api.github.com/repos/hifogeza40201-hub/xiaoyuya/issues/7/comments'
req = urllib.request.Request(url, headers=headers)

with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode('utf-8'))
    print("=== Issue #7 评论 ===")
    for i, comment in enumerate(data, 1):
        print(f"\n评论 #{i}")
        print(f"作者: {comment['user']['login']}")
        print(f"内容: {comment['body']}")
        print("-" * 50)