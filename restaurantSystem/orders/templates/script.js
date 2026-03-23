// ============================================
// CONFIGURATION & STATE
// ============================================

const API_BASE_URL = window.location.origin + '/orders';

let tables = [];
let currentTable = null;
let currentOrder = null;
let categories = [];
let menuItems = [];
let pendingItems = [];
let activeCategory = null;

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded, initializing...');
    
    // Load all data
    loadTables();
    loadCategories();
    
    // Setup event listeners
    setupEventListeners();
    
    // Initially disable menu
    disableMenu();
});

function setupEventListeners() {
    const allTablesSelector = document.getElementById('allTablesSelector');
    const activeTablesSelector = document.getElementById('activeTablesSelector');
    
    if (allTablesSelector) {
        allTablesSelector.addEventListener('change', function(e) {
            if (this.value) {
                selectTable(parseInt(this.value));
            }
        });
    }
    
    if (activeTablesSelector) {
        activeTablesSelector.addEventListener('change', function(e) {
            if (this.value) {
                selectTable(parseInt(this.value));
            }
        });
    }
}

// ============================================
// TABLE MANAGEMENT
// ============================================

async function loadTables() {
    try {
        const url = `${API_BASE_URL}/tables/`;
        console.log('Loading tables from:', url);
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        tables = Array.isArray(data) ? data : (data.results || []);
        
        // Sort numerically
        tables.sort((a, b) => a.number - b.number);
        
        console.log('Tables loaded:', tables);
        
        // Populate both selectors
        populateAllTablesSelector();
        updateActiveTablesSelector();
        
    } catch (error) {
        console.error('Error loading tables:', error);
        alert('Error loading tables: ' + error.message);
    }
}

function populateAllTablesSelector() {
    const selector = document.getElementById('allTablesSelector');
    if (!selector) return;
    
    selector.innerHTML = '<option value="">-- Elige una mesa --</option>';
    
    tables.forEach(table => {
        const option = document.createElement('option');
        option.value = table.id;
        option.textContent = `Mesa ${table.number} - ${
            table.is_occupied ? 'Ocupada' : 'Disponible'
        }`;
        selector.appendChild(option);
    });
}

function updateActiveTablesSelector() {
    const selector = document.getElementById('activeTablesSelector');
    if (!selector) return;
    
    selector.innerHTML = '<option value="">-- Mesas con pedidos --</option>';
    
    const activeTables = tables.filter(t => t.is_occupied).sort((a, b) => a.number - b.number);
    
    if (activeTables.length === 0) {
        selector.innerHTML = '<option value="">-- No hay mesas activas --</option>';
        return;
    }
    
    activeTables.forEach(table => {
        const option = document.createElement('option');
        option.value = table.id;
        const total = table.current_order_total 
            ? `€${parseFloat(table.current_order_total).toFixed(2)}` 
            : '€0.00';
        option.textContent = `Mesa ${table.number} - Total: ${total}`;
        selector.appendChild(option);
    });
}

async function selectTable(tableId) {
    try {
        const url = `${API_BASE_URL}/tables/${tableId}/`;
        console.log('Selecting table:', url);
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        currentTable = await response.json();
        console.log('Table selected:', currentTable);
        
        // Show table info
        showTableInfo();
        
        // Enable menu
        enableMenu();
        
        // Load order if table is occupied
        if (currentTable.is_occupied) {
            await loadCurrentOrder();
        } else {
            // Empty table - offer to open
            await openTable(tableId);
        }
        
    } catch (error) {
        console.error('Error selecting table:', error);
        alert('Error al seleccionar mesa: ' + error.message);
    }
}

async function loadCurrentOrder() {
    try {
        const url = `${API_BASE_URL}/tables/${currentTable.id}/current_order/`;
        const response = await fetch(url);
        
        if (response.ok) {
            currentOrder = await response.json();
            console.log('Order loaded:', currentOrder);
            displayOrderInfo();
        }
    } catch (error) {
        console.error('Error loading order:', error);
    }
}

