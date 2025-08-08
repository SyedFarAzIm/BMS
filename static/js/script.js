// Main JavaScript file for the Bakery Management System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Image Preview for product upload
    const imageInput = document.getElementById('image');
    if (imageInput) {
        imageInput.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (file) {
                const previewContainer = document.createElement('div');
                previewContainer.className = 'mt-2 mb-3';
                previewContainer.id = 'imagePreview';
                
                const oldPreview = document.getElementById('imagePreview');
                if (oldPreview) {
                    oldPreview.remove();
                }
                
                const previewImage = document.createElement('img');
                previewImage.className = 'img-thumbnail';
                previewImage.style.maxHeight = '200px';
                
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImage.src = e.target.result;
                };
                reader.readAsDataURL(file);
                
                previewContainer.appendChild(previewImage);
                imageInput.parentNode.insertBefore(previewContainer, imageInput.nextSibling);
            }
        });
    }

    // General utility functions
    // Initialize tooltips and animations
    initializeAnimations();
    initializeFormHandling();
    initializeAlerts();
    updateDateTime();
});

// Initialize card animations
function initializeAnimations() {
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in');
    });
}

// Handle form submissions with loading states
function initializeFormHandling() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton && this.checkValidity()) {
                const originalContent = submitButton.innerHTML;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Processing...';
                submitButton.disabled = true;
                
                // Re-enable button if form submission takes too long (safety net)
                setTimeout(() => {
                    submitButton.innerHTML = originalContent;
                    submitButton.disabled = false;
                }, 15000);
            }
        });
    });
}

// Auto-hide alerts after 5 seconds
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert) {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 150);
            }
        }, 5000);
    });
}

// Update current date/time
function updateDateTime() {
    const dateElement = document.getElementById('current-date');
    if (dateElement) {
        const now = new Date();
        dateElement.textContent = now.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }
}

// Product Management Functions
function confirmDelete(productId, productName) {
    if (confirm(`Are you sure you want to delete "${productName}"? This action cannot be undone.`)) {
        // Show loading state
        const deleteButton = event.target.closest('button');
        deleteButton.innerHTML = '<span class="loading me-2"></span>Deleting...';
        deleteButton.disabled = true;
        
        // Redirect to delete route
        window.location.href = `/admin/products/delete/${productId}`;
    }
}

// Order Management Functions
function updateProductTotal(productId) {
    const checkbox = document.getElementById(`product_${productId}`);
    const quantityInput = document.querySelector(`.quantity-input[data-product-id="${productId}"]`);
    const productTotal = document.querySelector(`.product-total[data-product-id="${productId}"]`);
    
    if (checkbox && checkbox.checked && quantityInput.value > 0) {
        const price = parseFloat(checkbox.getAttribute('data-price'));
        const quantity = parseInt(quantityInput.value);
        const total = price * quantity;
        productTotal.textContent = `$${total.toFixed(2)}`;
    } else {
        productTotal.textContent = '$0.00';
    }
}

function updateOrderTotal() {
    let total = 0;
    const checkboxes = document.querySelectorAll('.product-checkbox');
    
    checkboxes.forEach(checkbox => {
        if (checkbox.checked) {
            const productId = checkbox.value;
            const price = parseFloat(checkbox.getAttribute('data-price'));
            const quantityInput = document.querySelector(`.quantity-input[data-product-id="${productId}"]`);
            const quantity = parseInt(quantityInput.value);
            
            if (quantity > 0) {
                total += price * quantity;
            }
        }
    });
    
    const orderTotalElement = document.getElementById('order-total');
    if (orderTotalElement) {
        orderTotalElement.textContent = `$${total.toFixed(2)}`;
    }
}

// Form validation for orders
function validateOrderForm(event) {
    console.log('🔍 Validating order form...');
    
    const customerName = document.getElementById('customer_name')?.value.trim();
    console.log('Customer name:', customerName);
    
    const quantityInputs = document.querySelectorAll('.quantity-input');
    console.log('Found quantity inputs:', quantityInputs.length);
    
    let hasItems = false;
    let selectedItems = [];
    
    quantityInputs.forEach((input, index) => {
        const value = parseInt(input.value) || 0;
        const productName = input.closest('tr')?.querySelector('strong')?.textContent || `Product ${index}`;
        
        console.log(`${productName}: quantity = ${value}`);
        
        if (value > 0) {
            hasItems = true;
            selectedItems.push({
                name: productName,
                quantity: value,
                price: input.dataset.price
            });
        }
    });
    
    console.log('Has items:', hasItems);
    console.log('Selected items:', selectedItems);
    
    if (!customerName) {
        console.log('❌ Customer name missing');
        alert('Please enter customer name');
        document.getElementById('customer_name')?.focus();
        return false;
    }
    
    if (!hasItems) {
        console.log('❌ No items selected');
        alert('Please select at least one product with quantity > 0');
        return false;
    }
    
    console.log('✅ Form validation passed');
    return true;
}

