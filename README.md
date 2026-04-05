# ICNPS：智能校园通知推送系统

**ICNPS (Intelligent Campus Notification Push System)** 是一款专为大学生设计的个人信息过滤中枢。它能自动巡查分散的校园官网通知（如教务处、学院官网、OA 系统），利用大语言模型 (LLM) 进行智能摘要与个性化语义打分，确保你不会错过任何高价值的科研、竞赛或奖学金机会。

## 🌟 核心特性

- **🤖 双阶段智能处理**：先由 LLM 生成 100 字精炼摘要，再基于你的“个人画像”进行 1-5 分的相关度打分，精准过滤噪音。
- **🔌 灵活的模型接入**：默认支持调用兼容 OpenAI 格式的在线大模型 API（如 DeepSeek、OpenRouter、智谱等），同时也保留了对本地离线模型（Ollama）的代码支持。
- **⚙️ 自动化无感运行**：支持 Windows 开机静默启动，每日自动延迟运行一次，实现真正的“无感”邮件推送。
- **🛠️ 极简配置化管理**：通过 `config.json` 轻松管理多个抓取站点的 CSS 选择器，无需改动核心代码。
- **🧹 自动清理防膨胀**：历史记录滚动截断机制，始终保留最新的 500 条记录，防止日志文件无限膨胀。

## 📂 项目结构

```
ICNPS/
├── main.py                # 程序入口：控制延迟逻辑、运行锁及全流程
├── config.json            # 核心配置：存放站点选择器、SMTP 账号及 LLM 参数 (建议通过模板复制)
├── requirements.txt       # Python 依赖清单
├── icnps.bat              # Windows 执行脚本
├── run_hidden.vbs         # VBS 静默运行脚本 (防止黑窗口弹出)
├── data/
│   ├── user_profile.txt   # 你的个人画像提示词 (Prompt，建议通过模板复制)
│   └── history_links.log  # URL 去重数据库 (自动生成)
├── modules/
│   ├── scraper.py         # 增量爬虫模块
│   ├── llm_processor.py   # LLM 处理逻辑（摘要与打分）
│   └── mailer.py          # 邮件格式化与发送
└── utils/                 # 文本清洗与文件管理工具
```

## 🚀 快速开始

### 1. 环境安装

请确保你的电脑已安装 Python 3.8+，然后在项目根目录下运行：

```
pip install -r requirements.txt
```

### 2. 个性化配置

建议在本地进行如下操作：

1. **配置信息**：编辑 `config.json`，填入你的姓名（或者希望大模型对你的称呼）、大模型 API 参数（`api_base` 和 `api_key`）、邮箱、邮箱 SMTP 授权码以及目标网站的 CSS 选择器等。
2. **个人画像**：编辑 `data/user_profile.txt`，详细描述你的专业、兴趣和未来规划。形式自由，让 LLM 能够充分了解你的偏好。

### 3. Windows 开机自启部署

为了让系统每天默默为你工作，请执行以下操作：

1. **修改路径**：

   - 打开 `icnps.bat`，将 `cd /d` 后的路径和 `pythonw.exe` 的路径改为你电脑上的真实**绝对路径**。
   - 打开 `run_hidden.vbs`，将里面指向 `.bat` 文件的路径也改为**绝对路径**。

2. **⚠️ 编码要求**：

   - **`run_hidden.vbs` 若有中文路径，必须以 ANSI / GBK 编码保存**（在记事本/ VS Code中另存为时选择），否则中文路径会导致脚本报错。
   - 修改 `config.json` 和 `data/user_profile.txt` 时，请务必以 **UTF-8 编码**保存。

3. **放入启动文件夹**：

   - 将 `run_hidden.vbs` 的快捷方式放入以下 Windows 启动文件夹：

     `C:\Users\你的用户名\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`

------

## 💡 进阶指南：切换至本地离线模型 (Ollama)

如果你希望实现 **100% 的数据隐私保护**，不想将校园通知和个人画像发送给任何云端 API，可以切换回使用本地的 Ollama 模型。

### 1. 准备本地模型

下载并安装 [Ollama](https://ollama.com/)，在终端中拉取你想要的轻量级模型（例如：`ollama run gemma` 或 `ollama run qwen`）。

### 2. 修改 `config.json`

将 `api_base` 修改为 Ollama 的默认本地接口：`http://localhost:11434/api/generate`，并将 `model_name` 改为你下载的模型名称。

### 3. 修改代码 `modules/llm_processor.py`

打开 `modules/llm_processor.py` 的 `_call_llm` 函数：

- **注释掉** 下半部分的“调用在线 LLM API (OpenAI 兼容格式)”的代码块。
- **取消注释** 上半部分的“封装 Ollama API 调用”的代码块。

------

## 📝 开源协议

本项目采用 MIT 协议开源。欢迎根据自己学校的通知系统进行二次开发。如果你觉得好用，不妨点个 ⭐ Star！

------

## ⚠️ 免责声明

1. **合规使用**：本项目仅供学习与技术交流使用。在启用内网抓取和调用云端大模型 API 时，请务必遵守您所在学校的校园网与数据安全管理规定。
2. **数据安全**：切勿将涉密、敏感的内部通知或个人隐私数据通过公网 API 处理。如对数据隐私有较高要求，强烈建议按照文档使用本地离线模型（如 Ollama）。
3. **责任限制**：因不当使用本系统（如高频抓取导致 IP 被封、敏感信息泄露等）造成的任何后果及责任由使用者自行承担，原作者不承担任何连带责任。
