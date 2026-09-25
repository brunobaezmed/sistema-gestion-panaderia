from datetime import datetime, timedelta
from app.database import SessionLocal, engine, Base
from app.models.models import (
    User, UserRole, Category, Warehouse, Product, ProductType,
    Supplier, Customer, Recipe, RecipeDetail, InventoryMovement, MovementType
)
from app.services.auth_service import get_password_hash

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if already seeded
        if db.query(User).count() > 0:
            print("La base de datos ya contiene datos iniciales.")
            return

        print("Poblando base de datos inicial con datos de Panadería en Capiatá...")
        
        # 1. Usuarios del Sistema
        users = [
            User(
                username="admin",
                full_name="Bruno Báez (Administrador)",
                email="admin@panaderia.com.py",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.ADMIN
            ),
            User(
                username="cajero",
                full_name="María González (Caja Mostrador)",
                email="caja@panaderia.com.py",
                hashed_password=get_password_hash("cajero123"),
                role=UserRole.CAJERO
            ),
            User(
                username="panadero",
                full_name="Carlos Benítez (Maestro Panadero)",
                email="produccion@panaderia.com.py",
                hashed_password=get_password_hash("panadero123"),
                role=UserRole.PANADERO
            )
        ]
        db.add_all(users)
        db.flush()
        admin_user = users[0]

        # 2. Categorías
        cat_harinas = Category(name="Harinas e Insumos Secos", description="Harinas 000, 0000, almidón, etc.")
        cat_levaduras = Category(name="Levaduras y Mejoradores", description="Levaduras frescas, secas y aditivos")
        cat_grasas = Category(name="Grasas y Lácteos", description="Mantecas, margarinas, queso paraguay, leche")
        cat_panificados = Category(name="Panificados Tradicionales", description="Pan francés, felipe, trincha, galletas")
        cat_reposteria = Category(name="Facturas y Confitería", description="Medialunas, tortas, masas finas")
        cat_tradicional = Category(name="Típicos Paraguayos", description="Chipa almidón, chipa guasu, mbeju")
        
        db.add_all([cat_harinas, cat_levaduras, cat_grasas, cat_panificados, cat_reposteria, cat_tradicional])
        db.flush()

        # 3. Depósitos
        w1 = Warehouse(name="Depósito Central de Insumos", location="Planta Baja - Galpón Posterior")
        w2 = Warehouse(name="Cuadra de Producción", location="Área de Hornos y Amasadoras")
        w3 = Warehouse(name="Salón de Ventas / Mostrador", location="Atención al Público - Frente")
        db.add_all([w1, w2, w3])
        db.flush()

        # 4. Proveedores
        sup1 = Supplier(
            ruc="80012345-6",
            name="Molinos Harineros del Paraguay S.A.",
            phone="021-582-100",
            email="ventas@molinospy.com.py",
            address="Ruta D027 Km 21, Capiatá",
            contact_person="Ing. Roberto Almirón"
        )
        sup2 = Supplier(
            ruc="80067890-1",
            name="Distribuidora San Roque Insumos Panaderos",
            phone="021-574-900",
            email="contacto@sanroqueinsumos.com.py",
            address="Avda. Mcal. Estigarribia Km 14, San Lorenzo",
            contact_person="Lic. Patricia Bogado"
        )
        db.add_all([sup1, sup2])
        db.flush()

        # 5. Clientes
        c1 = Customer(
            document_number="44444401-7",
            name="Consumidor Final",
            phone="0981-000-000",
            email="mostrador@panaderia.com.py",
            address="Capiatá"
        )
        c2 = Customer(
            document_number="3584123-4",
            name="Despensa El Ahorro (Capiatá Centro)",
            phone="0971-223-344",
            email="elahorro@gmail.com",
            address="Barrio San Roque, Capiatá"
        )
        db.add_all([c1, c2])
        db.flush()

        # 6. Materias Primas e Insumos
        now = datetime.utcnow()
        mp_harina = Product(
            code="MP-001",
            name="Harina de Trigo 000 Especial (Bolsa 50kg)",
            description="Harina panadera de alta fuerza",
            category_id=cat_harinas.id,
            product_type=ProductType.MATERIA_PRIMA,
            unit="KG",
            cost_price=4500.0,
            sale_price=0.0,
            current_stock=500.0,
            min_stock=100.0,
            expiry_date=now + timedelta(days=90)
        )
        mp_levadura = Product(
            code="MP-002",
            name="Levadura Fresca Prensada",
            description="Bloque de levadura fresca de 500g",
            category_id=cat_levaduras.id,
            product_type=ProductType.MATERIA_PRIMA,
            unit="KG",
            cost_price=18000.0,
            sale_price=0.0,
            current_stock=25.0,
            min_stock=10.0,
            expiry_date=now + timedelta(days=12) # Alerta próxima a vencer
        )
        mp_manteca = Product(
            code="MP-003",
            name="Margarina / Manteca Vegetal",
            description="Grasa especial para panificación",
            category_id=cat_grasas.id,
            product_type=ProductType.MATERIA_PRIMA,
            unit="KG",
            cost_price=16000.0,
            sale_price=0.0,
            current_stock=60.0,
            min_stock=15.0,
            expiry_date=now + timedelta(days=120)
        )
        mp_sal = Product(
            code="MP-004",
            name="Sal Fina Entrefina Yodada",
            description="Sal para masa",
            category_id=cat_harinas.id,
            product_type=ProductType.MATERIA_PRIMA,
            unit="KG",
            cost_price=2500.0,
            sale_price=0.0,
            current_stock=40.0,
            min_stock=10.0,
            expiry_date=now + timedelta(days=365)
        )
        mp_almidon = Product(
            code="MP-005",
            name="Almidón de Mandioca Refinado",
            description="Almidón para elaboración de chipas",
            category_id=cat_harinas.id,
            product_type=ProductType.MATERIA_PRIMA,
            unit="KG",
            cost_price=8500.0,
            sale_price=0.0,
            current_stock=120.0,
            min_stock=30.0,
            expiry_date=now + timedelta(days=180)
        )
        mp_queso = Product(
            code="MP-006",
            name="Queso Paraguay Criollo",
            description="Queso estacionado para masa de chipa",
            category_id=cat_grasas.id,
            product_type=ProductType.MATERIA_PRIMA,
            unit="KG",
            cost_price=36000.0,
            sale_price=0.0,
            current_stock=8.0, # Alerta de bajo stock (min es 15)
            min_stock=15.0,
            expiry_date=now + timedelta(days=14)
        )
        
        # 7. Productos Terminados (Para Venta en Mostrador)
        pt_frances = Product(
            code="PT-101",
            name="Pan Francés Tradicional",
            description="Pan caliente crujiente de primera calidad",
            category_id=cat_panificados.id,
            product_type=ProductType.PRODUCTO_TERMINADO,
            unit="KG",
            cost_price=5000.0,
            sale_price=9000.0,
            current_stock=60.0,
            min_stock=20.0
        )
        pt_felipe = Product(
            code="PT-102",
            name="Pan Felipe / Trincha",
            description="Pan alargado de corteza dorada",
            category_id=cat_panificados.id,
            product_type=ProductType.PRODUCTO_TERMINADO,
            unit="KG",
            cost_price=5500.0,
            sale_price=10000.0,
            current_stock=35.0,
            min_stock=15.0
        )
        pt_chipa = Product(
            code="PT-201",
            name="Chipa Almidón Tradicional (Argolla)",
            description="Tradicional chipa recién horneada",
            category_id=cat_tradicional.id,
            product_type=ProductType.PRODUCTO_TERMINADO,
            unit="UNIDAD",
            cost_price=2500.0,
            sale_price=5000.0,
            current_stock=90.0,
            min_stock=25.0
        )
        pt_medialuna = Product(
            code="PT-301",
            name="Medialunas de Manteca Almibaradas",
            description="Facturas dulces tradicionales",
            category_id=cat_reposteria.id,
            product_type=ProductType.PRODUCTO_TERMINADO,
            unit="DOCENA",
            cost_price=18000.0,
            sale_price=36000.0,
            current_stock=12.0,
            min_stock=5.0
        )

        all_products = [
            mp_harina, mp_levadura, mp_manteca, mp_sal, mp_almidon, mp_queso,
            pt_frances, pt_felipe, pt_chipa, pt_medialuna
        ]
        db.add_all(all_products)
        db.flush()

        # Registrar Kardex inicial para cada producto
        for p in all_products:
            mov = InventoryMovement(
                product_id=p.id,
                user_id=admin_user.id,
                movement_type=MovementType.AJUSTE_POSITIVO,
                quantity=p.current_stock,
                previous_stock=0.0,
                new_stock=p.current_stock,
                reference="CARGA_INICIAL",
                reason="Inventario inicial de apertura"
            )
            db.add(mov)

        # 8. Recetas / Fórmulas de Producción
        # Receta Pan Francés: Para 50 kg de pan -> 35 kg harina, 1.2 kg levadura, 0.7 kg sal, 0.5 kg manteca
        receta_pan = Recipe(
            product_id=pt_frances.id,
            name="Fórmula Estándar - Pan Francés (Bacha 50 Kg)",
            description="Receta para horneado continuo en horno rotativo",
            yield_quantity=50.0,
            instructions="1. Amasar harina, sal y agua durante 12 min. 2. Añadir levadura y manteca. 3. Sobar y armar piezas. 4. Fermentar 90 min a 28°C. 5. Hornear con vapor a 220°C por 22 min."
        )
        db.add(receta_pan)
        db.flush()
        
        db.add_all([
            RecipeDetail(recipe_id=receta_pan.id, ingredient_id=mp_harina.id, quantity=35.0),
            RecipeDetail(recipe_id=receta_pan.id, ingredient_id=mp_levadura.id, quantity=1.2),
            RecipeDetail(recipe_id=receta_pan.id, ingredient_id=mp_sal.id, quantity=0.7),
            RecipeDetail(recipe_id=receta_pan.id, ingredient_id=mp_manteca.id, quantity=0.5)
        ])

        # Receta Chipa Almidón: Para 50 unidades -> 5 kg almidón, 3.5 kg queso paraguay, 1 kg manteca, 0.1 kg sal
        receta_chipa = Recipe(
            product_id=pt_chipa.id,
            name="Fórmula Tradicional - Chipa de Almidón (50 Unid)",
            description="Receta tradicional paraguaya",
            yield_quantity=50.0,
            instructions="1. Batir grasa de cerdo/manteca con queso paraguay desmenuzado. 2. Agregar salmuera de anís. 3. Incorporar almidón tamizado. 4. Amasar, moldear argollas y hornear a 250°C por 18 min."
        )
        db.add(receta_chipa)
        db.flush()

        db.add_all([
            RecipeDetail(recipe_id=receta_chipa.id, ingredient_id=mp_almidon.id, quantity=5.0),
            RecipeDetail(recipe_id=receta_chipa.id, ingredient_id=mp_queso.id, quantity=3.5),
            RecipeDetail(recipe_id=receta_chipa.id, ingredient_id=mp_manteca.id, quantity=1.0),
            RecipeDetail(recipe_id=receta_chipa.id, ingredient_id=mp_sal.id, quantity=0.1)
        ])

        db.commit()
        print("¡Base de datos inicializada y poblada exitosamente con datos de la panadería!")
    except Exception as e:
        db.rollback()
        print(f"Error al poblar la base de datos: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
