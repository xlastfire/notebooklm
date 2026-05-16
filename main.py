import asyncio
import sys
import warnings
from menu_agent import WizardAgent
from rich import print as rprint

# Suppress library warnings for a cleaner UI
warnings.filterwarnings("ignore")

async def main():
    wizard = WizardAgent()
    try:
        await wizard.run()
    except KeyboardInterrupt:
        pass
    finally:
        await wizard.agent.disconnect()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[yellow]Exiting Wizard Agent... Goodbye![/]")
    except Exception as e:
        print(f"\n[red]Unexpected error: {e}[/]")
