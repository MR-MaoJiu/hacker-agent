import requests
import json
import re
from platform_utils import get_os_type

def get_command_from_llm(user_input: str, tool_definitions: str, llm_config: dict, context: str = None) -> (str, str):
    """
    Gets a command from the LLM, separating thought process from the command.

    :param user_input: The user's natural language input.
    :param tool_definitions: A JSON string of available tool definitions.
    :param llm_config: A dictionary containing the LLM configuration (url, api_key, model_name).
    :param context: A string containing context from the previous turn's execution, like an error.
    :return: A tuple containing (thought_process, command).
    """
    os_type = get_os_type()
    package_manager = "brew" if os_type == "macos" else "apt"

    system_prompt = f"""
    You are a self-healing expert penetration testing assistant. Your goal is to translate user requests into executable shell commands for the host system.
    Respond in the same language as the user's query.

    You are running on a {os_type} system. The package manager is `{package_manager}`.
    You do NOT need to use `sudo` for `brew` commands on macOS, but you WILL need `sudo` for `apt` commands on Linux.

    **IMPORTANT LIMITATION**: Direct access to physical Wi-Fi hardware (e.g., putting adapters into monitor mode, packet injection) is highly dependent on the specific Wi-Fi adapter and its drivers, especially on macOS. Many built-in Wi-Fi cards do NOT support these advanced modes. If a user asks about Wi-Fi devices, explain this limitation and suggest using a compatible external USB Wi-Fi adapter for advanced Wi-Fi operations, or advise them to use network-level scanning (like `nmap` or `arp-scan`) to find devices on the local network.

    You will be given:
    1. The user's current request.
    2. A list of available tools.
    3. A `context` which may contain the result or error from the PREVIOUS command you ran.

    **CRITICAL RULE: If the `context` contains a "command not found" error, your ONLY priority is to fix it.**
    To fix it, you must first find the correct package name using `{package_manager} search <command>` (or `apt-cache search` on Linux, `brew search` on macOS), and then install it using `platform_utils.install_package("<package_name>")`. You may need to run `sudo apt-get update` first on Linux.

    General Workflow:
    1. Analyze the user's request and the `context`.
    2. If the context indicates a missing command, formulate a plan to install it using `platform_utils.install_package`.
    3. If there are no errors, formulate a plan to execute the user's request.
    4. Explain your plan and reasoning inside a <think> XML tag.
    5. Provide the final, single, raw, executable command or sequence of commands (e.g., `platform_utils.install_package("nmap")`) inside a <command> XML tag.

    Your final output MUST follow this structure:
    <think>
    Your reasoning and analysis here.
    </think>
    <command>
    The final command(s) here.
    </command>

    Available Tools:
    {tool_definitions}
    """

    headers = {
        "Content-Type": "application/json",
    }
    # Add API key if it exists (for OpenAI-compatible APIs)
    if llm_config.get("api_key"):
        headers["Authorization"] = f"Bearer {llm_config['api_key']}"

    # Construct the full API endpoint URL
    api_url = llm_config['url'].rstrip('/') + '/chat/completions'

    messages = [
        {"role": "system", "content": system_prompt}
    ]
    if context:
        messages.append({"role": "user", "content": f"My last command failed with this context: {context}. My new request is: {user_input}"})
    else:
        messages.append({"role": "user", "content": user_input})

    data = {
        "model": llm_config['model_name'],
        "messages": messages,
        "temperature": 0,
        "top_p": 1,
        "max_tokens": 1024
    }

    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(data), timeout=60)
        response.raise_for_status()

        full_response = response.json()["choices"][0]["message"]["content"]
        
        thought = re.search(r'<think>(.*?)</think>', full_response, re.DOTALL)
        command = re.search(r'<command>(.*?)</command>', full_response, re.DOTALL)

        thought_text = thought.group(1).strip() if thought else "(No thought process provided)"
        command_text = command.group(1).strip() if command else ""

        if not command_text and thought_text == "(No thought process provided)":
            return full_response, ""

        return thought_text, command_text

    except requests.exceptions.RequestException as e:
        return f"Error connecting to LLM: {e}", ""
    except (KeyError, IndexError):
        return "Error: Invalid response format from LLM.", ""

def summarize_output_with_llm(user_request: str, command_output: str, llm_config: dict) -> str:
    """
    Summarizes the command output using the LLM.

    :param user_request: The original user request.
    :param command_output: The raw output from the executed command.
    :param llm_config: A dictionary containing the LLM configuration.
    :return: A summarized string of the output.
    """
    system_prompt = f"""
    You are a helpful assistant. Your task is to summarize the output of a command in a concise and easy-to-understand manner.
    Respond in the same language as the user's original request.
    The user's original request was: "{user_request}"
    The command output is provided below. Please extract the key information and present it clearly.
    """

    headers = {
        "Content-Type": "application/json",
    }
    if llm_config.get("api_key"):
        headers["Authorization"] = f"Bearer {llm_config['api_key']}"

    api_url = llm_config['url'].rstrip('/') + '/chat/completions'

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Command Output:\n```\n{command_output}\n```"}
    ]

    data = {
        "model": llm_config['model_name'],
        "messages": messages,
        "temperature": 0.2, # A bit more creative for summarization
        "top_p": 1,
        "max_tokens": 512 # Sufficient for summaries
    }

    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(data), timeout=60)
        response.raise_for_status()
        summary = response.json()["choices"][0]["message"]["content"].strip()
        return summary
    except requests.exceptions.RequestException as e:
        return f"Error summarizing output: {e}"
    except (KeyError, IndexError):
        return "Error: Invalid response format from LLM during summarization."