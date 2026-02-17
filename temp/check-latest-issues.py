import urllib.request
import json
import os

token = os.environ.get('GITHUB_TOKEN')
url = 'https://api.github.com/repos/hifogeza40201-hub/xiaoyuya/issues?state=open&sort=created&direction=desc'

headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'xiaoyu-bot'
}

req = urllib.request.Request(url, headers=headers)

with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode('utf-8'))
    print('=== 最新GitHub Issues ===')
    for issue in data[:10]:
        print(f"\nIssue #{issue['number']}: {issue['title']}")
        print(f"  作者: {issue['user']['login']}")
        print(f"  时间: {issue['created_at'][:10]}")
        if '运营' in issue['title'] or '优化' in issue['title']:
            print(f"  ⚠️  找到运营相关Issue!")
        print(f"  链接: {issue['html_url']}")