const fs = require('fs');
const path = require('path');

// 读取密钥文件并转换为base64
const keyFile = path.join(process.env.USERPROFILE, '.openclaw', '.secure_key');
const keyData = fs.readFileSync(keyFile);
const keyBase64 = keyData.toString('base64');

// 创建邮件内容
const boundary = '----小雨密钥备份' + Date.now();
const emailContent = `
From: 小雨助手 <xiaoyu@local>
To: 9100182@qq.com
Subject: =?UTF-8?B?5bCP6YeO5Y+36K6+6K6h5oqk5Y+j5YiG5p6QIC0gMjAyNi0wMi0xMQ==?=
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="${boundary}"

--${boundary}
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: base64

${Buffer.from(`伟，你好！

这是小雨的密钥文件备份 (.secure_key)。

⚠️ 重要提醒：
- 此文件是解密配置的唯一钥匙
- 请妥善保管，不要泄露给他人
- 如果丢失，将无法恢复API密钥等敏感配置

密钥文件内容（Base64编码）：
${keyBase64}

请将此内容保存为文件：xiaoyu-secure-key-backup-2026-02-11.key

备份时间：2026-02-11 18:08
备份位置：D盘 + 公司电脑 + 此邮件

小雨 🌧️`).toString('base64')}

--${boundary}--
`;

// 保存邮件内容到文件
const emailFile = path.join(process.env.USERPROFILE, '.openclaw', 'workspace', 'secure-key-email.txt');
fs.writeFileSync(emailFile, emailContent);

console.log('✅ 邮件内容已生成！');
console.log('📧 邮件文件:', emailFile);
console.log('');
console.log('⚠️ 注意：由于邮件发送需要SMTP配置，');
console.log('   请手动复制以下Base64内容到安全位置：');
console.log('');
console.log(keyBase64.substring(0, 100) + '...');
console.log('');
console.log('💡 或者手动发送邮件，将此文件作为附件');
