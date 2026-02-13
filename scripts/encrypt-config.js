const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

/**
 * 小雨配置加密系统
 * 保护API密钥等敏感信息
 */

const ALGORITHM = 'aes-256-gcm';
const CONFIG_DIR = path.join(process.env.USERPROFILE || process.env.HOME, '.openclaw');
const CONFIG_FILE = path.join(CONFIG_DIR, 'openclaw.json');
const ENCRYPTED_FILE = path.join(CONFIG_DIR, 'openclaw.json.enc');
const KEY_FILE = path.join(CONFIG_DIR, '.secure_key');

/**
 * 生成或读取加密密钥
 */
function getOrCreateKey() {
  if (fs.existsSync(KEY_FILE)) {
    return fs.readFileSync(KEY_FILE);
  }
  // 生成32字节随机密钥
  const key = crypto.randomBytes(32);
  fs.writeFileSync(KEY_FILE, key);
  // 设置文件权限（仅当前用户可读）
  try {
    fs.chmodSync(KEY_FILE, 0o600);
  } catch (e) {
    console.log('⚠️ 无法设置文件权限，请手动保护:', KEY_FILE);
  }
  return key;
}

/**
 * 加密配置文件
 */
function encryptConfig() {
  try {
    // 读取原始配置
    const configData = fs.readFileSync(CONFIG_FILE, 'utf8');
    const config = JSON.parse(configData);
    
    // 提取敏感字段
    const sensitiveFields = {
      channels: config.channels,
      auth: config.auth,
      plugins: config.plugins
    };
    
    // 移除敏感字段的明文版本（保留其他配置）
    const publicConfig = { ...config };
    delete publicConfig.channels;
    delete publicConfig.auth;
    delete publicConfig.plugins;
    
    // 加密敏感数据
    const key = getOrCreateKey();
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv(ALGORITHM, key, iv);
    
    let encrypted = cipher.update(JSON.stringify(sensitiveFields), 'utf8', 'hex');
    encrypted += cipher.final('hex');
    
    const authTag = cipher.getAuthTag();
    
    // 保存加密数据
    const encryptedData = {
      iv: iv.toString('hex'),
      authTag: authTag.toString('hex'),
      data: encrypted,
      algorithm: ALGORITHM,
      encryptedAt: new Date().toISOString()
    };
    
    fs.writeFileSync(ENCRYPTED_FILE, JSON.stringify(encryptedData, null, 2));
    
    // 保存公开配置
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(publicConfig, null, 2));
    
    console.log('✅ 配置加密完成！');
    console.log('📁 加密文件:', ENCRYPTED_FILE);
    console.log('📁 密钥文件:', KEY_FILE);
    console.log('🔒 敏感字段已加密: channels, auth, plugins');
    console.log('');
    console.log('⚠️ 重要提醒：');
    console.log('   1. 请备份 .secure_key 文件，丢失将无法解密');
    console.log('   2. 不要上传 .secure_key 到GitHub');
    console.log('   3. 需要时运行: node decrypt-config.js');
    
    return true;
  } catch (error) {
    console.error('❌ 加密失败:', error.message);
    return false;
  }
}

/**
 * 解密配置文件
 */
function decryptConfig() {
  try {
    if (!fs.existsSync(ENCRYPTED_FILE)) {
      console.log('⚠️ 未找到加密文件');
      return false;
    }
    
    const key = getOrCreateKey();
    const encryptedData = JSON.parse(fs.readFileSync(ENCRYPTED_FILE, 'utf8'));
    
    const iv = Buffer.from(encryptedData.iv, 'hex');
    const authTag = Buffer.from(encryptedData.authTag, 'hex');
    
    const decipher = crypto.createDecipheriv(encryptedData.algorithm || ALGORITHM, key, iv);
    decipher.setAuthTag(authTag);
    
    let decrypted = decipher.update(encryptedData.data, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    
    const sensitiveFields = JSON.parse(decrypted);
    
    // 读取公开配置
    const publicConfig = JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
    
    // 合并配置
    const fullConfig = {
      ...publicConfig,
      ...sensitiveFields
    };
    
    // 保存完整配置
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(fullConfig, null, 2));
    
    console.log('✅ 配置解密完成！');
    console.log('🔓 完整配置已恢复');
    
    return true;
  } catch (error) {
    console.error('❌ 解密失败:', error.message);
    return false;
  }
}

// 主函数
const command = process.argv[2];

if (command === 'decrypt') {
  decryptConfig();
} else {
  encryptConfig();
}
