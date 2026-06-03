"""
Service layer package.

Services implement business logic. They are instantiated in FastAPI
route handlers via Depends() and receive a Session from get_session().

Pattern:
    class UserService:
        def __init__(self, db: Session) -> None:
            self.db = db

        def get_user_by_phone(self, phone: str) -> User | None:
            return db.execute(select(User).where(User.phone == phone)).scalar_one_or_none()

Services use SQLAlchemy 2.x style ONLY:
    select() + session.execute() - NEVER session.query()
"""