// Product Form Management
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the add/edit product page
    if (document.getElementById('productForm')) {
        initializeProductForm();
    }
    
    // Check if we're on the place order page
    if (document.getElementById('orderForm')) {
        initializePlaceOrderForm();
    }
    
    // Initialize other general functionality
    initializeFormHandling();
    initializeAlerts();
    updateDateTime();
});

// Initialize Product Form (Add/Edit Product)
function initializeProductForm() {
    const categorySelect = document.getElementById('category');
    const customCategoryRow = document.getElementById('customCategoryRow');
    const customCategoryInput = document.getElementById('customCategory');
    const imageInput = document.getElementById('image');
    const imagePreview = document.getElementById('imagePreview');
    const previewImg = document.getElementById('previewImg');
    const productForm = document.getElementById('productForm');
    
    // Handle category selection
    if (categorySelect) {
        categorySelect.addEventListener('change', function() {
            if (this.value === 'custom') {
                customCategoryRow.style.display = 'block';
                customCategoryInput.required = true;
                customCategoryInput.focus();
            } else {
                customCategoryRow.style.display = 'none';
                customCategoryInput.required = false;
                customCategoryInput.value = '';
            }
            updateProductSummary();
        });
        
        // Check initial state for edit mode
        if (categorySelect.value === 'custom') {
            customCategoryRow.style.display = 'block';
            customCategoryInput.required = true;
        }
    }
    
    // Handle image preview
    if (imageInput) {
        imageInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                // Validate file size (5MB max)
                if (file.size > 5 * 1024 * 1024) {
                    alert('File size too large! Please choose an image smaller than 5MB.');
                    this.value = '';
                    imagePreview.style.display = 'none';
                    return;
                }
                
                // Validate file type
                const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
                if (!allowedTypes.includes(file.type)) {
                    alert('Invalid file type! Please choose a JPG, PNG, or GIF image.');
                    this.value = '';
                    imagePreview.style.display = 'none';
                    return;
                }
                
                // Show preview
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImg.src = e.target.result;
                    imagePreview.style.display = 'block';
                };
                reader.readAsDataURL(file);
            } else {
                imagePreview.style.display = 'none';
            }
            updateProductSummary();
        });
    }
    
    // Add event listeners for real-time updates
    const formInputs = ['name', 'quantity', 'price'];
    formInputs.forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) {
            input.addEventListener('input', updateProductSummary);
        }
    });
    
    if (customCategoryInput) {
        customCategoryInput.addEventListener('input', updateProductSummary);
    }
    
    // Form validation
    if (productForm) {
        productForm.addEventListener('submit', function(e) {
            if (!validateProductForm()) {
                e.preventDefault();
            }
        });
    }
    
    // Initialize summary
    updateProductSummary();
}

