import json

with open('C:/Users/Admin/.openclaw/openclaw.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

print('=== 电报群聊配置详细检查 ===')
telegram = config.get('channels', {}).get('telegram', {})

print('\n1. 全局设置:')
print('   enabled:', telegram.get('enabled'))
print('   dmPolicy:', telegram.get('dmPolicy'))
print('   groupPolicy:', telegram.get('groupPolicy'))

print('\n2. 群组设置:')
groups = telegram.get('groups', {})
for group_id, group_config in groups.items():
    print('\n   群组ID:', group_id)
    print('   - requireMention:', group_config.get('requireMention'))
    print('   - groupPolicy:', group_config.get('groupPolicy'))

print('\n3. 其他设置:')
print('   allowFrom:', telegram.get('allowFrom'))
print('   streamMode:', telegram.get('streamMode'))

print('\n4. 配置分析:')
if groups:
    for gid, gcfg in groups.items():
        rm = gcfg.get('requireMention')
        if rm == False:
            print('   群组', gid, '的requireMention=false（配置正确）')
        else:
            print('   群组', gid, '的requireMention=', rm, '（配置错误）')
else:
    print('   未配置群组')