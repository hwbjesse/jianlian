/**
 * 抖音商品详情页导航脚本
 * 通过商品ID搜索并打开商品详情页（新标签页）
 * 
 * 使用方式: node navigate-to-product.js <商品ID> [BrowserID]
 * 示例: node navigate-to-product.js 3814257273484738596
 */

const WebSocket = require('ws');
const http = require('http');
const fs = require('fs');

const args = process.argv.slice(2);
if (args.length === 0) {
  console.error('用法: node navigate-to-product.js <商品ID> [BrowserID]');
  console.error('示例: node navigate-to-product.js 3814257273484738596');
  process.exit(1);
}

const PRODUCT_ID = args[0];
const TAILSCALE_IP = '100.70.54.13';
const TAILSCALE_PORT = '19234';

let ws = null;
let msgId = 0;
let pending = {};
let sessionId = null;

function log(msg) { console.log(`[${new Date().toLocaleTimeString()}] ${msg}`); }

function send(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++msgId;
    pending[id] = resolve;
    const payload = { id, method, params };
    if (sessionId) payload.sessionId = sessionId;
    ws.send(JSON.stringify(payload));
    setTimeout(() => {
      if (pending[id]) { delete pending[id]; reject(new Error(`CDP ${method} timeout`)); }
    }, 40000);
  });
}

// 获取当前可用页面
function getAvailablePage() {
  return new Promise((resolve, reject) => {
    http.get(`http://${TAILSCALE_IP}:${TAILSCALE_PORT}/json`, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const pages = JSON.parse(data);
          // 优先找选品广场页面
          let page = pages.find(p => p.type === 'page' && p.url.includes('merch-picking-library') && !p.url.includes('merch-promoting'));
          if (!page) page = pages.find(p => p.type === 'page' && !p.url.includes('douyin.com/platform'));
          if (!page) page = pages.find(p => p.type === 'page');
          resolve(page);
        } catch (e) { reject(e); }
      });
    }).on('error', reject);
  });
}

