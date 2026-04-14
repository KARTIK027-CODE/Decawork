import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from agent.parser import LLMParser
from agent.planner import TaskPlanner
from agent.executor import Executor
from agent.state import AgentState
from automation.browser import BrowserAutomation

async def main():
    print("====================================================")
    print("🤖 Production V2 IT Support Agent")
    print(f"Configs: MODE={settings.EXECUTION_MODE} | RETRIES={settings.MAX_RETRIES} | HEADLESS={settings.HEADLESS_MODE}")
    print("====================================================")

    parser = LLMParser()
    planner = TaskPlanner()
    
    import argparse
    cli_parser = argparse.ArgumentParser(description="🤖 Production V2 IT Support Agent")
    cli_parser.add_argument("request", nargs="*", help="Your IT request (e.g. 'login', 'create user')")
    args = cli_parser.parse_args()

    if args.request:
        user_input = " ".join(args.request)
    else:
        user_input = input("\\nEnter your IT request (or 'exit'): ")
        if user_input.lower() in ["exit", "q"]: return

    print("\\n[1/4] Semantic LLM Intent Parsing...")
    parsed = await parser.parse_request(user_input)
    print(f" -> Result: {parsed['intent']}")

    print("\\n[2/4] Generating Conditional Action Branches...")
    plan = planner.generate_plan(parsed)
    print(f" -> Plan bounded with {len(plan)} active tasks.")

    print(f"\\n[3/4] Initializing State Manager & Browser (Mode={settings.EXECUTION_MODE})...")
    
    is_dry_run = settings.EXECUTION_MODE == "DRY_RUN"
    state_manager = AgentState(is_dry_run=is_dry_run)
    browser = BrowserAutomation()
    
    try:
        await browser.start()
        executor = Executor(state_manager=state_manager, browser=browser)
        
        print("\\n[4/4] Starting ReAct Loop Execution...")
        await executor.execute_plan(plan)
        
        if state_manager.state.status == "completed":
            print("\\n✅ Execution Loop Successfully Completed.")
        else:
            print("\\n❌ Execution Aborted or Failed. See Logs.")
            
    except Exception as e:
        print(f"\\nCRITICAL SYSTEM FAILURE: {e}")
    finally:
        await browser.close()
        print("\\nLogs flushed to `logs/agent_execution.json`.")

if __name__ == "__main__":
    asyncio.run(main())