// Initialize Place Order Form
function initializePlaceOrderForm() {
    console.log('🚀 Initializing place order form...');
    
    const quantityInputs = document.querySelectorAll('.quantity-input');
    const grandTotalElement = document.getElementById('grandTotal');
    const orderSummary = document.getElementById('orderSummary');
    const categoryFilters = document.querySelectorAll('.category-filter');
    const productRows = document.querySelectorAll('.product-row');
    const orderForm = document.getElementById('orderForm');
    
    console.log('Found elements:', {
        quantityInputs: quantityInputs.length,
        grandTotal: !!grandTotalElement,
        orderSummary: !!orderSummary,
        categoryFilters: categoryFilters.length,
        productRows: productRows.length,
        orderForm: !!orderForm
    });
    
    // Category filtering functionality
    if (categoryFilters.length > 0) {
        categoryFilters.forEach(filter => {
            filter.addEventListener('click', function() {
                const selectedCategory = this.dataset.category;
                console.log('Category selected:', selectedCategory);
                
                // Update active button
                categoryFilters.forEach(f => f.classList.remove('active'));
                this.classList.add('active');
                
                // Filter products
                productRows.forEach(row => {
                    const productCategory = row.dataset.category;
                    if (selectedCategory === 'all' || productCategory === selectedCategory) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                        // Clear quantity when hiding
                        const quantityInput = row.querySelector('.quantity-input');
                        if (quantityInput && quantityInput.value > 0) {
                            quantityInput.value = 0;
                            updateOrderTotals();
                        }
                    }
                });
                
                updateCategoryStats();
            });
        });
    }
    
    // Handle quantity buttons (+ and - buttons) if they exist
    const quantityButtons = document.querySelectorAll('.quantity-btn');
    quantityButtons.forEach(button => {
        button.addEventListener('click', function() {
            const action = this.dataset.action;
            const inputGroup = this.closest('.input-group');
            const quantityInput = inputGroup.querySelector('.quantity-input');
            let currentValue = parseInt(quantityInput.value) || 0;
            
            if (action === 'increase' && currentValue < 999) {
                quantityInput.value = currentValue + 1;
            } else if (action === 'decrease' && currentValue > 0) {
                quantityInput.value = currentValue - 1;
            }
            
            // Trigger input event to update totals
            quantityInput.dispatchEvent(new Event('input'));
        });
    });
    
    // Update totals when quantity changes
    quantityInputs.forEach(input => {
        input.addEventListener('input', function() {
            let value = parseInt(this.value) || 0;
            
            // Enforce limits
            if (value < 0) {
                this.value = 0;
                value = 0;
            } else if (value > 999) {
                this.value = 999;
                value = 999;
            }
            
            console.log('Quantity changed:', this.closest('tr')?.querySelector('strong')?.textContent, 'to', value);
            updateOrderTotals();
        });
        
        // Handle keyboard shortcuts
        input.addEventListener('keydown', function(e) {
            const currentValue = parseInt(this.value) || 0;
            
            // Arrow up to increase
            if (e.key === 'ArrowUp' && currentValue < 999) {
                e.preventDefault();
                this.value = currentValue + 1;
                this.dispatchEvent(new Event('input'));
            }
            // Arrow down to decrease
            else if (e.key === 'ArrowDown' && currentValue > 0) {
                e.preventDefault();
                this.value = currentValue - 1;
                this.dispatchEvent(new Event('input'));
            }
        });
    });
    
    // Form validation for order - IMPORTANT: Remove duplicate form handling
    if (orderForm) {
        console.log('✅ Adding form submit handler');
        
        // Remove any existing event listeners to prevent duplicates
        orderForm.removeEventListener('submit', handleOrderSubmit);
        orderForm.addEventListener('submit', handleOrderSubmit);
    }
    
    // Initialize
    updateOrderTotals();
    updateCategoryStats();
}

// Separate function to handle order submission
function handleOrderSubmit(e) {
    console.log('📝 Form submission attempted');
    
    // Prevent the default submission temporarily
    e.preventDefault();
    
    // Validate the form
    if (validateOrderForm()) {
        console.log('✅ Validation passed, submitting form...');
        
        // Get the form data for debugging
        const formData = new FormData(e.target);
        console.log('Form data:');
        for (let [key, value] of formData.entries()) {
            console.log(`${key}: ${value}`);
        }
        
        // Show loading state
        const submitButton = e.target.querySelector('button[type="submit"]');
        if (submitButton) {
            const originalContent = submitButton.innerHTML;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Placing Order...';
            submitButton.disabled = true;
            
            // Re-enable after 10 seconds as safety net
            setTimeout(() => {
                submitButton.innerHTML = originalContent;
                submitButton.disabled = false;
            }, 10000);
        }
        
        // Submit the form
        e.target.submit();
    } else {
        console.log('❌ Validation failed');
    }
}

// Update category statistics for place order page
function updateCategoryStats() {
    const productRows = document.querySelectorAll('.product-row');
    const categoryStatsElement = document.getElementById('categoryStats');
    
    if (!categoryStatsElement) return;
    
    const categories = {};
    productRows.forEach(row => {
        if (row.style.display !== 'none') {
            const category = row.dataset.category;
            if (!categories[category]) {
                categories[category] = 0;
            }
            categories[category]++;
        }
    });
    
    let statsHtml = '';
    for (const [category, count] of Object.entries(categories)) {
        const icon = getCategoryIcon(category);
        statsHtml += `
            <div class="d-flex justify-content-between mb-1">
                <small>${icon} ${category}</small>
                <small class="text-muted">${count} items</small>
            </div>
        `;
    }
    
    categoryStatsElement.innerHTML = statsHtml || '<small class="text-muted">No items to show</small>';
}

