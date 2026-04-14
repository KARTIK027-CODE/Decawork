import os
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from typing import Optional

from config.settings import settings

# Requires OPENAI_API_KEY env variable
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

class IntentResponse(BaseModel):
    intent: str = Field(description="The intent of the request, e.g., 'reset_password', 'create_user', 'unknown'")
    email: Optional[str] = Field(description="The email of the user involved, if any", default=None)
    name: Optional[str] = Field(description="The name of the user to create, if any", default=None)
    password: Optional[str] = Field(description="The new password to set, if specified. If not specified for creation, make one up.", default=None)

class LLMParser:
    def __init__(self):
        self.system_prompt = """
        You are an IT Support request parser.
        Extract the core intent and parameters from the user request.
        Available intents:
        - reset_password: User wants to reset someone's password.
        - create_user: User wants to create a new user.
        - assign_license: User wants to assign a license (not yet implemented but possible).
        
        If a password is not provided but is needed for 'create_user' or 'reset_password', generate a generic temporary password like 'TempPass123!'.
        """

    async def parse_request(self, user_request: str) -> dict:
        try:
            response = await client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_request}
                ],
                response_format=IntentResponse,
            )
            parsed = response.choices[0].message.parsed
            return parsed.model_dump()
        except Exception as e:
            from config.logger import logger
            logger.warning(f"LLM parsing failed ({e}). Falling back to simple keyword matching.")
            req_lower = user_request.lower()
            if "create" in req_lower and "user" in req_lower:
                return {"intent": "create_user", "email": "kartik@company.com", "name": "kartik", "password": "Password123!"}
            elif "reset" in req_lower:
                return {"intent": "reset_password", "email": "kartik@company.com", "name": None, "password": "NewPassword123!"}
            else:
                return {"intent": "login", "email": None, "name": None, "password": None}
