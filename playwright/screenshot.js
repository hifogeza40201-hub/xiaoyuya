const { chromium } = require('playwright');

/**
 * 使用 Playwright 打开网页并截图
 * 用法: node screenshot.js <url> [output.png]
 */

async function screenshot(url, outputPath = 'screenshot.png') {
  console.log(`📸 正在截图: ${url}`);
  
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 });
    await page.waitForTimeout(2000); // 等待动态内容加载
    
    await page.screenshot({ 
      path: outputPath,
      fullPage: true 
    });
    
    console.log(`✅ 截图已保存: ${outputPath}`);
  } catch (error) {
    console.error('❌ 错误:', error.message);
  } finally {
    await browser.close();
  }
}

// 主函数
const url = process.argv[2];
const output = process.argv[3] || 'screenshot.png';

if (!url) {
  console.log('用法: node screenshot.js <url> [output.png]');
  console.log('示例: node screenshot.js https://manus.im/app manus.png');
  process.exit(1);
}

screenshot(url, output);