async function main() {
  try {
    // 获取可用页面
    log(`获取可用页面...`);
    const availablePage = await getAvailablePage();
    if (!availablePage) throw new Error('没有找到可用页面');
    log(`找到页面: ${availablePage.title} (${availablePage.id.substring(0, 16)}...)`);

    // 连接到CDP
    const WS_URL = availablePage.webSocketDebuggerUrl;
    ws = new WebSocket(WS_URL);
    
    ws.on('message', data => {
      const msg = JSON.parse(data.toString());
      if (msg.method === 'Target.attachedToTarget') sessionId = msg.params.sessionId;
      if (msg.id && pending[msg.id]) { pending[msg.id](msg.result); delete pending[msg.id]; }
    });
    
    ws.on('error', e => log(`WS错误: ${e.message}`));
    
    await new Promise((res, rej) => { ws.on('open', () => res()); setTimeout(() => rej(new Error('连接超时')), 10000); });
    log('CDP连接成功');

    // 如果不是选品广场页面，创建新的
    if (!availablePage.url.includes('merch-picking-library')) {
      log('创建新选品广场页面...');
      const newTarget = await send('Target.createTarget', { 
        url: 'https://buyin.jinritemai.com/dashboard/merch-picking-library' 
      });
      await new Promise(r => setTimeout(r, 3000));
      
      // 重新获取页面列表
      const newPage = await getAvailablePage();
      if (newPage) {
        availablePage.id = newPage.id;
        availablePage.webSocketDebuggerUrl = newPage.webSocketDebuggerUrl;
      }
    }

    // 等待页面加载
    await new Promise(r => setTimeout(r, 2000));

    // ===== 搜索商品ID =====
    log(`[步骤1] 搜索商品ID: ${PRODUCT_ID}`);
    
    // 清空搜索框
    await send('Runtime.evaluate', { 
      expression: `(() => { 
        var inp = document.querySelector('#rc_select_0'); 
        if (!inp) return 'not found';
        var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(inp, '');
        inp.dispatchEvent(new Event('input', {bubbles:true}));
        return 'cleared';
      })()` 
    });
    await new Promise(r => setTimeout(r, 200));
    
    // 输入商品ID
    await send('Runtime.evaluate', { 
      expression: `(() => { 
        var inp = document.querySelector('#rc_select_0');
        if (!inp) return 'not found';
        var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(inp, '${PRODUCT_ID}');
        inp.dispatchEvent(new Event('input', {bubbles:true}));
        inp.dispatchEvent(new Event('change', {bubbles:true}));
        return 'input done';
      })()` 
    });
    await new Promise(r => setTimeout(r, 1500));
    
    // 点击搜索按钮
    await send('Runtime.evaluate', { 
      expression: `(() => { 
        var btns = document.querySelectorAll('button');
        for (var b of btns) { 
          if (b.innerText && b.innerText.trim() === '搜索') { 
            b.click(); 
            return 'clicked'; 
          } 
        }
        return 'not found';
      })()` 
    });
    
    await new Promise(r => setTimeout(r, 5000));
    log('[步骤1] 搜索完成');

    // ===== 验证搜索结果 =====
    const pageText = await send('Runtime.evaluate', { 
      expression: 'document.body.innerText.substring(0, 2000)' 
    });
    const hasProduct = pageText?.result?.value?.includes(PRODUCT_ID.substring(0, 6));
    log(`[步骤2] 验证搜索结果: ${hasProduct ? '包含商品' : '未找到'}`);

    // ===== 点击商品图片位置 =====
    log('[步骤3] 点击商品图片位置...');
    
    // 点击前关闭已存在的商品详情页（避免重复）
    const targetsBefore = await send('Target.getTargets');
    const existingDetailPages = targetsBefore.targetInfos.filter(t => t.url.includes('merch-promoting'));
    if (existingDetailPages.length > 0) {
      log(`[步骤3] 关闭 ${existingDetailPages.length} 个已存在的详情页...`);
      for (const p of existingDetailPages) {
        await send('Target.closeTarget', { targetId: p.targetId });
      }
      await new Promise(r => setTimeout(r, 1000));
    }
    
    await send('Runtime.evaluate', { expression: 'window.scrollTo(0, 400)' });
    await new Promise(r => setTimeout(r, 1000));
    
    // CDP鼠标点击
    await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: 256, y: 575 });
    await new Promise(r => setTimeout(r, 200));
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: 256, y: 575, button: 'left', clickCount: 1 });
    await new Promise(r => setTimeout(r, 100));
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: 256, y: 575, button: 'left', clickCount: 1 });
    
    await new Promise(r => setTimeout(r, 5000));
    log('[步骤3] 点击完成');

    // ===== 页面清理：关闭详情页以外的所有页面 =====
    const targets = await send('Target.getTargets');
    const pages = targets.targetInfos.filter(t => t.type === 'page');
    log(`[步骤4] 当前页面数: ${pages.length}`);
    
    // 找到详情页（可能有多个）
    const detailPages = pages.filter(p => p.url.includes('merch-promoting'));
    
    if (detailPages.length > 0) {
      // 保留最后一个详情页（最新的）
      const latestDetailPage = detailPages[detailPages.length - 1];
      
      // 关闭所有其他页面
      for (const p of pages) {
        if (p.targetId !== latestDetailPage.targetId) {
          await send('Target.closeTarget', { targetId: p.targetId });
          log(`[步骤4] 已关闭页面: ${p.title}`);
        }
      }
      await new Promise(r => setTimeout(r, 1000));
      
      // 验证
      const urlMatch = latestDetailPage.url.match(/product_id=(\d+)/);
      const foundProductId = urlMatch ? urlMatch[1] : null;
      
      if (foundProductId && foundProductId === PRODUCT_ID) {
        log(`✅ 任务完成！商品ID ${PRODUCT_ID} 详情页已打开`);
      } else if (foundProductId) {
        log(`⚠️ 商品ID不匹配 - 搜索: ${PRODUCT_ID}, 详情页: ${foundProductId}`);
      } else {
        log(`✅ 详情页已打开`);
      }
      log(`URL: ${latestDetailPage.url.substring(0, 100)}...`);
    } else {
      log('[步骤4] 未找到详情页');
      pages.forEach((p, i) => log(`  ${i}: ${p.title} | ${p.url.substring(0, 80)}`));
    }

    ws.close();
    process.exit(0);
    
  } catch (e) {
    log(`错误: ${e.message}`);
    if (ws) ws.close();
    process.exit(1);
  }
}

main();
