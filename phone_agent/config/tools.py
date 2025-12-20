"""Tool definitions for Gemini Native Tool Calling."""

# The count and content of these tools match phone_agent/config/prompts_zh.py exactly.
GEMINI_TOOLS = [
    {
        "functionDeclarations": [
            {
                "name": "Tap",
                "description": "点击操作，点击屏幕上的特定点。坐标系统 0-999。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "element": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "点击坐标 [x, y]"
                        },
                        "thought": {
                            "type": "string",
                            "description": "当前的思考和行动原因"
                        },
                        "message": {
                            "type": "string", 
                            "description": "涉及财产、支付、隐私等敏感按钮时的说明"
                        }
                    },
                    "required": ["element", "thought"]
                }
            },
            {
                "name": "Launch",
                "description": "启动目标 app 操作。注意：仅支持有限的预设应用列表。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "app": {"type": "string", "description": "应用名称"},
                        "thought": {"type": "string", "description": "当前的思考和行动原因"}
                    },
                    "required": ["app", "thought"]
                }
            },
            {
                "name": "Type",
                "description": "在当前聚焦的输入框中输入文本。使用前请确保输入框已聚焦。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "要输入的文本内容"},
                        "thought": {"type": "string", "description": "当前的思考和行动原因"}
                    },
                    "required": ["text", "thought"]
                }
            },
            {
                "name": "Type_Name",
                "description": "输入人名的操作，基本功能同 Type。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "要输入的人名"},
                        "thought": {"type": "string", "description": "当前的思考和行动原因"}
                    },
                    "required": ["text", "thought"]
                }
            },
            {
                "name": "Interact",
                "description": "当有多个满足条件的选项时而触发的交互操作，询问用户如何选择。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "thought": {"type": "string", "description": "当前的思考和行动原因"}
                    },
                    "required": ["thought"]
                }
            },
            {
                "name": "Swipe",
                "description": "滑动操作，通过从起始坐标拖动到结束坐标来执行滑动手势。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "起始坐标 [x1, y1]"
                        },
                        "end": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "结束坐标 [x2, y2]"
                        },
                        "thought": {
                            "type": "string",
                            "description": "当前的思考和行动原因"
                        }
                    },
                    "required": ["start", "end", "thought"]
                }
            },
            {
                "name": "Note",
                "description": "记录当前页面内容以便后续总结。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "记录的消息或状态，如 'True'"},
                        "thought": {"type": "string", "description": "当前的思考和行动原因"}
                    },
                    "required": ["message", "thought"]
                }
            },
            {
                "name": "Call_API",
                "description": "总结或评论当前页面或已记录的内容。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "instruction": {"type": "string", "description": "总结或评论的指令"},
                        "thought": {"type": "string", "description": "当前的思考和行动原因"}
                    },
                    "required": ["instruction", "thought"]
                }
            },
            {
                "name": "Long_Press",
                "description": "长按操作，在屏幕上的特定点长按指定时间。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "element": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "长按坐标 [x, y]"
                        },
                        "thought": {
                            "type": "string",
                            "description": "当前的思考和行动原因"
                        }
                    },
                    "required": ["element", "thought"]
                }
            },
            {
                "name": "Double_Tap",
                "description": "双击操作，在屏幕上的特定点快速连续点按两次。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "element": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "双击坐标 [x, y]"
                        },
                        "thought": {
                            "type": "string",
                            "description": "当前的思考和行动原因"
                        }
                    },
                    "required": ["element", "thought"]
                }
            },
            {
                "name": "Take_over",
                "description": "接管操作，表示在登录和验证阶段需要用户协助。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "接管的原因或说明"},
                        "thought": {"type": "string", "description": "当前的思考和行动原因"}
                    },
                    "required": ["message", "thought"]
                }
            },
            {
                "name": "Back",
                "description": "导航返回到上一个屏幕或关闭当前对话框。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "thought": {"type": "string", "description": "当前的思考和行动原因"}
                    },
                    "required": ["thought"]
                }
            },
            {
                "name": "Home",
                "description": "回到系统桌面的操作。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "thought": {"type": "string", "description": "当前的思考和行动原因"}
                    },
                    "required": ["thought"]
                }
            },
            {
                "name": "Wait",
                "description": "等待页面加载。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "duration": {"type": "string", "description": "等待秒数，如 '2 seconds'"},
                        "thought": {"type": "string", "description": "当前的思考和行动原因"}
                    },
                    "required": ["duration", "thought"]
                }
            },
            {
                "name": "finish",
                "description": "结束任务的操作，表示准确完整完成任务。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "任务终止时的总结信息"},
                        "thought": {"type": "string", "description": "当前的思考和行动原因"}
                    },
                    "required": ["message", "thought"]
                }
            }
        ]
    }
]
