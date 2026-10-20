"""
Administrative Management CLI.

Provides safe administrative bootstrap and maintenance commands.

Usage:
    python -m app.cli bootstrap-admin [--username USERNAME] [--email EMAIL] [--full-name FULL_NAME]
"""

import argparse
import asyncio
import getpass
import logging
import os
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import audit_service
from app.core.enums import AuditAction, UserRole
from app.core.security import hash_password
from app.database import async_session_factory
from app.models.user import User

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("coop_bootstrap")


async def _run_bootstrap_logic(
    session: AsyncSession,
    username: str,
    email: str,
    full_name: str,
    password: str | None = None,
) -> bool:
    # Check if an ADMIN already exists
    stmt = select(User).where(User.role == UserRole.ADMIN)
    result = await session.execute(stmt)
    existing_admin = result.scalar_one_or_none()

    if existing_admin:
        logger.warning("An administrator account already exists. Duplicate bootstrap refused.")
        return False

    # Check username / email collision
    stmt_user = select(User).where((User.username == username) | (User.email == email))
    res_user = await session.execute(stmt_user)
    if res_user.scalar_one_or_none():
        logger.warning("User with username '%s' or email '%s' already exists. Bootstrap refused.", username, email)
        return False

    if not password:
        # Check env var first
        password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD")
        if not password:
            if sys.stdin.isatty():
                password = getpass.getpass("Enter password for initial administrator (min 8 chars): ")
            else:
                logger.error("No password provided. Set BOOTSTRAP_ADMIN_PASSWORD environment variable.")
                return False

    if len(password) < 8:
        logger.error("Administrator password must be at least 8 characters.")
        return False

    user = User(
        username=username,
        email=email,
        full_name=full_name,
        role=UserRole.ADMIN,
        hashed_password=hash_password(password),
        is_active=True,
    )
    session.add(user)
    await session.flush()

    await audit_service.log(
        session,
        user_id=user.id,
        action=AuditAction.CREATE,
        entity_type="User",
        entity_id=user.id,
        new_values={
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
        },
    )
    await session.commit()
    logger.info("Administrator '%s' successfully bootstrapped.", username)
    return True


async def bootstrap_admin(
    username: str,
    email: str,
    full_name: str,
    password: str | None = None,
    session: AsyncSession | None = None,
) -> bool:
    """
    Safely bootstrap the initial administrator.

    Guarantees:
        - Refuses duplicate initial-admin creation if an ADMIN user already exists
        - Does not print passwords or secrets to logs or standard output
        - Records an audit log entry for account creation
    """
    if session is not None:
        return await _run_bootstrap_logic(session, username, email, full_name, password)

    async with async_session_factory() as new_session:
        return await _run_bootstrap_logic(new_session, username, email, full_name, password)


def main() -> None:
    parser = argparse.ArgumentParser(description="Cooperative Financial ERP Management CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap_parser = subparsers.add_parser("bootstrap-admin", help="Create the initial administrator account")
    bootstrap_parser.add_argument(
        "--username",
        default=os.environ.get("BOOTSTRAP_ADMIN_USERNAME", "admin"),
        help="Administrator username",
    )
    bootstrap_parser.add_argument(
        "--email",
        default=os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "admin@coop.local"),
        help="Administrator email",
    )
    bootstrap_parser.add_argument(
        "--full-name",
        default="System Administrator",
        help="Administrator full name",
    )

    args = parser.parse_args()

    if args.command == "bootstrap-admin":
        success = asyncio.run(
            bootstrap_admin(
                username=args.username,
                email=args.email,
                full_name=args.full_name,
            )
        )
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
