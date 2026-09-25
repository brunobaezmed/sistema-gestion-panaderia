// ==========================================
// CONFIGURACIÓN & ESTADO GLOBAL
// ==========================================
const API_URL = '/api/v1';
let authToken = localStorage.getItem('bakery_token') || null;
let currentUser = JSON.parse(localStorage.getItem('bakery_user') || 'null');

let currentCart = [];
let allProducts = [];
let allCategories = [];
let allCustomers = [];
let allSuppliers = [];
let allRecipes = [];
let salesChartInstance = null;

// ==========================================
// INICIALIZACIÓN
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    if (authToken && currentUser) {
        showApp();
    } else {
        showLogin();
    }
});

function setupEventListeners() {
    // Login form
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    
    // POS filter/search
    document.getElementById('pos-search').addEventListener('input', filterPOSProducts);
    document.getElementById('pos-category-filter').addEventListener('change', filterPOSProducts);
    
    // Inventory filter/search
    document.getElementById('inv-search').addEventListener('input', filterInventoryTable);
    document.getElementById('inv-type-filter').addEventListener('change', filterInventoryTable);
    
    // Forms
    document.getElementById('product-create-form').addEventListener('submit', handleCreateProduct);
    document.getElementById('adjustment-form').addEventListener('submit', handleCreateAdjustment);
    document.getElementById('production-form').addEventListener('submit', handleExecuteProduction);
    document.getElementById('purchase-form').addEventListener('submit', handleCreatePurchase);
}

// ==========================================
// AUTENTICACIÓN
// ==========================================
async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value.trim();

    try {
        const res = await fetch(`${API_URL}/auth/login-json`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Error al iniciar sesión');

        authToken = data.access_token;
        currentUser = data.user;
        localStorage.setItem('bakery_token', authToken);
        localStorage.setItem('bakery_user', JSON.stringify(currentUser));

        Swal.fire({
            icon: 'success',
            title: `¡Bienvenido, ${currentUser.full_name}!`,
            text: `Rol: ${currentUser.role}`,
            timer: 1500,
            showConfirmButton: false
        });

        showApp();
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Error de acceso', text: err.message });
    }
}

function logout() {
    localStorage.removeItem('bakery_token');
    localStorage.removeItem('bakery_user');
    authToken = null;
    currentUser = null;
    location.reload();
}

function showLogin() {
    document.getElementById('login-modal').classList.remove('hidden');
    document.getElementById('app-container').classList.add('hidden');
}

function showApp() {
    document.getElementById('login-modal').classList.add('hidden');
    document.getElementById('app-container').classList.remove('hidden');

    document.getElementById('user-display-name').textContent = currentUser.full_name;
    document.getElementById('user-display-role').textContent = currentUser.role;

    switchTab('dashboard');
    loadInitialData();
}

// API Helper with JWT Header
async function fetchAuth(endpoint, options = {}) {
    options.headers = {
        ...options.headers,
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
    };
    const res = await fetch(`${API_URL}${endpoint}`, options);
    if (res.status === 401) {
        logout();
        throw new Error('Sesión expirada');
    }
    return res;
}

// ==========================================
// CARGA INICIAL DE DATOS
// ==========================================
async function loadInitialData() {
    try {
        await Promise.all([
            loadProducts(),
            loadCategories(),
            loadCustomers(),
            loadSuppliers(),
            loadRecipes()
        ]);
        loadDashboardData();
        loadCashStatus();
    } catch (err) {
        console.error('Error cargando datos iniciales:', err);
    }
}

async function loadProducts() {
    const res = await fetchAuth('/products/');
    allProducts = await res.json();
    renderInventoryTable(allProducts);
    renderPOSProducts(allProducts.filter(p => p.product_type === 'PRODUCTO_TERMINADO'));
}

async function loadCategories() {
    const res = await fetchAuth('/products/categories');
    allCategories = await res.json();
    
    // Populate select elements
    const posCatSelect = document.getElementById('pos-category-filter');
    const newProdCatSelect = document.getElementById('new-prod-cat');
    
    let optionsHtml = '<option value="">Todas las Categorías</option>';
    let modalCatOptions = '<option value="">Sin Categoría</option>';
    
    allCategories.forEach(c => {
        optionsHtml += `<option value="${c.id}">${c.name}</option>`;
        modalCatOptions += `<option value="${c.id}">${c.name}</option>`;
    });
    
    posCatSelect.innerHTML = optionsHtml;
    newProdCatSelect.innerHTML = modalCatOptions;
}

async function loadCustomers() {
    const res = await fetchAuth('/customers/');
    allCustomers = await res.json();
    const custSelect = document.getElementById('pos-customer-select');
    let html = '';
    allCustomers.forEach(c => {
        html += `<option value="${c.id}">${c.name} (${c.document_number})</option>`;
    });
    custSelect.innerHTML = html;
}

async function loadSuppliers() {
    const res = await fetchAuth('/suppliers/');
    allSuppliers = await res.json();
    const supSelect = document.getElementById('purch-supplier');
    let html = '';
    allSuppliers.forEach(s => {
        html += `<option value="${s.id}">${s.name} - RUC: ${s.ruc}</option>`;
    });
    supSelect.innerHTML = html;
    
    // Add default purchase line
    if (document.getElementById('purchase-lines-container').children.length === 0) {
        addPurchaseLine();
    }
}

