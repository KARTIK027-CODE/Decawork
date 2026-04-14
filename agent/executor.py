import asyncio
from typing import List, Dict, Any
from config.settings import settings
from config.logger import logger
from agent.state import AgentState
from agent.page_analyzer import PageAnalyzer
from automation.browser import BrowserAutomation

class Executor:
    """Core ReAct-style Evaluation loop."""
    
    def __init__(self, state_manager: AgentState, browser: BrowserAutomation):
        self.state_manager = state_manager
        self.browser = browser

    async def _evaluate_condition(self, condition: str, snapshot: Dict[str, Any]) -> bool:
        """
        Reasoning Step. Decides if a step should be executed or skipped based on semantic DOM text.
        """
        if not condition:
            return True
            
        semantic_text = PageAnalyzer.simplify_for_llm(snapshot).lower()
        
        if condition == "NOT_LOGGED_IN":
            return "login" in semantic_text and "password" in semantic_text
        elif condition.startswith("USER_EXISTS:"):
            email = condition.split(":")[1].strip().lower()
            return email in semantic_text
        elif condition.startswith("USER_DOES_NOT_EXIST:"):
            email = condition.split(":")[1].strip().lower()
            return email not in semantic_text
            
        return True

    async def execute_plan(self, plan: List[Dict[str, Any]]):
        self.state_manager.state.total_steps = len(plan)
        self.state_manager.set_status("running")
        
        for index, step in enumerate(plan):
            self.state_manager.state.current_step_index = index + 1
            step_id = step.get("id", "unknown")
            action = step.get("action")
            condition = step.get("condition")
            
            # Perceive: Take snapshot of current world state
            snapshot = await PageAnalyzer.get_snapshot(self.browser.page)
            self.state_manager.update_snapshot(snapshot)
            
            # Reason: Evaluate if action needs to be taken
            should_execute = await self._evaluate_condition(condition, snapshot)
            if not should_execute:
                self.state_manager.log_execution("Reasoning", "skipped", f"Condition '{condition}' evaluated FALSE. Skipping.", target=step_id)
                continue

            # Check for DRY RUN
            if self.state_manager.state.is_dry_run:
                self.state_manager.log_execution(action, "success", f"[DRY RUN] Would execute: {step.get('description')}", target=step_id)
                continue

            # Failure Handling & Retries
            retry_count = 0
            success = False
            
            while retry_count <= settings.MAX_RETRIES and not success:
                try:
                    self.state_manager.log_execution("Attempt", "running", f"Action: {action} (Attempt {retry_count+1})", target=step_id)

                    # Act: Execute the underlying browser instructions
                    if action == "navigate":
                        await self.browser.navigate(step["url"])
                    
                    elif action == "login":
                        await self.browser.type_text("input[name='email']", step["email"])
                        await self.browser.type_text("input[name='password']", step["password"])
                        await self.browser.click("button[type='submit']")
                        await self.browser.wait_for_text("Dashboard")
                        
                    elif action == "reset_password":
                        email = step["email"]
                        await self.browser.click(f"tr:has-text('{email}') >> text='Reset Password'")
                        await self.browser.wait_for_text("Reset Password")
                        await self.browser.type_text("input[name='new_password']", step["new_password"])
                        await self.browser.click("button[type='submit']")

                    elif action == "create_user_flow":
                        await self.browser.click("a[href='/users/create']")
                        await self.browser.wait_for_text("Create New User")
                        await self.browser.type_text("input[name='email']", step["email"])
                        await self.browser.type_text("input[name='name']", step["name"])
                        await self.browser.type_text("input[name='password']", step["password"])
                        await self.browser.click("button[type='submit']")

                    elif action == "abort":
                        raise Exception(step.get("description", "Abort requested."))

                    success = True
                    self.state_manager.log_execution(action, "success", f"Step '{step_id}' completed successfully.", target=step_id)
                
                except Exception as e:
                    retry_count += 1
                    self.state_manager.increment_retry(step_id)
                    backoff = settings.RETRY_BACKOFF_FACTOR ** retry_count
                    
                    self.state_manager.log_execution(action, "failed", f"Failed ({e}). Retrying in {backoff}s...", target=step_id)
                    
                    if retry_count > settings.MAX_RETRIES:
                        self.state_manager.log_execution("Escalation", "failed", "Max retries exceeded. Aborting execution loop.", target=step_id)
                        self.state_manager.set_status("failed")
                        return # Safe abort
                    
                    await asyncio.sleep(backoff)

        if self.state_manager.state.status == "running":
            self.state_manager.set_status("completed")
