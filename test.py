from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()
console.clear()
console.print(Panel("[b]Welcome to Gemini Code AI Assistant![/b]", border_style="blue", expand=False))
while True:
    try:
        userinput1 = console.input("[bold blue]You:[/bold blue] ")
        userinput2 = console.input("[bold blue]&Me:[/bold blue] ")
        console.print(Markdown(userinput1), highlight=True, soft_wrap=True,end="")
        console.print(Markdown(userinput2), highlight=True, soft_wrap=True,end="")

    except KeyboardInterrupt:
        break
