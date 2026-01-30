import logging
import os
import asyncio
import aiohttp
from typing import Optional

from ncatbot.plugin_system import NcatBotPlugin
from ncatbot.plugin_system import command_registry
from ncatbot.plugin_system import filter_registry
from ncatbot.core.event import BaseMessageEvent

# 初始化日志
logger = logging.getLogger("clawdbot_plugin")

# Clawdbot Gateway 配置
CLAWDBOT_GATEWAY_URL = os.getenv("CLAWDBOT_GATEWAY_URL", "http://127.0.0.1:18789")
CLAWDBOT_TOKEN = os.getenv("CLAWDBOT_TOKEN")

# 权限配置：可选，仅允许特定用户的私聊
ALLOWED_PRIVATE_USER_ID = os.getenv("CLAWDBOT_ALLOWED_PRIVATE_USER_ID")


class clawdbot_plugin(NcatBotPlugin):
    """
    Clawdbot 集成插件
    可选限制特定用户的私聊（通过环境变量配置）
    """

    name = "clawdbot_plugin"
    version = "1.1.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session: Optional[aiohttp.ClientSession] = None
        self._tasks: set[asyncio.Task] = set()

    async def on_load(self):
        """插件加载时执行"""
        logger.info(f"{self.name} v{self.version} 正在加载...")

        # 不在这里创建 session，而是在需要时创建
        if not CLAWDBOT_TOKEN:
            logger.warning("CLAWDBOT_TOKEN 未配置，插件将无法请求 Clawdbot。")
        if ALLOWED_PRIVATE_USER_ID:
            logger.info(f"Clawdbot 插件已加载，仅支持用户 {ALLOWED_PRIVATE_USER_ID} 的私聊")
        else:
            logger.info("Clawdbot 插件已加载，允许所有私聊用户访问")

    async def on_unload(self):
        """插件卸载时执行"""
        if self._tasks:
            for task in list(self._tasks):
                task.cancel()
            await asyncio.gather(*self._tasks, return_exceptions=True)
            self._tasks.clear()
        if self.session and not self.session.closed:
            await self.session.close()
        logger.info("Clawdbot 插件已卸载")

    def _spawn_task(self, coro, task_name: str) -> None:
        task = asyncio.create_task(coro, name=task_name)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    def check_permission(self, event: BaseMessageEvent) -> bool:
        """
        检查权限：可选限制特定用户的私聊
        
        :param event: 消息事件
        :return: True 如果有权限，False 否则
        """
        if not hasattr(event, "message_type"):
            logger.warning("事件没有 message_type 属性")
            return False

        if event.message_type != "private":
            logger.debug(f"拒绝非私聊消息: {event.message_type}")
            return False

        user_id = str(event.user_id)
        if ALLOWED_PRIVATE_USER_ID and user_id != ALLOWED_PRIVATE_USER_ID:
            logger.warning(f"拒绝未授权用户: {user_id}")
            return False

        return True

    async def send_to_clawdbot(
        self, message: str, user_id: str, session_id: Optional[str] = None
    ) -> Optional[str]:
        """
        发送消息到 Clawdbot Gateway

        :param message: 要发送的消息内容
        :param user_id: 用户 ID
        :param session_id: 会话 ID（可选，用于新建会话）
        :return: Clawdbot 的回复，如果失败则返回 None
        """
        # 使用 OpenResponses API 端点
        url = f"{CLAWDBOT_GATEWAY_URL}/v1/responses"

        # 构造 OpenResponses 格式的请求
        payload = {
            "model": "clawdbot:main",
            "input": message,
            "user": session_id or f"qq_{user_id}",  # 会话持久化
            "stream": False,
        }

        if not CLAWDBOT_TOKEN:
            logger.error("CLAWDBOT_TOKEN 未设置，无法访问 Clawdbot。")
            return None

        # 添加自定义 header
        headers = {
            "Authorization": f"Bearer {CLAWDBOT_TOKEN}",
            "Content-Type": "application/json",
            "x-clawdbot-agent-id": "main",
        }

        logger.info(f"发送消息到 Clawdbot: {message[:50]}...")

        try:
            # 每次请求创建新的 session，避免事件循环关闭问题
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status == 200:
                        result = await response.json()

                        # 解析 OpenResponses 格式的响应
                        output_items = result.get("output", [])

                        # 提取文本内容
                        reply_parts = []
                        for item in output_items:
                            if item.get("type") == "message":
                                content = item.get("content", [])
                                for part in content:
                                    if part.get("type") in ["output_text", "text"]:
                                        reply_parts.append(part.get("text", ""))

                        reply = "\n".join(reply_parts) if reply_parts else "（无回复内容）"
                        logger.info(f"收到 Clawdbot 回复: {reply[:50]}...")
                        return reply
                    else:
                        error_text = await response.text()
                        logger.error(f"Clawdbot API 返回错误 {response.status}: {error_text}")
                        return None

        except asyncio.TimeoutError:
            logger.error("请求 Clawdbot 超时")
            return None
        except Exception as e:
            logger.error(f"发送消息到 Clawdbot 时出错: {e}", exc_info=True)
            return None

    async def clawd_command(self, event: BaseMessageEvent):
        """
        /clawd 命令：与 Clawdbot 对话
        用法: /clawd <消息内容>
        仅支持特定用户的私聊
        """
        # 权限检查
        if not self.check_permission(event):
            await event.reply("❌ Who are you?")
            return  # 静默拒绝，不回复

        msg = event.raw_message.strip()
        parts = msg.split(maxsplit=1)

        if len(parts) < 2:
            await event.reply("❌ 用法: /clawd <消息内容>\n示例: /clawd 你好，请帮我查询天气")
            return

        user_message = parts[1]
        user_id = str(event.user_id)

        # 发送"正在思考"的提示
        await event.reply("🤔 正在向 Clawdbot 发送消息...")

        self._spawn_task(
            self._handle_clawd_request(event, user_message, user_id),
            f"clawdbot:clawd:{user_id}",
        )

    @filter_registry.private_filter
    async def on_private_message(self, event: BaseMessageEvent):
        """私聊过滤：手动处理 /clawd，避免命令参数解析失败"""
        msg = (event.raw_message or "").strip()
        if not msg:
            return

        if msg == "/clawd" or msg.startswith("/clawd "):
            await self.clawd_command(event)
            return

        if msg == "/clwad" or msg.startswith("/clwad "):
            await self.clawd_command(event)

    @command_registry.command("clawdtest")
    async def test_connection(self, event: BaseMessageEvent):
        """
        测试与 Clawdbot 的连接
        用法: /clawdtest
        仅支持特定用户的私聊
        """
        # 权限检查
        if not self.check_permission(event):
            return  # 静默拒绝，不回复

        await event.reply("🔍 正在测试 Clawdbot 连接...")

        user_id = str(event.user_id)

        self._spawn_task(
            self._handle_test_connection(event, user_id),
            f"clawdbot:clawdtest:{user_id}",
        )

    @command_registry.command("clawdnew")
    async def new_session(self, event: BaseMessageEvent):
        """
        创建新的 Clawdbot 会话（清除当前上下文）
        用法: /clawdnew
        仅支持特定用户的私聊
        """
        # 权限检查
        if not self.check_permission(event):
            return  # 静默拒绝，不回复

        user_id = str(event.user_id)

        # 生成新的 session ID（添加时间戳）
        import time
        new_session_id = f"qq_{user_id}_{int(time.time())}"

        await event.reply("🔄 正在创建新会话...")

        self._spawn_task(
            self._handle_new_session(event, user_id, new_session_id),
            f"clawdbot:clawdnew:{user_id}",
        )

    async def _handle_clawd_request(
        self, event: BaseMessageEvent, user_message: str, user_id: str
    ) -> None:
        try:
            reply = await self.send_to_clawdbot(user_message, user_id)
            if reply:
                await event.reply(f"🤖 Clawdbot 回复:\n{reply}")
            else:
                await event.reply("❌ 无法连接到 Clawdbot 或获取回复失败")
        except Exception as e:
            logger.error(f"处理 /clawd 请求时出错: {e}", exc_info=True)
            try:
                await event.reply("❌ 处理请求时发生错误，请稍后重试")
            except Exception:
                pass

    async def _handle_test_connection(
        self, event: BaseMessageEvent, user_id: str
    ) -> None:
        try:
            reply = await self.send_to_clawdbot(
                "Hello, this is a test message from QQ bot", user_id
            )
            if reply:
                await event.reply(f"✅ 连接成功！\n回复: {reply}")
            else:
                await event.reply("❌ 连接失败，请检查 Clawdbot Gateway 是否运行")
        except Exception as e:
            logger.error(f"测试连接时出错: {e}", exc_info=True)
            try:
                await event.reply("❌ 测试连接时发生错误，请稍后重试")
            except Exception:
                pass

    async def _handle_new_session(
        self, event: BaseMessageEvent, user_id: str, new_session_id: str
    ) -> None:
        try:
            reply = await self.send_to_clawdbot(
                "新会话已创建。请简短确认。", user_id, new_session_id
            )
            if reply:
                await event.reply(
                    f"✅ 已创建新的 Clawdbot 会话\n"
                    f"🆔 Session ID: {new_session_id}\n\n"
                    f"{reply}"
                )
                logger.info(f"创建新会话: {new_session_id}")
            else:
                await event.reply("❌ 创建新会话失败，请稍后重试")
        except Exception as e:
            logger.error(f"创建新会话时出错: {e}", exc_info=True)
            try:
                await event.reply("❌ 创建新会话时发生错误，请稍后重试")
            except Exception:
                pass
