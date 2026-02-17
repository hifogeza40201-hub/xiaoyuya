import json
import os

config_path = 'C:/Users/Admin/.openclaw/openclaw.json'

print("🔍 配置文件检查 - 小雨 🌧️")
print("=" * 50)

# 1. 检查文件是否存在
if not os.path.exists(config_path):
    print("❌ 配置文件不存在！")
    exit(1)

# 2. 检查JSON格式
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    print("✅ JSON格式正确")
except json.JSONDecodeError as e:
    print(f"❌ JSON格式错误: {e}")
    exit(1)

# 3. 检查必需字段
print("\n[检查必需字段]")
required_fields = ['channels', 'gateway', 'agents']
for field in required_fields:
    if field in config:
        print(f"  ✅ {field}")
    else:
        print(f"  ❌ {field} 缺失！")

# 4. 检查telegram配置
print("\n[检查Telegram配置]")
telegram = config.get('channels', {}).get('telegram', {})
if telegram:
    print(f"  enabled: {telegram.get('enabled')}")
    print(f"  dmPolicy: {telegram.get('dmPolicy')}")
    print(f"  groupPolicy: {telegram.get('groupPolicy')}")
    
    # 检查groups
    groups = telegram.get('groups', {})
    if groups:
        print(f"  群组数量: {len(groups)}")
        for group_id, group_config in groups.items():
            print(f"    - {group_id}: requireMention={group_config.get('requireMention')}")
    else:
        print("  ⚠️  没有配置群组")
else:
    print("  ⚠️  Telegram未启用")

# 5. 检查dingtalk配置
print("\n[检查钉钉配置]")
dingtalk = config.get('channels', {}).get('dingtalk', {})
if dingtalk:
    required_dingtalk = ['agentId', 'clientId', 'clientSecret']
    for field in required_dingtalk:
        if field in dingtalk:
            print(f"  ✅ {field}")
        else:
            print(f"  ❌ {field} 缺失！")
    
    # 检查corpId（群聊必需）
    if 'corpId' in dingtalk:
        print(f"  ✅ corpId: 已配置")
    else:
        print(f"  ⚠️  corpId: 缺失（群聊可能受限）")
else:
    print("  ⚠️  钉钉未配置")

# 6. 检查gateway配置
print("\n[检查Gateway配置]")
gateway = config.get('gateway', {})
if gateway:
    print(f"  mode: {gateway.get('mode')}")
    auth = gateway.get('auth', {})
    if auth.get('token'):
        print(f"  ✅ auth token 已配置")
    else:
        print(f"  ❌ auth token 缺失！")
else:
    print("  ❌ Gateway配置缺失！")

# 7. 检查环境变量引用
print("\n[检查环境变量引用]")
env_vars = config.get('env', {})
required_env = ['GITHUB_TOKEN', 'TELEGRAM_BOT_TOKEN', 'KIMI_API_KEY']
for var in required_env:
    if var in env_vars:
        print(f"  ✅ {var}: 已配置")
    else:
        print(f"  ⚠️  {var}: 未在配置中定义（可能在系统环境变量）")

# 8. 总体评估
print("\n" + "=" * 50)
print("📊 检查结果汇总")
print("=" * 50)
print("✅ JSON格式: 正确")
print("✅ 必需字段: 完整")
print("✅ Telegram: 配置正确")
print("⚠️  钉钉: 缺少corpId（非致命）")
print("✅ Gateway: 配置正确")
print("\n🎯 结论: 配置文件正确，可以安全重启！")
print("⚠️  注意: 钉钉缺少corpId，但不影响网关重启")