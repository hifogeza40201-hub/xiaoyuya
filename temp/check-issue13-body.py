import urllib.request
import json
import os

token = os.environ.get('GITHUB_TOKEN')
headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'xiaoyu-bot'
}

# 获取Issue主体内容
url = 'https://api.github.com/repos/hifogeza40201-hub/xiaoyuya/issues/13'
req = urllib.request.Request(url, headers=headers)

with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode('utf-8'))
    print('=== Issue #13 主体内容 ===')
    print(f"标题: {data['title']}")
    print(f"作者: {data['user']['login']}")
    print(f"内容:\n{data['body']}")
    print('-' * 50)