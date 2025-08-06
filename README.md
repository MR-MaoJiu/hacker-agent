# AI Hacker Agent

## 项目简介

AI Hacker Agent 是一个由大型语言模型 (LLM) 驱动的命令行工具，旨在帮助用户通过自然语言与操作系统进行交互，执行渗透测试、系统管理等任务。它具备环境感知、工具自动安装/卸载、命令执行、结果总结以及友好的命令行界面等功能。

**核心理念**：将 LLM 的智能与本地系统工具的强大功能相结合，提供一个直观、高效且可扩展的自动化操作平台。

## 主要功能

*   **自然语言交互**：通过 LLM 将用户的自然语言请求转换为可执行的 shell 命令。
*   **跨平台支持**：自动识别 macOS 和 Linux 操作系统，并使用相应的包管理器（Homebrew 或 apt）进行工具管理。
*   **工具自动安装与自愈**：
    *   当 LLM 尝试执行一个系统中不存在的命令时，Agent 会识别“command not found”错误。
    *   它会主动尝试使用系统包管理器（如 `brew install` 或 `apt-get install`）来安装缺失的工具。
    *   Agent 会记录通过自身安装的工具，方便后续管理。
*   **命令执行与结果总结**：
    *   执行 LLM 生成的命令，并捕获其标准输出和错误输出。
    *   将命令执行结果发送回 LLM 进行总结，以更直观、易懂的方式呈现给用户。
*   **工具管理**：
    *   支持一键卸载所有由 Agent 安装的工具。
    *   支持卸载单个由 Agent 安装的工具。
    *   `list tools`：查看所有由 Agent 安装的工具列表。
    *   `list all known tools`：查看 Agent 在您的系统上识别到的所有工具及其描述。
*   **可配置的 LLM 后端**：支持 Ollama 和兼容 OpenAI API 格式的 LLM 服务（如 Kimi、GPT-4 等），用户可灵活配置和切换。
*   **美观的命令行界面**：采用 `rich` 库美化输出，提供清晰的思考过程展示、命令语法高亮、状态提示和错误信息。

## 先决条件

在运行 Agent 之前，请确保您的系统满足以下条件：

*   **Python 3.8+**：推荐使用最新稳定版本。
*   **pip**：Python 包管理器，通常随 Python 一起安装。
*   **包管理器**：
    *   **macOS**：需要安装 [Homebrew](https://brew.sh/)。
    *   **Linux**：需要 `apt` 包管理器（Debian/Ubuntu 系）。
*   **LLM 服务**：
    *   **Ollama**：如果您使用 Ollama，请确保其已在您的本地或远程服务器上运行，并且您已拉取了所需的模型（例如 `ollama pull qwen3:235b` 或 `ollama pull kimi-k2-0711-preview`）。
    *   **OpenAI 兼容 API**：如果您使用其他服务，请确保您有 API URL 和 API Key。

## 安装

1.  **克隆项目仓库**：
    ```bash
    git clone https://github.com/MR-MaoJiu/hacker-agent.git
    cd hacker-agent
    ```
2.  **安装 Python 依赖**：
    ```bash
    pip install -r requirements.txt
    ```

## 配置 LLM

Agent 启动时会引导您配置 LLM。配置信息存储在 `hacker-agent/config.json` 文件中。

1.  **首次运行**：
    如果 `config.json` 不存在或为空，Agent 会提示您输入 LLM 配置信息：
    *   `Enter a name for this configuration`: 给您的 LLM 配置起一个名字（例如 `My Ollama` 或 `Kimi API`）。
    *   `Enter the API base URL`: LLM 服务的 API 地址。
        *   **Ollama**：通常是 `http://<your_ollama_ip>:11434/v1`
        *   **OpenAI 兼容 API**：例如 `https://api.openai.com/v1` 或其他服务商提供的地址。
    *   `Enter the API key (leave blank if not needed)`: 如果是 Ollama 等本地服务，通常不需要 API Key，直接回车留空。对于 OpenAI 或其他商业 API，请输入您的 API Key。
    *   `Enter the model name`: 您希望使用的模型名称（例如 `qwen3:235b` 或 `gpt-4-turbo`）。

2.  **管理多个 LLM 配置**：
    您可以手动编辑 `hacker-agent/config.json` 文件来添加、修改或删除 LLM 配置。`config.json` 应该是一个 JSON 数组，每个元素是一个 LLM 配置对象。
    示例 `config.json`：
    ```json
    [
      {
        "name": "My Ollama",
        "url": "http://localhost:11434/v1",
        "api_key": null,
        "model_name": "qwen3:235b"
      },
      {
        "name": "Kimi API",
        "url": "https://api.moonshot.cn/v1",
        "api_key": "sk-YOUR_KIMI_API_KEY",
        "model_name": "kimi-k2-0711-preview"
      }
    ]
    ```
    如果存在多个配置，Agent 启动时会列出所有配置供您选择。

## 使用方法

1.  **启动 Agent**：
    ```bash
    NO_PROXY="*" python3 main.py
    ```
    *   `NO_PROXY="*"`：这个环境变量很重要，它会告诉 Python 忽略系统级的代理设置，直接连接到 LLM 服务。如果您没有设置代理，也可以省略。

2.  **与 Agent 交互**：
    Agent 启动后，会显示 `>>>` 提示符。您可以输入自然语言指令，Agent 会尝试理解并执行相应的操作。

    示例：
    ```
    >>> 帮我查看一下我的 IP 地址
    ```

3.  **特殊命令**：
    *   `exit`：退出 Agent。
    *   `help`：显示所有特殊命令的列表。
    *   `list tools`：查看所有由 Agent 安装的工具列表。
    *   `list all known tools`：查看 Agent 在您的系统上识别到的所有工具及其描述。
    *   `uninstall <tool_name>`：卸载由 Agent 安装的指定工具。
        *   示例：`uninstall nmap`
    *   `uninstall all`：卸载所有由 Agent 安装的工具。Agent 会要求您确认。

## 重要限制与注意事项

*   **`sudo` 权限**：在 Linux 系统上，安装和卸载工具（如 `apt-get install`）通常需要 `sudo` 权限。Agent 会尝试使用 `sudo`，您可能需要输入密码。
*   **Wi-Fi 硬件访问**：
    *   Agent 运行在宿主机上，但直接访问物理 Wi-Fi 硬件（例如，将网卡置于监听模式、数据包注入）高度依赖于特定的 Wi-Fi 适配器及其驱动程序。
    *   macOS 的内置 Wi-Fi 网卡通常不支持这些高级模式。
    *   如果您需要进行高级 Wi-Fi 操作，强烈建议使用兼容的外置 USB Wi-Fi 适配器。
    *   LLM 已被告知此限制，当您询问 Wi-Fi 设备时，它会尝试解释并建议使用网络层面的扫描（如 `nmap` 或 `arp-scan`）来查找局域网内的设备。
*   **LLM 响应时间**：LLM 的响应速度取决于您使用的服务和网络状况。
*   **LLM 幻觉**：LLM 可能会生成不正确或不存在的命令。Agent 的自愈机制会尝试纠正，但并非万无一失。请始终谨慎对待 Agent 生成的命令。
*   **安全风险**：Agent 会在您的真机上执行命令。请确保您理解并信任 Agent 的行为，避免执行来自不可信来源的指令。

## 贡献

欢迎对本项目提出建议和贡献！

---