async function loadRecipes() {
    const res = await fetchAuth('/production/recipes');
    allRecipes = await res.json();
    renderRecipesList(allRecipes);
    
    const recipeSelect = document.getElementById('prod-recipe-select');
    let html = '<option value="">-- Selecciona una fórmula registrada --</option>';
    allRecipes.forEach(r => {
        html += `<option value="${r.id}">${r.name} (Rinde: ${r.yield_quantity} ${r.product ? r.product.unit : ''})</option>`;
    });
    recipeSelect.innerHTML = html;
}

// ==========================================
// GESTIÓN DE TABS
// ==========================================
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.nav-tab').forEach(btn => btn.classList.remove('tab-active'));

    const activeTab = document.getElementById(`tab-${tabId}`);
    const activeBtn = document.getElementById(`tab-btn-${tabId}`);

    if (activeTab) activeTab.classList.remove('hidden');
    if (activeBtn) activeBtn.classList.add('tab-active');

    if (tabId === 'dashboard') loadDashboardData();
    if (tabId === 'reports') loadKardexMovements();
    if (tabId === 'cash') loadCashStatus();
    if (tabId === 'inventory') loadProducts();
}

// ==========================================
// 1. DASHBOARD & MÉTRICAS
// ==========================================
async function loadDashboardData() {
    try {
        const res = await fetchAuth('/reports/dashboard');
        const data = await res.json();

        document.getElementById('kpi-sales-today').textContent = `Gs. ${data.total_sales_today.toLocaleString('es-PY')}`;
        document.getElementById('kpi-sales-count').innerHTML = `<i class="fa-solid fa-receipt"></i> ${data.sales_count_today} transacciones`;
        document.getElementById('kpi-inventory-val').textContent = `Gs. ${data.total_inventory_value.toLocaleString('es-PY')}`;
        document.getElementById('kpi-low-stock-count').textContent = data.low_stock_count;
        document.getElementById('kpi-expiring-count').textContent = data.expiring_soon_count;

        // Header Alert Banner
        const totalAlerts = data.low_stock_count + data.expiring_soon_count;
        const alertBanner = document.getElementById('alert-banner');
        if (totalAlerts > 0) {
            alertBanner.classList.remove('hidden');
            document.getElementById('alert-text').textContent = `${totalAlerts} alertas críticas`;
        } else {
            alertBanner.classList.add('hidden');
        }

        // Alerts List
        const alertsList = document.getElementById('dashboard-alerts-list');
        let alertsHtml = '';
        
        data.low_stock_products.forEach(p => {
            alertsHtml += `
                <div class="p-2.5 bg-rose-50 border border-rose-200 rounded-xl flex items-center justify-between text-xs">
                    <div class="flex items-center gap-2">
                        <i class="fa-solid fa-triangle-exclamation text-rose-600"></i>
                        <div>
                            <p class="font-bold text-slate-800">${p.name}</p>
                            <p class="text-[10px] text-rose-700">Stock: <b>${p.current_stock} ${p.unit}</b> (Mínimo: ${p.min_stock})</p>
                        </div>
                    </div>
                    <span class="px-2 py-0.5 bg-rose-200 text-rose-800 text-[10px] font-bold rounded">Bajo Stock</span>
                </div>
            `;
        });

        data.expiring_products.forEach(p => {
            const expDate = p.expiry_date ? new Date(p.expiry_date).toLocaleDateString('es-PY') : 'N/A';
            alertsHtml += `
                <div class="p-2.5 bg-orange-50 border border-orange-200 rounded-xl flex items-center justify-between text-xs">
                    <div class="flex items-center gap-2">
                        <i class="fa-solid fa-clock text-orange-600"></i>
                        <div>
                            <p class="font-bold text-slate-800">${p.name}</p>
                            <p class="text-[10px] text-orange-700">Vence: <b>${expDate}</b></p>
                        </div>
                    </div>
                    <span class="px-2 py-0.5 bg-orange-200 text-orange-800 text-[10px] font-bold rounded">Próximo Vencimiento</span>
                </div>
            `;
        });

        if (!alertsHtml) {
            alertsHtml = '<div class="text-center py-8 text-emerald-600 text-xs font-semibold"><i class="fa-solid fa-circle-check text-2xl mb-1 block"></i>No hay alertas críticas pendientes.</div>';
        }
        alertsList.innerHTML = alertsHtml;

        // Recent Sales Table
        const recentTbody = document.getElementById('recent-sales-tbody');
        let salesHtml = '';
        data.recent_sales.forEach(s => {
            const sDate = new Date(s.created_at).toLocaleString('es-PY');
            salesHtml += `
                <tr class="hover:bg-slate-50 transition-colors">
                    <td class="py-2.5 px-3 font-bold text-slate-800">${s.invoice_number}</td>
                    <td class="py-2.5 px-3 text-slate-500">${sDate}</td>
                    <td class="py-2.5 px-3"><span class="px-2 py-0.5 bg-slate-100 rounded text-[10px] font-bold">${s.payment_method}</span></td>
                    <td class="py-2.5 px-3 text-right font-black text-amber-700">Gs. ${s.total_amount.toLocaleString('es-PY')}</td>
                </tr>
            `;
        });
        recentTbody.innerHTML = salesHtml || '<tr><td colspan="4" class="text-center py-4 text-slate-400">Sin ventas recientes</td></tr>';

        // Load Sales Chart
        loadSalesChart();
    } catch (err) {
        console.error('Error cargando métricas:', err);
    }
}

