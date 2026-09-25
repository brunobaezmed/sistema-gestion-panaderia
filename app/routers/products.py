from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.models import Product, Category, ProductType, User, InventoryMovement, MovementType
from app.schemas.schemas import (
    ProductCreate, ProductUpdate, ProductResponse,
    CategoryCreate, CategoryResponse
)
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/products", tags=["Productos e Insumos"])

# ==================== CATEGORÍAS ====================
@router.get("/categories", response_model=List[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name).all()

@router.post("/categories", response_model=CategoryResponse)
def create_category(
    cat_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(Category).filter(Category.name == cat_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="La categoría ya existe")
    cat = Category(name=cat_in.name, description=cat_in.description)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

# ==================== PRODUCTOS ====================
@router.get("/", response_model=List[ProductResponse])
def list_products(
    product_type: Optional[ProductType] = None,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    low_stock_only: bool = False,
    db: Session = Depends(get_db)
):
    query = db.query(Product).filter(Product.is_active == True)
    
    if product_type:
        query = query.filter(Product.product_type == product_type)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if search:
        search_fmt = f"%{search}%"
        query = query.filter((Product.name.ilike(search_fmt)) | (Product.code.ilike(search_fmt)))
    if low_stock_only:
        query = query.filter(Product.current_stock <= Product.min_stock)
        
    return query.order_by(Product.name).all()

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product

@router.post("/", response_model=ProductResponse)
def create_product(
    prod_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(Product).filter(Product.code == prod_in.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="El código de producto ya existe")
    
    product = Product(
        code=prod_in.code,
        name=prod_in.name,
        description=prod_in.description,
        category_id=prod_in.category_id,
        product_type=prod_in.product_type,
        unit=prod_in.unit.upper(),
        cost_price=prod_in.cost_price,
        sale_price=prod_in.sale_price,
        current_stock=prod_in.current_stock,
        min_stock=prod_in.min_stock,
        expiry_date=prod_in.expiry_date,
        is_active=prod_in.is_active
    )
    db.add(product)
    db.flush()
    
    # Register initial movement if stock > 0
    if prod_in.current_stock > 0:
        movement = InventoryMovement(
            product_id=product.id,
            user_id=current_user.id,
            movement_type=MovementType.AJUSTE_POSITIVO,
            quantity=prod_in.current_stock,
            previous_stock=0.0,
            new_stock=prod_in.current_stock,
            reference="INVENTARIO_INICIAL",
            reason="Carga de inventario inicial"
        )
        db.add(movement)
        
    db.commit()
    db.refresh(product)
    return product

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    prod_in: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    update_data = prod_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
        
    db.commit()
    db.refresh(product)
    return product

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    product.is_active = False # Soft delete
    db.commit()
    return {"message": "Producto desactivado correctamente"}
