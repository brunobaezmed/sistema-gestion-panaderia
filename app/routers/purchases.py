from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.models import Purchase, PurchaseDetail, Product, InventoryMovement, MovementType, User
from app.schemas.schemas import PurchaseCreate, PurchaseResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/purchases", tags=["Compras"])

@router.get("/", response_model=List[PurchaseResponse])
def list_purchases(db: Session = Depends(get_db)):
    return db.query(Purchase).order_by(Purchase.created_at.desc()).all()

@router.get("/{purchase_id}", response_model=PurchaseResponse)
def get_purchase(purchase_id: int, db: Session = Depends(get_db)):
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    return purchase

@router.post("/", response_model=PurchaseResponse)
def create_purchase(
    purchase_in: PurchaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not purchase_in.details:
        raise HTTPException(status_code=400, detail="La compra debe incluir al menos un producto o insumo")
    
    total_amount = sum(d.quantity * d.unit_cost for d in purchase_in.details)
    
    purchase = Purchase(
        invoice_number=purchase_in.invoice_number,
        supplier_id=purchase_in.supplier_id,
        user_id=current_user.id,
        total_amount=total_amount,
        notes=purchase_in.notes
    )
    db.add(purchase)
    db.flush()
    
    for item in purchase_in.details:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Producto con ID {item.product_id} no encontrado")
        
        subtotal = item.quantity * item.unit_cost
        detail = PurchaseDetail(
            purchase_id=purchase.id,
            product_id=product.id,
            quantity=item.quantity,
            unit_cost=item.unit_cost,
            subtotal=subtotal,
            expiry_date=item.expiry_date
        )
        db.add(detail)
        
        # Update stock and cost price
        prev_stock = product.current_stock
        product.current_stock += item.quantity
        product.cost_price = item.unit_cost
        if item.expiry_date:
            product.expiry_date = item.expiry_date
            
        # Register in Kardex
        movement = InventoryMovement(
            product_id=product.id,
            user_id=current_user.id,
            movement_type=MovementType.COMPRA,
            quantity=item.quantity,
            previous_stock=prev_stock,
            new_stock=product.current_stock,
            reference=f"Factura Compra #{purchase.invoice_number}",
            reason=f"Ingreso por compra a proveedor ID {purchase.supplier_id}"
        )
        db.add(movement)
        
    db.commit()
    db.refresh(purchase)
    return purchase
