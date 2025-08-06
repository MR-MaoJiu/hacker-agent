import json
from platform_utils import get_os_type, run_command_on_host

# A curated list of common and high-value tools to look for.
# This strikes a balance between full dynamic discovery and practicality.
CORE_TOOLS = [
    "nmap", "hydra", "sqlmap", "metasploit", "msfconsole", "nikto",
    "wireshark", "tshark", "aircrack-ng", "john", "hashcat", "burpsuite",
    "whois", "dig", "ping", "netstat", "ss", "ifconfig", "nmcli",
    "brew", "apt-get", "apt-cache", "dpkg"
]

async def discover_tools_on_host():
    """
    Discovers available tools on the host system and gets their descriptions.

    :return: A JSON string of tool definitions for the LLM.
    """
    print("Starting tool discovery on host system...")
    definitions = []
    os_type = get_os_type()

    if os_type == "macos":
        # For macOS, use `brew list` to find installed packages
        try:
            installed_packages = run_command_on_host("brew list").splitlines()
            for tool in CORE_TOOLS:
                if tool in installed_packages:
                    # Attempt to get a short description using `man -f` or `whatis`
                    try:
                        description = run_command_on_host(f"whatis {tool} 2>/dev/null").splitlines()[0].strip()
                        if description and "nothing appropriate" not in description:
                            definitions.append({"tool_name": tool, "description": description})
                        else:
                            definitions.append({"tool_name": tool, "description": f"A common command-line tool for {tool}."})
                    except Exception:
                        definitions.append({"tool_name": tool, "description": f"A common command-line tool for {tool}."})
        except RuntimeError as e:
            print(f"Error discovering tools with brew: {e}")

    elif os_type == "linux":
        # For Linux, use `dpkg -l` or `apt list --installed`
        try:
            installed_packages_output = run_command_on_host("dpkg -l | grep '^ii' | awk '{print $2}'").splitlines()
            installed_packages = [pkg.split(':')[0] for pkg in installed_packages_output]

            for tool in CORE_TOOLS:
                if tool in installed_packages:
                    try:
                        description = run_command_on_host(f"whatis {tool} 2>/dev/null").splitlines()[0].strip()
                        if description and "nothing appropriate" not in description:
                            definitions.append({"tool_name": tool, "description": description})
                        else:
                            definitions.append({"tool_name": tool, "description": f"A common command-line tool for {tool}."})
                    except Exception:
                        definitions.append({"tool_name": tool, "description": f"A common command-line tool for {tool}."})
        except RuntimeError as e:
            print(f"Error discovering tools with dpkg: {e}")

    print(f"Discovery complete. Found {len(definitions)} tools.")
    return json.dumps(definitions, indent=4)