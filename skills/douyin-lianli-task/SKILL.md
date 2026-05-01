---
name: douyin-lianli-task
description: 处理招商系统建联任务。当用户发送"处理建联任务"或"获取联系方式"时，检查后端待处理任务，执行CDP流程获取商家联系方式并回填。
---

# 招商系统建联任务处理

## 触发条件

用户发送以下内容时执行：
- "处理建联任务"
- "获取联系方式"
- "建联"
- 或复制了包含 `record_id` 和 `commodity_id` 的指令

## 工作流程

```
1. 接收用户指令（包含 commodity_id 和 record_id）
2. 调用 CDP 进入达人工作台选品广场
3. 搜索商品ID，进入详情页
4. 点击「联系商家」按钮，获取手机号/微信号
5. 调用后端 API 回填联系方式
6. 告知用户完成
```

## API 端点

招商系统后端运行在 `106.14.167.159:8001`

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/lianli-tasks/pending` | 获取所有待处理任务 |
| GET | `/api/lianli-task/{record_id}` | 获取特定记录的任务 |
| PUT | `/api/lianli-task/{task_id}` | 更新任务状态和联系方式 |

### 更新任务格式

```bash
curl -X PUT "http://106.14.167.159:8001/api/lianli-task/{task_id}" \
  -H "Content-Type: application/json" \
  -d '{"contact_wechat": "微信号", "contact_phone": "手机号", "status": "completed"}'
```

## CDP 操作（参考 douyin-product-contact skill）

### 步骤1：搜索商品
```javascript
// 清空搜索框并输入商品ID
var inp = document.querySelector('#rc_select_0');
var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
setter.call(inp, '');
inp.dispatchEvent(new Event('input', {bubbles:true}));

setter.call(inp, '商品ID');
inp.dispatchEvent(new Event('input', {bubbles:true}));
inp.dispatchEvent(new Event('change', {bubbles:true}));

// 点击搜索
var btns = document.querySelectorAll('button');
for (var b of btns) {
  if (b.innerText && b.innerText.trim() === '搜索') {
    b.click();
    break;
  }
}
```

### 步骤2：进入详情页
```javascript
// 等待结果，点击商品图片
await new Promise(r => setTimeout(r, 5000));
window.scrollTo(0, 400);
await new Promise(r => setTimeout(r, 1000));

// 点击商品图片 (x:256, y:575)
Input.dispatchMouseEvent({ type: 'mouseMoved', x: 256, y: 575 });
Input.dispatchMouseEvent({ type: 'mousePressed', x: 256, y: 575, button: 'left', clickCount: 1 });
Input.dispatchMouseEvent({ type: 'mouseReleased', x: 256, y: 575, button: 'left', clickCount: 1 });

await new Promise(r => setTimeout(r, 5000));
```

### 步骤3：获取联系方式
```javascript
// 悬浮到联系商家按钮（坐标 x:1322, y:377）
Input.dispatchMouseEvent({ type: 'mouseMoved', x: 1322, y: 377 });
await new Promise(r => setTimeout(r, 1500));

// 点击眼睛图标
var eyeIcon = document.querySelector('span.index__eye____8a66');
if (eyeIcon) eyeIcon.click();
await new Promise(r => setTimeout(r, 1000));

// 读取浮层中的联系方式
var overlay = document.querySelector('.product-info__button-contact-overlay');
if (overlay) {
  var phoneEl = overlay.querySelector('.index__right____8a66');
  var phone = phoneEl ? phoneEl.textContent.trim() : '';
  console.log('手机号:', phone);
}
```

## 关键DOM元素

| 元素 | 选择器 |
|------|--------|
| 联系商家按钮 | `button.auxo-btn.product-info__button-contact` |
| 浮层 | `.product-info__button-contact-overlay` |
| 手机号区域 | `.index__right____8a66` |
| 眼睛图标 | `span.index__eye____8a66` |

## CDP 连接

- Tailscale IP: `100.70.54.13`
- 端口: `19234`

## 注意事项

1. 只需获取手机号或微信号中的任意一个即可
2. 如果商家同时有手机号和微信号，都需要获取
3. 完成后必须调用 PUT API 回填数据
4. 状态设为 `completed`
