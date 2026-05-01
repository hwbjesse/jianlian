# 建联任务 Skill 仓库

存储抖音建联任务相关的 Skills，用于通过 CDP 连接本地 Chrome 浏览器执行商品建联流程。

## Skills

### douyin-lianli-task
招商系统建联任务处理主控 Skill，完整流程：接收指令 → CDP 进入选品广场 → 搜索商品 → 获取联系方式 → 回填数据库。

### douyin-product-contact
通过商品 ID 获取商家联系方式（手机号/微信号）。完整链路：搜索商品 → 点击商品卡片 → 悬浮联系商家 → 获取联系方式。

### douyin-product-nav
通过商品 ID 打开商品详情页（不获取联系方式）。用于验证商品信息或查看详情。

## CDP 连接

- **地址**: `100.70.54.13:19234`
- **说明**: 需要保持本地电脑开机并运行 Chrome

## 使用方式

任务文案中指定所需 skill，例如：
```
skill: douyin-lianli-task + douyin-product-contact + douyin-product-nav
```

## 更新日志

- 2024-05-02: 初始上传三个建联 skill
