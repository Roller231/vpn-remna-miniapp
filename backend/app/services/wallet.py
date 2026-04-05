"""
Wallet service — all balance operations with idempotency guarantees.
"""
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status

from app.models.wallet import Wallet, WalletTransaction, TransactionType
from app.models.user import User


class InsufficientFundsError(Exception):
    pass


class WalletService:

    @staticmethod
    async def get_or_create_wallet(user_id: int, db: AsyncSession) -> Wallet:
        result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
        wallet = result.scalar_one_or_none()
        if not wallet:
            wallet = Wallet(user_id=user_id, balance=Decimal("0.00"))
            db.add(wallet)
            await db.flush()
        return wallet

    @staticmethod
    async def credit(
        user_id: int,
        amount: Decimal,
        tx_type: TransactionType,
        db: AsyncSession,
        description: Optional[str] = None,
        reference_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> WalletTransaction:
        """Add funds to wallet. Idempotent if idempotency_key provided."""
        if idempotency_key:
            existing = await db.execute(
                select(WalletTransaction).where(WalletTransaction.idempotency_key == idempotency_key)
            )
            if tx := existing.scalar_one_or_none():
                return tx

        wallet = await WalletService.get_or_create_wallet(user_id, db)
        balance_before = wallet.balance
        wallet.balance += amount

        if tx_type == TransactionType.CASHBACK:
            wallet.total_cashback_earned += amount

        tx = WalletTransaction(
            wallet_id=wallet.id,
            type=tx_type,
            amount=amount,
            balance_before=balance_before,
            balance_after=wallet.balance,
            description=description,
            reference_id=reference_id,
            idempotency_key=idempotency_key,
        )
        db.add(tx)
        await db.flush()
        return tx

    @staticmethod
    async def debit(
        user_id: int,
        amount: Decimal,
        tx_type: TransactionType,
        db: AsyncSession,
        description: Optional[str] = None,
        reference_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> WalletTransaction:
        """Deduct funds from wallet. Raises InsufficientFundsError if balance too low."""
        if idempotency_key:
            existing = await db.execute(
                select(WalletTransaction).where(WalletTransaction.idempotency_key == idempotency_key)
            )
            if tx := existing.scalar_one_or_none():
                return tx

        wallet = await WalletService.get_or_create_wallet(user_id, db)
        if wallet.balance < amount:
            raise InsufficientFundsError(
                f"Balance {wallet.balance} is less than required {amount}"
            )

        balance_before = wallet.balance
        wallet.balance -= amount

        tx = WalletTransaction(
            wallet_id=wallet.id,
            type=tx_type,
            amount=amount,
            balance_before=balance_before,
            balance_after=wallet.balance,
            description=description,
            reference_id=reference_id,
            idempotency_key=idempotency_key,
        )
        db.add(tx)
        await db.flush()
        return tx

    @staticmethod
    async def get_transactions(
        user_id: int,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[WalletTransaction], int]:
        wallet = await WalletService.get_or_create_wallet(user_id, db)
        offset = (page - 1) * page_size

        count_result = await db.execute(
            select(func.count()).where(WalletTransaction.wallet_id == wallet.id)
        )
        total = count_result.scalar_one()

        result = await db.execute(
            select(WalletTransaction)
            .where(WalletTransaction.wallet_id == wallet.id)
            .order_by(WalletTransaction.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = list(result.scalars().all())
        return items, total


wallet_service = WalletService()
