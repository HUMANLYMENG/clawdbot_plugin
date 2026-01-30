#!/usr/bin/env python3
"""
Clawdbot 插件独立测试脚本
用于测试与 Clawdbot Gateway 的通信，不依赖 catbot 系统
"""

import asyncio
import aiohttp
import json
import os
import sys

# Clawdbot Gateway 配置
CLAWDBOT_GATEWAY_URL = os.getenv("CLAWDBOT_GATEWAY_URL", "http://127.0.0.1:18789")
CLAWDBOT_TOKEN = os.getenv("CLAWDBOT_TOKEN", "")


async def test_connection():
    """测试基本连接"""
    print("=" * 60)
    print("测试 1: 基本连接测试")
    print("=" * 60)
    
    url = f"{CLAWDBOT_GATEWAY_URL}/v1/responses"
    
    headers = {
        "Authorization": f"Bearer {CLAWDBOT_TOKEN}",
        "Content-Type": "application/json",
        "x-clawdbot-agent-id": "main"
    }
    
    payload = {
        "model": "clawdbot:main",
        "input": "Hello, this is a test message. Please reply with 'OK'.",
        "stream": False
    }
    
    print(f"\n📡 发送请求到: {url}")
    print(f"📝 消息: {payload['input']}")
    print(f"⏱️  超时: 60 秒")
    print("\n等待响应...\n")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, 
                json=payload, 
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                print(f"✅ HTTP 状态码: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    
                    # 打印完整响应（用于调试）
                    print("\n📦 完整响应:")
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                    
                    # 解析响应
                    output_items = result.get("output", [])
                    
                    print("\n" + "=" * 60)
                    print("📨 提取的回复内容:")
                    print("=" * 60)
                    
                    for item in output_items:
                        if item.get("type") == "message":
                            content = item.get("content", [])
                            for part in content:
                                # OpenResponses API 返回的类型是 "output_text"
                                if part.get("type") in ["output_text", "text"]:
                                    text = part.get("text", "")
                                    print(f"\n{text}\n")
                    
                    # Token 使用情况
                    usage = result.get("usage", {})
                    if usage:
                        print("=" * 60)
                        print("📊 Token 使用情况:")
                        print("=" * 60)
                        print(f"输入 tokens: {usage.get('input_tokens', 0)}")
                        print(f"输出 tokens: {usage.get('output_tokens', 0)}")
                        print(f"总计 tokens: {usage.get('total_tokens', 0)}")
                    
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 错误: HTTP {response.status}")
                    print(f"错误内容: {error_text}")
                    return False
                    
    except asyncio.TimeoutError:
        print("❌ 请求超时（60秒）")
        return False
    except aiohttp.ClientError as e:
        print(f"❌ 网络错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_conversation():
    """测试对话功能"""
    print("\n\n" + "=" * 60)
    print("测试 2: 对话测试")
    print("=" * 60)
    
    url = f"{CLAWDBOT_GATEWAY_URL}/v1/responses"
    
    headers = {
        "Authorization": f"Bearer {CLAWDBOT_TOKEN}",
        "Content-Type": "application/json",
        "x-clawdbot-agent-id": "main"
    }
    
    # 测试对话序列
    messages = [
        "你好，我的名字是测试用户",
        "你还记得我的名字吗？",
        "请用一句话介绍你自己"
    ]
    
    session_id = "test_session_001"
    
    async with aiohttp.ClientSession() as session:
        for i, message in enumerate(messages, 1):
            print(f"\n--- 对话 {i} ---")
            print(f"👤 用户: {message}")
            
            payload = {
                "model": "clawdbot:main",
                "input": message,
                "user": session_id,  # 使用相同的 session_id 保持上下文
                "stream": False
            }
            
            try:
                async with session.post(
                    url, 
                    json=payload, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        output_items = result.get("output", [])
                        
                        reply_parts = []
                        for item in output_items:
                            if item.get("type") == "message":
                                content = item.get("content", [])
                                for part in content:
                                    # OpenResponses API 返回的类型是 "output_text"
                                    if part.get("type") in ["output_text", "text"]:
                                        reply_parts.append(part.get("text", ""))
                        
                        reply = "\n".join(reply_parts) if reply_parts else "（无回复）"
                        print(f"🤖 Clawdbot: {reply}")
                    else:
                        error_text = await response.text()
                        print(f"❌ 错误: HTTP {response.status} - {error_text}")
                        return False
                        
            except Exception as e:
                print(f"❌ 错误: {e}")
                return False
            
            # 等待一下再发送下一条消息
            if i < len(messages):
                await asyncio.sleep(1)
    
    return True


async def test_chinese():
    """测试中文支持"""
    print("\n\n" + "=" * 60)
    print("测试 3: 中文支持测试")
    print("=" * 60)
    
    url = f"{CLAWDBOT_GATEWAY_URL}/v1/responses"
    
    headers = {
        "Authorization": f"Bearer {CLAWDBOT_TOKEN}",
        "Content-Type": "application/json",
        "x-clawdbot-agent-id": "main"
    }
    
    payload = {
        "model": "clawdbot:main",
        "input": "请用中文回答：什么是人工智能？请简短回答。",
        "stream": False
    }
    
    print(f"\n📝 测试消息: {payload['input']}")
    print("\n等待响应...\n")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, 
                json=payload, 
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    output_items = result.get("output", [])
                    
                    for item in output_items:
                        if item.get("type") == "message":
                            content = item.get("content", [])
                            for part in content:
                                # OpenResponses API 返回的类型是 "output_text"
                                if part.get("type") in ["output_text", "text"]:
                                    text = part.get("text", "")
                                    print(f"🤖 回复:\n{text}\n")
                    
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ 错误: HTTP {response.status} - {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


async def main():
    """主测试函数"""
    if not CLAWDBOT_TOKEN:
        print("❌ 未设置 CLAWDBOT_TOKEN 环境变量，无法进行测试。")
        print("请先设置：export CLAWDBOT_TOKEN=\"<your_token>\"")
        return 1

    print("\n" + "🚀" * 30)
    print("Clawdbot 插件独立测试")
    print("🚀" * 30 + "\n")
    
    print(f"Gateway URL: {CLAWDBOT_GATEWAY_URL}")
    print(f"Token: {CLAWDBOT_TOKEN[:20]}...")
    print()
    
    # 运行所有测试
    tests = [
        ("基本连接", test_connection),
        ("对话功能", test_conversation),
        ("中文支持", test_chinese),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ 测试 '{test_name}' 发生异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # 打印测试总结
    print("\n\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！Clawdbot 集成工作正常。")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查配置和日志。")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试脚本发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
