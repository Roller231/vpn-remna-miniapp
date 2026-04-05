import uuid
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.payment import Payment, PaymentStatus, PaymentMethodType
from app.schemas.wallet import WalletOut, TransactionListOut, TransactionOut
from app.schemas.payment import TopUpRequest, TopUpResponse
from app.services.wallet import wallet_service
from app.services.yookassa import yookassa_service, YookassaError

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("", response_model=WalletOut)
async def get_wallet(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    wallet = await wallet_service.get_or_create_wallet(user.id, db)
    return WalletOut.model_validate(wallet)


@router.get("/transactions", response_model=TransactionListOut)
async def get_transactions(
    page: int = 1,
    page_size: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await wallet_service.get_transactions(user.id, db, page, page_size)
    return TransactionListOut(
        items=[TransactionOut.model_validate(tx) for tx in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/topup", response_model=TopUpResponse)
async def top_up(
    body: TopUpRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a payment to top up the wallet via YooKassa."""
    if body.amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be positive")

    idem_key = str(uuid.uuid4())
    return_url = body.return_url or str(request.base_url)

    payment = Payment(
        user_id=user.id,
        amount=body.amount,
        currency="RUB",
        status=PaymentStatus.PENDING,
        method=PaymentMethodType.YOOKASSA,
        idempotency_key=idem_key,
        description=f"Пополнение баланса на {body.amount} ₽",
        is_topup=True,
    )
    db.add(payment)
    await db.flush()

    try:
        yk_data = await yookassa_service.create_payment(
            amount=body.amount,
            description=payment.description,
            return_url=return_url,
            metadata={"payment_id": payment.id, "user_id": user.id},
            idempotency_key=idem_key,
        )
        payment.provider_payment_id = yk_data.get("id")
        payment.provider_meta = yk_data
        confirmation_url = yk_data.get("confirmation", {}).get("confirmation_url")
    except YookassaError as e:
        payment.status = PaymentStatus.FAILED
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    return TopUpResponse(
        payment_id=payment.id,
        provider_payment_id=payment.provider_payment_id,
        confirmation_url=confirmation_url,
        status=payment.status,
    )
