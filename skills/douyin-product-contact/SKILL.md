---
name: douyin-product-contact
description: 抖音达人工作台 - 通过商品ID获取商家联系方式。完整链路：商品ID搜索 → 进入详情页 → 悬浮联系商家 → 获取手机号/微信号。触发场景：(1) 用户发送商品ID并要求获取商家联系方式 (2) 用户说"获取联系方式"、"联系商家"等关键词。
---

# 抖音商品商家联系方式获取

## 完整工作流程

```
商品ID → 选品广场搜索 → 点击商品卡片打开详情页 → 悬浮联系商家 → 获取手机号/微信号
```

## ⚠️ 执行约束（必须遵守）

1. **停止检查**：每次操作前轮询 `GET http://106.14.167.159:8001/api/global-stop`，返回 `{"stop":true}` 时立即停止当前商品，换下一个
2. **超时限制**：单个商品超过3分钟未完成，标记为超时失败，自动换下一个商品
3. **只悬浮不点击**：联系商家按钮只能悬浮，不能点击按钮本身
4. **不主动关闭详情页**：任务完成后保留详情页，不关闭
5. **关闭旧详情页时机**：处理下一个商品时，先搜索打开新详情页，再关闭上一个旧详情页
6. **无效状态**：若详情页没有"联系商家"按钮或浮层无有效联系方式，则微信=无，手机号=无，备注原因，状态改为"无效"

## CDP 连接信息

- **Tailscale IP**: `100.70.54.13`
- **端口**: `19234`
- **Browser ID**: 通过 `http://100.70.54.13:19234/json` 获取

## 阶段一：进入商品详情页

### 1. 搜索商品（通过搜索结果点击打开详情页）

**禁止直接URL导航**，直接导航会导致"请求失败"，必须通过搜索结果点击打开。

```javascript
// 搜索（合并为一次调用）
var inp = document.querySelector('#rc_select_0');
var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
setter.call(inp, '');
inp.dispatchEvent(new Event('input', {bubbles:true}));
setter.call(inp, '商品ID');
inp.dispatchEvent(new Event('input', {bubbles:true}));
inp.dispatchEvent(new Event('change', {bubbles:true}));
var b = document.querySelectorAll('button');
for (var x of b) { if (x.innerText && x.innerText.trim() === '搜索') { x.click(); break; } }

// 等待搜索结果
await new Promise(r => setTimeout(r, 4000));
```

### 2. 点击商品图片打开详情页

```javascript
// 点击商品图片位置 (x:256, y:575)
Input.dispatchMouseEvent({ type: 'mouseMoved', x: 256, y: 575 });
Input.dispatchMouseEvent({ type: 'mousePressed', x: 256, y: 575, button: 'left', clickCount: 1 });
Input.dispatchMouseEvent({ type: 'mouseReleased', x: 256, y: 575, button: 'left', clickCount: 1 });

// 等待详情页打开
await new Promise(r => setTimeout(r, 4000));
```

### 重要：SPA导航行为

点击商品后，**当前选品库页面URL会变为详情页**（不是新标签页），是单页应用（SPA）导航。

## 阶段二：获取商家联系方式

### 关键DOM元素

| 元素 | 选择器 |
|------|--------|
| 联系商家按钮 | `button.auxo-btn.product-info__button-contact` |
| 浮层 | `.product-info__button-contact-overlay` |
| 眼睛图标 | `span.index__eye____8a66` |

### 1. 获取按钮真实位置

```javascript
var btn = document.querySelector('button.auxo-btn.product-info__button-contact');
if (btn) {
  var r = btn.getBoundingClientRect();
  var cx = Math.round(r.left + r.width / 2);
  var cy = Math.round(r.top + r.height / 2);
  JSON.stringify({cx: cx, cy: cy});
} else {
  'no_button';
}
```

### 2. 触发悬浮（先移动鼠标，再触发mouseenter）

