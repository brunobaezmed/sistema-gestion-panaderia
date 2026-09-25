from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.models import Customer, User
from app.schemas.schemas import CustomerCreate, CustomerResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/customers", tags=["Clientes"])

@router.get("/", response_model=List[CustomerResponse])
def list_customers(search: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Customer)
    if search:
        search_fmt = f"%{search}%"
        query = query.filter((Customer.name.ilike(search_fmt)) | (Customer.document_number.ilike(search_fmt)))
    return query.order_by(Customer.name).all()

@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return customer

@router.post("/", response_model=CustomerResponse)
def create_customer(
    cust_in: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(Customer).filter(Customer.document_number == cust_in.document_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="El documento o RUC del cliente ya existe")
    
    customer = Customer(**cust_in.dict())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer

@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    cust_in: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    for key, value in cust_in.dict().items():
        setattr(customer, key, value)
        
    db.commit()
    db.refresh(customer)
    return customer
