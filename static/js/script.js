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
});

// Function to confirm product deletion
function confirmDelete(productName, deleteUrl) {
    if (confirm(`Are you sure you want to delete "${productName}"?`)) {
        window.location.href = deleteUrl;
    }
}