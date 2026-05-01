---
name: douyin-product-nav
description: 抖音达人工作台 - 通过商品ID搜索并打开商品详情页。使用场景：(1) 用户发送商品ID要求打开详情页 (2) 需要在选品广场搜索特定商品 (3) 验证搜索结果是否为唯一商品。工作流程：CDP连接→搜索商品ID→验证结果→点击商品图片位置→打开新标签页详情页。注意：不执行获取商家联系方式的任务。
---

# 抖音商品详情页导航

## 工作流程

1. **连接CDP** - 连接到Chrome远程调试端口
2. **搜索商品ID** - 在选品广场搜索框输入商品ID
3. **验证搜索结果** - 确认只有1个结果
4. **点击打开详情页** - 点击商品图片位置打开新标签页
5. **完成任务** - 告知用户检验

## ⚠️ 导航方法

**只用搜索框方法，不使用直接URL导航**

## CDP连接信息

**可用地点（2个）：**

| 地点 | 地址 | 说明 |
|------|------|------|
| 本地Windows | `100.70.54.13:19234` | 需保持开机 |


- Browser ID: 通过 `http://100.70.54.13:19234/json` 获取当前可用页面
- 选品库URL: `https://buyin.jinritemai.com/dashboard/merch-picking-library`

**登录态维护**：
- Chrome用户目录: `/tmp/my-chrome-profile`
- 若登录态失效：在桌面双击「Chrome (CDP)」快捷方式 → 登录达人工作台 → 登录态自动同步

## 关键选择器

- 搜索框: `#rc_select_0`
- 搜索按钮: `button:has-text("搜索")`
- 商品卡片: `[class*=cardContent]`
- 商品图片: 卡片内的 `<img>` 元素（需计算中心位置）

## 操作步骤

### 1. 获取可用页面并连接

```javascript
// 获取当前页面列表
const response = await fetch('http://100.70.54.13:19234/json');
const pages = await response.json();

// 找到选品广场页面或创建新页面
const selectionPage = pages.find(p => p.url.includes('merch-picking-library') && !p.url.includes('merch-promoting'));
// 或创建新页面: POST http://100.70.54.13:19234/json/new
```

### 2. 搜索商品ID

```javascript
// 清空搜索框
var inp = document.querySelector('#rc_select_0');
var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
setter.call(inp, '');
inp.dispatchEvent(new Event('input', {bubbles:true}));

// 输入商品ID
setter.call(inp, '商品ID');
inp.dispatchEvent(new Event('input', {bubbles:true}));
inp.dispatchEvent(new Event('change', {bubbles:true}));

// 点击搜索按钮
var btns = document.querySelectorAll('button');
for (var b of btns) {
  if (b.innerText && b.innerText.trim() === '搜索') {
    b.click();
    break;
  }
}
```

### 3. 滚动到商品位置

**⚠️ 重要：这个页面使用内部DIV容器滚动，不是window.scrollTo()**

```javascript
// 查找并滚动内部滚动容器
var divs = document.querySelectorAll('div');
for(var div of divs){
    var style = window.getComputedStyle(div);
    if((style.overflowY === 'auto' || style.overflowY === 'scroll' || style.overflowY === 'overlay') && div.scrollHeight > div.clientHeight){
        div.scrollTop = 500;  // 滚动内部DIV容器
        console.log('已滚动 div, scrollTop='+div.scrollTop);
        break;
    }
}
await new Promise(r => setTimeout(r, 1000));

// 验证卡片可见
var cards = document.querySelectorAll('[class*="cardContent"]');
for(var card of cards){
    if(card.textContent.includes('商品名称或ID')){
        var rect = card.getBoundingClientRect();
        console.log('卡片Y:', rect.top, '可见:', rect.top < window.innerHeight && rect.bottom > 0);
    }
}
```

### 4. 点击商品图片

```javascript
// 获取商品卡片中的图片位置
var cards = document.querySelectorAll('[class*="cardContent"]');
for(var card of cards){
    if(card.textContent.includes('商品名称或ID')){
        var imgs = card.querySelectorAll('img');
        for(var img of imgs){
            if(img.offsetWidth > 100){
                var r = img.getBoundingClientRect();
                var cx = r.left + r.width/2;  // 图片中心X
                var cy = r.top + r.height/2;  // 图片中心Y
                
                // 点击图片中心
                Input.dispatchMouseEvent({ type: 'mouseMoved', x: cx, y: cy });
                Input.dispatchMouseEvent({ type: 'mousePressed', x: cx, y: cy, button: 'left', clickCount: 1 });
                Input.dispatchMouseEvent({ type: 'mouseReleased', x: cx, y: cy, button: 'left', clickCount: 1 });
                console.log('已点击图片中心:', cx, cy);
                break;
            }
        }
        break;
    }
}

// 等待新标签页打开
await new Promise(r => setTimeout(r, 5000));
```

## 注意事项

- **滚动方式**: 必须滚动内部DIV容器，不能使用window.scrollTo()
- **图片位置**: 需获取卡片内图片的实际中心坐标，不能使用固定坐标
- 点击后会在新标签页打开商品详情页
- 不要执行获取商家联系方式的任务
- CDP连接超时设置为40秒

## 页面数量控制 ⚠️ 重要

**规则**：进入详情页后，**关闭所有其他标签页，只保留详情页**

**原因**：每次搜索商品ID时可以重新打开选品广场，无需保持选品广场页面

**执行后**：
- 只保留1个页面（商品详情页）
- 如果需要搜索新商品，重新打开选品广场

## 优化记录

### 已验证有效的优化
1. ✅ 商品ID验证 - URL中 `product_id` 参数与搜索ID匹配
2. ✅ 页面清理 - 打开详情页后应关闭旧的选品广场页面
3. ✅ 页面数量控制 - 始终保持2个页面

## 快速测试

商品ID: `3814257273484738596`
预期结果: 商品详情页新标签页打开
