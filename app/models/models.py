from datetime import datetime
import enum
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum, Numeric
)
from sqlalchemy.orm import relationship
from app.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    CAJERO = "CAJERO"
    PANADERO = "PANADERO"

class ProductType(str, enum.Enum):
    MATERIA_PRIMA = "MATERIA_PRIMA"       # Harina, levadura, azúcar, etc.
    PRODUCTO_TERMINADO = "PRODUCTO_TERMINADO" # Pan francés, medialunas, etc.
    INSUMO = "INSUMO"                     # Bolsas, cajas, envoltorios

class MovementType(str, enum.Enum):
    COMPRA = "COMPRA"                     # Entrada por compra
    VENTA = "VENTA"                       # Salida por venta
    PRODUCCION_ENTRADA = "PRODUCCION_ENTRADA" # Entrada de producto elaborado
    PRODUCCION_CONSUMO = "PRODUCCION_CONSUMO" # Salida de materias primas
    TRANSFERENCIA = "TRANSFERENCIA"       # Entre depósitos
    AJUSTE_POSITIVO = "AJUSTE_POSITIVO"   # Ajuste inventario sobrante
    AJUSTE_NEGATIVO = "AJUSTE_NEGATIVO"   # Ajuste inventario faltante
    MERMA = "MERMA"                       # Desperdicio / Vencido

class PaymentMethod(str, enum.Enum):
    EFECTIVO = "EFECTIVO"
    TARJETA = "TARJETA"
    TRANSFERENCIA = "TRANSFERENCIA"
    QR = "QR"

class CashRegisterStatus(str, enum.Enum):
    ABIERTA = "ABIERTA"
    CERRADA = "CERRADA"

# ==================== USUARIOS ====================
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CAJERO, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sales = relationship("Sale", back_populates="user")
    purchases = relationship("Purchase", back_populates="user")
    productions = relationship("ProductionOrder", back_populates="user")
    movements = relationship("InventoryMovement", back_populates="user")
    cash_registers = relationship("CashRegister", back_populates="user")

# ==================== CATEGORÍAS & DEPÓSITOS ====================
class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    
    products = relationship("Product", back_populates="category")

class Warehouse(Base):
    __tablename__ = "warehouses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False) # Depósito Central, Cuadra de Producción, Salón de Ventas
    location = Column(String(255), nullable=True)
    description = Column(String(255), nullable=True)

# ==================== PRODUCTOS / MATERIAS PRIMAS ====================
class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(150), index=True, nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    product_type = Column(Enum(ProductType), default=ProductType.PRODUCTO_TERMINADO, nullable=False)
    unit = Column(String(20), default="UNIDAD", nullable=False) # KG, G, LITRO, UNIDAD, DOCENA
    
    cost_price = Column(Float, default=0.0) # Precio de costo en Guaraníes (PYG)
    sale_price = Column(Float, default=0.0) # Precio de venta en Guaraníes (PYG)
    
    current_stock = Column(Float, default=0.0)
    min_stock = Column(Float, default=5.0)  # Nivel para disparar alerta
    
    expiry_date = Column(DateTime, nullable=True) # Para materias primas perecederas
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category", back_populates="products")
    recipe = relationship("Recipe", back_populates="product", uselist=False)
    recipe_ingredients = relationship("RecipeDetail", back_populates="ingredient")
    sale_details = relationship("SaleDetail", back_populates="product")
    purchase_details = relationship("PurchaseDetail", back_populates="product")
    movements = relationship("InventoryMovement", back_populates="product")

# ==================== RECETAS / FÓRMULAS DE PRODUCCIÓN ====================
class Recipe(Base):
    __tablename__ = "recipes"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True, nullable=False) # Producto final
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    yield_quantity = Column(Float, default=1.0) # Cantidad producida con esta receta (ej: 10 kg pan)
    instructions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="recipe")
    details = relationship("RecipeDetail", back_populates="recipe", cascade="all, delete-orphan")
    production_orders = relationship("ProductionOrder", back_populates="recipe")

class RecipeDetail(Base):
    __tablename__ = "recipe_details"
    
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("products.id"), nullable=False) # Materia prima
    quantity = Column(Float, nullable=False) # Cantidad requerida según unidad del insumo
    
    recipe = relationship("Recipe", back_populates="details")
    ingredient = relationship("Product", back_populates="recipe_ingredients")

# ==================== ÓRDENES DE PRODUCCIÓN ====================
class ProductionOrder(Base):
    __tablename__ = "production_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quantity_to_produce = Column(Float, nullable=False) # Cantidad de producto final
    status = Column(String(30), default="COMPLETADA") # PENDIENTE, EN_PROCESO, COMPLETADA
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    recipe = relationship("Recipe", back_populates="production_orders")
    user = relationship("User", back_populates="productions")

# ==================== PROVEEDORES & CLIENTES ====================
class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    ruc = Column(String(30), unique=True, index=True, nullable=False)
    name = Column(String(150), nullable=False)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)
    contact_person = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    purchases = relationship("Purchase", back_populates="supplier")

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    document_number = Column(String(30), unique=True, index=True, nullable=False) # CI o RUC
    name = Column(String(150), nullable=False)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sales = relationship("Sale", back_populates="customer")

# ==================== COMPRAS ====================
class Purchase(Base):
    __tablename__ = "purchases"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_amount = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    supplier = relationship("Supplier", back_populates="purchases")
    user = relationship("User", back_populates="purchases")
    details = relationship("PurchaseDetail", back_populates="purchase", cascade="all, delete-orphan")

class PurchaseDetail(Base):
    __tablename__ = "purchase_details"
    
    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_cost = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    expiry_date = Column(DateTime, nullable=True)

    purchase = relationship("Purchase", back_populates="details")
    product = relationship("Product", back_populates="purchase_details")

# ==================== VENTAS & DETALLES ====================
class Sale(Base):
    __tablename__ = "sales"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True) # Puede ser Consumidor Final
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.EFECTIVO, nullable=False)
    total_amount = Column(Float, default=0.0)
    amount_paid = Column(Float, default=0.0)
    change_given = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="sales")
    user = relationship("User", back_populates="sales")
    details = relationship("SaleDetail", back_populates="sale", cascade="all, delete-orphan")

class SaleDetail(Base):
    __tablename__ = "sale_details"
    
    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    sale = relationship("Sale", back_populates="details")
    product = relationship("Product", back_populates="sale_details")

# ==================== MOVIMIENTOS DE INVENTARIO / KARDEX ====================
class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    movement_type = Column(Enum(MovementType), nullable=False)
    quantity = Column(Float, nullable=False) # Positivo para entradas, negativo para salidas
    previous_stock = Column(Float, nullable=False)
    new_stock = Column(Float, nullable=False)
    reference = Column(String(100), nullable=True) # Ej: "Venta #001", "Orden Prod #OP-10", "Ajuste por Merma"
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="movements")
    user = relationship("User", back_populates="movements")

# ==================== CAJA DIARIA / ARQUEO ====================
class CashRegister(Base):
    __tablename__ = "cash_registers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    initial_cash = Column(Float, default=0.0)
    final_cash = Column(Float, nullable=True)
    expected_cash = Column(Float, nullable=True)
    difference = Column(Float, nullable=True)
    status = Column(Enum(CashRegisterStatus), default=CashRegisterStatus.ABIERTA, nullable=False)
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="cash_registers")
