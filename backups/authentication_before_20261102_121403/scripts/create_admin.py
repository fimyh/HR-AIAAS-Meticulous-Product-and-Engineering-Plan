import asyncio
from datetime import datetime, timezone
from getpass import getpass
from uuid import uuid4

from sqlalchemy import select

from hr_aiaas.db.models.identity import User
from hr_aiaas.db.session import SessionFactory
from hr_aiaas.security.passwords import hash_password

async def main() -> None:
    email = input("Admin email: ").strip().lower()
    full_name = input("Admin full name: ").strip()
    password = getpass("Admin password (12+ characters): ")
    if len(password) < 12:
        raise SystemExit("Password must contain at least 12 characters.")
    async with SessionFactory() as db:
        if await db.scalar(select(User.id).where(User.email == email)):
            raise SystemExit("A user with that email already exists.")
        now = datetime.now(timezone.utc)
        db.add(User(public_id=str(uuid4()), email=email, password_hash=hash_password(password), full_name=full_name, is_active=True, is_superuser=True, created_at=now, updated_at=now))
        await db.commit()
    print("Administrator created.")

if __name__ == "__main__":
    asyncio.run(main())