// Update order totals for place order page
function updateOrderTotals() {
    const quantityInputs = document.querySelectorAll('.quantity-input');
    const grandTotalElement = document.getElementById('grandTotal');
    const orderSummary = document.getElementById('orderSummary');
    
    let grandTotal = 0;
    let orderItems = [];
    
    quantityInputs.forEach((input) => {
        const quantity = parseInt(input.value) || 0;
        const price = parseFloat(input.dataset.price);
        const subtotal = quantity * price;
        
        // Update subtotal display
        const subtotalElement = input.closest('tr')?.querySelector('.subtotal');
        if (subtotalElement) {
            subtotalElement.textContent = `$${subtotal.toFixed(2)}`;
        }
        
        // Add to grand total
        grandTotal += subtotal;
        
        // Add to order summary if quantity > 0
        if (quantity > 0) {
            const productName = input.closest('tr')?.querySelector('strong')?.textContent;
            if (productName) {
                orderItems.push({
                    name: productName,
                    quantity: quantity,
                    price: price,
                    subtotal: subtotal
                });
            }
        }
    });
    
    // Update grand total
    if (grandTotalElement) {
        grandTotalElement.textContent = `$${grandTotal.toFixed(2)}`;
    }
    
    // Update order summary
    updateOrderSummary(orderItems, grandTotal);
}

// Update order summary display
function updateOrderSummary(items, total) {
    const orderSummary = document.getElementById('orderSummary');
    if (!orderSummary) return;
    
    if (items.length === 0) {
        orderSummary.innerHTML = '<p class="text-muted text-center">No items selected</p>';
        return;
    }
    
    let html = '<div class="order-items">';
    items.forEach(item => {
        html += `
            <div class="d-flex justify-content-between mb-2">
                <div>
                    <small><strong>${item.name}</strong></small><br>
                    <small class="text-muted">${item.quantity} × $${item.price.toFixed(2)}</small>
                </div>
                <div class="text-end">
                    <small class="fw-bold">$${item.subtotal.toFixed(2)}</small>
                </div>
            </div>
        `;
    });
    html += '</div>';
    html += `
        <hr>
        <div class="d-flex justify-content-between">
            <strong>Total:</strong>
            <strong class="text-success">$${total.toFixed(2)}</strong>
        </div>
    `;
    
    orderSummary.innerHTML = html;
}

// Update product summary preview
function updateProductSummary() {
    const name = document.getElementById('name')?.value || '';
    const quantity = document.getElementById('quantity')?.value || '';
    const price = document.getElementById('price')?.value || '';
    const categorySelect = document.getElementById('category');
    const customCategoryInput = document.getElementById('customCategory');
    const imageInput = document.getElementById('image');
    
    let category = '';
    if (categorySelect) {
        category = categorySelect.value === 'custom' ? (customCategoryInput?.value || '') : categorySelect.value;
    }
    
    const hasImage = (imageInput && imageInput.files.length > 0) || document.querySelector('.img-thumbnail');
    
    let summary = '';
    
    if (name || quantity || price || category) {
        const categoryIcon = getCategoryIcon(category);
        summary = `
            <div class="row">
                <div class="col-md-6">
                    <p class="mb-1"><strong>📝 Name:</strong> ${name || '<span class="text-muted">Not set</span>'}</p>
                    <p class="mb-1"><strong>📦 Quantity:</strong> ${quantity || '<span class="text-muted">Not set</span>'}</p>
                </div>
                <div class="col-md-6">
                    <p class="mb-1"><strong>💰 Price:</strong> ${price ? '$' + parseFloat(price).toFixed(2) : '<span class="text-muted">Not set</span>'}</p>
                    <p class="mb-1"><strong>🏷️ Category:</strong> ${category ? categoryIcon + ' ' + category : '<span class="text-muted">Not selected</span>'}</p>
                </div>
            </div>
            <p class="mb-0"><strong>🖼️ Image:</strong> ${hasImage ? '<span class="text-success">✅ Image available</span>' : '<span class="text-muted">❌ No image</span>'}</p>
        `;
    } else {
        summary = '<p class="text-muted">Fill in the product details to see a preview</p>';
    }
    
    const summaryElement = document.getElementById('productSummary');
    if (summaryElement) {
        summaryElement.innerHTML = summary;
    }
}

// Get category icon
function getCategoryIcon(category) {
    const icons = {
        'Bread': '🍞',
        'Pastries': '🥐',
        'Cakes': '🎂',
        'Cookies': '🍪',
        'Drinks': '☕',
        'Desserts': '🍰',
        'Sandwiches': '🥪',
        'Other': '📦'
    };
    return icons[category] || '🍪';
}