async function loadSalesChart() {
    try {
        const res = await fetchAuth('/reports/sales-chart?days=7');
        const chartData = await res.json();

        const ctx = document.getElementById('salesChart').getContext('2d');
        if (salesChartInstance) salesChartInstance.destroy();

        salesChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartData.labels.length ? chartData.labels : ['Hoy'],
                datasets: [{
                    label: 'Ventas (Gs.)',
                    data: chartData.data.length ? chartData.data : [0],
                    backgroundColor: 'rgba(217, 119, 6, 0.85)',
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: value => 'Gs. ' + value.toLocaleString('es-PY')
                        }
                    }
                }
            }
        });
    } catch (err) {
        console.error('Error cargando gráfico:', err);
    }
}

// ==========================================
// 2. PUNTO DE VENTA (POS)
// ==========================================
function renderPOSProducts(products) {
    const grid = document.getElementById('pos-products-grid');
    if (!products.length) {
        grid.innerHTML = '<div class="col-span-3 text-center py-10 text-slate-400 text-xs">No se encontraron productos disponibles</div>';
        return;
    }

    grid.innerHTML = products.map(p => `
        <div onclick="addToCart(${p.id})" class="cursor-pointer bg-slate-50 hover:bg-amber-50/80 border border-slate-200 hover:border-amber-400 rounded-xl p-3 transition-all flex flex-col justify-between shadow-sm group">
            <div>
                <div class="flex items-center justify-between text-[10px] text-slate-400 mb-1">
                    <span class="font-bold text-amber-700">${p.code}</span>
                    <span class="px-1.5 py-0.2 bg-slate-200 rounded font-semibold">${p.unit}</span>
                </div>
                <h4 class="font-bold text-slate-800 text-xs line-clamp-2 group-hover:text-amber-800">${p.name}</h4>
            </div>
            <div class="mt-3 flex items-center justify-between border-t border-slate-200 pt-2">
                <span class="text-xs font-black text-slate-900">Gs. ${p.sale_price.toLocaleString('es-PY')}</span>
                <span class="text-[10px] ${p.current_stock <= p.min_stock ? 'text-rose-600 font-bold' : 'text-slate-500'}">
                    Stock: ${p.current_stock}
                </span>
            </div>
        </div>
    `).join('');
}

function filterPOSProducts() {
    const search = document.getElementById('pos-search').value.toLowerCase();
    const catId = document.getElementById('pos-category-filter').value;

    const filtered = allProducts.filter(p => {
        const matchesType = p.product_type === 'PRODUCTO_TERMINADO';
        const matchesSearch = p.name.toLowerCase().includes(search) || p.code.toLowerCase().includes(search);
        const matchesCat = !catId || (p.category_id && p.category_id.toString() === catId);
        return matchesType && matchesSearch && matchesCat;
    });

    renderPOSProducts(filtered);
}

function addToCart(productId) {
    const product = allProducts.find(p => p.id === productId);
    if (!product) return;

    if (product.current_stock <= 0) {
        Swal.fire({ icon: 'warning', title: 'Sin Stock', text: `El producto '${product.name}' no tiene existencias disponibles.` });
        return;
    }

    const existing = currentCart.find(item => item.product_id === productId);
    if (existing) {
        if (existing.quantity + 1 > product.current_stock) {
            Swal.fire({ icon: 'warning', title: 'Límite de Stock', text: `Stock máximo disponible: ${product.current_stock} ${product.unit}` });
            return;
        }
        existing.quantity += 1;
        existing.subtotal = existing.quantity * existing.unit_price;
    } else {
        currentCart.push({
            product_id: product.id,
            name: product.name,
            unit: product.unit,
            unit_price: product.sale_price,
            quantity: 1,
            max_stock: product.current_stock,
            subtotal: product.sale_price
        });
    }

    renderCart();
}

function updateCartQty(productId, newQty) {
    const item = currentCart.find(i => i.product_id === productId);
    if (!item) return;

    newQty = parseFloat(newQty);
    if (isNaN(newQty) || newQty <= 0) {
        removeFromCart(productId);
        return;
    }

    if (newQty > item.max_stock) {
        Swal.fire({ icon: 'warning', title: 'Límite de Stock', text: `Stock máximo disponible: ${item.max_stock} ${item.unit}` });
        item.quantity = item.max_stock;
    } else {
        item.quantity = newQty;
    }

    item.subtotal = item.quantity * item.unit_price;
    renderCart();
}

function removeFromCart(productId) {
    currentCart = currentCart.filter(i => i.product_id !== productId);
    renderCart();
}

function clearCart() {
    currentCart = [];
    renderCart();
}

