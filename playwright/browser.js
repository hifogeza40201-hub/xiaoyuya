const { chromium } = require('playwright');

/**
 * 通用 Playwright 自动化脚本
 * 用于替代不稳定的 Chrome CDP 连接
 */

class PlaywrightBrowser {
  constructor(options = {}) {
    this.headless = options.headless ?? false;
    this.browser = null;
    this.page = null;
  }

  async launch() {
    console.log('🚀 启动 Playwright Chrome...');
    this.browser = await chromium.launch({
      headless: this.headless,
      args: ['--disable-blink-features=AutomationControlled']
    });
    
    const context = await this.browser.newContext({
      viewport: { width: 1400, height: 900 }
    });
    
    this.page = await context.newPage();
    console.log('✅ 浏览器已启动');
    return this;
  }

  async goto(url, options = {}) {
    if (!this.page) throw new Error('浏览器未启动');
    
    console.log(`🌐 打开: ${url}`);
    await this.page.goto(url, {
      waitUntil: options.waitUntil || 'networkidle',
      timeout: options.timeout || 60000
    });
    
    if (options.delay) {
      await this.page.waitForTimeout(options.delay);
    }
    
    return this;
  }

  async click(textOrSelector) {
    if (!this.page) throw new Error('浏览器未启动');
    
    // 尝试作为文本查找
    const byText = this.page.locator(`text=${textOrSelector}`).first();
    if (await byText.isVisible().catch(() => false)) {
      console.log(`🖱️ 点击文本: "${textOrSelector}"`);
      await byText.click();
      return this;
    }
    
    // 尝试作为选择器
    const bySelector = this.page.locator(textOrSelector).first();
    if (await bySelector.isVisible().catch(() => false)) {
      console.log(`🖱️ 点击元素: ${textOrSelector}`);
      await bySelector.click();
      return this;
    }
    
    throw new Error(`未找到可点击元素: ${textOrSelector}`);
  }

  async type(text, selector = 'input, textarea') {
    if (!this.page) throw new Error('浏览器未启动');
    
    const input = this.page.locator(selector).first();
    if (await input.isVisible().catch(() => false)) {
      console.log(`⌨️ 输入文本: "${text.substring(0, 30)}..."`);
      await input.fill(text);
      return this;
    }
    
    throw new Error(`未找到输入框: ${selector}`);
  }

  async screenshot(name = 'screenshot') {
    if (!this.page) throw new Error('浏览器未启动');
    
    const filename = `${name}-${Date.now()}.png`;
    await this.page.screenshot({ path: filename, fullPage: true });
    console.log(`📸 截图已保存: ${filename}`);
    return filename;
  }

  async close() {
    if (this.browser) {
      await this.browser.close();
      console.log('👋 浏览器已关闭');
    }
  }
}

// 示例用法
async function main() {
  const browser = new PlaywrightBrowser({ headless: false });
  
  try {
    await browser.launch();
    await browser.goto('https://manus.im/app', { delay: 3000 });
    await browser.screenshot('manus-home');
    
    // 示例：如果要发送消息
    // await browser.click('炊影商拍');
    // await browser.type('请帮我部署到 Vercel');
    
  } catch (error) {
    console.error('❌ 错误:', error.message);
  } finally {
    await browser.close();
  }
}

// 如果直接运行此脚本
if (require.main === module) {
  main();
}

module.exports = { PlaywrightBrowser };
