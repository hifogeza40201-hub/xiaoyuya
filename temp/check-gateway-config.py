import json

# 读取配置文件
with open('C:/Users/Admin/.openclaw/openclaw.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 检查gateway配置
print('=== 检查Gateway配置 ===')
gateway = config.get('gateway', {})

print('\n当前gateway配置:')
for key, value in gateway.items():
    print('  ' + key + ': ' + str(value))

# 检查是否有bind字段
if 'bind' in gateway:
    bind_value = gateway['bind']
    print('\n⚠️  发现bind字段: ' + str(bind_value))
    print('   bind字段可能格式不正确！')
else:
    print('\n✅ 没有bind字段（正常）')

# 检查auth配置
if 'auth' in gateway:
    auth = gateway['auth']
    print('\nauth配置:')
    print('  mode: ' + str(auth.get('mode')))
    if 'token' in auth:
        print('  ✅ token已配置')
    else:
        print('  ❌ token缺失')

# 建议修复
print('\n=== 建议修复方案 ===')
print('如果bind字段导致错误，可以:')
print('1. 删除bind字段')
print('2. 或将其改为正确的格式（如 127.0.0.1:18789）')
print('3. 或将其改为null')