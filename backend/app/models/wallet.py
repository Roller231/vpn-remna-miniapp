import enum
from decimal import Decimal
from datetime import datetime
from sqlalchemy import (
    BigInteger, String, Numeric, DateTime, Enum, Text, ForeignKey,
    func, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    PURCHASE = "purchase"
    RENEWAL = "renewal"
    CASHBACK = "cashback"
    REFUND = "refund"
    ADMIN_CREDIT = "admin_credit"
    ADMIN_DEBIT = "admin_debit"
    TRAFFIC_RESET = "traffic_reset"


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    total_cashback_earned: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="wallet")
    transactions: Mapped[list["WalletTransaction"]] = relationship(
        "WalletTransaction", back_populates="wallet", order_by="WalletTransaction.created_at.desc()"
    )

    def __repr__(self) -> str:
        return f"<Wallet user_id={self.user_id} balance={self.balance}>"


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    wallet_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    balance_before: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="transactions")

    __table_args__ = (
        Index("ix_wallet_transactions_wallet_id", "wallet_id"),
        Index("ix_wallet_transactions_type", "type"),
        Index("ix_wallet_transactions_idempotency_key", "idempotency_key"),
    )
