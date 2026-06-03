"""
Repository layer package.

Repositories handle data access patterns. Optional layer for complex queries.
Services may call repositories directly for complex data operations.

Pattern (when used):
    class UserRepository:
        def __init__(self, db: Session) -> None:
            self.db = db

        def find_by_phone(self, phone: str) -> User | None:
            return self.db.execute(
                select(User).where(User.phone == phone)
            ).scalar_one_or_none()
"""
