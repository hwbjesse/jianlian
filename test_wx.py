import wxauto
import time

print("正在初始化微信...")
try:
    wx = wxauto.WeChat()
    print("✅ 微信初始化成功")
    
    print("获取会话列表...")
    friends = wx.GetSessionList()
    print(f"✅ 找到 {len(friends)} 个会话")
    for f in friends[:10]:
        print(f"  - {f}")
except Exception as e:
    print(f"❌ 错误: {e}")
