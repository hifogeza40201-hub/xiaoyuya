const https = require('https');

const verifyData = JSON.stringify({
  verification_code: 'moltbook_verify_016df06f9d223484674801fd41f4b0ec',
  answer: '28.00'
});

const options = {
  hostname: 'www.moltbook.com',
  path: '/api/v1/verify',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer moltbook_sk_M4Hnlcujs8D5_jDvzkoKtOQJXhxNHOQB',
    'Content-Length': Buffer.byteLength(verifyData)
  }
};

const req = https.request(options, (res) => {
  let body = '';
  res.on('data', chunk => body += chunk);
  res.on('end', () => {
    console.log(body);
  });
});

req.write(verifyData);
req.end();
