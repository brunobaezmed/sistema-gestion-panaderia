from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.models import Supplier, User
from app.schemas.schemas import SupplierCreate, SupplierResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/suppliers", tags=["Proveedores"])

@router.get("/", response_model=List[SupplierResponse])
def list_suppliers(search: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Supplier)
    if search:
        search_fmt = f"%{search}%"
        query = query.filter((Supplier.name.ilike(search_fmt)) | (Supplier.ruc.ilike(search_fmt)))
    return query.order_by(Supplier.name).all()

@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return supplier

@router.post("/", response_model=SupplierResponse)
def create_supplier(
    sup_in: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(Supplier).filter(Supplier.ruc == sup_in.ruc).first()
    if existing:
        raise HTTPException(status_code=400, detail="El RUC del proveedor ya está registrado")
    
    supplier = Supplier(**sup_in.dict())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier

@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    sup_in: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    for key, value in sup_in.dict().items():
        setattr(supplier, key, value)
        
    db.commit()
    db.refresh(supplier)
    return supplier
