from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.syntax import Syntax
from rich.table import Table

console = Console()

def print_welcome():
    """Displays a welcome message."""
    console.print(
        Panel(
            "[bold green]Welcome to the AI Hacker Agent! :robot:[/bold green]", 
            expand=False, 
            border_style="yellow"
        )
    )

def get_llm_config_from_user():
    """Guides the user to create a new LLM configuration."""
    console.print("[bold yellow]No LLM configurations found. Let's set one up![/bold yellow]")
    name = Prompt.ask("Enter a name for this configuration (e.g., 'My Ollama')")
    url = Prompt.ask("Enter the API base URL (e.g., 'http://localhost:11434/v1')")
    api_key = Prompt.ask("Enter the API key (leave blank if not needed)", default=None)
    model_name = Prompt.ask("Enter the model name (e.g., 'qwen3:235b')")
    return {
        "name": name,
        "url": url,
        "api_key": api_key,
        "model_name": model_name
    }

def choose_llm_config(configs):
    """Allows the user to choose from existing LLM configurations."""
    table = Table(title="Available LLM Configurations")
    table.add_column("Index", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("URL", style="green")
    table.add_column("Model", style="yellow")

    for i, config in enumerate(configs):
        table.add_row(str(i + 1), config['name'], config['url'], config['model_name'])
    
    console.print(table)
    choice = IntPrompt.ask("Choose a configuration to use for this session", choices=[str(i+1) for i in range(len(configs))])
    return configs[choice - 1]

def print_thought_process(thought):
    """Displays the LLM's thought process in a panel."""
    console.print(
        Panel(
            thought,
            title="[bold yellow]:brain: LLM Thought Process[/bold yellow]",
            border_style="yellow",
            expand=False
        )
    )

def print_command_to_execute(command):
    """Displays the command to be executed with syntax highlighting."""
    console.print("[bold green]Executing Command:[/bold green]")
    console.print(Syntax(command, "bash", theme="monokai", line_numbers=True))


def print_command_output(output):
    """Displays the output from the executed command."""
    # Simple print for now, can be enhanced later
    console.print(output, end='')

def print_summary(summary):
    """
    Displays the LLM's summary of the command output in a panel.
    """
    console.print(
        Panel(
            summary,
            title="[bold blue]:bulb: Summary[/bold blue]",
            border_style="blue",
            expand=False
        )
    )

def print_error(message):
    """Displays an error message in a styled panel."""
    console.print(Panel(f"[bold red]Error: {message}[/bold red]", title="[bold red]Error[/bold red]"))