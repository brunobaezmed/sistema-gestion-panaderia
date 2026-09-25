from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.models import Sale, SaleDetail, Product, InventoryMovement, MovementType, User
from app.schemas.schemas import SaleCreate, SaleResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/sales", tags=["Ventas / Punto de Venta"])

@router.get("/", response_model=List[SaleResponse])
def list_sales(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(Sale).order_by(Sale.created_at.desc()).limit(limit).all()

@router.get("/{sale_id}", response_model=SaleResponse)
def get_sale(sale_id: int, db: Session = Depends(get_db)):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return sale

@router.post("/", response_model=SaleResponse)
def create_sale(
    sale_in: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not sale_in.details:
        raise HTTPException(status_code=400, detail="La venta debe incluir al menos un producto")
    
    total_amount = sum(d.quantity * d.unit_price for d in sale_in.details)
    
    if sale_in.amount_paid < total_amount:
        raise HTTPException(
            status_code=400,
            detail=f"El monto recibido (Gs. {sale_in.amount_paid:,.0f}) es menor al total a pagar (Gs. {total_amount:,.0f})"
        )
        
    change_given = sale_in.amount_paid - total_amount
    
    # Generate sequential invoice number
    count_today = db.query(Sale).count() + 1
    invoice_num = f"TICK-{datetime.now().strftime('%Y%m%d')}-{count_today:04d}"
    
    sale = Sale(
        invoice_number=invoice_num,
        customer_id=sale_in.customer_id,
        user_id=current_user.id,
        payment_method=sale_in.payment_method,
        total_amount=total_amount,
        amount_paid=sale_in.amount_paid,
        change_given=change_given
    )
    db.add(sale)
    db.flush()
    
    for item in sale_in.details:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Producto con ID {item.product_id} no encontrado")
        
        if product.current_stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para '{product.name}'. Disponible: {product.current_stock} {product.unit}, Solicitado: {item.quantity} {product.unit}"
            )
            
        subtotal = item.quantity * item.unit_price
        detail = SaleDetail(
            sale_id=sale.id,
            product_id=product.id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=subtotal
        )
        db.add(detail)
        
        # Deduct stock
        prev_stock = product.current_stock
        product.current_stock -= item.quantity
        
        # Register Kardex movement
        movement = InventoryMovement(
            product_id=product.id,
            user_id=current_user.id,
            movement_type=MovementType.VENTA,
            quantity=-item.quantity,
            previous_stock=prev_stock,
            new_stock=product.current_stock,
            reference=f"Ticket Venta #{sale.invoice_number}",
            reason="Salida por venta en mostrador"
        )
        db.add(movement)
        
    db.commit()
    db.refresh(sale)
    return sale
