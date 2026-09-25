from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.models import CashRegister, CashRegisterStatus, Sale, PaymentMethod, User
from app.schemas.schemas import CashRegisterOpen, CashRegisterClose, CashRegisterResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/cash", tags=["Caja y Arqueo"])

@router.get("/current", response_model=Optional[CashRegisterResponse])
def get_current_cash_register(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(CashRegister).filter(
        CashRegister.user_id == current_user.id,
        CashRegister.status == CashRegisterStatus.ABIERTA
    ).first()

@router.post("/open", response_model=CashRegisterResponse)
def open_cash_register(
    open_data: CashRegisterOpen,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(CashRegister).filter(
        CashRegister.user_id == current_user.id,
        CashRegister.status == CashRegisterStatus.ABIERTA
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya tienes una caja abierta")
        
    cash = CashRegister(
        user_id=current_user.id,
        initial_cash=open_data.initial_cash,
        status=CashRegisterStatus.ABIERTA,
        notes=open_data.notes
    )
    db.add(cash)
    db.commit()
    db.refresh(cash)
    return cash

@router.post("/close", response_model=CashRegisterResponse)
def close_cash_register(
    close_data: CashRegisterClose,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cash = db.query(CashRegister).filter(
        CashRegister.user_id == current_user.id,
        CashRegister.status == CashRegisterStatus.ABIERTA
    ).first()
    if not cash:
        raise HTTPException(status_code=400, detail="No tienes ninguna caja abierta actualmente")
        
    # Calculate total cash sales during the open session
    cash_sales = db.query(func.coalesce(func.sum(Sale.total_amount), 0.0)).filter(
        Sale.user_id == current_user.id,
        Sale.payment_method == PaymentMethod.EFECTIVO,
        Sale.created_at >= cash.opened_at
    ).scalar()
    
    expected = cash.initial_cash + float(cash_sales)
    diff = close_data.final_cash - expected
    
    cash.final_cash = close_data.final_cash
    cash.expected_cash = expected
    cash.difference = diff
    cash.status = CashRegisterStatus.CERRADA
    cash.closed_at = datetime.utcnow()
    if close_data.notes:
        cash.notes = f"{cash.notes or ''} | Cierre: {close_data.notes}".strip(" |")
        
    db.commit()
    db.refresh(cash)
    return cash

@router.get("/history", response_model=List[CashRegisterResponse])
def get_cash_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(CashRegister).order_by(CashRegister.opened_at.desc()).limit(30).all()
