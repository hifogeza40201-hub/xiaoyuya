const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ 
    headless: false,
    args: ['--disable-blink-features=AutomationControlled']
  });
  
  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 }
  });
  
  const page = await context.newPage();
  
  try {
    console.log('🚀 打开 Manus...');
    await page.goto('https://manus.im/app', { waitUntil: 'networkidle', timeout: 60000 });
    
    // 等待页面加载
    await page.waitForTimeout(2000);
    
    // 查找输入框（通常是 textarea 或带有特定 placeholder 的输入框）
    console.log('🔍 查找输入框...');
    
    // 尝试多种选择器找输入框
    const inputSelectors = [
      'textarea[placeholder*="提问"]',
      'textarea[placeholder*="发送消息"]',
      'textarea[placeholder*="输入"]',
      'input[type="text"]',
      'div[contenteditable="true"]',
      'textarea'
    ];
    
    let inputBox = null;
    for (const selector of inputSelectors) {
      const box = page.locator(selector).first();
      if (await box.isVisible().catch(() => false)) {
        inputBox = box;
        console.log(`✅ 找到输入框: ${selector}`);
        break;
      }
    }
    
    if (!inputBox) {
      console.log('⚠️ 未找到标准输入框，尝试截图查看页面状态...');
      await page.screenshot({ path: 'manus-screenshot.png' });
      console.log('📸 已保存截图: manus-screenshot.png');
      
      // 列出页面上所有可能的输入元素
      const elements = await page.locator('textarea, input, div[contenteditable]').all();
      console.log(`找到 ${elements.length} 个可能输入元素`);
      
      for (let i = 0; i < Math.min(elements.length, 5); i++) {
        const tag = await elements[i].evaluate(el => el.tagName);
        const placeholder = await elements[i].getAttribute('placeholder').catch(() => '');
        console.log(`  ${i}: ${tag} - ${placeholder}`);
      }
    } else {
      // 输入部署消息
      const message = `请帮我把"炊影商拍"应用部署到 Vercel，解决预览不稳定的问题。

需求：
1. 将当前 React Native + Expo 项目构建为 Web 版本
2. 部署到 Vercel 并生成永久访问链接
3. 确保以下功能正常运行：
   - 菜品图片上传
   - 场景选择（高级餐厅、温暖木质等）
   - 风格调整
   - 图片生成

如果无法直接部署到 Vercel，请提供：
1. 项目导出步骤
2. 本地运行指南（npm start / expo start）
3. 或者部署到 Netlify 的替代方案

请优先选择最稳定的方案，谢谢！`;

      console.log('✍️ 正在输入消息...');
      await inputBox.fill(message);
      console.log('✅ 消息已输入');
      
      // 查找发送按钮
      const sendButton = page.locator('button[type="submit"], button:has-text("发送"), button:has(> svg)').first();
      if (await sendButton.isVisible().catch(() => false)) {
        console.log('📤 点击发送按钮...');
        await sendButton.click();
        console.log('✅ 消息已发送！');
      } else {
        // 尝试按回车发送
        console.log('⌨️ 按回车发送...');
        await inputBox.press('Enter');
        console.log('✅ 已尝试发送');
      }
      
      // 等待响应
      console.log('⏳ 等待 5 秒查看响应...');
      await page.waitForTimeout(5000);
    }
    
    // 保存最终截图
    await page.screenshot({ path: 'manus-final.png' });
    console.log('📸 已保存最终截图: manus-final.png');
    
    console.log('\n✅ Playwright 自动化测试完成！');
    
  } catch (error) {
    console.error('❌ 错误:', error.message);
    await page.screenshot({ path: 'manus-error.png' });
    console.log('📸 已保存错误截图: manus-error.png');
  } finally {
    await browser.close();
  }
})();
