import json

# 读取当前配置
with open('C:/Users/Admin/.openclaw/openclaw.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 检查telegram配置
telegram = config.get('channels', {}).get('telegram', {})

print("=== 当前电报配置 ===")
print(f"enabled: {telegram.get('enabled')}")
print(f"dmPolicy: {telegram.get('dmPolicy')}")
print(f"groupPolicy: {telegram.get('groupPolicy')}")
print(f"groups: {telegram.get('groups')}")

# 检查组配置
groups = telegram.get('groups', {})
for group_id, group_config in groups.items():
    print(f"\n群组 {group_id}:")
    print(f"  requireMention: {group_config.get('requireMention')}")
    print(f"  groupPolicy: {group_config.get('groupPolicy')}")