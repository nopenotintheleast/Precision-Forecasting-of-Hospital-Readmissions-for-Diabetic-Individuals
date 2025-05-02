// Mobile sidebar toggle
document.getElementById('sidebar-toggle').addEventListener('click', function() {
    const sidebar = document.getElementById('mobile-sidebar');
    sidebar.classList.toggle('hidden');
});

// Close mobile sidebar when clicking outside
document.addEventListener('click', function(event) {
    const sidebar = document.getElementById('mobile-sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle');
    
    if (!sidebar.contains(event.target) && event.target !== toggleBtn) {
        sidebar.classList.add('hidden');
    }
});

// Flash message auto-dismiss
setTimeout(() => {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        alert.style.transition = 'opacity 0.5s ease-out';
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 500);
    });
}, 5000);

// Form validation helpers
function validatePassword(password, confirmPassword) {
    if (password !== confirmPassword) {
        alert('Passwords do not match');
        return false;
    }
    if (password.length < 8) {
        alert('Password must be at least 8 characters');
        return false;
    }
    return true;
}

// Print functionality
function printReport() {
    window.print();
}

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(tooltip => {
        tooltip.addEventListener('mouseenter', showTooltip);
        tooltip.addEventListener('mouseleave', hideTooltip);
    });
});

function showTooltip(event) {
    const tooltipText = this.getAttribute('data-tooltip');
    const tooltip = document.createElement('div');
    tooltip.className = 'absolute z-50 bg-black text-white text-xs px-2 py-1 rounded';
    tooltip.textContent = tooltipText;
    this.appendChild(tooltip);
    
    positionTooltip(this, tooltip);
}

function hideTooltip() {
    const tooltip = this.querySelector('.absolute');
    if (tooltip) tooltip.remove();
}

function positionTooltip(element, tooltip) {
    const rect = element.getBoundingClientRect();
    tooltip.style.top = `${rect.top - 30}px`;
    tooltip.style.left = `${rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;
}