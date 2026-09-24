# Agent Switchboard

Agent Switchboard 是一个本地 Codex 插件。它提供设置面板和对话工具，用来选择模型、推理强度、速度、上下文窗口和自动压缩阈值。

插件只编辑 Codex 的官方 TOML 配置，不另存一份模型或项目设置。

## 功能

- 全局设置写入 CODEX_HOME/config.toml；项目设置写入项目的 .codex/config.toml。
- 主 Agent 和默认子 Agent 使用 Codex 提供的配置项。
- 命名角色通过 agents.<name>.config_file 引用角色 TOML。
- 可在命名角色管理器中查看、编辑和删除项目角色与全局角色。
- 模型选项、推理档位和上下文上限从本机 Codex CLI 的模型目录读取，并随当前 Codex 版本更新。
- 插件操作日志保存在 CODEX_HOME/logs/agent-switchboard.jsonl。列表显示操作状态和耗时；展开详情可查看写入路径、修改字段和值。日志只记录插件管理的 Codex 配置项。
- 面板启动时先读取主配置；角色文件只在打开“已有角色”或编辑命名角色时读取。模型目录在插件进程内缓存 5 分钟，点“刷新模型目录”会立即重新读取本机 Codex CLI。
- 自动压缩阈值按 Codex 默认值建议为上下文窗口的 90%，用户仍可手动调整。
- TOML 更新保留现有注释和无关字段，并用原子替换写入文件。
- validate_config 和 diff_config 可在写入前检查模型能力和变更内容。

## 安装依赖与构建面板

需要 Python 3.11 或更新版本、uv、Node.js 20 或更新版本。

在插件目录运行：

    uv sync
    npm install
    npm run build:ui

Codex 从 .mcp.json 启动本地 MCP 服务。服务通过标准输入输出与 Codex 通信。

## 在 Codex 中安装

1. 在构建面板后，把整个 agent-switchboard 文件夹复制到个人插件源目录：

       %USERPROFILE%\.codex\plugins\agent-switchboard

2. 在 %USERPROFILE%\.agents\plugins\marketplace.json 的 plugins 数组中添加以下条目。保留文件里已有的市场名称和其他插件条目：

       {
         "name": "agent-switchboard",
         "source": {
           "source": "local",
           "path": "./.codex/plugins/agent-switchboard"
         },
         "policy": {
           "installation": "AVAILABLE",
           "authentication": "ON_INSTALL"
         },
         "category": "Productivity"
       }

3. 在 Codex 的 Plugins Directory 中打开 personal 市场并安装 Agent Switchboard。

安装后，在新任务中选择 Agent Switchboard，或直接提出配置要求，例如：

- 打开 Agent Switchboard，查看当前项目的子 Agent 配置。
- 当前项目的默认子 Agent 使用 GPT-6 Luna、high reasoning、Fast、500000 context 和 440000 compact。
- 全局 Reviewer 使用 GPT-6 Sol 和 high reasoning，保留其他配置。
- 清除这个项目的 Worker 模型覆盖。

在项目聊天中打开面板会默认进入当前项目，并选中“默认子 Agent”；项目绝对路径由插件技能传入，也可改成其他项目路径。粘贴带双引号的 Windows 路径也能识别。没有当前项目时会进入全局作用域。

面板先展示作用范围、Agent 类型、配置文件、修改前后值和注意事项；确认后才写入 TOML。主 Agent 的模型、推理强度和速度请在聊天框右下角的模型选择器中修改，面板仍可管理它的上下文和自动压缩阈值。

项目作用域写入项目的 `.codex/config.toml`。Codex 只会读取受信任项目中的项目配置。

## 在 ChatGPT 中连接

ChatGPT 云端不能直接访问本机文件。要让 ChatGPT 管理本机 Codex 配置，需要用官方 Secure MCP Tunnel 连接本地 MCP 服务，再在 ChatGPT Developer Mode 中注册该 tunnel endpoint。连接成功后，使用新连接返回的 plugin_asdk_app ID 更新 .app.json。

此项目尚未连接到 ChatGPT 账号，也没有部署公网 MCP 服务。Secure MCP Tunnel 用于本地开发连接；公开发布还需要稳定的 HTTPS MCP endpoint。

## 作用域和生效时机

| 作用域 | 保存位置 | 说明 |
| --- | --- | --- |
| 全局 | CODEX_HOME/config.toml | 用户级默认值，项目配置和命令行参数可以覆盖它 |
| 项目 | 项目/.codex/config.toml | 只为这个项目设置覆盖值；项目需要受信任 |

模型、推理强度和 service_tier 会写入配置，供后续请求读取。Codex 在新 Agent 启动时读取上下文和压缩阈值。

Codex 为默认子 Agent 单独提供 model 和 reasoning effort 设置。service_tier、model_context_window 和 model_auto_compact_token_limit 是同一层的通用配置，可能影响继承这些值的主 Agent 和其他子 Agent。命名角色的设置则写入该角色的 config_file。

选择“命名角色”后，可打开角色列表查看项目和全局角色。编辑会载入该角色的现有值，并继续使用预览和确认流程；删除前会显示确认窗口。删除角色定义时，默认角色文件会一并删除；自定义路径或被其他角色共用的文件会保留。

service_tier=fast 会请求 Fast。选择“标准”会移除此层的 Fast 覆盖；如果其他适用层仍设置了 Fast，Codex 可能继续使用 Fast。

## MCP 工具

| 工具 | 用途 |
| --- | --- |
| get_resolved_config | 查看已管理设置在全局、profile、项目和角色层中的值 |
| get_model_catalog | 获取模型、reasoning effort、上下文范围和速度档位 |
| set_global_config | 修改 CODEX_HOME/config.toml |
| set_project_config | 修改项目 .codex/config.toml |
| set_agent_role | 更新 agents.<name>.config_file 和对应角色 TOML |
| validate_config | 检查字段、模型能力和数值范围 |
| diff_config | 预览语义变化，不回显认证等无关配置 |
| reset_override | 移除选定作用域的覆盖，让 Codex 继承下一层 |
| delete_agent_role | 删除选定作用域中的命名角色 |
| get_plugin_logs | 查看本机 Agent Switchboard 操作日志 |
| open_switchboard | 打开设置面板 |

## 示例配置

- examples/global.config.toml：全局主 Agent、子 Agent 和 Reviewer 示例。
- examples/project.config.toml：项目覆盖示例。
- examples/roles/：命名角色示例。

示例文件只用于参考。插件运行时只编辑用户明确选择的 Codex 配置文件。

## 验证

在插件目录运行：

    uv run python -m unittest discover -s tests -v
    npm run build:ui
    python "$env:USERPROFILE\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py" .

测试使用临时目录，不会改写真实的 CODEX_HOME 或项目配置。

## 官方文档

- [Codex 配置基础](https://learn.chatgpt.com/docs/config-file/config-basic)
- [Codex 配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)
- [OpenAI 插件打包](https://developers.openai.com/plugins/build/plugins)
- [OpenAI MCP Apps 界面](https://developers.openai.com/plugins/build/chatgpt-ui)
- [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)
