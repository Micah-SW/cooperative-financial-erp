"""
Member Service.

Module: Member
See: service_contracts.md → MemberService
"""

import uuid
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import audit_service
from app.core.enums import AuditAction, MemberStatus
from app.core.exceptions import (
    BusinessValidationError,
    DuplicateError,
    InvalidStateTransitionError,
    NotFoundError,
)
from app.core.pagination import PaginatedResult, paginate
from app.models.member import Member, _share_sort_key
from app.models.share import Share
from app.schemas.member import MemberCreate, MemberExitRequest, MemberUpdate
from app.services.config_service import config_service
from app.utils.money import round_money


def get_current_shares(member: Member) -> tuple[int, Decimal]:
    """
    Derive the current share count and valuation from the latest share history snapshot.

    Sorts deterministically by (effective_date DESC, created_at DESC).
    """
    if not member.shares or member.status == MemberStatus.EXITED:
        return 0, Decimal("0.00")
    latest = max(member.shares, key=_share_sort_key)
    return latest.share_count, latest.total_value


class MemberService:
    """
    Manages member lifecycle: registration through exit.

    Responsibilities:
        - Create members with initial share assignment
        - Update mutable member fields
        - Query member profiles and paged directories
        - Process member exit atomically (status -> EXITED, extinguishing zero-share record)

    Must NOT:
        - Delete members or share records
        - Allow member_number or status changes through ordinary update
        - Silently invent exit payout formulas or execute financial settlements (UBR-1, UBR-14)
    """

    async def create_member(
        self,
        db: AsyncSession,
        data: MemberCreate,
        user_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Member:
        """
        Create a new member with initial share assignment.

        Enforces:
            - MEMBERSHIP_OPEN config check (fails closed if absent or false)
            - member_number uniqueness
            - Initial share record with configured count and value
            - Transactional audit log (AuditAction.CREATE)
        """
        # 1. Enforce MEMBERSHIP_OPEN setting (fail-closed)
        try:
            cfg_open = await config_service.get(db, "MEMBERSHIP_OPEN")
            is_open = cfg_open.config_value.strip().lower() in ("true", "1")
        except NotFoundError:
            is_open = False

        if not is_open:
            raise BusinessValidationError("Membership is currently closed")

        # 2. Check member_number uniqueness
        stmt = select(Member).where(Member.member_number == data.member_number)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise DuplicateError("member_number", data.member_number)

        # 3. Retrieve and validate effective SHARE_VALUE and SHARES_PER_MEMBER
        try:
            cfg_share_val = await config_service.get(db, "SHARE_VALUE", as_of=data.date_joined)
            raw_val = cfg_share_val.config_value
            try:
                value_per_share = Decimal(str(raw_val).strip())
            except Exception as exc:
                raise BusinessValidationError(
                    f"Invalid configured SHARE_VALUE: '{raw_val}'"
                ) from exc
            if value_per_share <= Decimal(0):
                raise BusinessValidationError(
                    f"Configured SHARE_VALUE must be strictly positive, got {value_per_share}"
                )
        except NotFoundError:
            value_per_share = Decimal("5000.00")

        try:
            cfg_shares_count = await config_service.get(
                db, "SHARES_PER_MEMBER", as_of=data.date_joined
            )
            raw_count = cfg_shares_count.config_value
            try:
                share_count = int(str(raw_count).strip())
            except Exception as exc:
                raise BusinessValidationError(
                    f"Invalid configured SHARES_PER_MEMBER: '{raw_count}'"
                ) from exc
            if share_count <= 0:
                raise BusinessValidationError(
                    f"Configured SHARES_PER_MEMBER must be strictly positive, got {share_count}"
                )
        except NotFoundError:
            share_count = 12

        total_value = round_money(Decimal(share_count) * value_per_share)

        # 4. Create member entity
        member = Member(
            id=uuid.uuid4(),
            member_number=data.member_number,
            full_name=data.full_name,
            phone=data.phone,
            email=str(data.email) if data.email else None,
            address=data.address,
            date_joined=data.date_joined,
            status=MemberStatus.ACTIVE,
            notes=data.notes,
            created_by=user_id,
        )

        # 5. Create initial share allocation
        initial_share = Share(
            id=uuid.uuid4(),
            member_id=member.id,
            share_count=share_count,
            value_per_share=value_per_share,
            total_value=total_value,
            effective_date=data.date_joined,
            created_by=user_id,
        )
        member.shares.append(initial_share)

        # 6. Flush within a savepoint to catch concurrent unique constraint violations safely
        try:
            async with db.begin_nested():
                db.add(member)
                db.add(initial_share)
                await db.flush()
        except IntegrityError as exc:
            if self._is_member_number_duplicate(exc):
                raise DuplicateError("member_number", data.member_number) from exc
            raise

        # 7. Record audit log
        await audit_service.log(
            db,
            user_id=user_id,
            action=AuditAction.CREATE,
            entity_type="Member",
            entity_id=member.id,
            old_values=None,
            new_values={
                "member_number": member.member_number,
                "full_name": member.full_name,
                "phone": member.phone,
                "email": member.email,
                "date_joined": member.date_joined.isoformat(),
                "status": MemberStatus.ACTIVE.value,
                "initial_shares": share_count,
                "value_per_share": str(value_per_share),
                "total_value": str(total_value),
            },
            ip_address=ip_address,
        )

        return member

    async def update_member(
        self,
        db: AsyncSession,
        member_id: uuid.UUID,
        data: MemberUpdate,
        user_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Member:
        """
        Update mutable fields of a member profile.

        Prohibits changes to member_number and status.
        """
        member = await self.get_member(db, member_id)

        update_dict = data.model_dump(exclude_unset=True)
        if "member_number" in update_dict:
            raise BusinessValidationError("Field 'member_number' is immutable and cannot be updated")
        if "status" in update_dict:
            raise BusinessValidationError(
                "Member status cannot be updated directly; use designated lifecycle endpoints"
            )

        old_values = {
            "full_name": member.full_name,
            "phone": member.phone,
            "email": member.email,
            "address": member.address,
            "notes": member.notes,
        }

        if "full_name" in update_dict and update_dict["full_name"] is not None:
            member.full_name = update_dict["full_name"]
        if "phone" in update_dict and update_dict["phone"] is not None:
            member.phone = update_dict["phone"]
        if "email" in update_dict:
            member.email = str(update_dict["email"]) if update_dict["email"] else None
        if "address" in update_dict:
            member.address = update_dict["address"]
        if "notes" in update_dict:
            member.notes = update_dict["notes"]

        new_values = {
            "full_name": member.full_name,
            "phone": member.phone,
            "email": member.email,
            "address": member.address,
            "notes": member.notes,
        }

        await audit_service.log(
            db,
            user_id=user_id,
            action=AuditAction.UPDATE,
            entity_type="Member",
            entity_id=member.id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
        )

        return member

    @staticmethod
    def _is_member_number_duplicate(exc: IntegrityError) -> bool:
        """
        Narrowly detect if an IntegrityError was caused by uq_members_member_number.

        Checks:
            1. PostgreSQL driver constraint diagnostics (orig.constraint_name / diag.constraint_name).
            2. Constraint name in error string ('uq_members_member_number').
            3. SQLite column uniqueness error string ('unique constraint failed: ...members.member_number').
        """
        orig = getattr(exc, "orig", None)
        if orig is not None:
            constraint = getattr(orig, "constraint_name", None)
            if constraint == "uq_members_member_number":
                return True
            diag = getattr(orig, "diag", None)
            if diag is not None:
                diag_constraint = getattr(diag, "constraint_name", None)
                if diag_constraint == "uq_members_member_number":
                    return True

        err_str = str(exc).lower()
        if "uq_members_member_number" in err_str:
            return True

        # SQLite format: "UNIQUE constraint failed: coop.members.member_number" or "members.member_number"
        return bool("unique constraint failed" in err_str and "members.member_number" in err_str)

    async def get_member(self, db: AsyncSession, member_id: uuid.UUID) -> Member:
        """
        Retrieve member details with share history.

        Raises:
            NotFoundError: If no member matches member_id.
        """
        stmt = (
            select(Member)
            .options(selectinload(Member.shares))
            .where(Member.id == member_id)
        )
        result = await db.execute(stmt)
        member = result.scalar_one_or_none()
        if not member:
            raise NotFoundError(f"Member with ID '{member_id}' not found")
        if member.shares:
            member.shares.sort(key=_share_sort_key, reverse=True)
        return member

    async def list_members(
        self,
        db: AsyncSession,
        *,
        status: MemberStatus | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 25,
    ) -> PaginatedResult:
        """List members with optional status filter, substring search, and pagination."""
        stmt = select(Member).options(selectinload(Member.shares))

        if status:
            stmt = stmt.where(Member.status == status)

        if search and search.strip():
            clean_search = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Member.member_number.ilike(clean_search),
                    Member.full_name.ilike(clean_search),
                    Member.phone.ilike(clean_search),
                )
            )

        stmt = stmt.order_by(Member.member_number.asc())
        return await paginate(db, stmt, page=page, per_page=per_page)

    async def exit_member(
        self,
        db: AsyncSession,
        member_id: uuid.UUID,
        data: MemberExitRequest,
        user_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Member:
        """
        Execute an authorized member exit lifecycle event.

        Updates member status to EXITED, records date_exited and exit_reason,
        appends an extinguishing share snapshot with share_count = 0,
        and logs AuditAction.EXIT.

        Does NOT calculate exit settlement or issue withdrawals (deferred to Chapter 05).
        """
        member = await self.get_member(db, member_id)

        current_st = (
            member.status.value
            if isinstance(member.status, MemberStatus)
            else str(member.status)
        )
        if member.status == MemberStatus.EXITED:
            raise InvalidStateTransitionError("Member", current_st, MemberStatus.EXITED.value)
        if member.status != MemberStatus.ACTIVE:
            raise InvalidStateTransitionError("Member", current_st, MemberStatus.EXITED.value)

        if data.exit_date < member.date_joined:
            raise BusinessValidationError("Exit date cannot precede join date")

        # Determine prevailing share valuation for historical continuity
        if member.shares:
            latest_share = max(member.shares, key=_share_sort_key)
            val_per_share = latest_share.value_per_share
        else:
            try:
                cfg_share_val = await config_service.get(db, "SHARE_VALUE", as_of=data.exit_date)
                val_per_share = Decimal(cfg_share_val.config_value)
            except NotFoundError:
                val_per_share = Decimal("5000.00")

        old_values = {
            "status": (
                member.status.value
                if isinstance(member.status, MemberStatus)
                else str(member.status)
            ),
            "date_exited": member.date_exited.isoformat() if member.date_exited else None,
            "exit_reason": member.exit_reason,
            "current_share_count": member.current_share_count,
            "current_share_value": str(member.current_share_value),
        }

        # Apply state transition
        member.status = MemberStatus.EXITED
        member.date_exited = data.exit_date
        member.exit_reason = data.exit_reason
        if data.notes:
            member.notes = (
                f"{member.notes}\n[Exit]: {data.notes}" if member.notes else f"[Exit]: {data.notes}"
            )

        # Append extinguishing zero-share record
        extinguishing_share = Share(
            id=uuid.uuid4(),
            member_id=member.id,
            share_count=0,
            value_per_share=val_per_share,
            total_value=Decimal("0.00"),
            effective_date=data.exit_date,
            created_by=user_id,
        )
        db.add(extinguishing_share)
        member.shares.append(extinguishing_share)

        # Flush and refresh to establish authoritative state within the transaction
        await db.flush()
        await db.refresh(extinguishing_share)
        member.shares.sort(key=_share_sort_key, reverse=True)

        new_values = {
            "status": MemberStatus.EXITED.value,
            "date_exited": data.exit_date.isoformat(),
            "exit_reason": data.exit_reason,
            "current_share_count": 0,
            "current_share_value": "0.00",
        }

        await audit_service.log(
            db,
            user_id=user_id,
            action=AuditAction.EXIT,
            entity_type="Member",
            entity_id=member.id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
        )

        return member


member_service = MemberService()
