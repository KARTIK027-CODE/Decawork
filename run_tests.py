import asyncio
import sys
import os
import multiprocessing
import time
import uvicorn

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.main import app
from agent.planner import TaskPlanner
from agent.executor import Executor
from agent.state import AgentState
from automation.browser import BrowserAutomation
from config.settings import settings

def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")

async def test_scenario(name: str, intent_data: dict, is_dry_run: bool = False):
    print(f"\\n========================================")
    print(f"🧪 Test Scenario: {name} (DRY_RUN={is_dry_run})")
    print(f"========================================")
    
    planner = TaskPlanner()
    plan = planner.generate_plan(intent_data)
    
    state_manager = AgentState(is_dry_run=is_dry_run)
    browser = BrowserAutomation()
    
    try:
        await browser.start()
        executor = Executor(state_manager, browser)
        await executor.execute_plan(plan)
        
        status = state_manager.state.status
        print(f"✅ Final State Status: {status}")
        assert status == "completed" or (is_dry_run and status == "completed")
        
        # Output some telemetry
        print(f"Metrics: Retries Initiated: {sum(state_manager.state.retry_metrics.values())}")
        
    finally:
        await browser.close()

async def run_all_tests():
    print("Starting integration test server...")
    server = multiprocessing.Process(target=run_server)
    server.start()
    time.sleep(2)
    
    try:
        # Scenario 1: DRY RUN Execution
        await test_scenario("DRY RUN - Password Reset", {
            "intent": "reset_password", "email": "test@company.com", "password": "pass", "name": None
        }, is_dry_run=True)
        
        # Scenario 2: LIVE - Create User
        await test_scenario("LIVE - Create New User", {
            "intent": "create_user", "email": "newuser@test.io", "password": "pass", "name": "New User"
        }, is_dry_run=False)
        
        # Scenario 3: Conditional Avoidance - User already exists
        await test_scenario("LIVE - Conditional Subversion (User already exists)", {
            "intent": "create_user", "email": "newuser@test.io", "password": "pass", "name": "New User"
        }, is_dry_run=False)
        
        print("\\n🎉 Integration Suite Passed Beautifully. Observability logs generated.")
        
    finally:
        server.terminate()
        server.join()

if __name__ == "__main__":
    # Configure strict timeouts for tests
    settings.DEFAULT_TIMEOUT_MS = 2000
    settings.MAX_RETRIES = 1
    
    asyncio.run(run_all_tests())
