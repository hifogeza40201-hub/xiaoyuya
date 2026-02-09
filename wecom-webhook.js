# 企业微信 Webhook 接收器
# 用于 OpenClaw 接收企业微信机器人消息

const express = require('express');
const crypto = require('crypto');
const app = express();

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

const TOKEN = 'pAFfWdfiOn8U5yLhNbxJQ4ssEyepB';
const AES_KEY = '1cRdLawLwmMvpIONeyRjokxU53o7OaMwPp4KFJdczwn';

// 验证企业微信服务器
app.get('/wecom', (req, res) => {
    const { msg_signature, timestamp, nonce, echostr } = req.query;
    
    // 验证签名
    const signature = getSignature(TOKEN, timestamp, nonce, echostr);
    if (signature !== msg_signature) {
        return res.status(403).send('Forbidden');
    }
    
    // 返回 echostr
    res.send(echostr);
});

// 接收消息
app.post('/wecom', (req, res) => {
    console.log('收到企业微信消息:', req.body);
    
    // 解析消息并转发到 OpenClaw
    // TODO: 实现与 OpenClaw 的集成
    
    res.send('success');
});

function getSignature(token, timestamp, nonce, encrypt) {
    const str = [token, timestamp, nonce, encrypt].sort().join('');
    return crypto.createHash('sha1').update(str).digest('hex');
}

const PORT = 18789;
app.listen(PORT, () => {
    console.log(`企业微信 Webhook 服务运行在端口 ${PORT}`);
});