async function openTable(tableId) {
    if (!confirm(`¿Abrir mesa ${currentTable.number}?`)) {
        return;
    }
    
    try {
        const url = `${API_BASE_URL}/tables/${tableId}/open/`;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({})
        });
        
        if (response.ok) {
            currentOrder = await response.json();
            console.log('Table opened:', currentOrder);
            
            // Refresh table list
            await loadTables();
            
            // Show order info
            displayOrderInfo();
            
            showNotification(`Mesa ${currentTable.number} abierta`, 'success');
        }
    } catch (error) {
        console.error('Error opening table:', error);
        alert('Error al abrir mesa: ' + error.message);
    }
}

// ============================================
// UI DISPLAY
// ============================================

function showTableInfo() {
    const infoDiv = document.getElementById('selectedTableInfo');
    const tableNameEl = document.getElementById('selectedTableName');
    
    if (infoDiv && tableNameEl) {
        infoDiv.classList.remove('hidden');
        tableNameEl.textContent = `Mesa ${currentTable.number}`;
    }
}

function displayOrderInfo() {
    const orderDetailsEl = document.getElementById('orderDetails');
    const createOrderBtn = document.getElementById('createOrderBtn');
    
    if (!orderDetailsEl) return;
    
    if (!currentOrder) {
        orderDetailsEl.innerHTML = '<p style="color: #51cf66;">✓ Mesa disponible - Crear nuevo pedido</p>';
        if (createOrderBtn) {
            createOrderBtn.classList.remove('hidden');
            createOrderBtn.onclick = () => location.reload();
        }
        return;
    }
    
    // Show existing order
    if (createOrderBtn) {
        createOrderBtn.classList.add('hidden');
    }
    
    const itemsHTML = currentOrder.items.map(item => `
        <div class="order-item">
            <div class="order-item-name">${item.menu_item.name}</div>
            <div class="order-item-quantity">Cantidad: x${item.quantity}</div>
            <div class="order-item-price">€${(item.unit_price * item.quantity).toFixed(2)}</div>
        </div>
    `).join('');
    
    orderDetailsEl.innerHTML = `
        <div class="order-status">
            <span class="order-status-label">Estado:</span>
            <span class="order-status-value">${currentOrder.status}</span>
        </div>
        <div style="margin-top: 20px;">
            <strong>Productos:</strong>
            ${itemsHTML || '<p>Sin productos aún</p>'}
        </div>
        <div class="order-total">
            <div class="order-total-label">Total:</div>
            <div class="order-total-amount">€${parseFloat(currentOrder.total_amount).toFixed(2)}</div>
        </div>
    `;
}

function enableMenu() {
    const menuSection = document.querySelector('.menu-section');
    if (menuSection) {
        menuSection.classList.remove('menu-disabled');
    }
}

function disableMenu() {
    const menuSection = document.querySelector('.menu-section');
    if (menuSection) {
        menuSection.classList.add('menu-disabled');
    }
}

// ============================================
// MENU MANAGEMENT
// ============================================

