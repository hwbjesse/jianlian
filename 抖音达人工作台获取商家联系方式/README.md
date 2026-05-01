# 建联任务 Skill 仓库

通过商品 ID 进入抖音达人工作台，获取商品商家的**微信号**和**手机号**。

## Skills

### douyin-lianli-task
招商系统建联任务主控 Skill，完整流程：接收指令 → CDP 进入选品广场 → 搜索商品 → 获取联系方式 → 回填数据库。

### douyin-product-contact
核心获取联系方式 Skill。通过商品 ID 搜索 → 进入商品详情页 → 悬浮联系商家 → 获取商家微信号/手机号。

### douyin-product-nav
通过商品 ID 打开商品详情页（仅导航，不获取联系方式）。用于验证商品或查看详情。

## CDP 连接

- **地址**: 本地 Chrome 浏览器（通过 Tailscale 映射）
- **说明**: 需要本地电脑开机并运行 Chrome

## 任务执行

任务文案中指定所需 skill，例如：
```
skill: douyin-lianli-task + douyin-product-contact + douyin-product-nav
```

## 更新日志

- 2024-05-02: 初始上传
