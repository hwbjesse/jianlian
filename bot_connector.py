#!/usr/bin/env python3
"""
微信机器人连接器 - Windows 端运行
整合 wxauto，支持面板下发指令控制微信
"""
import requests
import json
import time
import uuid
import socket
import sys
import os

try:
    import wxauto
    HAS_WXAUTO = True
except ImportError:
    HAS_WXAUTO = False
    print("⚠️  wxauto 未安装，请先运行: pip install git+https://github.com/cluic/wxauto.git")

PANEL_API = "http://100.114.79.7:10001"
BOT_ID_FILE = os.path.join(os.path.dirname(__file__), '.bot_id')
HEARTBEAT_INTERVAL = 30

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def load_bot_id():
    try:
        with open(BOT_ID_FILE, 'r') as f:
            return f.read().strip()
    except:
        bot_id = str(uuid.uuid4())
        try:
            with open(BOT_ID_FILE, 'w') as f:
                f.write(bot_id)
        except:
            pass
        return bot_id

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

class WeChatBot:
    def __init__(self):
        self.wx = None
        self.is_ready = False

    def init(self):
        if not HAS_WXAUTO:
            return False, "wxauto 未安装"
        try:
            self.wx = wxauto.WeChat()
            self.is_ready = True
            return True, "微信初始化成功"
        except Exception as e:
            self.is_ready = False
            return False, f"微信初始化失败: {str(e)}"

    def send_message(self, name, msg):
        if not self.is_ready:
            return False, "微信未初始化"
        try:
            self.wx.SendMsg(msg, name)
            return True, f"消息已发送给: {name}"
        except Exception as e:
            return False, f"发送失败: {str(e)}"

    def get_messages(self, name, n=10):
        if not self.is_ready:
            return False, "微信未初始化"
        try:
            msgs = self.wx.GetMessage(name=name, n=n)
            if not msgs:
                return True, f"暂无消息记录: {name}"
            result = [f"[{m.get('type', 'text')}] {m.get('sender', '')}: {m.get('content', '')}" for m in msgs[-n:]]
            return True, "\n".join(result)
        except Exception as e:
            return False, f"获取消息失败: {str(e)}"

    def get_friends(self):
        if not self.is_ready:
            return False, "微信未初始化"
        try:
            friends = self.wx.GetSessionList()
            if not friends:
                return True, "暂无好友"
            return True, "好友/群列表:\n" + "\n".join(friends[:50])
        except Exception as e:
            return False, f"获取好友失败: {str(e)}"

    def get_status(self):
        if not self.is_ready:
            return {"status": "not_ready", "wxauto": HAS_WXAUTO}
        try:
            sessions = self.wx.GetSessionList()
            return {"status": "running", "friends_count": len(sessions) if sessions else 0, "wxauto": True}
        except:
            return {"status": "running", "wxauto": True}

