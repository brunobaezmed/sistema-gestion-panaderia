from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import io
import csv

from app.database import get_db
from app.models.models import (
    Product, Sale, SaleDetail, Purchase, ProductionOrder,
    InventoryMovement, MovementType, User
)
from app.schemas.schemas import DashboardMetrics, ProductResponse, SaleResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/reports", tags=["Reportes y Estadísticas"])

@router.get("/dashboard", response_model=DashboardMetrics)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    today_start = datetime.combine(date.today(), datetime.min.time())
    
    # Sales today
    sales_today_query = db.query(
        func.coalesce(func.sum(Sale.total_amount), 0.0),
        func.count(Sale.id)
    ).filter(Sale.created_at >= today_start).first()
    
    total_sales_today = float(sales_today_query[0])
    sales_count_today = int(sales_today_query[1])
    
    # Low stock
    low_stock_query = db.query(Product).filter(
        Product.is_active == True,
        Product.current_stock <= Product.min_stock
    )
    low_stock_count = low_stock_query.count()
    low_stock_products = low_stock_query.limit(10).all()
    
    # Expiring soon (next 15 days)
    threshold = datetime.utcnow() + timedelta(days=15)
    expiring_query = db.query(Product).filter(
        Product.is_active == True,
        Product.expiry_date != None,
        Product.expiry_date <= threshold
    )
    expiring_soon_count = expiring_query.count()
    expiring_products = expiring_query.order_by(Product.expiry_date.asc()).limit(10).all()
    
    # Total inventory valuation
    inventory_val = db.query(
        func.coalesce(func.sum(Product.current_stock * Product.cost_price), 0.0)
    ).filter(Product.is_active == True).scalar()
    
    # Recent sales
    recent_sales = db.query(Sale).order_by(Sale.created_at.desc()).limit(10).all()
    
    return {
        "total_sales_today": total_sales_today,
        "sales_count_today": sales_count_today,
        "low_stock_count": low_stock_count,
        "expiring_soon_count": expiring_soon_count,
        "total_inventory_value": float(inventory_val),
        "recent_sales": recent_sales,
        "low_stock_products": low_stock_products,
        "expiring_products": expiring_products
    }

@router.get("/top-products")
def get_top_selling_products(limit: int = 10, db: Session = Depends(get_db)):
    # Top products by quantity sold
    results = db.query(
        Product.name,
        Product.unit,
        func.sum(SaleDetail.quantity).label("total_sold"),
        func.sum(SaleDetail.subtotal).label("total_revenue")
    ).join(SaleDetail, Product.id == SaleDetail.product_id)\
     .group_by(Product.id)\
     .order_by(func.sum(SaleDetail.quantity).desc())\
     .limit(limit).all()
     
    return [
        {
            "name": row[0],
            "unit": row[1],
            "total_sold": float(row[2]),
            "total_revenue": float(row[3])
        } for row in results
    ]

@router.get("/sales-chart")
def get_sales_chart_data(days: int = 7, db: Session = Depends(get_db)):
    start_date = datetime.utcnow() - timedelta(days=days)
    sales = db.query(
        func.date(Sale.created_at).label("sale_date"),
        func.sum(Sale.total_amount).label("daily_total"),
        func.count(Sale.id).label("daily_count")
    ).filter(Sale.created_at >= start_date)\
     .group_by(func.date(Sale.created_at))\
     .order_by(func.date(Sale.created_at).asc()).all()
     
    labels = []
    data = []
    for row in sales:
        labels.append(str(row[0]))
        data.append(float(row[1]))
        
    return {"labels": labels, "data": data}

@router.get("/export/inventory-csv")
def export_inventory_csv(db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.is_active == True).order_by(Product.name).all()
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["Codigo", "Nombre", "Tipo", "Unidad", "Precio Costo (Gs)", "Precio Venta (Gs)", "Stock Actual", "Stock Minimo", "Valor Total (Gs)", "Vencimiento"])
    
    for p in products:
        val_total = p.current_stock * p.cost_price
        venc = p.expiry_date.strftime("%d/%m/%Y") if p.expiry_date else "N/A"
        writer.writerow([
            p.code,
            p.name,
            p.product_type.value,
            p.unit,
            f"{p.cost_price:,.0f}",
            f"{p.sale_price:,.0f}",
            f"{p.current_stock:.2f}",
            f"{p.min_stock:.2f}",
            f"{val_total:,.0f}",
            venc
        ])
        
    output.seek(0)
    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=inventario_panaderia_{date.today()}.csv"
    return response
