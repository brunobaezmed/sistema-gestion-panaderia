from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.models import UserRole, ProductType, MovementType, PaymentMethod, CashRegisterStatus

# ==================== AUTH & USERS ====================
class UserBase(BaseModel):
    username: str
    full_name: str
    email: Optional[str] = None
    role: UserRole = UserRole.CAJERO
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

# ==================== CATEGORIES & WAREHOUSES ====================
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    class Config:
        from_attributes = True

class WarehouseBase(BaseModel):
    name: str
    location: Optional[str] = None
    description: Optional[str] = None

class WarehouseResponse(WarehouseBase):
    id: int
    class Config:
        from_attributes = True

# ==================== PRODUCTS ====================
class ProductBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    product_type: ProductType = ProductType.PRODUCTO_TERMINADO
    unit: str = "UNIDAD"
    cost_price: float = 0.0
    sale_price: float = 0.0
    current_stock: float = 0.0
    min_stock: float = 5.0
    expiry_date: Optional[datetime] = None
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    product_type: Optional[ProductType] = None
    unit: Optional[str] = None
    cost_price: Optional[float] = None
    sale_price: Optional[float] = None
    min_stock: Optional[float] = None
    expiry_date: Optional[datetime] = None
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    category: Optional[CategoryResponse] = None

    class Config:
        from_attributes = True

# ==================== RECIPES / PRODUCTION ====================
class RecipeDetailBase(BaseModel):
    ingredient_id: int
    quantity: float

class RecipeDetailCreate(RecipeDetailBase):
    pass

class RecipeDetailResponse(RecipeDetailBase):
    id: int
    ingredient: Optional[ProductResponse] = None

    class Config:
        from_attributes = True

class RecipeBase(BaseModel):
    product_id: int
    name: str
    description: Optional[str] = None
    yield_quantity: float = 1.0
    instructions: Optional[str] = None

class RecipeCreate(RecipeBase):
    details: List[RecipeDetailCreate]

class RecipeResponse(RecipeBase):
    id: int
    created_at: datetime
    product: Optional[ProductResponse] = None
    details: List[RecipeDetailResponse] = []

    class Config:
        from_attributes = True

class ProductionOrderCreate(BaseModel):
    recipe_id: int
    quantity_to_produce: float
    notes: Optional[str] = None

class ProductionOrderResponse(BaseModel):
    id: int
    order_number: str
    recipe_id: int
    user_id: int
    quantity_to_produce: float
    status: str
    notes: Optional[str] = None
    created_at: datetime
    recipe: Optional[RecipeResponse] = None

    class Config:
        from_attributes = True

# ==================== SUPPLIERS & CUSTOMERS ====================
class SupplierBase(BaseModel):
    ruc: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None

class SupplierCreate(SupplierBase):
    pass

class SupplierResponse(SupplierBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class CustomerBase(BaseModel):
    document_number: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ==================== PURCHASES ====================
class PurchaseDetailCreate(BaseModel):
    product_id: int
    quantity: float
    unit_cost: float
    expiry_date: Optional[datetime] = None

class PurchaseCreate(BaseModel):
    invoice_number: str
    supplier_id: int
    notes: Optional[str] = None
    details: List[PurchaseDetailCreate]

class PurchaseDetailResponse(BaseModel):
    id: int
    product_id: int
    quantity: float
    unit_cost: float
    subtotal: float
    expiry_date: Optional[datetime] = None
    product: Optional[ProductResponse] = None

    class Config:
        from_attributes = True

class PurchaseResponse(BaseModel):
    id: int
    invoice_number: str
    supplier_id: int
    user_id: int
    total_amount: float
    notes: Optional[str] = None
    created_at: datetime
    supplier: Optional[SupplierResponse] = None
    details: List[PurchaseDetailResponse] = []

    class Config:
        from_attributes = True

# ==================== SALES ====================
class SaleDetailCreate(BaseModel):
    product_id: int
    quantity: float
    unit_price: float

class SaleCreate(BaseModel):
    customer_id: Optional[int] = None
    payment_method: PaymentMethod = PaymentMethod.EFECTIVO
    amount_paid: float
    details: List[SaleDetailCreate]

class SaleDetailResponse(BaseModel):
    id: int
    product_id: int
    quantity: float
    unit_price: float
    subtotal: float
    product: Optional[ProductResponse] = None

    class Config:
        from_attributes = True

class SaleResponse(BaseModel):
    id: int
    invoice_number: str
    customer_id: Optional[int] = None
    user_id: int
    payment_method: PaymentMethod
    total_amount: float
    amount_paid: float
    change_given: float
    created_at: datetime
    customer: Optional[CustomerResponse] = None
    details: List[SaleDetailResponse] = []

    class Config:
        from_attributes = True

# ==================== INVENTORY MOVEMENTS / ADJUSTMENTS ====================
class InventoryAdjustmentCreate(BaseModel):
    product_id: int
    movement_type: MovementType # AJUSTE_POSITIVO, AJUSTE_NEGATIVO, MERMA
    quantity: float
    reason: str

class InventoryMovementResponse(BaseModel):
    id: int
    product_id: int
    user_id: int
    movement_type: MovementType
    quantity: float
    previous_stock: float
    new_stock: float
    reference: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime
    product: Optional[ProductResponse] = None
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True

# ==================== CASH REGISTER ====================
class CashRegisterOpen(BaseModel):
    initial_cash: float
    notes: Optional[str] = None

class CashRegisterClose(BaseModel):
    final_cash: float
    notes: Optional[str] = None

class CashRegisterResponse(BaseModel):
    id: int
    user_id: int
    initial_cash: float
    final_cash: Optional[float] = None
    expected_cash: Optional[float] = None
    difference: Optional[float] = None
    status: CashRegisterStatus
    opened_at: datetime
    closed_at: Optional[datetime] = None
    notes: Optional[str] = None
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True

# ==================== DASHBOARD / REPORT METRICS ====================
class DashboardMetrics(BaseModel):
    total_sales_today: float
    sales_count_today: int
    low_stock_count: int
    expiring_soon_count: int
    total_inventory_value: float
    recent_sales: List[SaleResponse]
    low_stock_products: List[ProductResponse]
    expiring_products: List[ProductResponse]