```javascript
// 先移动鼠标到按钮中心
Input.dispatchMouseEvent({ type: 'mouseMoved', x: cx, y: cy });

// 触发React的mouseenter事件
var btn = document.querySelector('button.auxo-btn.product-info__button-contact');
if (btn) {
  btn.dispatchEvent(new MouseEvent('mouseenter', {view: window, bubbles: true, cancelable: true}));
}
```

### 3. 点击眼睛图标 + 读取联系方式（分两次，共2次CDP往返）

**阶段1：点击眼睛图标**
```javascript
var ov = document.querySelector('.product-info__button-contact-overlay');
if (ov) {
  var eyes = ov.querySelectorAll('span.index__eye____8a66');
  for (var i = 0; i < eyes.length; i++) { eyes[i].click(); }
}
// 等待解密
await new Promise(r => setTimeout(r, 1500));
```

**阶段2：读取联系方式**
```javascript
var ov = document.querySelector('.product-info__button-contact-overlay');
if (!ov) return 'no_overlay';
var ss = [];
ov.querySelectorAll('span, div').forEach(function(s) {
  if (s.offsetWidth > 0) {
    var t = s.textContent.trim();
    if (t && t.length > 1 && t !== '在线沟通') ss.push(t);
  }
});
JSON.stringify(ss);
```

**浮层内容格式示例**：
```
["微信号jiaodou8989手机号17200949830(+9267)"]
// 或者有眼睛图标的格式：
["在线沟通","微信号","oks138168188","手机号","15784104227(+8490)"]
```

### 4. 解析联系方式

```javascript
// 手机号：10位以上数字
phone_m = re.search(r'(\d{10,})', content)

// 微信号：字母开头，2-15位字母数字下划线
wechat_m = re.search(r'([A-Za-z][A-Za-z0-9_]{2,15})', content)

// 注意：虚拟号格式如 17200949830(+9267)，主号是11位数字
// 分机号在括号内，拨号时需要
```

### 商家无联系方式的情况

如果浮层只有"在线沟通"或联系商家按钮不存在，商家未配置联系方式：
- 状态改为"无效"
- 备注："商家未配置联系方式"

## 阶段三：保存联系方式到招商后台

### 数据库信息
- **路径**: `/home/ubuntu/dongxiao-system/backend/dongxiao.db`
- **表**: `submissions`（商品表）, `lianli_queue`（待建联队列）

### 保存Python代码

```python
import sqlite3, datetime

COMMODITY_ID = "商品ID"
phone = "手机号"
wechat = "微信号"

conn = sqlite3.connect('/home/ubuntu/dongxiao-system/backend/dongxiao.db')
c = conn.cursor()

c.execute("SELECT id FROM submissions WHERE product_url LIKE ?", (f'%{COMMODITY_ID}%',))
row = c.fetchone()
if row:
    record_id = row[0]
    if phone or wechat:
        c.execute("UPDATE submissions SET contact_phone=?, contact_wechat=?, status='已建联', updated_at=? WHERE id=?",
                 (phone or '', wechat or '', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), record_id))
        print(f'已建联: phone={phone}, wechat={wechat}')
    else:
        c.execute("UPDATE submissions SET contact_wechat='无', contact_phone='无', status='无效', remark='商家未配置联系方式', updated_at=? WHERE id=?",
                 (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), record_id))
        print('无效')
    c.execute("UPDATE lianli_queue SET status='completed' WHERE commodity_id=?", (COMMODITY_ID,))
else:
    print('Record not found')

conn.commit()
conn.close()
```

## 标签页管理

- **不主动关闭详情页**：任务完成后保留当前详情页
- **切换商品时**：先搜索打开新详情页，再关闭旧详情页
- **SPA导航注意**：点击商品后当前页面变为详情页（URL变化但页面ID不变），不需要也不应该关闭后再开新的

## 测试商品ID

- Hellokitty雨伞：`3810938792773288085`
- 成功案例1：3755056902543900873（惠维诗官方旗舰店，微信号oks138168188，手机号15784104227）
- 成功案例2：3805904285762453990（jiaodou8989，虚拟号17200949830）
- 成功案例3：3811117903655338035（oks138168188，15784104227）