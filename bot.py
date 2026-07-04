"""
一个基于 Telegram 的 Claude AI 聊天机器人。

工作流程：
1. 用户在 Telegram 里发消息给机器人
2. python-telegram-bot 库收到消息，触发我们写的 handler 函数
3. handler 把消息转发给 Claude API
4. 拿到 Claude 的回复后，发回给用户

学习重点：
- 异步编程（async/await）：Telegram 库是异步的，因为要同时处理很多用户的消息
- 环境变量管理：API Key 这类敏感信息不能写死在代码里
- 字典（dict）的使用：给每个用户维护独立的对话历史
"""

import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from anthropic import Anthropic

# ---------- 1. 初始化配置 ----------

# 从 .env 文件加载环境变量（Bot Token、API Key）
load_dotenv(override=True)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "gpt-5.5")

if not TELEGRAM_BOT_TOKEN or not ANTHROPIC_API_KEY:
    raise ValueError(
        "请先在 .env 文件里配置 TELEGRAM_BOT_TOKEN 和 ANTHROPIC_API_KEY，"
        "可以参考 .env.example"
    )

# 打印日志，方便调试（能看到机器人收到了什么、报了什么错）
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Claude API 客户端
claude_kwargs = {"api_key": ANTHROPIC_API_KEY}
if ANTHROPIC_BASE_URL:
    claude_kwargs["base_url"] = ANTHROPIC_BASE_URL
claude = Anthropic(**claude_kwargs)

# 系统提示词：定义机器人的"人设"和行为
SYSTEM_PROMPT = "你是一个友好、简洁的 Telegram 聊天助手，用中文回复。回答尽量简短，适合手机阅读。"

# ---------- 2. 对话历史存储 ----------

# key 是 Telegram 用户 ID，value 是这个用户的对话历史（列表）
# 用内存字典存储：优点是简单，缺点是机器人重启后历史会丢失
# 后续想持久化，可以换成数据库（比如 SQLite）
conversation_history: dict[int, list[dict]] = {}

# 每个用户最多保留多少轮对话，避免历史无限增长、消耗过多 token
MAX_HISTORY_MESSAGES = 20


def get_history(user_id: int) -> list[dict]:
    """获取某个用户的对话历史，如果没有则初始化为空列表"""
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    return conversation_history[user_id]


def trim_history(user_id: int) -> None:
    """裁剪历史，只保留最近 N 条，防止无限增长"""
    history = conversation_history[user_id]
    if len(history) > MAX_HISTORY_MESSAGES:
        conversation_history[user_id] = history[-MAX_HISTORY_MESSAGES:]


# ---------- 3. Telegram 命令处理 ----------


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 /start 命令：用户第一次打开机器人时触发"""
    await update.message.reply_text(
        "你好！我是接入了 Claude 的聊天机器人 🤖\n"
        "直接给我发消息就能聊天。\n"
        "发送 /reset 可以清空对话历史，重新开始。"
    )


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 /reset 命令：清空当前用户的对话历史"""
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    await update.message.reply_text("对话历史已清空，我们重新开始吧！")


# ---------- 4. 核心：处理普通消息 ----------


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    处理用户发来的普通文本消息：
    1. 把消息加入这个用户的历史
    2. 调用 Claude API，把历史一起传过去（这样它才有"记忆"）
    3. 把回复发回 Telegram，同时存入历史
    """
    user_id = update.effective_user.id
    user_message = update.message.text

    logger.info(f"收到用户 {user_id} 的消息: {user_message}")

    history = get_history(user_id)
    history.append({"role": "user", "content": user_message})

    # 给用户一个"正在输入"的反馈，体验更好
    await update.message.chat.send_action(action="typing")

    try:
        response = claude.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=history,
        )
        reply_text = response.content[0].text
    except Exception as e:
        logger.error(f"调用 Claude API 出错: {e}")
        reply_text = "抱歉，我这边出了点问题，请稍后再试～"
        await update.message.reply_text(reply_text)
        return

    # 把机器人的回复也存入历史，下一轮对话才能带上下文
    history.append({"role": "assistant", "content": reply_text})
    trim_history(user_id)

    await update.message.reply_text(reply_text)


# ---------- 5. 启动机器人 ----------


def main() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # 注册命令处理器
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("reset", reset_command))

    # 注册普通文本消息处理器（排除命令）
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("机器人启动中...")
    app.run_polling()  # 持续轮询 Telegram 服务器，获取新消息


if __name__ == "__main__":
    main()
