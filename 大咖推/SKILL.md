---
name: combined-duoke-dakatui
description: 综合工具 - 抖客助手转链 + 大咖推修改对接人。根据用户输入自动判断执行哪个操作。收到抖音链接去抖客助手转链，收到商品ID+对接人去大咖推修改。
---

# 抖客助手 & 大咖推 综合工具

## ⚠️ 核心能力（必须记住！）

我有两个核心能力，根据用户输入自动判断：

### 1️⃣ 抖客助手 - 转链
**触发**：收到抖音商品链接
**操作**：登录抖客助手，将链接转为带佣金的购买口令

### 2️⃣ 大咖推 - 修改对接人
**触发**：收到商品ID + 新对接人姓名
**操作**：登录大咖推，修改商品的对接人

---

## 自动判断规则

| 用户输入 | 执行操作 |
|---------|---------|
| 抖音链接（v.douyin.com, haohuo.jinritemai.com） | 抖客助手转链 |
| 抖客助手账号密码 + Token相关信息 | 获取Token |
| 商品ID + "修改"/"改成"/"改为" + 姓名 | 大咖推修改对接人 |
| 商品ID + "查询"/"是谁"/"多少" | 查询商品对接人 |

---

## 1️⃣ 抖客助手转链

### 工具
- **工具**: agent-browser 或 Playwright
- **地址**: http://36.151.144.7:33162/#/login

### 流程
1. agent-browser登录
2. 进入转链页面
3. 填写链接
4. 转链
5. 返回口令

### 返回格式
```
🍊 转链成功！

商品信息：
· 商品名称: xxx
· 价格: ¥xx
· 佣金比例: xx%

购买口令:
xxxxx

使用方法：在抖音APP中长按粘贴口令即可查看商品详情。
```

---

## 2️⃣ 大咖推修改对接人

### 工具
- **工具**: Playwright (Python)
- **地址**: https://tz.dakatui.com

### 关键要点
1. **必须用Playwright**，不能用agent-browser
2. **必须用CSS让hover元素可见**
3. **必须用Playwright的`.click()`提交**，不能用JS的`click()`！

### 流程
1. Playwright登录大咖推
2. 进入商品列表（进行中）
3. 搜索商品ID
4. 点击"修改对接人"
5. 选择新对接人
6. 提交

### 返回格式
```
✅ 已将商品 {商品ID} 的对接人修改为 {新对接人姓名}
```

---

## 快捷命令

```bash
# 转链
~/.openclaw/workspace/skills/douyin-link-converter/scripts/douyin-convert.sh "<链接>"

# 或用Playwright
python3 << 'EOF'
# 转链脚本
EOF
```

```bash
# 修改对接人（必须用Playwright）
python3 << 'EOF'
# 修改对接人脚本（见 dakatui-person-modify/SKILL.md）
EOF
```
