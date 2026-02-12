const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

/**
 * 解密配置文件
 * 用法: node decrypt-config.js
 */

const ALGORITHM = 'aes-256-gcm';
const CONFIG_DIR = path.join(process.env.USERPROFILE || process.env.HOME, '.openclaw');
const CONFIG_FILE = path.join(CONFIG_DIR, 'openclaw.json');
const ENCRYPTED_FILE = path.join(CONFIG_DIR, 'openclaw.json.enc');
const KEY_FILE = path.join(CONFIG_DIR, '.secure_key');

function decryptConfig() {
  try {
    if (!fs.existsSync(ENCRYPTED_FILE)) {
      console.log('⚠️ 未找到加密文件，可能已解密或未加密');
      return false;
    }
    
    if (!fs.existsSync(KEY_FILE)) {
      console.error('❌ 错误: 密钥文件不存在！');
      console.error('   位置:', KEY_FILE);
      console.error('   无法解密，请检查备份');
      return false;
    }
    
    const key = fs.readFileSync(KEY_FILE);
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
    
    // 备份当前配置
    const backupFile = CONFIG_FILE + '.backup.' + Date.now();
    fs.writeFileSync(backupFile, JSON.stringify(publicConfig, null, 2));
    
    // 保存完整配置
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(fullConfig, null, 2));
    
    console.log('✅ 配置解密完成！');
    console.log('🔓 完整配置已恢复');
    console.log('💾 原配置备份:', backupFile);
    
    return true;
  } catch (error) {
    console.error('❌ 解密失败:', error.message);
    return false;
  }
}

decryptConfig();
