from typing import List, Dict, Any
from config.settings import settings
import uuid

class TaskPlanner:
    """
    Dynamic planner generating a step-by-step action sequence.
    Includes built-in branching conditions that the Executor evaluates against the DOM.
    """

    def generate_plan(self, parsed_request: Dict[str, Any]) -> List[Dict[str, Any]]:
        intent = parsed_request.get("intent")
        email = parsed_request.get("email")
        name = parsed_request.get("name")
        password = parsed_request.get("password")

        steps = []
        
        # Absolute requirement: Must start by authenticating
        steps.append({
            "id": "nav_base",
            "action": "navigate",
            "url": settings.BASE_URL,
            "condition": None, # Unconditional execution
            "description": "Navigate to mock admin panel base URL."
        })
        
        steps.append({
            "id": "auth_login",
            "action": "login",
            "email": "admin@company.com", 
            "password": "adminpass",
            "condition": "NOT_LOGGED_IN", # Execute only if login form is still visible
            "description": "Authenticate as super admin."
        })

        if intent == "reset_password":
            steps.append({"id": "nav_users", "action": "navigate", "url": f"{settings.BASE_URL}/users", "condition": None, "description": "Navigate to users management."})
            
            # Branches: if user exists, reset. Else throw error.
            steps.append({
                "id": "reset_user_pass", 
                "action": "reset_password", 
                "email": email, 
                "new_password": password,
                "condition": f"USER_EXISTS:{email}",
                "description": f"Trigger password reset for {email}."
            })
            
        elif intent == "create_user":
            steps.append({"id": "nav_users", "action": "navigate", "url": f"{settings.BASE_URL}/users", "condition": None, "description": "Navigate to users management."})
            
            steps.append({
                "id": "create_user", 
                "action": "create_user_flow", 
                "email": email, 
                "name": name, 
                "password": password,
                "condition": f"USER_DOES_NOT_EXIST:{email}",
                "description": f"Create new user {email} only if they don't already exist."
            })
            
        else:
            steps.append({"id": "abort", "action": "abort", "description": f"Aborting due to unknown intent: {intent}"})

        return steps
