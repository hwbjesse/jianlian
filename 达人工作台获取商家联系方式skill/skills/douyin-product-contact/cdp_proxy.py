#!/usr/bin/env python3
"""
CDP中转脚本 - 放在用户Windows上运行
把服务器HTTP请求转为Chrome CDP WebSocket（origin=localhost不受限）
启动: python cdp_proxy.py
"""
import json
import threading
import websocket
from flask import Flask, request, jsonify

app = Flask(__name__)

CDP_HOST = "100.70.54.13"
CDP_PORT = 19234

# 停止标志
stop_flag = [False]

def cdp_ws_connect(page_id, timeout=10):
    """建立WebSocket连接到指定页面"""
    ws_url = f"ws://{CDP_HOST}:{CDP_PORT}/devtools/page/{page_id}"
    ws = websocket.create_connection(
        ws_url, timeout=timeout,
        header=["Origin: http://localhost"]
    )
    return ws

def cdp_eval(page_id, expression, timeout=10):
    """在指定页面执行JS并返回结果"""
    ws = cdp_ws_connect(page_id, timeout)
    msg_id = 1
    ws.send(json.dumps({
        "id": msg_id,
        "method": "Runtime.evaluate",
        "params": {"expression": expression, "returnByValue": True}
    }))
    resp = ws.recv()
    ws.close()
    return json.loads(resp)

def cdp_mouse(page_id, kind, x, y, button="left", clickCount=1):
    """发送鼠标事件"""
    ws = cdp_ws_connect(page_id)
    msg_id = 1
    if kind == "move":
        ws.send(json.dumps({
            "id": msg_id, "method": "Input.dispatchMouseEvent",
            "params": {"type": "mouseMoved", "x": x, "y": y}
        }))
    elif kind == "press":
        ws.send(json.dumps({
            "id": msg_id, "method": "Input.dispatchMouseEvent",
            "params": {"type": "mousePressed", "x": x, "y": y, "button": button, "clickCount": clickCount}
        }))
    elif kind == "release":
        ws.send(json.dumps({
            "id": msg_id, "method": "Input.dispatchMouseEvent",
            "params": {"type": "mouseReleased", "x": x, "y": y, "button": button, "clickCount": clickCount}
        }))
    ws.close()
    return {"ok": True}

@app.route("/json", methods=["GET"])
def list_pages():
    """返回页面列表"""
    import httpx
    try:
        resp = httpx.get(f"http://{CDP_HOST}:{CDP_PORT}/json", timeout=5)
        pages = resp.json()
        return jsonify({"success": True, "pages": [
            {"id": p["id"], "title": p.get("title",""), "url": p.get("url","")[:100]}
            for p in pages if p.get("type") == "page"
        ]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/eval", methods=["POST"])
def eval_js():
    """在页面执行JS表达式"""
    data = request.json
    page_id = data.get("page_id")
    expression = data.get("expression", "")
    if not page_id:
        return jsonify({"success": False, "error": "page_id required"}), 400
    try:
        resp = cdp_eval(page_id, expression)
        return jsonify({"success": True, "result": resp})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/mouse", methods=["POST"])
def mouse_event():
    """发送鼠标事件"""
    data = request.json
    page_id = data.get("page_id")
    kind = data.get("kind")  # move/press/release
    x = data.get("x", 0)
    y = data.get("y", 0)
    if not page_id or not kind:
        return jsonify({"success": False, "error": "page_id and kind required"}), 400
    try:
        result = cdp_mouse(page_id, kind, x, y)
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/scroll", methods=["POST"])
def scroll_page():
    """滚动页面"""
    data = request.json
    page_id = data.get("page_id")
    y = data.get("y", 0)
    if not page_id:
        return jsonify({"success": False, "error": "page_id required"}), 400
    try:
        resp = cdp_eval(page_id, f"window.scrollTo(0, {y})")
        return jsonify({"success": True, "result": resp})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "proxy": "cdp-relay"})

@app.route("/stop", methods=["GET"])
def check_stop():
    """AI轮询此接口，返回是否点击了停止"""
    if stop_flag[0]:
        stop_flag[0] = False
        return jsonify({"stop": True})
    return jsonify({"stop": False})

@app.route("/stop", methods=["POST"])
def set_stop():
    """用户点击停止按钮时调用"""
    stop_flag[0] = True
    return jsonify({"ok": True})

if __name__ == "__main__":
    # 监听本地9223端口
    print("CDP中转启动: http://localhost:9223")
    print("把服务器请求转发到 Chrome CDP (100.70.54.13:19234)")
    app.run(host="0.0.0.0", port=9223, debug=False)
