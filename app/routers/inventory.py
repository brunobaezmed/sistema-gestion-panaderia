from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.models import (
    Product, InventoryMovement, MovementType, User
)
from app.schemas.schemas import (
    InventoryAdjustmentCreate, InventoryMovementResponse, ProductResponse
)
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/inventory", tags=["Control de Inventario y Kardex"])

@router.get("/movements", response_model=List[InventoryMovementResponse])
def list_movements(
    product_id: Optional[int] = None,
    movement_type: Optional[MovementType] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(InventoryMovement)
    if product_id:
        query = query.filter(InventoryMovement.product_id == product_id)
    if movement_type:
        query = query.filter(InventoryMovement.movement_type == movement_type)
    return query.order_by(InventoryMovement.created_at.desc()).limit(limit).all()

@router.post("/adjustments", response_model=InventoryMovementResponse)
def create_adjustment(
    adj_in: InventoryAdjustmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == adj_in.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
        
    if adj_in.quantity <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a 0")
        
    prev_stock = product.current_stock
    
    if adj_in.movement_type in [MovementType.AJUSTE_NEGATIVO, MovementType.MERMA]:
        if product.current_stock < adj_in.quantity:
            raise HTTPException(status_code=400, detail="No se puede descontar más stock del existente")
        product.current_stock -= adj_in.quantity
        delta_qty = -adj_in.quantity
    elif adj_in.movement_type == MovementType.AJUSTE_POSITIVO:
        product.current_stock += adj_in.quantity
        delta_qty = adj_in.quantity
    else:
        raise HTTPException(status_code=400, detail="Tipo de movimiento no válido para ajustes manuales")
        
    movement = InventoryMovement(
        product_id=product.id,
        user_id=current_user.id,
        movement_type=adj_in.movement_type,
        quantity=delta_qty,
        previous_stock=prev_stock,
        new_stock=product.current_stock,
        reference="AJUSTE_MANUAL",
        reason=adj_in.reason
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement

@router.get("/alerts/low-stock", response_model=List[ProductResponse])
def get_low_stock_alerts(db: Session = Depends(get_db)):
    # Products where current_stock <= min_stock
    return db.query(Product).filter(
        Product.is_active == True,
        Product.current_stock <= Product.min_stock
    ).order_by(Product.current_stock.asc()).all()

@router.get("/alerts/expiring-soon", response_model=List[ProductResponse])
def get_expiring_soon_alerts(days: int = 15, db: Session = Depends(get_db)):
    # Products with expiry date within the next X days
    threshold = datetime.utcnow() + timedelta(days=days)
    return db.query(Product).filter(
        Product.is_active == True,
        Product.expiry_date != None,
        Product.expiry_date <= threshold
    ).order_by(Product.expiry_date.asc()).all()
