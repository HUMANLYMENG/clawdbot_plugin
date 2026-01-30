# Clawdbot 集成架构说明

## 📐 系统架构

```
QQ 用户
   ↓
QQ 服务器
   ↓
catbot (QQ 机器人)
   ↓
clawdbot_plugin (插件)
   ↓ HTTP POST /v1/responses
Clawdbot Gateway (localhost:18789)
   ↓
Clawdbot Agent (main)
   ↓
AI 模型 (Claude Sonnet 4.5)
   ↓
响应返回
```

## 🔄 消息流程

### 1. 用户发送消息
```
QQ 群/私聊: /clawd 你好
```

### 2. catbot 接收消息
- catbot 的事件系统捕获消息
- 识别 `/clawd` 命令
- 调用 `clawdbot_plugin` 的 `clawd_command` 方法

### 3. 插件处理
```python
# 提取消息内容
user_message = "你好"
user_id = "123456789"
group_id = "987654321"

# 构造 OpenResponses API 请求
payload = {
    "model": "clawdbot:main",
    "input": "你好",
    "user": "qq_987654321",  # 用于会话持久化
    "stream": false
}
```

### 4. 发送到 Clawdbot Gateway
```http
POST http://127.0.0.1:18789/v1/responses
Authorization: Bearer <CLAWDBOT_TOKEN>
Content-Type: application/json
x-clawdbot-agent-id: main

{
  "model": "clawdbot:main",
  "input": "你好",
  "user": "qq_987654321",
  "stream": false
}
```

### 5. Clawdbot 处理
- Gateway 验证 Token
- 路由到 `main` agent
- Agent 使用会话 ID `qq_987654321` 查找或创建会话
- 将消息发送给 AI 模型
- 获取 AI 回复

### 6. 响应返回
```json
{
  "id": "resp_xxx",
  "status": "completed",
  "output": [
    {
      "type": "message",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "你好！我是 Clawdbot..."
        }
      ]
    }
  ]
}
```

### 7. 插件解析响应
```python
# 提取文本内容
reply = "你好！我是 Clawdbot..."
```

### 8. 发送回 QQ
```python
await event.reply(f"🤖 Clawdbot 回复:\n{reply}")
```

### 9. 用户收到回复
```
机器人: 🤖 Clawdbot 回复:
你好！我是 Clawdbot...
```

## 🔐 安全性

### 认证
- 使用 Bearer Token 认证
- Token 存储在插件代码中（仅本地访问）
- Gateway 绑定到 loopback (127.0.0.1)，仅本地可访问

### 会话隔离
- 每个 QQ 群/用户有独立的会话 ID
- 格式：`qq_<群号>` 或 `qq_<用户QQ号>`
- 不同群/用户的对话互不干扰

### 数据隐私
- 消息仅在本地服务器之间传输
- 不经过外部服务器（除了 AI 模型 API）
- 符合 Clawdbot 的隐私政策

## ⚙️ 技术细节

### 异步处理
```python
# 插件使用 asyncio 和 aiohttp
async def send_to_clawdbot(self, message: str, ...):
    async with self.session.post(url, json=payload) as response:
        result = await response.json()
        return reply
```

- 不会阻塞 catbot 的其他功能
- 多个请求可以并发处理
- 超时保护（默认 60 秒）

### 会话持久化
- 使用 OpenResponses API 的 `user` 字段
- Clawdbot Gateway 自动管理会话
- 对话历史保存在 Clawdbot 的会话存储中

### 错误处理
```python
try:
    reply = await self.send_to_clawdbot(message, user_id, group_id)
    if reply:
        await event.reply(f"🤖 Clawdbot 回复:\n{reply}")
    else:
        await event.reply("❌ 无法连接到 Clawdbot 或获取回复失败")
except Exception as e:
    logger.error(f"错误: {e}")
```

## 📊 性能考虑

### 响应时间
- 网络延迟：< 10ms (本地)
- Clawdbot 处理：3-10 秒（取决于 AI 模型）
- 总响应时间：约 3-10 秒

### 资源消耗
- **内存**：aiohttp session 约 1-2MB
- **CPU**：几乎无消耗（等待 I/O）
- **网络**：仅本地回环，无带宽限制

### Token 消耗
- 每次对话消耗 AI 模型 token
- 包含系统提示 + 对话历史 + 当前消息
- 建议监控 Clawdbot 的 token 使用情况

## 🔧 配置文件

### Clawdbot Gateway 配置
位置：`/path/to/.clawdbot/clawdbot.json`

关键配置：
```json
{
  "gateway": {
    "port": 18789,
    "auth": {
      "mode": "token",
      "token": "<CLAWDBOT_TOKEN>"
    },
    "http": {
      "endpoints": {
        "responses": {
          "enabled": true
        }
      }
    }
  }
}
```

### 插件配置
位置：`/path/to/Documents/ncatbot/main/plugins/clawdbot_plugin/clawdbot_plugin.py`

关键常量：
```python
CLAWDBOT_GATEWAY_URL = "http://127.0.0.1:18789"
CLAWDBOT_TOKEN = "<CLAWDBOT_TOKEN>"
```

## 🚀 扩展可能性

### 1. 自动转发所有消息
可以添加一个消息监听器，自动将所有消息发送给 Clawdbot：

```python
@bot.on_group_message()
async def auto_forward(event: GroupMessage):
    # 过滤条件（例如：只转发特定群）
    if event.group_id in [123456]:
        reply = await self.send_to_clawdbot(event.raw_message, ...)
        if reply:
            await event.reply(reply)
```

**注意**：这会大量消耗 token，请谨慎使用。

### 2. 多 Agent 支持
可以添加命令来切换不同的 agent：

```python
@command_registry.command("clawdagent")
async def switch_agent(self, event: BaseMessageEvent):
    # /clawdagent beta
    agent_id = event.raw_message.split()[1]
    # 更新配置...
```

### 3. 流式响应
可以启用流式响应，实时显示 Clawdbot 的回复：

```python
payload = {
    "model": "clawdbot:main",
    "input": message,
    "stream": true  # 启用流式
}

# 处理 SSE 事件
async for line in response.content:
    # 解析并实时发送...
```

### 4. 工具调用
可以让 Clawdbot 调用 catbot 的功能（例如查询 EVE 数据）：

```python
# 在请求中添加工具定义
payload = {
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "query_eve_price",
                "description": "查询 EVE 物品价格",
                "parameters": {...}
            }
        }
    ]
}
```

## 📚 相关文档

- [Clawdbot 官方文档](https://docs.clawd.bot)
- [OpenResponses API 文档](https://docs.clawd.bot/gateway/openresponses-http-api)
- [catbot 插件系统文档](../../../README.md)

## 🎯 总结

这个集成实现了：
- ✅ QQ 机器人与 Clawdbot 的双向通信
- ✅ 异步处理，不阻塞其他功能
- ✅ 会话持久化，保持对话上下文
- ✅ 安全的本地通信
- ✅ 简单易用的命令接口

现在你的 QQ 机器人拥有了 Clawdbot 的全部能力！🎉