// Validate product form
function validateProductForm() {
    const name = document.getElementById('name')?.value.trim();
    const quantity = document.getElementById('quantity')?.value.trim();
    const price = document.getElementById('price')?.value;
    const categorySelect = document.getElementById('category');
    const customCategoryInput = document.getElementById('customCategory');
    
    let category = '';
    if (categorySelect) {
        category = categorySelect.value === 'custom' ? (customCategoryInput?.value.trim() || '') : categorySelect.value;
    }
    
    // Check required fields
    if (!name) {
        alert('Please enter a product name');
        document.getElementById('name')?.focus();
        return false;
    }
    
    if (!quantity) {
        alert('Please enter quantity/description');
        document.getElementById('quantity')?.focus();
        return false;
    }
    
    if (!price || parseFloat(price) <= 0) {
        alert('Please enter a valid price greater than 0');
        document.getElementById('price')?.focus();
        return false;
    }
    
    if (!category) {
        alert('Please select a category');
        categorySelect?.focus();
        return false;
    }
    
    if (categorySelect?.value === 'custom' && !customCategoryInput?.value.trim()) {
        alert('Please enter a custom category name');
        customCategoryInput?.focus();
        return false;
    }
    
    return true;
}

// Validate order form
function validateOrderForm() {
    console.log('🔍 Validating order form...');
    
    const customerName = document.getElementById('customer_name')?.value.trim();
    console.log('Customer name:', customerName);
    
    const quantityInputs = document.querySelectorAll('.quantity-input');
    console.log('Found quantity inputs:', quantityInputs.length);
    
    let hasItems = false;
    let selectedItems = [];
    
    quantityInputs.forEach((input, index) => {
        const value = parseInt(input.value) || 0;
        const productName = input.closest('tr')?.querySelector('strong')?.textContent || `Product ${index}`;
        
        console.log(`${productName}: quantity = ${value}`);
        
        if (value > 0) {
            hasItems = true;
            selectedItems.push({
                name: productName,
                quantity: value,
                price: input.dataset.price
            });
        }
    });
    
    console.log('Has items:', hasItems);
    console.log('Selected items:', selectedItems);
    
    if (!customerName) {
        console.log('❌ Customer name missing');
        alert('Please enter customer name');
        document.getElementById('customer_name')?.focus();
        return false;
    }
    
    if (!hasItems) {
        console.log('❌ No items selected');
        alert('Please select at least one product with quantity > 0');
        return false;
    }
    
    console.log('✅ Form validation passed');
    return true;
}

// Clear form function
function clearForm() {
    if (confirm('Are you sure you want to clear all form data?')) {
        const productForm = document.getElementById('productForm');
        if (productForm) {
            productForm.reset();
            
            // Reset custom elements
            const imagePreview = document.getElementById('imagePreview');
            const customCategoryRow = document.getElementById('customCategoryRow');
            const customCategoryInput = document.getElementById('customCategory');
            
            if (imagePreview) imagePreview.style.display = 'none';
            if (customCategoryRow) customCategoryRow.style.display = 'none';
            if (customCategoryInput) {
                customCategoryInput.required = false;
                customCategoryInput.value = '';
            }
            
            updateProductSummary();
        }
    }
}

// Clear order function
function clearOrder() {
    const customerNameInput = document.getElementById('customer_name');
    const quantityInputs = document.querySelectorAll('.quantity-input');
    
    if (customerNameInput) customerNameInput.value = '';
    quantityInputs.forEach(input => {
        input.value = 0;
    });
    updateOrderTotals();
}

// Handle form submissions with loading states
function initializeFormHandling() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton && this.checkValidity()) {
                const originalContent = submitButton.innerHTML;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Processing...';
                submitButton.disabled = true;
                
                // Re-enable button if form submission takes too long (safety net)
                setTimeout(() => {
                    submitButton.innerHTML = originalContent;
                    submitButton.disabled = false;
                }, 15000);
            }
        });
    });
}

// Auto-hide alerts after 5 seconds
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert) {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 150);
            }
        }, 5000);
    });
}

// Update current date/time
function updateDateTime() {
    const dateElement = document.getElementById('current-date');
    if (dateElement) {
        const now = new Date();
        dateElement.textContent = now.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }
}

// Utility function for formatting currency
function formatCurrency(amount) {
    return `$${parseFloat(amount).toFixed(2)}`;
}

// Utility function for form field validation
function validateField(fieldId, fieldName, required = true) {
    const field = document.getElementById(fieldId);
    if (!field) return false;
    
    const value = field.value.trim();
    if (required && !value) {
        alert(`Please enter ${fieldName}`);
        field.focus();
        return false;
    }
    
    return true;
}

// Dark mode toggle (if needed)
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
}

// Initialize dark mode from localStorage
function initializeDarkMode() {
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
    }
}