async function loadCategories() {
    try {
        const url = `${API_BASE_URL}/categories/`;
        const response = await fetch(url);
        categories = await response.json();
        renderCategories();
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

function renderCategories() {
    const container = document.getElementById('categoryTabs');
    if (!container) return;
    
    container.innerHTML = `
        <button class="category-tab ${!activeCategory ? 'active' : ''}" 
                onclick="filterByCategory(null)">
            Todos
        </button>
        ${categories.map(cat => `
            <button class="category-tab ${activeCategory === cat.slug ? 'active' : ''}" 
                    onclick="filterByCategory('${cat.slug}')">
                ${cat.name}
            </button>
        `).join('')}
    `;
}

function filterByCategory(categorySlug) {
    activeCategory = categorySlug;
    
    document.querySelectorAll('.category-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    if (event && event.target) {
        event.target.classList.add('active');
    }
    
    loadMenuItems();
}

async function loadMenuItems() {
    try {
        let url;
        
        if (activeCategory) {
            url = `${API_BASE_URL}/menu-items/?category_slug=${activeCategory}`;
        } else {
            url = `${API_BASE_URL}/menu-items/by_category/`;
        }
        
        const response = await fetch(url);
        
        if (!response.ok && !activeCategory) {
            const fallbackResponse = await fetch(`${API_BASE_URL}/menu-items/`);
            const fallbackData = await fallbackResponse.json();
            menuItems = fallbackData.results || fallbackData;
            renderMenuItems();
        } else {
            const data = await response.json();
            
            if (activeCategory || !Array.isArray(data) || data.length === 0) {
                menuItems = data.results || data;
                renderMenuItems();
            } else {
                renderMenuItemsByCategory(data);
            }
        }
    } catch (error) {
        console.error('Error loading menu items:', error);
        const container = document.getElementById('menuItems');
        if (container) {
            container.innerHTML = '<p>Error al cargar el menú</p>';
        }
    }
}

function renderMenuItems() {
    const container = document.getElementById('menuItems');
    if (!container) return;
    
    if (!menuItems || menuItems.length === 0) {
        container.innerHTML = '<p>No hay items disponibles</p>';
        return;
    }
    
    container.innerHTML = menuItems.map(item => `
        <div class="menu-item">
            <div class="menu-item-info">
                <div class="menu-item-name">${item.name}</div>
                ${item.description ? `<div class="menu-item-description">${item.description}</div>` : ''}
                <div class="menu-item-price">€${parseFloat(item.price).toFixed(2)}</div>
            </div>
            <button class="add-button" onclick="addToOrder(${item.id}, '${escapeString(item.name)}', ${item.price})">
                Añadir
            </button>
        </div>
    `).join('');
}

function renderMenuItemsByCategory(data) {
    const container = document.getElementById('menuItems');
    if (!container) return;
    
    if (!data || data.length === 0) {
        container.innerHTML = '<p>No hay items disponibles</p>';
        return;
    }
    
    container.innerHTML = data.map(group => `
        <div class="category-section">
            <h3 style="color: #667eea; margin: 20px 0 10px 0; padding-bottom: 5px; border-bottom: 2px solid #667eea;">
                ${group.category.name}
            </h3>
            ${group.items.map(item => `
                <div class="menu-item">
                    <div class="menu-item-info">
                        <div class="menu-item-name">${item.name}</div>
                        ${item.description ? `<div class="menu-item-description">${item.description}</div>` : ''}
                        <div class="menu-item-price">€${parseFloat(item.price).toFixed(2)}</div>
                    </div>
                    <button class="add-button" onclick="addToOrder(${item.id}, '${escapeString(item.name)}', ${item.price})">
                        Añadir
                    </button>
                </div>
            `).join('')}
        </div>
    `).join('');
}

// ============================================
// ORDER MANAGEMENT
// ============================================

function addToOrder(menuItemId, itemName, itemPrice) {
    // Check if table is selected
    if (!currentTable) {
        alert('Por favor, seleccione una mesa primero');
        return;
    }
    
    // Check if order exists
    if (!currentOrder) {
        alert('No hay pedido activo');
        return;
    }
    
    // Find item in menuItems
    let item = menuItems.find(m => m.id === menuItemId);
    
    if (!item) {
        item = {
            id: menuItemId,
            name: itemName,
            price: itemPrice
        };
    }
    
    // Check if already in pending
    const existingItem = pendingItems.find(p => p.menu_item_id === menuItemId);
    
    if (existingItem) {
        existingItem.quantity++;
    } else {
        pendingItems.push({
            menu_item_id: menuItemId,
            quantity: 1,
            notes: '',
            menu_item: item
        });
    }
    
    renderPendingItems();
    showNotification(`${item.name} añadido al pedido`, 'success');
}

function updatePendingQuantity(menuItemId, delta) {
    const item = pendingItems.find(p => p.menu_item_id === menuItemId);
    
    if (item) {
        item.quantity += delta;
        if (item.quantity <= 0) {
            pendingItems = pendingItems.filter(p => p.menu_item_id !== menuItemId);
        }
        renderPendingItems();
    }
}

function removeFromPending(menuItemId) {
    pendingItems = pendingItems.filter(p => p.menu_item_id !== menuItemId);
    renderPendingItems();
}

function renderPendingItems() {
    const container = document.getElementById('orderItems');
    if (!container) return;
    
    let html = '';
    
    // Show existing confirmed items
    if (currentOrder && currentOrder.items && currentOrder.items.length > 0) {
        html += '<div style="margin-bottom: 15px;"><strong style="color: #333;">Items Confirmados:</strong>';
        html += currentOrder.items.map(item => `
            <div class="order-item">
                <div>${item.quantity}x ${item.menu_item.name}</div>
                <div>€${parseFloat(item.subtotal).toFixed(2)}</div>
            </div>
        `).join('');
        html += '</div>';
    }
    
    // Show pending items
    if (pendingItems.length > 0) {
        html += '<div style="margin-top: 10px; padding-top: 10px; border-top: 2px dashed #667eea;"><strong style="color: #667eea;">Nuevos Items:</strong>';
        html += pendingItems.map(item => `
            <div class="order-item" style="background: #f0f4ff; padding: 10px; margin: 5px 0; border-radius: 5px; display: flex; justify-content: space-between; align-items: center;">
                <div style="flex: 1;">
                    <div style="font-weight: 500;">${item.menu_item.name}</div>
                    <div style="color: #667eea; font-size: 12px;">€${parseFloat(item.menu_item.price).toFixed(2)} c/u</div>
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <button class="quantity-btn" onclick="updatePendingQuantity(${item.menu_item_id}, -1)">-</button>
                    <span style="min-width: 20px; text-align: center;">${item.quantity}</span>
                    <button class="quantity-btn" onclick="updatePendingQuantity(${item.menu_item_id}, 1)">+</button>
                    <button class="quantity-btn" onclick="removeFromPending(${item.menu_item_id})">×</button>
                </div>
                <div style="min-width: 80px; text-align: right; font-weight: bold;">€${(item.quantity * parseFloat(item.menu_item.price)).toFixed(2)}</div>
            </div>
        `).join('');
        html += '</div>';
        
        html += `<button class="submit-order" onclick="sendToKitchen()" style="width: 100%; margin-top: 15px;">Enviar a Cocina</button>`;
    }
    
    if (!html) {
        html = '<p style="color: #999; text-align: center; padding: 20px;">No hay items en el pedido</p>';
    }
    
    container.innerHTML = html;
    updateTotal();
}

function updateTotal() {
    let total = 0;
    
    if (currentOrder && currentOrder.total_amount) {
        total += parseFloat(currentOrder.total_amount);
    }
    
    pendingItems.forEach(item => {
        total += item.quantity * parseFloat(item.menu_item.price);
    });
    
    const totalElement = document.getElementById('orderTotal');
    if (totalElement) {
        totalElement.textContent = total.toFixed(2);
    }
}

async function sendToKitchen() {
    if (pendingItems.length === 0) {
        alert('No hay items nuevos para enviar');
        return;
    }
    
    if (!currentTable || !currentOrder) {
        alert('Error: Mesa u orden no seleccionada');
        return;
    }
    
    try {
        const url = `${API_BASE_URL}/tables/${currentTable.id}/add_items/`;
        const response = await fetch(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                items: pendingItems.map(item => ({
                    menu_item_id: item.menu_item_id,
                    quantity: item.quantity,
                    notes: item.notes || ''
                }))
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            currentOrder = data.order;
            pendingItems = [];
            renderPendingItems();
            showNotification('¡Items enviados a cocina!', 'success');
        } else {
            const error = await response.json();
            alert('Error: ' + (error.detail || 'Error desconocido'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al enviar items');
    }
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

function escapeString(str) {
    if (!str) return '';
    return str.replace(/'/g, "\\'").replace(/"/g, '\\"');
}

function showNotification(message, type = 'info') {
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 10px;
        color: white;
        font-weight: bold;
        z-index: 10000;
        background: ${type === 'success' ? '#00b894' : type === 'error' ? '#d63031' : '#667eea'};
    `;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => toast.remove(), 3000);
}