class PanelConnector:
    def __init__(self):
        self.api = PANEL_API.rstrip('/')
        self.bot_id = load_bot_id()
        self.bot_name = socket.gethostname()
        self.running = True
        self.registered = False
        self.wxbot = WeChatBot()

    def _post(self, path, data=None, timeout=10):
        try:
            r = requests.post(f"{self.api}{path}", json=data or {}, timeout=timeout, headers={'Content-Type': 'application/json'})
            return r.json()
        except requests.exceptions.Timeout:
            return {'status': 'error', 'message': '请求超时'}
        except requests.exceptions.ConnectionError:
            return {'status': 'error', 'message': '无法连接到服务器'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _get(self, path, params=None, timeout=10):
        try:
            r = requests.get(f"{self.api}{path}", params=params or {}, timeout=timeout)
            return r.json()
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def register(self):
        log(f"正在注册到面板: {self.api}")
        result = self._post('/api/bot/register', {
            'bot_id': self.bot_id,
            'bot_name': self.bot_name,
            'version': '2.0.0-wxauto',
            'info': {'local_ip': get_local_ip(), 'start_time': time.strftime('%Y-%m-%d %H:%M:%S'), 'python_version': sys.version.split()[0], 'wxauto': HAS_WXAUTO}
        })
        if result.get('status') == 'success':
            self.registered = True
            log(f"✅ 注册成功，机器人ID: {self.bot_id}")
            return True
        else:
            log(f"❌ 注册失败: {result.get('message', '未知错误')}")
            return False

    def heartbeat(self):
        result = self._post('/api/bot/heartbeat', {'bot_id': self.bot_id, 'info': {'local_ip': get_local_ip(), 'memory_usage_mb': 0}})
        return result.get('status') == 'success'

    def pull_command(self):
        result = self._get('/api/bot/command', params={'bot_id': self.bot_id})
        if result.get('status') == 'success' and result.get('command'):
            cmd = result['command']
            if isinstance(cmd, dict):
                return cmd.get('cmd')
            return cmd
        return None

    def report_result(self, result_data):
        self._post('/api/bot/report', {'bot_id': self.bot_id, 'result': result_data})

    def notify_offline(self):
        self._post('/api/bot/offline', {'bot_id': self.bot_id}, timeout=5)

    def handle_command(self, cmd):
        cmd = cmd.strip()
        log(f"📨 收到指令: {cmd}")
        if not self.wxbot.is_ready:
            ok, msg = self.wxbot.init()
            if not ok:
                return {'type': 'error', 'data': msg}
        if cmd == 'status':
            return {'type': 'status', 'data': self.wxbot.get_status()}
        elif cmd == 'restart':
            log("🔄 收到重启指令，机器人将重启...")
            self.running = False
            return {'type': 'restart'}
        elif cmd == 'info':
            return {'type': 'info', 'data': {'bot_id': self.bot_id, 'bot_name': self.bot_name, 'local_ip': get_local_ip(), 'start_time': time.strftime('%Y-%m-%d %H:%M:%S'), 'version': '2.0.0-wxauto', 'wxauto_ready': self.wxbot.is_ready}}
        elif cmd == 'ping':
            return {'type': 'pong', 'data': {'time': time.strftime('%Y-%m-%d %H:%M:%S')}}
        elif cmd.startswith('send:'):
            parts = cmd.split(':', 2)
            if len(parts) < 3:
                return {'type': 'error', 'data': '格式: send:好友名:消息内容'}
            name, msg = parts[1], parts[2]
            ok, res = self.wxbot.send_message(name, msg)
            return {'type': 'send', 'data': res if ok else res}
        elif cmd.startswith('getmsg:'):
            parts = cmd.split(':', 2)
            if len(parts) < 2:
                return {'type': 'error', 'data': '格式: getmsg:好友名[:条数]'}
            name = parts[1]
            n = int(parts[2]) if len(parts) > 2 else 10
            ok, res = self.wxbot.get_messages(name, n)
            return {'type': 'messages', 'data': res}
        elif cmd == 'friends':
            ok, res = self.wxbot.get_friends()
            return {'type': 'friends', 'data': res}
        else:
            return {'type': 'unknown', 'data': {'cmd': cmd, 'message': '未知指令'}}

    def run(self):
        log("=" * 40)
        log("🤖 微信机器人管理面板连接器")
        log(f"📡 面板地址: {self.api}")
        log(f"🔑 机器人ID: {self.bot_id}")
        log(f"📦 wxauto: {'已安装' if HAS_WXAUTO else '未安装'}")
        log("=" * 40)
        if not self.register():
            log("⚠️  注册失败，5秒后重试...")
            time.sleep(5)
            if not self.register():
                log("❌ 连续注册失败")
                return
        heartbeat_count = 0
        while self.running:
            heartbeat_count += 1
            if heartbeat_count % 2 == 0:
                if not self.heartbeat():
                    log("⚠️  心跳失败，重新注册...")
                    self.registered = False
                    time.sleep(3)
                    self.register()
            cmd = self.pull_command()
            if cmd:
                result = self.handle_command(cmd)
                if result:
                    self.report_result(result)
                    if result.get('type') == 'restart':
                        break
            time.sleep(HEARTBEAT_INTERVAL // 2)
        try:
            self.notify_offline()
        except:
            pass
        log("👋 连接器已退出")

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("  微信机器人管理面板 - Windows 连接器 (wxauto版)")
    print("=" * 50)
    print(f"  面板API: {PANEL_API}")
    print(f"  机器人ID: {load_bot_id()}")
    print("=" * 50 + "\n")
    connector = PanelConnector()
    try:
        connector.run()
    except KeyboardInterrupt:
        print("\n正在停止...")
        connector.running = False
        connector.notify_offline()
        print("已退出")
