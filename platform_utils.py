

import platform
import subprocess
import json
import os

INSTALLED_TOOLS_FILE = "hacker-agent/installed_tools.json"

def get_os_type():
    """Returns 'macos' or 'linux' based on the operating system."""
    system = platform.system()
    if system == "Darwin":
        return "macos"
    elif system == "Linux":
        return "linux"
    else:
        raise NotImplementedError(f"Unsupported operating system: {system}")

def get_package_manager():
    """Returns the appropriate package manager for the current OS."""
    os_type = get_os_type()
    if os_type == "macos":
        return "brew"
    elif os_type == "linux":
        return "apt"
    else:
        raise NotImplementedError(f"No package manager defined for {os_type}")

def run_command_on_host(command: str, check_output: bool = True, shell: bool = True) -> str:
    """
    Runs a shell command directly on the host system.

    :param command: The command string to execute.
    :param check_output: If True, raises an exception for non-zero exit codes.
    :param shell: If True, the command will be executed through the shell.
    :return: The stdout of the command.
    """
    try:
        result = subprocess.run(
            command,
            shell=shell,
            check=check_output,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command failed: {e.cmd}\nStdout: {e.stdout}\nStderr: {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError(f"Command not found: {command.split()[0]}")

def _load_installed_tools():
    """
    Loads the list of tools installed by the agent from a JSON file.
    """
    if not os.path.exists(INSTALLED_TOOLS_FILE):
        return []
    try:
        with open(INSTALLED_TOOLS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def _save_installed_tools(tools):
    """
    Saves the list of tools installed by the agent to a JSON file.
    """
    with open(INSTALLED_TOOLS_FILE, 'w') as f:
        json.dump(tools, f, indent=4)

def install_package(package_name: str) -> str:
    """
    Installs a package using the detected package manager.
    """
    pm = get_package_manager()
    if pm == "brew":
        cmd = f"brew install {package_name}"
    elif pm == "apt":
        cmd = f"sudo apt-get update && sudo apt-get install -y {package_name}"
    else:
        raise NotImplementedError(f"Install not supported for {pm}")

    print(f"Attempting to install {package_name} using {pm}...")
    output = run_command_on_host(cmd)
    
    installed_tools = _load_installed_tools()
    if package_name not in installed_tools:
        installed_tools.append(package_name)
        _save_installed_tools(installed_tools)
    return output

def uninstall_package(package_name: str) -> str:
    """
    Uninstalls a package using the detected package manager.
    """
    pm = get_package_manager()
    if pm == "brew":
        cmd = f"brew uninstall {package_name}"
    elif pm == "apt":
        cmd = f"sudo apt-get remove -y {package_name}"
    else:
        raise NotImplementedError(f"Uninstall not supported for {pm}")

    print(f"Attempting to uninstall {package_name} using {pm}...")
    output = run_command_on_host(cmd)

    installed_tools = _load_installed_tools()
    if package_name in installed_tools:
        installed_tools.remove(package_name)
        _save_installed_tools(installed_tools)
    return output

def get_installed_by_agent() -> list:
    """
    Returns a list of packages installed by the agent.
    """
    return _load_installed_tools()