function renderCart() {
    const container = document.getElementById('cart-items-container');
    if (!currentCart.length) {
        container.innerHTML = '<p class="text-xs text-slate-400 text-center py-8">El carrito está vacío.<br>Selecciona productos a la izquierda.</p>';
        document.getElementById('cart-subtotal').textContent = 'Gs. 0';
        document.getElementById('cart-total').textContent = 'Gs. 0';
        document.getElementById('pos-amount-paid').value = '';
        calculateChange();
        return;
    }

    let total = 0;
    container.innerHTML = currentCart.map(item => {
        total += item.subtotal;
        return `
            <div class="py-2 flex items-center justify-between gap-2 text-xs">
                <div class="flex-1">
                    <p class="font-bold text-slate-800 line-clamp-1">${item.name}</p>
                    <p class="text-[10px] text-slate-400">Gs. ${item.unit_price.toLocaleString('es-PY')} x ${item.unit}</p>
                </div>
                <div class="flex items-center gap-1">
                    <input type="number" min="0.1" step="0.5" value="${item.quantity}" onchange="updateCartQty(${item.product_id}, this.value)"
                        class="w-16 px-1.5 py-1 text-center font-bold bg-white border border-slate-300 rounded text-xs">
                </div>
                <div class="text-right w-24">
                    <p class="font-black text-slate-900">Gs. ${item.subtotal.toLocaleString('es-PY')}</p>
                    <button onclick="removeFromCart(${item.product_id})" class="text-[10px] text-rose-500 hover:underline">Quitar</button>
                </div>
            </div>
        `;
    }).join('');

    document.getElementById('cart-subtotal').textContent = `Gs. ${total.toLocaleString('es-PY')}`;
    document.getElementById('cart-total').textContent = `Gs. ${total.toLocaleString('es-PY')}`;
    calculateChange();
}

function calculateChange() {
    const totalText = document.getElementById('cart-total').textContent.replace(/[^\d]/g, '');
    const total = parseFloat(totalText) || 0;
    const paid = parseFloat(document.getElementById('pos-amount-paid').value) || 0;
    const change = paid - total;

    const changeInput = document.getElementById('pos-change-given');
    if (change >= 0) {
        changeInput.value = `Gs. ${change.toLocaleString('es-PY')}`;
        changeInput.className = "w-full px-3 py-2 bg-slate-200/80 border border-slate-300 rounded-lg text-xs font-black text-emerald-700";
    } else {
        changeInput.value = `Faltan: Gs. ${Math.abs(change).toLocaleString('es-PY')}`;
        changeInput.className = "w-full px-3 py-2 bg-rose-100 border border-rose-300 rounded-lg text-xs font-bold text-rose-700";
    }
}

