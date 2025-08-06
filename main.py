

import asyncio
import sys
import json
from llm_handler import get_command_from_llm, summarize_output_with_llm
from tool_discovery import discover_tools_on_host
from platform_utils import run_command_on_host, get_installed_by_agent, uninstall_package
from ui import (
    console, print_welcome, get_llm_config_from_user, choose_llm_config,
    print_thought_process, print_command_to_execute, print_command_output, print_error, Prompt, print_summary
)

CONFIG_FILE = "hacker-agent/config.json"
MAX_RETRIES = 3 # Max attempts for LLM to fix a command

async def main():
    """
    The main function for the hacker agent.
    """
    print_welcome()

    # --- LLM Configuration Management ---
    llm_configs = []
    try:
        with open(CONFIG_FILE, 'r') as f:
            llm_configs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        llm_configs = []

    if not llm_configs:
        new_config = get_llm_config_from_user()
        llm_configs.append(new_config)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(llm_configs, f, indent=4)
        selected_llm_config = new_config
    else:
        selected_llm_config = choose_llm_config(llm_configs)

    console.print(f"[bold green]Using LLM: {selected_llm_config['name']} ({selected_llm_config['model_name']})[/bold green]\n")

    # --- Dynamic Tool Discovery ---
    tool_defs = await discover_tools_on_host()
    console.print("[bold green]Agent is ready. Type your commands or 'exit' to quit. Type 'help' for a list of commands.[/bold green]")

    try:
        loop = asyncio.get_running_loop()
        while True:
            user_input = await loop.run_in_executor(
                None, lambda: Prompt.ask("[bold cyan]>>>[/bold cyan]"))
            user_input = user_input.strip()

            if user_input.lower() == 'exit':
                break

            if user_input.lower() == 'help':
                console.print("[bold green]Available Agent Commands:[/bold green]")
                console.print("  - [cyan]exit[/cyan]: Exit the Agent.")
                console.print("  - [cyan]list tools[/cyan]: List tools installed by the Agent.")
                console.print("  - [cyan]list all known tools[/cyan]: List all tools the Agent is aware of on your system.")
                console.print("  - [cyan]uninstall <tool_name>[/cyan]: Uninstall a specific tool installed by the Agent.")
                console.print("  - [cyan]uninstall all[/cyan]: Uninstall all tools installed by the Agent.")
                console.print("  - [cyan]help[/cyan]: Display this help message.")
                continue

            if user_input.lower() == 'list all known tools':
                if tool_defs:
                    console.print("[bold green]All known tools on your system:[/bold green]")
                    # tool_defs is a JSON string, need to parse it
                    parsed_tool_defs = json.loads(tool_defs)
                    for tool in parsed_tool_defs:
                        console.print(f"  - [cyan]{tool['tool_name']}[/cyan]: {tool['description']}")
                else:
                    console.print("[bold yellow]No tools discovered yet.[/bold yellow]")
                continue

            if user_input.lower() == 'list tools':
                installed_tools = get_installed_by_agent()
                if installed_tools:
                    console.print("[bold green]Tools installed by Agent:[/bold green]")
                    for tool in installed_tools:
                        console.print(f"  - [cyan]{tool}[/cyan]")
                else:
                    console.print("[bold yellow]No tools have been installed by the Agent yet.[/bold yellow]")
                continue

            if user_input.lower() == 'uninstall all':
                installed_tools = get_installed_by_agent()
                if not installed_tools:
                    console.print("[bold yellow]No tools installed by the agent to uninstall.[/bold yellow]")
                    continue
                confirm = Prompt.ask(f"[bold red]Are you sure you want to uninstall ALL {len(installed_tools)} tools installed by the agent? (yes/no)[/bold red]")
                if confirm.lower() == 'yes':
                    for tool in installed_tools:
                        try:
                            console.print(f"[bold blue]Uninstalling {tool}...[/bold blue]")
                            uninstall_package(tool)
                            console.print(f"[bold green]{tool} uninstalled successfully.[/bold green]")
                        except Exception as e:
                            print_error(f"Failed to uninstall {tool}: {e}")
                continue

            if user_input.lower().startswith('uninstall '):
                tool_to_uninstall = user_input.split(' ', 1)[1].strip()
                if not tool_to_uninstall:
                    print_error("Please specify a tool to uninstall.")
                    continue
                installed_tools = get_installed_by_agent()
                if tool_to_uninstall not in installed_tools:
                    console.print(f"[bold yellow]{tool_to_uninstall} was not installed by the agent.[/bold yellow]")
                    continue
                confirm = Prompt.ask(f"[bold red]Are you sure you want to uninstall {tool_to_uninstall}? (yes/no)[/bold red]")
                if confirm.lower() == 'yes':
                    try:
                        console.print(f"[bold blue]Uninstalling {tool_to_uninstall}...[/bold blue]")
                        uninstall_package(tool_to_uninstall)
                        console.print(f"[bold green]{tool_to_uninstall} uninstalled successfully.[/bold green]")
                    except Exception as e:
                        print_error(f"Failed to uninstall {tool_to_uninstall}: {e}")
                continue

            if not user_input:
                continue

            current_context = None
            command_executed_successfully = False

            for attempt in range(MAX_RETRIES):
                # Get thought process and command from LLM, providing context from the last error
                with console.status(f"[bold green]Asking LLM for the command (Attempt {attempt + 1}/{MAX_RETRIES})...[/bold green]"):
                    thought, command = get_command_from_llm(user_input, tool_defs, selected_llm_config, context=current_context)

                if thought:
                    print_thought_process(thought)

                if not command:
                    print_error("LLM did not provide a command. Retrying...")
                    current_context = "LLM did not provide a command." # Provide context for retry
                    continue

                print_command_to_execute(command)
                
                # Execute command on host
                try:
                    with console.status("[bold green]Executing command...[/bold green]"):
                        output = run_command_on_host(command)
                    print_command_output(output + "\n")
                    
                    # Summarize output if it's not an error
                    if "command not found" not in output and output.strip():
                        with console.status("[bold green]Summarizing output...[/bold green]"):
                            summary = summarize_output_with_llm(user_input, output, selected_llm_config)
                        print_summary(summary)

                    command_executed_successfully = True
                    break # Command executed successfully, exit retry loop

                except RuntimeError as e:
                    print_error(f"Command execution failed: {e}")
                    current_context = str(e) # Save the error for the next retry
            
            if not command_executed_successfully:
                print_error(f"Failed to execute command after {MAX_RETRIES} attempts. Please refine your request or check the environment.")

    except (KeyboardInterrupt, EOFError):
        console.print("\n[bold yellow]Caught interrupt or EOF, shutting down...[/bold yellow]")
    except Exception as e:
        print_error(f"An unexpected error occurred: {e}")
    finally:
        console.print("[bold blue]Agent session ended.[/bold blue]")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print_error(f"Failed to start agent: {e}")

