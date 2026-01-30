# Clawdbot 插件快速启动指南

## ✅ 已完成的配置

1. ✅ Clawdbot Gateway HTTP API 已启用
2. ✅ Token 已配置到环境变量
3. ✅ API 测试成功

## 🚀 如何使用

### 0. 配置环境变量

在启动 ncatbot 之前设置：

```bash
export CLAWDBOT_TOKEN="<your_token>"
export CLAWDBOT_GATEWAY_URL="http://127.0.0.1:18789"  # 可选
export CLAWDBOT_ALLOWED_PRIVATE_USER_ID="<your_qq_id>" # 可选
```

### 1. 重启你的 QQ 机器人

插件已经创建在 `plugins/clawdbot_plugin/` 目录中。重启 catbot 以加载插件：

```bash
# 停止当前运行的机器人（按 Ctrl+C）
# 然后重新启动
cd /path/to/ncatbot/main
sudo /path/to/ncatbot/botenv/bin/python catbot_event.py
```

### 2. 在 QQ 中测试

#### 测试连接
在 QQ 群或私聊中发送：
```
/clawdtest
```

如果看到 "✅ 连接成功！" 说明插件工作正常。

#### 与 Clawdbot 对话
```
/clawd 你好，请介绍一下你自己
```

```
/clawd 帮我查询今天的天气
```

```
/clawd 写一个 Python 函数来计算斐波那契数列
```

### 3. 会话管理

- **群聊**：每个群有独立的对话上下文
- **私聊**：每个用户有独立的对话上下文
- Clawdbot 会记住之前的对话内容

### 4. 示例对话

```
用户: /clawd 你好
机器人: 🤔 正在向 Clawdbot 发送消息...
机器人: 🤖 Clawdbot 回复:
你好！我是 Clawdbot，一个 AI 助手。我可以帮你完成各种任务...

用户: /clawd 你刚才说了什么？
机器人: 🤖 Clawdbot 回复:
我刚才介绍了自己，说我是 Clawdbot，一个 AI 助手...
```

## 📝 可用命令

- `/clawd <消息>` - 与 Clawdbot 对话
- `/clawdtest` - 测试连接

## 🔧 高级配置

### 修改超时时间

如果 Clawdbot 响应较慢，可以编辑插件文件增加超时：

```bash
nano /path/to/ncatbot/main/plugins/clawdbot_plugin/clawdbot_plugin.py
```

找到这一行：
```python
timeout=aiohttp.ClientTimeout(total=60)
```

改为更长的时间（例如 120 秒）：
```python
timeout=aiohttp.ClientTimeout(total=120)
```

### 使用不同的 Agent

默认使用 `main` agent。如果你有其他 agent（例如 `beta`），可以修改：

```python
"model": "clawdbot:main",  # 改为 "clawdbot:beta"
```

## 🐛 故障排除

### 问题：连接失败

**检查清单：**
1. Clawdbot Gateway 是否运行？
   ```bash
   clawdbot gateway status
   ```

2. HTTP API 是否启用？（已完成 ✅）

3. Token 是否正确？
   - 请检查 `CLAWDBOT_TOKEN` 是否已设置

### 问题：超时

增加超时时间（见上面的高级配置）

### 问题：插件没有加载

检查 catbot 的日志输出，搜索 `clawdbot_plugin` 相关信息。

确保插件目录结构正确：
```
plugins/
└── clawdbot_plugin/
    ├── __init__.py
    ├── clawdbot_plugin.py
    └── README.md
```

## 📊 性能说明

- 每次调用会消耗 Clawdbot 的 API token
- 建议在群聊中使用命令触发，而不是自动转发所有消息
- 响应时间取决于 Clawdbot 的处理速度（通常 3-10 秒）

## 🎉 完成！

现在你的 QQ 机器人已经可以与 Clawdbot 通信了！

试试在 QQ 中发送 `/clawdtest` 来测试连接吧！
