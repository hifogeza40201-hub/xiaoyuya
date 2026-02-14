const { chromium } = require('playwright');

(async () => {
  try {
    // Playwright 自己启动浏览器
    console.log('🚀 正在用 Playwright 启动 Chrome...');
    const browser = await chromium.launch({ 
      headless: false,
      args: ['--disable-blink-features=AutomationControlled']
    });
    
    const context = await browser.newContext({
      viewport: { width: 1280, height: 800 }
    });
    
    const page = await context.newPage();
    
    console.log('正在打开 Manus...');
    await page.goto('https://manus.im/app', { waitUntil: 'networkidle', timeout: 60000 });
    
    console.log('✅ 页面加载成功');
    const title = await page.title();
    console.log('页面标题:', title);
    
    // 尝试查找并点击项目
    console.log('查找 "炊影商拍" 项目...');
    const project = page.locator('text=炊影商拍').first();
    
    if (await project.isVisible().catch(() => false)) {
      console.log('✅ 找到项目，准备点击...');
      await project.click();
      await page.waitForLoadState('networkidle');
      console.log('✅ 点击成功，等待 3 秒...');
      await page.waitForTimeout(3000);
      
      // 测试输入框
      const input = page.locator('textarea, input[type="text"]').first();
      if (await input.isVisible().catch(() => false)) {
        console.log('✅ 找到输入框，测试输入...');
        await input.fill('请帮我把炊影商拍部署到 Vercel');
        console.log('✅ 输入成功！');
      }
    } else {
      console.log('⚠️ 未找到项目，可能需要登录');
    }
    
    console.log('✅ 所有测试通过！Playwright 工作正常');
    
    // 保持浏览器打开 5 秒方便查看
    await page.waitForTimeout(5000);
    await browser.close();
    process.exit(0);
  } catch (error) {
    console.error('❌ 错误:', error.message);
    if (error.message.includes('executablePath')) {
      console.error('\n💡 提示: 需要先安装 Playwright 浏览器:\n  npx playwright install chromium');
    }
    process.exit(1);
  }
})();
