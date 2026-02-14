const https = require('https');

const options = {
  hostname: 'www.moltbook.com',
  path: '/api/v1/feed?sort=new&limit=10',
  method: 'GET',
  headers: {
    'Authorization': 'Bearer moltbook_sk_M4Hnlcujs8D5_jDvzkoKtOQJXhxNHOQB'
  }
};

const req = https.request(options, (res) => {
  let body = '';
  res.on('data', chunk => body += chunk);
  res.on('end', () => {
    console.log(body);
  });
});

req.end();
