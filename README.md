# Sistema de Gestión de Inventario y Ventas para Panadería

**Trabajo Final de Grado (TFG) - Ingeniería en Informática**  
**Universidad Gran Asunción (UNIGRAN) - Sede Capiatá**  
**Autor:** Bruno Matías Báez Medina  

---

## 📌 Descripción del Proyecto

El **Sistema de Gestión de Panadería** es una solución integral diseñada para automatizar y optimizar los procesos operativos, el control de inventario, la planificación de la producción y la gestión de ventas de panaderías y confiterías. 

Resuelve problemáticas críticas como el desabastecimiento de materias primas, pérdidas por vencimiento de insumos perecederos, falta de control en el rendimiento de recetas (BOM - *Bill of Materials*), cuadre de caja diaria y ausencia de reportes oportunos para la toma de decisiones.

---

## 🚀 Características y Módulos Principales

1. **Control de Inventario & Kardex Físico-Valorado:**
   - Clasificación por tipo: *Materias Primas* (harina, levadura, manteca, queso), *Productos Terminados* (panificados, facturas, chipas) e *Insumos/Empaques*.
   - Alertas automáticas en tiempo real de **Stock Crítico (Mínimo)** e **Insumos Próximos a Vencer** (< 15 días).
   - Auditoría completa de movimientos (Entradas por compra, Salidas por venta, Consumo en cuadra, Entrada de horneado, Mermas y Ajustes).

2. **Módulo de Producción & Fórmulas Estandarizadas (Recetas / BOM):**
   - Definición de recetas con proporciones exactas de insumos según rendimiento.
   - Cálculo automático de insumos requeridos para lotes de cualquier tamaño.
   - Verificación de stock disponible antes de hornear.
   - Descuento automático de materias primas e ingreso de productos terminados al inventario en un solo clic.

3. **Punto de Venta Rápido (POS) para Mostrador:**
   - Interfaz táctil y rápida con buscador en tiempo real y filtrado por categorías.
   - Selección de cliente (Consumidor Final o RUC/CI).
   - Métodos de pago múltiples: Efectivo, Tarjeta, Transferencia (SIPAP) y QR.
   - Cálculo instantáneo de vuelto en Guaraníes (Gs.) y emisión de ticket.

4. **Gestión de Compras & Proveedores:**
   - Registro de facturas de compra con detalle de insumos adquiridos.
   - Actualización automática del precio de costo y stock.
   - Control de vencimientos por lote de compra.

5. **Control de Caja y Arqueo Diario:**
   - Apertura con fondo de cambio inicial.
   - Control de ingresos por ventas en efectivo.
   - Cierre de caja con arqueo físico y detección automática de sobrantes o faltantes.

6. **Reportes y Analítica:**
   - Dashboard interactivo con indicadores clave de rendimiento (KPIs).
   - Gráfico de evolución de ventas diarias.
   - Exportación de inventario valorizado a formato **CSV / Excel**.
   - Documentación interactiva de API con **Swagger OpenAPI**.

---

## 🛠️ Stack Tecnológico

* **Backend:** Python 3.13 + [FastAPI](https://fastapi.tiangolo.com/) (Asíncrono, Alto Rendimiento, OpenAPI 3.0)
* **Base de Datos:** SQLite / PostgreSQL mediante [SQLAlchemy ORM](https://www.sqlalchemy.org/) (Cumplimiento ACID)
* **Seguridad & Autenticación:** JWT (*JSON Web Tokens*) + Cifrado `bcrypt` con control de roles (`ADMIN`, `CAJERO`, `PANADERO`)
* **Frontend:** HTML5, CSS3 ([Tailwind CSS](https://tailwindcss.com/)), JavaScript Moderno (ES6+), [Chart.js](https://www.chartjs.org/) y [SweetAlert2](https://sweetalert2.github.io/)

---

## 📋 Estructura del Directorio

```text
sistema-gestion-panaderia/
├── app/
│   ├── config.py           # Configuración general y variables de entorno
│   ├── database.py         # Conexión SQLAlchemy y gestión de sesiones
│   ├── main.py             # Punto de entrada de la aplicación FastAPI
│   ├── models/             # Modelos de base de datos relacionales
│   │   └── models.py
│   ├── schemas/            # Esquemas de validación y serialización Pydantic
│   │   └── schemas.py
│   ├── routers/            # Endpoints REST de la API
│   │   ├── auth.py
│   │   ├── products.py
│   │   ├── suppliers.py
│   │   ├── customers.py
│   │   ├── purchases.py
│   │   ├── sales.py
│   │   ├── production.py
│   │   ├── inventory.py
│   │   ├── reports.py
│   │   └── cash.py
│   ├── services/           # Lógica de negocio y seguridad
│   │   └── auth_service.py
│   └── static/             # Frontend Web SPA (HTML, JS, CSS)
│       ├── index.html
│       └── js/
│           └── app.js
├── seed_data.py            # Script para poblar la base de datos con datos de panadería
├── requirements.txt        # Dependencias de Python
├── start.bat               # Ejecutor rápido para Windows
├── start.ps1               # Script PowerShell de ejecución
└── README.md               # Documentación oficial del proyecto
```

---

## ⚡ Instalación y Puesta en Marcha

### 1. Clonar el repositorio
```bash
git clone https://github.com/brunobaezmed/sistema-gestion-panaderia.git
cd sistema-gestion-panaderia
```

### 2. Crear y activar el entorno virtual
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Instalar las dependencias
```bash
pip install -r requirements.txt
```

### 4. Inicializar la Base de Datos con datos de demostración
```bash
python seed_data.py
```

### 5. Iniciar el servidor
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
O simplemente haciendo doble clic en `start.bat`.

---

## 🌐 Acceso al Sistema

* **Interfaz Web del Sistema:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **Documentación Interactiva Swagger (API Docs):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **Especificación ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 👥 Credenciales de Acceso Inicial

| Usuario | Contraseña | Rol / Perfil | Alcance |
| :--- | :--- | :--- | :--- |
| **admin** | `admin123` | **ADMIN** | Acceso total al sistema, reportes, usuarios y configuraciones. |
| **cajero** | `cajero123` | **CAJERO** | Punto de Venta (POS), registro de cobros y apertura/cierre de caja. |
| **panadero** | `panadero123` | **PANADERO** | Consulta de recetas, ejecución de órdenes de producción y mermas. |

---

## 📄 Licencia y Derechos

Desarrollado por **Bruno Matías Báez Medina** para la carrera de **Ingeniería en Informática**, Facultad de Ciencias Empresariales y Tecnología, Universidad Gran Asunción (UNIGRAN).
