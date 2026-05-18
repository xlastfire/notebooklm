import asyncio
import os
import sys
from glob import glob
from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt
from rich import print as rprint

from client_wrapper import NotebookAgent

console = Console()

class WizardAgent:
    def __init__(self):
        self.agent = NotebookAgent()
        self.state = "SELECT_ACCOUNT"
        self.running = True
        self.accounts = []
        self.notebooks = []
        self.sources = []
        self.artifacts = []

    def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def header(self, subtitle=""):
        self.clear()
        acc = self.agent.storage_path.split(os.sep)[-1] if self.agent.storage_path else "None"
        nb = self.agent.current_nb_title or "None"
        status_info = ""
        if self.agent.active_tasks_count > 0:
            status_info = f" | [bold yellow]Tasks: {self.agent.active_tasks_count} active[/]"
        
        acc_1 = '.'.join(acc.split('\\')[-1].split('.')[:-1])
        info = f"Account: [bold green]{acc_1}[/] | NB: [bold blue]{nb}[/]{status_info}"
        console.print(Panel(info, title="[bold cyan]NotebookLM Wizard Agent[/]", border_style="bold blue"))
        
        # Show pending notifications
        while self.agent.notifications:
            n = self.agent.notifications.pop(0)
            console.print(Panel(n, border_style="green", expand=False))

        if subtitle:
            console.print(f"[bold yellow]>>> {subtitle}[/]\n")

    async def run(self):
        while self.running:
            if self.state == "SELECT_ACCOUNT":
                await self.menu_select_account()
            elif self.state == "SELECT_NOTEBOOK":
                await self.menu_select_notebook()
            elif self.state == "NOTEBOOK_ACTIONS":
                await self.menu_notebook_actions()
            elif self.state == "MANAGE_SOURCES":
                await self.menu_manage_sources()
            elif self.state == "MANAGE_ARTIFACTS":
                await self.menu_manage_artifacts()
            else:
                self.running = False

    async def menu_select_account(self):
        self.accounts = glob("accounts/*.json")
        # Fallback to current dir if accounts/ doesn't exist or is empty
        if not self.accounts:
            self.accounts = glob("*.json")
        self.header("Select Account")
        
        table = Table(box=None)
        table.add_column("Key", style="bold magenta")
        table.add_column("Account File", style="white")
        
        for i, acc in enumerate(self.accounts):
            table.add_row(str(i+1), acc)
        
        table.add_row("0", "Exit")
        console.print(table)
        
        choice = IntPrompt.ask("\nChoose an account", choices=[str(i) for i in range(len(self.accounts) + 1)])
        
        if choice == 0:
            self.running = False
        else:
            path = self.accounts[choice-1]
            with console.status(f"[bold green]Connecting to {path}..."):
                if await self.agent.connect(path):
                    self.state = "SELECT_NOTEBOOK"
                else:
                    console.print(f"[red]Failed to connect to {path}[/]")
                    await asyncio.sleep(2)

    async def menu_select_notebook(self):
        with console.status("[bold blue]Fetching notebooks..."):
            self.notebooks = await self.agent.list_notebooks()
        
        self.header("Select Notebook")
        table = Table(box=None)
        table.add_column("Key", style="bold magenta")
        table.add_column("Notebook Title", style="white")
        table.add_column("Sources", style="dim")

        for i, nb in enumerate(self.notebooks):
            table.add_row(str(i+1), nb.title, str(nb.sources_count))
        
        table.add_row("+", "Create New Notebook")
        table.add_row("!", "[bold red]Delete ALL Notebooks[/]")
        table.add_row("0", "Back to Accounts")
        console.print(table)
        
        choices = [str(i) for i in range(len(self.notebooks) + 1)] + ["+", "!"]
        choice = Prompt.ask("\nChoice", choices=choices)
        
        if choice == "0":
            self.state = "SELECT_ACCOUNT"
        elif choice == "+":
            title = Prompt.ask("Enter notebook title")
            with console.status("[bold green]Creating..."):
                nb = await self.agent.create_notebook(title)
                if nb:
                    self.state = "NOTEBOOK_ACTIONS"
        elif choice == "!":
            if Confirm.ask("[bold red]Are you absolutely sure you want to delete ALL notebooks in this account?[/]"):
                with console.status("[bold red]Deleting all notebooks..."):
                    for nb in self.notebooks:
                        await self.agent.delete_notebook(nb.id)
                console.print("[bold green]All notebooks deleted.[/]")
                await asyncio.sleep(1)
        else:
            nb = self.notebooks[int(choice)-1]
            self.agent.current_nb_id = nb.id
            self.agent.current_nb_title = nb.title
            self.state = "NOTEBOOK_ACTIONS"

    async def menu_notebook_actions(self):
        self.header(f"Actions for '{self.agent.current_nb_title}'")
        
        menu = [
            ("1", "Chat / Ask Questions"),
            ("2", "Manage Sources (Add/List)"),
            ("3", "Research Automation (Web Research)"),
            ("4", "Generate & Download Artifacts"),
            ("5", "Full Auto-Pilot (Topic -> Podcast)"),
            ("6", "Delete this Notebook"),
            ("0", "Back to Notebook Selection")
        ]
        
        table = Table(box=None)
        for key, desc in menu:
            table.add_row(f"[bold cyan]{key}.[/]", desc)
        console.print(table)
        
        choice = Prompt.ask("\nAction", choices=[m[0] for m in menu])
        
        if choice == "0":
            self.state = "SELECT_NOTEBOOK"
        elif choice == "1":
            await self.sub_chat()
        elif choice == "2":
            self.state = "MANAGE_SOURCES"
        elif choice == "3":
            await self.sub_research()
        elif choice == "4":
            self.state = "MANAGE_ARTIFACTS"
        elif choice == "5":
            await self.sub_auto_pilot()
        elif choice == "6":
            if Confirm.ask("Are you sure you want to delete this notebook?"):
                await self.agent.delete_notebook(self.agent.current_nb_id)
                self.state = "SELECT_NOTEBOOK"

    async def sub_chat(self):
        self.header("Chat Mode")
        console.print("[dim]Type 'exit' or leave blank to go back.[/]\n")
        while True:
            query = Prompt.ask("Question")
            if not query or query.lower() == "exit": break
            with console.status("[bold blue]Thinking..."):
                res = await self.agent.chat(query)
                if res:
                    console.print(Panel(res.answer, title="Answer", border_style="blue"))
                    console.print("\n")

    async def menu_manage_sources(self):
        with console.status("[bold blue]Fetching sources..."):
            self.sources = await self.agent.list_sources()
        
        self.header("Manage Sources")
        table = Table(title="Current Sources")
        table.add_column("Key", style="bold magenta")
        table.add_column("Type", style="dim")
        table.add_column("Title")
        
        for i, s in enumerate(self.sources):
            table.add_row(str(i+1), str(s.kind), s.title)
        
        console.print(table)
        
        opt_table = Table(box=None, show_header=False)
        opt_table.add_row("[bold cyan]1.[/]", "Add URL (Website/YouTube)")
        opt_table.add_row("[bold cyan]2.[/]", "Add File (PDF/Docx/Txt)")
        opt_table.add_row("[bold cyan]3.[/]", "Add Text (Paste)")
        opt_table.add_row("[bold cyan]4.[/]", "Delete a Source")
        opt_table.add_row("[bold magenta]0.[/]", "Back")
        console.print(opt_table)
        
        choice = Prompt.ask("\nChoice", choices=["0", "1", "2", "3", "4"])
        
        if choice == "0":
            self.state = "NOTEBOOK_ACTIONS"
        elif choice == "1":
            url = Prompt.ask("Enter URL")
            console.print("[bold yellow]Adding URL in background...[/]")
            asyncio.create_task(self.agent.add_source_bg("url", url))
            await asyncio.sleep(0.5)
        elif choice == "2":
            path = Prompt.ask("Enter file path")
            if os.path.exists(path):
                console.print("[bold yellow]Uploading file in background...[/]")
                asyncio.create_task(self.agent.add_source_bg("file", path))
                await asyncio.sleep(0.5)
            else:
                console.print("[red]File not found.[/]")
                await asyncio.sleep(1)
        elif choice == "3":
            title = Prompt.ask("Title for snippet")
            text = Prompt.ask("Paste text")
            console.print("[bold yellow]Saving text in background...[/]")
            asyncio.create_task(self.agent.add_source_bg("text", text, title=title))
            await asyncio.sleep(0.5)

        elif choice == "4":
            idx = IntPrompt.ask("Enter Key of source to delete", choices=[str(i+1) for i in range(len(self.sources))])
            if Confirm.ask(f"Delete '{self.sources[idx-1].title}'?"):
                await self.agent.delete_source(self.sources[idx-1].id)

    async def sub_research(self):
        self.header("Research Automation")
        query = Prompt.ask("What topic do you want to research?")
        deep = Confirm.ask("Use Deep Research? (Takes longer, more thorough)", default=False)
        
        console.print("[bold yellow]Starting research in background... You can continue working.[/]")
        asyncio.create_task(self.agent.research_auto(query, deep))
        await asyncio.sleep(1)

        Prompt.ask("\nPress Enter to continue")
    async def menu_manage_artifacts(self):
        self.header("Manage Artifacts")
        with console.status("[bold blue]Fetching artifacts..."):
            self.artifacts = await self.agent.client.artifacts.list(self.agent.current_nb_id)
        
        if self.artifacts:
            table = Table(title="Available Artifacts")
            table.add_column("Key", style="bold magenta")
            table.add_column("Type", style="dim")
            table.add_column("Title")
            table.add_column("Status")
            for i, a in enumerate(self.artifacts):
                kind_str = str(a.kind).split(".")[-1].lower()
                status_str = str(a.status).split(".")[-1].upper()
                color = "green" if status_str == "COMPLETED" else "yellow"
                table.add_row(str(i+1), kind_str, a.title, f"[{color}]{status_str}[/]")
            console.print(table)
            console.print("[dim]Use [bold cyan]D <key>[/] to download an existing artifact (e.g. D 1)[/]\n")
        
        gen_table = Table(title="Generate New Artifact", box=None, show_header=False)
        types = ["audio", "quiz", "flashcards", "mind_map", "briefing_doc", "study_guide", "blog_post", "slide_deck"]
        for i, t in enumerate(types):
            gen_table.add_row(f"[bold cyan]{i+1}.[/]", t)
        gen_table.add_row("[bold magenta]0.[/]", "Go Back to Notebook Menu")
        console.print(gen_table)
        
        choice = Prompt.ask("\nChoice").strip()
        
        if choice == "0":
            self.state = "NOTEBOOK_ACTIONS"
            return

        if choice.lower().startswith("d "):
            try:
                idx = int(choice.split()[1])
                art = self.artifacts[idx-1]
                kind = str(art.kind).split(".")[-1].lower()
                console.print(f"[bold yellow]Download started in background for {art.title}...[/]")
                asyncio.create_task(self.agent.download_artifact_bg(art.id, kind, art.title))
                await asyncio.sleep(0.5)
            except (ValueError, IndexError):
                console.print("[red]Invalid artifact key.[/]")
            Prompt.ask("\nPress Enter to continue")
            
        elif choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(types):
                art_type = types[idx-1]
                lang = Prompt.ask("Target Language", default="Sinhala")
                instr = Prompt.ask("Any custom instructions? (Leave blank for default)", default="")
                console.print(f"[bold yellow]Starting {art_type} generation in {lang} background...[/]")
                asyncio.create_task(self.agent.generate_artifact_bg(art_type, instr, language=lang))
                await asyncio.sleep(0.5)


                Prompt.ask("\nPress Enter to continue")
            else:
                console.print("[red]Invalid choice.[/]")
                await asyncio.sleep(1)

    async def sub_auto_pilot(self):
        self.header("Full Auto-Pilot Pipeline")
        topic = Prompt.ask("Enter topic for full research + podcast")
        lang = Prompt.ask("Target Language", default="Sinhala")
        
        if topic:
            console.print(f"[bold yellow]Starting Full Auto-Pilot in background ({lang}) for '{topic}'...[/]")
            console.print("[dim]This will create a notebook, research the topic, and generate a podcast mp3.[/]")
            asyncio.create_task(self.agent.auto_pilot_bg(topic, language=lang))
            await asyncio.sleep(1)

        
        Prompt.ask("\nPress Enter to return to menu")

if __name__ == "__main__":
    wizard = WizardAgent()
    try:
        asyncio.run(wizard.run())
    except KeyboardInterrupt:
        pass
    finally:
        asyncio.run(wizard.agent.disconnect())
