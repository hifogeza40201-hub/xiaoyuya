import json
import shutil

config_path = 'C:/Users/Admin/.openclaw/openclaw.json'
backup_path = 'C:/Users/Admin/.openclaw/openclaw.json.backup'

# 备份
shutil.copy(config_path, backup_path)
print('✅ 已备份原配置')

# 读取配置
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# 添加 corpId（群聊必需）
config['channels']['dingtalk']['corpId'] = 'ding794140cd378094fa35c2f4657eb6378f'

# 保存
with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print('✅ 已添加 corpId 到钉钉配置')
print('⚠️ 需要重启 Gateway 生效')