async function processSale() {
    if (!currentCart.length) {
        Swal.fire({ icon: 'warning', title: 'Carrito Vacío', text: 'Agrega al menos un producto para cobrar.' });
        return;
    }

    const totalText = document.getElementById('cart-total').textContent.replace(/[^\d]/g, '');
    const total = parseFloat(totalText) || 0;
    let paid = parseFloat(document.getElementById('pos-amount-paid').value);

    const paymentMethod = document.getElementById('pos-payment-method').value;
    if (paymentMethod !== 'EFECTIVO' && (!paid || paid === 0)) {
        paid = total; // Exact amount for Card / QR
    }

    if (isNaN(paid) || paid < total) {
        Swal.fire({ icon: 'error', title: 'Monto insuficiente', text: 'El monto ingresado es menor al total de la venta.' });
        return;
    }

    const customerId = document.getElementById('pos-customer-select').value || null;

    const salePayload = {
        customer_id: customerId ? parseInt(customerId) : null,
        payment_method: paymentMethod,
        amount_paid: paid,
        details: currentCart.map(item => ({
            product_id: item.product_id,
            quantity: item.quantity,
            unit_price: item.unit_price
        }))
    };

    try {
        const res = await fetchAuth('/sales/', {
            method: 'POST',
            body: JSON.stringify(salePayload)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Error al procesar la venta');

        Swal.fire({
            icon: 'success',
            title: '¡Venta Registrada con Éxito!',
            html: `
                <div class="text-left text-xs bg-slate-50 p-4 rounded-xl space-y-1 font-mono">
                    <p><b>Comprobante:</b> ${data.invoice_number}</p>
                    <p><b>Total Cobrado:</b> Gs. ${data.total_amount.toLocaleString('es-PY')}</p>
                    <p><b>Pagado:</b> Gs. ${data.amount_paid.toLocaleString('es-PY')}</p>
                    <p><b>Vuelto:</b> Gs. ${data.change_given.toLocaleString('es-PY')}</p>
                    <p class="text-slate-400 text-[10px] mt-2">Inventario actualizado automáticamente en Kardex.</p>
                </div>
            `,
            confirmButtonText: 'Imprimir / Aceptar'
        });

        clearCart();
        loadProducts();
        loadDashboardData();
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Error al cobrar', text: err.message });
    }
}

// ==========================================
// 3. INVENTARIO & PRODUCTOS
// ==========================================
function renderInventoryTable(products) {
    const tbody = document.getElementById('inventory-tbody');
    if (!products.length) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center py-6 text-slate-400">No se encontraron artículos registrados</td></tr>';
        return;
    }

    tbody.innerHTML = products.map(p => {
        const isLow = p.current_stock <= p.min_stock;
        const expDate = p.expiry_date ? new Date(p.expiry_date).toLocaleDateString('es-PY') : '-';
        return `
            <tr class="hover:bg-slate-50 transition-colors border-b border-slate-100">
                <td class="py-3 px-4 font-bold text-amber-700">${p.code}</td>
                <td class="py-3 px-4 font-bold text-slate-800">${p.name}</td>
                <td class="py-3 px-4"><span class="px-2 py-0.5 bg-slate-100 rounded text-[10px] font-semibold">${p.product_type}</span></td>
                <td class="py-3 px-4 font-semibold text-slate-500">${p.unit}</td>
                <td class="py-3 px-4 text-right">Gs. ${p.cost_price.toLocaleString('es-PY')}</td>
                <td class="py-3 px-4 text-right font-semibold text-slate-900">${p.sale_price > 0 ? 'Gs. ' + p.sale_price.toLocaleString('es-PY') : '-'}</td>
                <td class="py-3 px-4 text-center font-black ${isLow ? 'text-rose-600 bg-rose-50/60 rounded' : 'text-slate-800'}">${p.current_stock}</td>
                <td class="py-3 px-4 text-center text-slate-400">${p.min_stock}</td>
                <td class="py-3 px-4 text-slate-500">${expDate}</td>
                <td class="py-3 px-4 text-center">
                    ${isLow ? '<span class="px-2 py-0.5 bg-rose-100 text-rose-700 font-bold text-[10px] rounded-full">Bajo Stock</span>' : '<span class="px-2 py-0.5 bg-emerald-100 text-emerald-700 font-bold text-[10px] rounded-full">Óptimo</span>'}
                </td>
            </tr>
        `;
    }).join('');
}

function filterInventoryTable() {
    const search = document.getElementById('inv-search').value.toLowerCase();
    const typeFilter = document.getElementById('inv-type-filter').value;

    const filtered = allProducts.filter(p => {
        const matchesSearch = p.name.toLowerCase().includes(search) || p.code.toLowerCase().includes(search);
        const matchesType = !typeFilter || p.product_type === typeFilter;
        return matchesSearch && matchesType;
    });

    renderInventoryTable(filtered);
}

function openNewProductModal() {
    document.getElementById('modal-product').classList.remove('hidden');
}

function closeProductModal() {
    document.getElementById('modal-product').classList.add('hidden');
}

async function handleCreateProduct(e) {
    e.preventDefault();
    const payload = {
        code: document.getElementById('new-prod-code').value.trim(),
        name: document.getElementById('new-prod-name').value.trim(),
        product_type: document.getElementById('new-prod-type').value,
        category_id: document.getElementById('new-prod-cat').value ? parseInt(document.getElementById('new-prod-cat').value) : null,
        unit: document.getElementById('new-prod-unit').value,
        cost_price: parseFloat(document.getElementById('new-prod-cost').value) || 0,
        sale_price: parseFloat(document.getElementById('new-prod-sale').value) || 0,
        current_stock: parseFloat(document.getElementById('new-prod-stock').value) || 0,
        min_stock: parseFloat(document.getElementById('new-prod-min-stock').value) || 5,
        expiry_date: document.getElementById('new-prod-expiry').value ? new Date(document.getElementById('new-prod-expiry').value).toISOString() : null
    };

    try {
        const res = await fetchAuth('/products/', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Error al guardar artículo');

        Swal.fire({ icon: 'success', title: 'Artículo Creado', text: 'El artículo ha sido registrado en el inventario.' });
        closeProductModal();
        loadProducts();
        loadDashboardData();
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Error', text: err.message });
    }
}

function openAdjustmentModal() {
    const select = document.getElementById('adj-product-select');
    select.innerHTML = allProducts.map(p => `
        <option value="${p.id}">${p.name} (${p.code}) - Stock: ${p.current_stock} ${p.unit}</option>
    `).join('');
    document.getElementById('modal-adjustment').classList.remove('hidden');
}

function closeAdjustmentModal() {
    document.getElementById('modal-adjustment').classList.add('hidden');
}

async function handleCreateAdjustment(e) {
    e.preventDefault();
    const payload = {
        product_id: parseInt(document.getElementById('adj-product-select').value),
        movement_type: document.getElementById('adj-type').value,
        quantity: parseFloat(document.getElementById('adj-qty').value),
        reason: document.getElementById('adj-reason').value.trim()
    };

    try {
        const res = await fetchAuth('/inventory/adjustments', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Error al registrar ajuste');

        Swal.fire({ icon: 'success', title: 'Ajuste Registrado', text: 'Se ha asentado el movimiento en el Kardex.' });
        closeAdjustmentModal();
        loadProducts();
        loadDashboardData();
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Error en Ajuste', text: err.message });
    }
}

// ==========================================
// 4. PRODUCCIÓN & RECETAS (BOM)
// ==========================================
function renderRecipesList(recipes) {
    const container = document.getElementById('recipes-list-container');
    if (!recipes.length) {
        container.innerHTML = '<p class="text-xs text-slate-400 text-center py-6">No hay recetas registradas</p>';
        return;
    }

    container.innerHTML = recipes.map(r => `
        <div class="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2 hover:border-amber-400 transition-all">
            <div class="flex items-center justify-between">
                <h4 class="font-bold text-slate-800 text-xs">${r.name}</h4>
                <span class="px-2 py-0.5 bg-amber-100 text-amber-800 font-bold text-[10px] rounded">Rinde ${r.yield_quantity} ${r.product ? r.product.unit : ''}</span>
            </div>
            <p class="text-[11px] text-slate-500">${r.description || ''}</p>
            <div class="bg-white p-2.5 rounded-lg border border-slate-200 text-[10px] space-y-1">
                <p class="font-bold text-slate-600 uppercase">Ingredientes requeridos:</p>
                ${r.details.map(d => `
                    <div class="flex justify-between text-slate-700">
                        <span>• ${d.ingredient ? d.ingredient.name : 'Insumo'}</span>
                        <span class="font-bold">${d.quantity} ${d.ingredient ? d.ingredient.unit : ''}</span>
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('');
}

function onRecipeSelected() {
    const recipeId = parseInt(document.getElementById('prod-recipe-select').value);
    const recipe = allRecipes.find(r => r.id === recipeId);
    if (!recipe) {
        document.getElementById('prod-ingredients-preview').innerHTML = '<p class="text-slate-400 italic">Selecciona una receta para ver los insumos.</p>';
        return;
    }

    document.getElementById('prod-unit-display').value = recipe.product ? recipe.product.unit : 'UNIDAD';
    document.getElementById('prod-quantity').value = recipe.yield_quantity;
    calculateRequiredIngredients();
}

function calculateRequiredIngredients() {
    const recipeId = parseInt(document.getElementById('prod-recipe-select').value);
    const recipe = allRecipes.find(r => r.id === recipeId);
    if (!recipe) return;

    const qtyToProduce = parseFloat(document.getElementById('prod-quantity').value) || 0;
    const multiplier = qtyToProduce / recipe.yield_quantity;

    const preview = document.getElementById('prod-ingredients-preview');
    preview.innerHTML = recipe.details.map(d => {
        const required = d.quantity * multiplier;
        const currentStock = d.ingredient ? d.ingredient.current_stock : 0;
        const hasEnough = currentStock >= required;

        return `
            <div class="py-1 flex justify-between items-center text-xs">
                <span class="font-semibold text-slate-800">• ${d.ingredient ? d.ingredient.name : 'Insumo'}</span>
                <div class="text-right">
                    <span class="font-bold text-amber-900">${required.toFixed(2)} ${d.ingredient ? d.ingredient.unit : ''}</span>
                    <span class="text-[10px] ml-2 ${hasEnough ? 'text-emerald-600' : 'text-rose-600 font-black'}">(Disp: ${currentStock.toFixed(2)})</span>
                </div>
            </div>
        `;
    }).join('');
}

async function handleExecuteProduction(e) {
    e.preventDefault();
    const recipeId = parseInt(document.getElementById('prod-recipe-select').value);
    const qty = parseFloat(document.getElementById('prod-quantity').value);
    const notes = document.getElementById('prod-notes').value.trim();

    if (!recipeId || qty <= 0) {
        Swal.fire({ icon: 'warning', title: 'Datos incompletos', text: 'Selecciona una receta y una cantidad válida.' });
        return;
    }

    try {
        const res = await fetchAuth('/production/orders', {
            method: 'POST',
            body: JSON.stringify({
                recipe_id: recipeId,
                quantity_to_produce: qty,
                notes: notes
            })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Error al procesar la producción');

        Swal.fire({
            icon: 'success',
            title: '¡Producción Procesada!',
            text: `Orden ${data.order_number} completada. Materias primas descontadas y productos ingresados al stock.`
        });

        loadProducts();
        loadDashboardData();
        document.getElementById('prod-notes').value = '';
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Error en Producción', text: err.message });
    }
}

// ==========================================
// 5. COMPRAS & PROVEEDORES
// ==========================================
function addPurchaseLine() {
    const container = document.getElementById('purchase-lines-container');
    const lineId = Date.now();

    const rawMaterials = allProducts.filter(p => p.product_type === 'MATERIA_PRIMA' || p.product_type === 'INSUMO');

    const div = document.createElement('div');
    div.id = `purch-line-${lineId}`;
    div.className = 'grid grid-cols-12 gap-2 items-center bg-white p-2.5 rounded-lg border border-slate-200 text-xs';
    div.innerHTML = `
        <div class="col-span-5">
            <select class="purch-prod-select w-full px-2 py-1.5 border border-slate-300 rounded font-semibold focus:ring-2 focus:ring-amber-500 focus:outline-none">
                ${rawMaterials.map(p => `<option value="${p.id}" data-cost="${p.cost_price}">${p.name} (${p.unit})</option>`).join('')}
            </select>
        </div>
        <div class="col-span-2">
            <input type="number" min="0.1" step="0.5" value="10" placeholder="Cant." oninput="calcPurchaseTotal()"
                class="purch-qty-input w-full px-2 py-1.5 border border-slate-300 rounded text-center font-bold focus:outline-none">
        </div>
        <div class="col-span-2">
            <input type="number" min="0" step="500" value="5000" placeholder="Costo Unit" oninput="calcPurchaseTotal()"
                class="purch-cost-input w-full px-2 py-1.5 border border-slate-300 rounded text-right font-bold focus:outline-none">
        </div>
        <div class="col-span-2 text-right font-black text-slate-800 purch-line-subtotal">
            Gs. 50.000
        </div>
        <div class="col-span-1 text-center">
            <button type="button" onclick="document.getElementById('purch-line-${lineId}').remove(); calcPurchaseTotal();" class="text-rose-500 hover:text-rose-700">
                <i class="fa-solid fa-circle-xmark"></i>
            </button>
        </div>
    `;

    container.appendChild(div);
    calcPurchaseTotal();
}

function calcPurchaseTotal() {
    let total = 0;
    document.querySelectorAll('#purchase-lines-container > div').forEach(line => {
        const qty = parseFloat(line.querySelector('.purch-qty-input').value) || 0;
        const cost = parseFloat(line.querySelector('.purch-cost-input').value) || 0;
        const subtotal = qty * cost;
        total += subtotal;
        line.querySelector('.purch-line-subtotal').textContent = `Gs. ${subtotal.toLocaleString('es-PY')}`;
    });
    document.getElementById('purchase-total-display').textContent = `Gs. ${total.toLocaleString('es-PY')}`;
}

async function handleCreatePurchase(e) {
    e.preventDefault();
    const invoiceNumber = document.getElementById('purch-invoice').value.trim();
    const supplierId = parseInt(document.getElementById('purch-supplier').value);
    const notes = document.getElementById('purch-notes').value.trim();

    const details = [];
    document.querySelectorAll('#purchase-lines-container > div').forEach(line => {
        const productId = parseInt(line.querySelector('.purch-prod-select').value);
        const quantity = parseFloat(line.querySelector('.purch-qty-input').value);
        const unitCost = parseFloat(line.querySelector('.purch-cost-input').value);

        if (productId && quantity > 0 && unitCost >= 0) {
            details.push({
                product_id: productId,
                quantity: quantity,
                unit_cost: unitCost
            });
        }
    });

    if (!details.length) {
        Swal.fire({ icon: 'warning', title: 'Sin líneas', text: 'Agrega al menos un insumo en la compra.' });
        return;
    }

    try {
        const res = await fetchAuth('/purchases/', {
            method: 'POST',
            body: JSON.stringify({
                invoice_number: invoiceNumber,
                supplier_id: supplierId,
                notes: notes,
                details: details
            })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Error al guardar la compra');

        Swal.fire({
            icon: 'success',
            title: '¡Compra Registrada!',
            text: `Factura ${data.invoice_number} asentada. El stock y costos han sido actualizados.`
        });

        document.getElementById('purch-invoice').value = '';
        document.getElementById('purch-notes').value = '';
        loadProducts();
        loadDashboardData();
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Error en Compra', text: err.message });
    }
}

// ==========================================
// 6. REPORTES & KARDEX
// ==========================================
async function loadKardexMovements() {
    try {
        const typeFilter = document.getElementById('kardex-type-filter').value;
        let url = '/inventory/movements?limit=100';
        if (typeFilter) url += `&movement_type=${typeFilter}`;

        const res = await fetchAuth(url);
        const movements = await res.json();

        const tbody = document.getElementById('kardex-tbody');
        if (!movements.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center py-6 text-slate-400">No hay movimientos registrados</td></tr>';
            return;
        }

        tbody.innerHTML = movements.map(m => {
            const date = new Date(m.created_at).toLocaleString('es-PY');
            const isPositive = m.quantity > 0;
            return `
                <tr class="hover:bg-slate-50 transition-colors border-b border-slate-100">
                    <td class="py-2.5 px-3 text-slate-500">${date}</td>
                    <td class="py-2.5 px-3 font-bold text-slate-800">${m.product ? m.product.name : 'Artículo'}</td>
                    <td class="py-2.5 px-3"><span class="px-2 py-0.5 bg-slate-100 rounded text-[10px] font-bold text-slate-700">${m.movement_type}</span></td>
                    <td class="py-2.5 px-3 text-right font-black ${isPositive ? 'text-emerald-600' : 'text-rose-600'}">
                        ${isPositive ? '+' : ''}${m.quantity} ${m.product ? m.product.unit : ''}
                    </td>
                    <td class="py-2.5 px-3 text-right text-slate-500">${m.previous_stock}</td>
                    <td class="py-2.5 px-3 text-right font-bold text-slate-800">${m.new_stock}</td>
                    <td class="py-2.5 px-3 text-slate-600">${m.reference || ''} ${m.reason ? `(${m.reason})` : ''}</td>
                </tr>
            `;
        }).join('');
    } catch (err) {
        console.error('Error cargando Kardex:', err);
    }
}

// ==========================================
// 7. CONTROL DE CAJA Y ARQUEO
// ==========================================
async function loadCashStatus() {
    try {
        const res = await fetchAuth('/cash/current');
        const activeCash = await res.json();

        const container = document.getElementById('cash-status-container');
        if (activeCash) {
            const openedDate = new Date(activeCash.opened_at).toLocaleString('es-PY');
            container.innerHTML = `
                <div class="bg-emerald-50 border border-emerald-200 p-5 rounded-2xl space-y-3 text-xs">
                    <div class="flex items-center justify-between">
                        <span class="px-3 py-1 bg-emerald-600 text-white rounded-full font-bold text-[10px]">CAJA ABIERTA</span>
                        <span class="text-slate-500 font-semibold">${openedDate}</span>
                    </div>
                    <div class="grid grid-cols-2 gap-3 pt-2">
                        <div>
                            <p class="text-slate-500 font-semibold uppercase text-[10px]">Saldo Inicial (Fondo de Cambio)</p>
                            <p class="text-lg font-black text-slate-800">Gs. ${activeCash.initial_cash.toLocaleString('es-PY')}</p>
                        </div>
                        <div>
                            <p class="text-slate-500 font-semibold uppercase text-[10px]">Cajero Responsable</p>
                            <p class="text-sm font-bold text-slate-800">${currentUser.full_name}</p>
                        </div>
                    </div>

                    <div class="border-t border-emerald-200 pt-3 space-y-2">
                        <label class="block text-xs font-bold text-slate-700 uppercase">Monto Físico Real en Caja al Cierre</label>
                        <input type="number" id="close-cash-amount" step="1000" placeholder="Ej: 850000"
                            class="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl font-bold text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                        
                        <input type="text" id="close-cash-notes" placeholder="Observaciones de arqueo..."
                            class="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-xs focus:outline-none">

                        <button onclick="closeCashRegister()" class="w-full py-2.5 bg-rose-600 hover:bg-rose-700 text-white font-bold rounded-xl text-xs shadow-md transition-all">
                            <i class="fa-solid fa-lock mr-1"></i> Cerrar Caja y Realizar Arqueo
                        </button>
                    </div>
                </div>
            `;
        } else {
            container.innerHTML = `
                <div class="bg-slate-50 border border-slate-200 p-5 rounded-2xl space-y-3 text-xs">
                    <div class="flex items-center gap-2 text-amber-700 font-bold">
                        <i class="fa-solid fa-door-closed text-lg"></i>
                        <span>No tienes una caja abierta en este momento</span>
                    </div>
                    <p class="text-slate-500">Ingresa el fondo de cambio inicial para abrir la sesión de ventas.</p>
                    
                    <div class="space-y-2 pt-2">
                        <label class="block font-bold text-slate-700 uppercase text-[10px]">Fondo Inicial de Caja (Gs.)</label>
                        <input type="number" id="open-cash-amount" value="200000" step="10000"
                            class="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl font-bold text-sm focus:ring-2 focus:ring-amber-500 focus:outline-none">
                        <input type="text" id="open-cash-notes" placeholder="Observación inicial..."
                            class="w-full px-3 py-2 bg-white border border-slate-300 rounded-xl text-xs focus:outline-none">
                        
                        <button onclick="openCashRegister()" class="w-full py-2.5 bg-amber-600 hover:bg-amber-700 text-white font-bold rounded-xl text-xs shadow-md transition-all">
                            <i class="fa-solid fa-door-open mr-1"></i> Abrir Caja
                        </button>
                    </div>
                </div>
            `;
        }

        // Load History
        const histRes = await fetchAuth('/cash/history');
        const history = await histRes.json();
        const histTbody = document.getElementById('cash-history-tbody');
        histTbody.innerHTML = history.map(c => {
            const opDate = new Date(c.opened_at).toLocaleDateString('es-PY');
            const clDate = c.closed_at ? new Date(c.closed_at).toLocaleTimeString('es-PY') : 'Abierta';
            const diff = c.difference || 0;
            return `
                <tr class="hover:bg-slate-50 border-b border-slate-100">
                    <td class="py-2.5 px-3 font-semibold">${opDate}</td>
                    <td class="py-2.5 px-3 text-slate-500">${clDate}</td>
                    <td class="py-2.5 px-3 text-right">Gs. ${c.initial_cash.toLocaleString('es-PY')}</td>
                    <td class="py-2.5 px-3 text-right font-bold">Gs. ${(c.expected_cash || 0).toLocaleString('es-PY')}</td>
                    <td class="py-2.5 px-3 text-right font-black ${diff < 0 ? 'text-rose-600' : (diff > 0 ? 'text-blue-600' : 'text-emerald-600')}">
                        Gs. ${diff.toLocaleString('es-PY')}
                    </td>
                </tr>
            `;
        }).join('') || '<tr><td colspan="5" class="text-center py-4 text-slate-400">Sin historial registrado</td></tr>';
    } catch (err) {
        console.error('Error cargando caja:', err);
    }
}

async function openCashRegister() {
    const amount = parseFloat(document.getElementById('open-cash-amount').value) || 0;
    const notes = document.getElementById('open-cash-notes').value.trim();

    try {
        const res = await fetchAuth('/cash/open', {
            method: 'POST',
            body: JSON.stringify({ initial_cash: amount, notes: notes })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Error al abrir caja');

        Swal.fire({ icon: 'success', title: 'Caja Abierta', text: 'Sesión de ventas iniciada con éxito.' });
        loadCashStatus();
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Error', text: err.message });
    }
}

async function closeCashRegister() {
    const finalAmount = parseFloat(document.getElementById('close-cash-amount').value);
    const notes = document.getElementById('close-cash-notes').value.trim();

    if (isNaN(finalAmount)) {
        Swal.fire({ icon: 'warning', title: 'Monto requerido', text: 'Ingresa el conteo físico del dinero en caja.' });
        return;
    }

    try {
        const res = await fetchAuth('/cash/close', {
            method: 'POST',
            body: JSON.stringify({ final_cash: finalAmount, notes: notes })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Error al cerrar caja');

        const diff = data.difference || 0;
        let diffMsg = diff === 0 ? '¡Arqueo exacto y perfecto!' : (diff > 0 ? `Sobrante en caja de Gs. ${diff.toLocaleString('es-PY')}` : `Faltante en caja de Gs. ${Math.abs(diff).toLocaleString('es-PY')}`);

        Swal.fire({
            icon: diff === 0 ? 'success' : 'info',
            title: 'Arqueo de Caja Completado',
            html: `
                <div class="text-left text-xs bg-slate-50 p-4 rounded-xl space-y-1 font-mono">
                    <p><b>Fondo Inicial:</b> Gs. ${data.initial_cash.toLocaleString('es-PY')}</p>
                    <p><b>Monto Esperado:</b> Gs. ${data.expected_cash.toLocaleString('es-PY')}</p>
                    <p><b>Monto Real Contado:</b> Gs. ${data.final_cash.toLocaleString('es-PY')}</p>
                    <p class="font-bold mt-2 ${diff < 0 ? 'text-rose-600' : 'text-emerald-600'}">${diffMsg}</p>
                </div>
            `
        });

        loadCashStatus();
    } catch (err) {
        Swal.fire({ icon: 'error', title: 'Error al cerrar caja', text: err.message });
    }
}
