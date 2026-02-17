import urllib.request
import json

# 尝试获取会话列表
try:
    req = urllib.request.Request('http://127.0.0.1:18789/api/sessions')
    with urllib.request.urlopen(req, timeout=5) as response:
        data = json.loads(response.read().decode('utf-8'))
        print('会话列表:')
        for session in data.get('sessions', []):
            print(' ', session.get('key'))
except Exception as e:
    print('无法获取会话列表:', e)
    print('这可能意味着Gateway未运行或API不可用')