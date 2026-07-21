# Telegram OpenAI 聊天机器人

一个接入 OpenAI API 的 Telegram 智能聊天机器人，用来练习 Python + AI API 调用 + 异步编程。

## 第一步：拿到两个必需的密钥

### 1. Telegram Bot Token
1. 在 Telegram 里搜索 `@BotFather`
2. 发送 `/newbot`，按提示起个名字（比如 `MyOpenAIBot`）
3. 完成后 BotFather 会给你一串 token，形如 `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
4. 复制保存好

### 2. OpenAI API Key
1. 打开 https://platform.openai.com/
2. 注册/登录后，进入 API Keys 页面
3. 创建一个新的 key，复制保存好（注意：这个 key 只会完整显示一次）

## 第二步：本地环境配置

```bash
# 进入项目目录
cd tg-claude-bot

# 建议用虚拟环境，避免和其他项目的依赖冲突
python3 -m venv venv
source venv/bin/activate   # Windows 用: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置密钥
cp .env.example .env
# 然后用编辑器打开 .env，把两个密钥填进去
```

## 第三步：运行

```bash
python bot.py
```

看到日志输出 "机器人启动中..." 就说明启动成功了。这时候去 Telegram 找到你的机器人，发送 `/start` 试试。

## 代码结构讲解（建议对照 bot.py 逐段看）

1. **初始化配置**：读取 .env 里的密钥，创建 OpenAI 客户端
2. **对话历史存储**：用一个字典 `{用户ID: [消息列表]}` 给每个用户维护独立的聊天记录
3. **命令处理**：`/start`（欢迎语）、`/reset`（清空历史）
4. **核心消息处理**：收到消息 → 存入历史 → 调用 OpenAI API → 把回复发回去
5. **启动**：注册所有 handler，开始轮询 Telegram 服务器

## 常见问题

- **机器人不回复**：检查 `.env` 里的 token 是否正确，看终端日志有没有报错
- **报 "Invalid API Key"**：OpenAI API Key 填错了，或者账户没有可用额度
- **想换成流式回复（打字机效果）**：可以研究 OpenAI SDK 的流式接口，这是进阶练习
- **想让机器人重启后还记得历史**：需要把内存字典换成 SQLite 或其他数据库，这也是很好的下一步练习

## 建议的下一步练习

1. 给 `/reset` 加一个确认步骤
2. 把对话历史持久化到 SQLite 数据库
3. 加一个 `/model` 命令，让用户可以切换不同的 OpenAI 模型
4. 研究流式输出，让回复像打字一样逐字出现
5. 加异常处理的边界情况：比如用户发图片、发很长的消息时怎么办
