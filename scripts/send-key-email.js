const nodemailer = require('nodemailer');
const fs = require('fs');
const path = require('path');

// QQ邮箱配置
const transporter = nodemailer.createTransport({
  host: 'smtp.qq.com',
  port: 465,
  secure: true,
  auth: {
    user: '9100182@qq.com',
    pass: 'ldiombpprgrbcbbb'  // 授权码
  }
});

// 读取密钥文件
const keyFile = path.join(process.env.USERPROFILE, '.openclaw', '.secure_key');

const mailOptions = {
  from: '"小雨助手" <9100182@qq.com>',
  to: '9100182@qq.com',
  subject: '小雨密钥文件备份 - 2026-02-11',
  text: `伟，你好！

这是小雨的密钥文件备份 (.secure_key)。

⚠️ 重要提醒：
- 此文件是解密配置的唯一钥匙
- 请妥善保管，不要泄露给他人
- 如果丢失，将无法恢复API密钥等敏感配置

备份时间：2026-02-11 18:10
备份位置：D盘 + 公司电脑 + 此邮件

小雨 🌧️`,
  attachments: [
    {
      filename: 'xiaoyu-secure-key-backup-2026-02-11.key',
      path: keyFile
    }
  ]
};

transporter.sendMail(mailOptions, (error, info) => {
  if (error) {
    console.error('❌ 发送失败:', error);
  } else {
    console.log('✅ 邮件发送成功！');
    console.log('📧 邮件ID:', info.messageId);
  }
});
