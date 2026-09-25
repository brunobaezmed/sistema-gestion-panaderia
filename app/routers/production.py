from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.models import (
    Recipe, RecipeDetail, Product, ProductType,
    ProductionOrder, InventoryMovement, MovementType, User
)
from app.schemas.schemas import (
    RecipeCreate, RecipeResponse,
    ProductionOrderCreate, ProductionOrderResponse
)
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/production", tags=["Producción y Recetas"])

# ==================== RECETAS / FÓRMULAS ====================
@router.get("/recipes", response_model=List[RecipeResponse])
def list_recipes(db: Session = Depends(get_db)):
    return db.query(Recipe).all()

@router.get("/recipes/{recipe_id}", response_model=RecipeResponse)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    return recipe

@router.post("/recipes", response_model=RecipeResponse)
def create_recipe(
    recipe_in: RecipeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = db.query(Product).filter(Product.id == recipe_in.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto terminado no encontrado")
    
    existing = db.query(Recipe).filter(Recipe.product_id == recipe_in.product_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Este producto ya tiene una receta registrada")
        
    recipe = Recipe(
        product_id=recipe_in.product_id,
        name=recipe_in.name,
        description=recipe_in.description,
        yield_quantity=recipe_in.yield_quantity,
        instructions=recipe_in.instructions
    )
    db.add(recipe)
    db.flush()
    
    for item in recipe_in.details:
        ingredient = db.query(Product).filter(Product.id == item.ingredient_id).first()
        if not ingredient:
            raise HTTPException(status_code=404, detail=f"Ingrediente ID {item.ingredient_id} no encontrado")
        
        detail = RecipeDetail(
            recipe_id=recipe.id,
            ingredient_id=ingredient.id,
            quantity=item.quantity
        )
        db.add(detail)
        
    db.commit()
    db.refresh(recipe)
    return recipe

# ==================== EJECUCIÓN DE PRODUCCIÓN ====================
@router.get("/orders", response_model=List[ProductionOrderResponse])
def list_production_orders(db: Session = Depends(get_db)):
    return db.query(ProductionOrder).order_by(ProductionOrder.created_at.desc()).all()

@router.post("/orders", response_model=ProductionOrderResponse)
def execute_production(
    order_in: ProductionOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    recipe = db.query(Recipe).filter(Recipe.id == order_in.recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    
    if order_in.quantity_to_produce <= 0:
        raise HTTPException(status_code=400, detail="La cantidad a producir debe ser mayor a 0")
        
    # Multiplier based on recipe base yield
    multiplier = order_in.quantity_to_produce / recipe.yield_quantity
    
    # 1. Check raw materials stock availability
    for detail in recipe.details:
        required_qty = detail.quantity * multiplier
        if detail.ingredient.current_stock < required_qty:
            raise HTTPException(
                status_code=400,
                detail=f"Insumo insuficiente: '{detail.ingredient.name}'. Requerido: {required_qty:.2f} {detail.ingredient.unit}, Disponible: {detail.ingredient.current_stock:.2f} {detail.ingredient.unit}"
            )
            
    # Generate Order Number
    count_today = db.query(ProductionOrder).count() + 1
    order_num = f"OP-{datetime.now().strftime('%Y%m%d')}-{count_today:04d}"
    
    order = ProductionOrder(
        order_number=order_num,
        recipe_id=recipe.id,
        user_id=current_user.id,
        quantity_to_produce=order_in.quantity_to_produce,
        status="COMPLETADA",
        notes=order_in.notes
    )
    db.add(order)
    db.flush()
    
    # 2. Deduct raw materials (Consumption)
    for detail in recipe.details:
        required_qty = detail.quantity * multiplier
        prev_stock = detail.ingredient.current_stock
        detail.ingredient.current_stock -= required_qty
        
        movement = InventoryMovement(
            product_id=detail.ingredient.id,
            user_id=current_user.id,
            movement_type=MovementType.PRODUCCION_CONSUMO,
            quantity=-required_qty,
            previous_stock=prev_stock,
            new_stock=detail.ingredient.current_stock,
            reference=f"Orden Prod #{order.order_number}",
            reason=f"Consumo de insumo para elaborar {order_in.quantity_to_produce} {recipe.product.unit} de {recipe.product.name}"
        )
        db.add(movement)
        
    # 3. Add finished product to inventory (Production Entry)
    finished_prod = recipe.product
    prev_prod_stock = finished_prod.current_stock
    finished_prod.current_stock += order_in.quantity_to_produce
    
    prod_movement = InventoryMovement(
        product_id=finished_prod.id,
        user_id=current_user.id,
        movement_type=MovementType.PRODUCCION_ENTRADA,
        quantity=order_in.quantity_to_produce,
        previous_stock=prev_prod_stock,
        new_stock=finished_prod.current_stock,
        reference=f"Orden Prod #{order.order_number}",
        reason=f"Ingreso de producto terminado horneado/elaborado"
    )
    db.add(prod_movement)
    
    db.commit()
    db.refresh(order)
    return order
