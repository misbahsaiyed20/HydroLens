"""
Controlled REVIEWER bootstrap. This is the ONLY supported way to create or
promote a REVIEWER account — there is no API endpoint for it, and public
signup (POST /auth/signup) can never create one. Run manually, with direct
access to the deployment's DATABASE_URL:

    cd backend
    python scripts/create_reviewer.py reviewer@example.com "a-strong-password" "Reviewer Name"

If the email already exists, it is promoted to REVIEWER (password left
unchanged unless a password is also provided as the 2nd arg — an existing
user is only promoted, not re-created).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import *  # noqa: F401,F403,E402 - register all models on Base
from app.models.enums import UserRole  # noqa: E402
from app.models.user import User  # noqa: E402


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else None
    display_name = sys.argv[3] if len(sys.argv) > 3 else None

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.role = UserRole.REVIEWER
            if password:
                user.password_hash = hash_password(password)
            if display_name:
                user.display_name = display_name
            action = "promoted existing user to"
        else:
            if not password:
                print("A password is required when creating a new reviewer.")
                sys.exit(1)
            user = User(
                email=email,
                display_name=display_name,
                password_hash=hash_password(password),
                role=UserRole.REVIEWER,
            )
            db.add(user)
            action = "created new"
        db.commit()
        db.refresh(user)
        print(f"OK: {action} REVIEWER — id={user.id} email={user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
