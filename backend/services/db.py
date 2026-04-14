import uuid
from typing import List, Optional
from backend.models.user import User

class Database:
    def __init__(self):
        self.users = {}
        # Add a default admin user
        self.create_user("admin@company.com", "Admin User", "adminpass", "admin")
        self.create_user("test@company.com", "Test User", "testpass", "user")

    def create_user(self, email: str, name: str, password: str, role: str = "user") -> User:
        user_id = str(uuid.uuid4())
        user = User(id=user_id, email=email, name=name, password=password, role=role)
        self.users[email] = user
        return user

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.users.get(email)

    def list_users(self) -> List[User]:
        return list(self.users.values())

    def update_password(self, email: str, new_password: str) -> bool:
        if email in self.users:
            self.users[email].password = new_password
            return True
        return False

# Global in-memory DB instance
db = Database()
