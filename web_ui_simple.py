import http.server
import socketserver
import threading
import json
import os
import base64
import subprocess
from urllib.parse import urlparse, parse_qs, unquote
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv

from phone_agent.agent import PhoneAgent, AgentConfig
from phone_agent.model import ModelConfig

load_dotenv()

CONFIG_FILE = "ui_config.json"
# 强制本地不走代理
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "model_name": os.getenv("MODEL_NAME", "gpt-4o"),
        "api_type": "openai",
        "device_id": "",
        "lang": "cn",
        "max_steps": 15
    }

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

# 全局状态
state = {
    "history": [], # 存储步骤对象
    "running": False,
    "current_step": 0,
    "config": load_config()
}

class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(self.get_html().encode())
            
        elif parsed_path.path == '/state':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            # 只返回界面需要的状态，不包含巨大的图片数据
            self.wfile.write(json.dumps({
                "running": state["running"],
                "history": state["history"],
                "config": state["config"]
            }).encode())
            
        elif parsed_path.path == '/screenshot.png':
            if os.path.exists("latest_screenshot.png"):
                self.send_response(200)
                self.send_header('Content-type', 'image/png')
                self.end_headers()
                with open("latest_screenshot.png", "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()

        elif parsed_path.path == '/start':
            query = parse_qs(parsed_path.query)
            # 更新并保存配置
            new_config = {
                "api_key": query.get('api_key', [''])[0],
                "base_url": query.get('base_url', [''])[0],
                "model_name": query.get('model_name', [''])[0],
                "api_type": query.get('api_type', ['openai'])[0],
                "device_id": query.get('device_id', [''])[0],
                "lang": query.get('lang', ['cn'])[0],
                "max_steps": int(query.get('max_steps', [15])[0])
            }
            state["config"] = new_config
            save_config(new_config)
            
            task = query.get('task', [''])[0]
            if task and not state['running']:
                threading.Thread(target=run_agent_thread, args=(task, new_config)).start()
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

    def get_html(self):
        c = state["config"]
        return f"""
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Open-AutoGLM Lite Full</title>
            <style>
                body {{ font-family: -apple-system, system-ui, sans-serif; margin: 0; background: #f4f7f9; color: #333; }}
                .app {{ display: flex; flex-direction: column; height: 100vh; }}
                header {{ background: #202123; color: white; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; }}
                .main {{ display: flex; flex: 1; overflow: hidden; }}
                
                /* Sidebar Settings */
                .sidebar {{ width: 300px; background: white; border-right: 1px solid #ddd; padding: 20px; overflow-y: auto; font-size: 13px; flex-shrink: 0; }}
                .sidebar h3 {{ margin-top: 0; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                .field {{ margin-bottom: 15px; }}
                .field label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
                .field input, .field select {{ width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }}
                
                /* Content Area */
                .content {{ flex: 1; display: flex; flex-direction: column; padding: 20px; overflow-y: auto; }}
                .control-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 20px; }}
                .task-row {{ display: flex; gap: 10px; }}
                .task-row input {{ flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 16px; min-width: 0; }}
                .btn-run {{ background: #10a37f; color: white; border: none; padding: 0 20px; border-radius: 6px; cursor: pointer; font-weight: bold; flex-shrink: 0; }}
                .btn-run:disabled {{ background: #ccc; }}
                
                /* Output Area */
                .output-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; flex: 1; min-height: 0; }}
                .screen-box, .log-box {{ background: white; border-radius: 8px; padding: 15px; border: 1px solid #ddd; display: flex; flex-direction: column; min-height: 300px; }}
                .log-box {{ overflow-y: auto; }}
                #screenshot {{ max-width: 100%; height: auto; object-fit: contain; margin: auto; border: 1px solid #eee; }}
                
                /* Mobile Responsive */
                @media (max-width: 768px) {{
                    .main {{ flex-direction: column; overflow-y: auto; }}
                    .sidebar {{ width: 100%; border-right: none; border-bottom: 1px solid #ddd; height: auto; overflow-y: visible; }}
                    .output-grid {{ grid-template-columns: 1fr; }}
                    .app {{ height: auto; min-height: 100vh; }}
                    .main {{ overflow: visible; }}
                }}
                
                /* Log Styling */
                .step-item {{ border-bottom: 1px solid #eee; padding: 10px 0; }}
                .step-num {{ color: #10a37f; font-weight: bold; }}
                .thought {{ font-style: italic; color: #555; background: #f9f9f9; padding: 8px; margin: 5px 0; border-radius: 4px; }}
                .action-tag {{ display: inline-block; background: #e7f3ff; color: #007bff; padding: 2px 6px; border-radius: 3px; font-family: monospace; }}
            </style>
        </head>
        <body>
            <div class="app">
                <header>
                    <strong>📱 Open-AutoGLM Lite</strong>
                    <div id="status-badge">● 准备就绪</div>
                </header>
                <div class="main">
                    <div class="sidebar">
                        <h3>⚙️ 设置</h3>
                        <div class="field">
                            <label>API Key</label>
                            <input type="password" id="api_key" value="{c['api_key']}">
                        </div>
                        <div class="field">
                            <label>Base URL</label>
                            <input type="text" id="base_url" value="{c['base_url']}">
                        </div>
                        <div class="field">
                            <label>Model Name</label>
                            <input type="text" id="model_name" value="{c['model_name']}">
                        </div>
                        <div class="field">
                            <label>API Type</label>
                            <select id="api_type">
                                <option value="openai" {"selected" if c['api_type']=='openai' else ""}>OpenAI</option>
                                <option value="gemini" {"selected" if c['api_type']=='gemini' else ""}>Gemini</option>
                            </select>
                        </div>
                        <div class="field">
                            <label>Device ID (Optional)</label>
                            <input type="text" id="device_id" value="{c['device_id']}" placeholder="adb serial">
                        </div>
                        <div class="field">
                            <label>Max Steps</label>
                            <input type="number" id="max_steps" value="{c['max_steps']}">
                        </div>
                    </div>
                    
                    <div class="content">
                        <div class="control-card">
                            <div class="task-row">
                                <input type="text" id="task_input" placeholder="请输入指令，例如：打开浏览器搜索今天的新闻">
                                <button class="btn-run" id="run_btn" onclick="startTask()">开始运行</button>
                            </div>
                        </div>
                        
                        <div class="output-grid">
                            <div class="screen-box">
                                <strong>实时画面:</strong>
                                <img id="screenshot" src="/screenshot.png">
                            </div>
                            <div class="log-box" id="history">
                                <strong>运行日志:</strong>
                                <div id="history_list"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                let lastHistoryLen = 0;
                let lastStatus = false;

                function startTask() {{
                    const params = new URLSearchParams({{
                        task: document.getElementById('task_input').value,
                        api_key: document.getElementById('api_key').value,
                        base_url: document.getElementById('base_url').value,
                        model_name: document.getElementById('model_name').value,
                        api_type: document.getElementById('api_type').value,
                        device_id: document.getElementById('device_id').value,
                        max_steps: document.getElementById('max_steps').value,
                        lang: 'cn'
                    }});
                    fetch('/start?' + params.toString());
                    document.getElementById('history_list').innerHTML = '<div class="step-item">🚀 正在启动 Agent...</div>';
                    lastHistoryLen = 0;
                }}

                function update() {{
                    fetch('/state').then(r => r.json()).then(data => {{
                        const btn = document.getElementById('run_btn');
                        const status = document.getElementById('status-badge');
                        
                        if (btn.disabled !== data.running) {{
                            btn.disabled = data.running;
                            status.innerText = data.running ? "● 正在运行" : "● 准备就绪";
                            status.style.color = data.running ? "#f39c12" : "#10a37f";
                        }}
                        
                        if (data.running || lastStatus !== data.running) {{
                            document.getElementById('screenshot').src = "/screenshot.png?t=" + Date.now();
                        }}
                        lastStatus = data.running;
                        
                        if (data.history.length !== lastHistoryLen) {{
                            let html = "";
                            data.history.forEach((step, idx) => {{
                                html = `<div class="step-item">
                                    <div class="step-num">Step ${{idx + 1}}</div>
                                    <div class="thought">🤔 ${{step.thinking}}</div>
                                    ${{step.action ? `<div>🎯 动作: <span class="action-tag">${{step.action.action}}</span></div>` : ""}}
                                    ${{step.message ? `<div style="margin-top:5px">💬 ${{step.message}}</div>` : ""}}
                                </div>` + html;
                            }});
                            document.getElementById('history_list').innerHTML = html || "等待任务开始...";
                            lastHistoryLen = data.history.length;
                        }}
                    }});
                }}
                setInterval(update, 2000);
            </script>
        </body>
        </html>
        """

def run_agent_thread(task, config):
    state['running'] = True
    state['history'] = []
    
    try:
        model_cfg = ModelConfig(
            api_key=config['api_key'],
            base_url=config['base_url'],
            model_name=config['model_name'],
            api_type=config['api_type']
        )
        agent_cfg = AgentConfig(
            lang=config['lang'], 
            max_steps=config['max_steps'],
            device_id=config['device_id'] if config['device_id'] else None
        )
        
        agent = PhoneAgent(model_config=model_cfg, agent_config=agent_cfg)
        agent.reset()
        
        # 第一步
        result = agent.step(task)
        _update_step(result)
        
        while not result.finished and len(state['history']) < agent_cfg.max_steps:
            result = agent.step()
            _update_step(result)
            
    except Exception as e:
        state['history'].append({"thinking": f"错误: {str(e)}", "action": None, "message": "已停止"})
    
    state['running'] = False

def send_termux_notification(title, message):
    """通过 Termux:API 发送系统通知"""
    try:
        # 使用 termux-notification 命令
        subprocess.run([
            "termux-notification",
            "--title", title,
            "--content", message,
            "--id", "autoglm_notify",
            "--group", "autoglm"
        ], capture_output=True)
    except:
        pass

def _update_step(result):
    # 保存截图
    if result.screenshot:
        try:
            img_data = base64.b64decode(result.screenshot)
            with open("latest_screenshot.png", "wb") as f:
                f.write(img_data)
        except: pass
    
    # 添加到历史
    state['history'].append({
        "thinking": result.thinking,
        "action": result.action,
        "message": result.message
    })

    # 发送通知到手机系统
    try:
        step_num = len(state['history'])
        action_desc = result.action.get('action', '进行中') if result.action else '思考中'
        notif_msg = f"Step {step_num}: {action_desc}\n{result.thinking[:60]}..."
        if result.finished:
            notif_msg = f"✅ 任务已完成!\n{result.message}"
        send_termux_notification("🤖 Open-AutoGLM", notif_msg)
    except:
        pass

if __name__ == "__main__":
    PORT = 7860
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), SimpleHandler) as httpd:
        print(f"🚀 全功能 Lite 版已启动!")
        print(f"📱 请访问: http://localhost:{{PORT}}")
        httpd.serve_forever()
