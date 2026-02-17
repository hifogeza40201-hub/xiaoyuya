import urllib.request
import json
import os

token = os.environ.get('GITHUB_TOKEN')
url = 'https://api.github.com/repos/hifogeza40201-hub/xiaoyuya/issues?state=all&per_page=50'

headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'xiaoyu-bot'
}

req = urllib.request.Request(url, headers=headers)

with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode('utf-8'))
    print('=== 搜索运营相关Issues ===')
    found = False
    for issue in data:
        title = issue['title']
        body = issue.get('body', '')
        if any(keyword in title or keyword in body for keyword in ['运营', '持续', '程序', '优化方案']):
            print(f"\n✅ Issue #{issue['number']}: {title}")
            print(f"   链接: {issue['html_url']}")
            found = True
    
    if not found:
        print('\n没有找到标题包含"运营"的Issue')
        print('\n最新的Issues是:')
        for issue in data[:5]:
            print(f"  #{issue['number']}: {issue['title']}")