// Global JavaScript for Hologram Management System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        if (alert.classList.contains('alert-success')) {
            setTimeout(function() {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        }
    });

    // Form validation helpers
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Number formatting for display
    window.formatNumber = function(num) {
        return new Intl.NumberFormat().format(num);
    };

    // Loading state management
    window.showLoading = function(element) {
        if (element) {
            element.classList.add('loading');
            const spinner = document.createElement('span');
            spinner.className = 'spinner-border spinner-border-sm me-2';
            spinner.setAttribute('role', 'status');
            element.insertBefore(spinner, element.firstChild);
        }
    };

    window.hideLoading = function(element) {
        if (element) {
            element.classList.remove('loading');
            const spinner = element.querySelector('.spinner-border');
            if (spinner) {
                spinner.remove();
            }
        }
    };

    // Confirmation dialogs for destructive actions
    window.confirmAction = function(message) {
        return confirm(message || 'Are you sure you want to proceed?');
    };

    // Date formatting helper
    window.formatDate = function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        });
    };

    // Series range validation
    window.validateSeriesRange = function(startSeries, endSeries) {
        if (!startSeries || !endSeries) {
            return { valid: false, message: 'Both start and end series are required' };
        }
        
        if (endSeries <= startSeries) {
            return { valid: false, message: 'End series must be greater than start series' };
        }
        
        const total = endSeries - startSeries + 1;
        if (total !== 100000) {
            return { valid: false, message: 'Each carton must contain exactly 100,000 holograms' };
        }
        
        return { valid: true, message: 'Valid series range' };
    };

    // Stock availability checker
    window.checkStockAvailability = function(required, available) {
        if (required > available) {
            return {
                available: false,
                message: `Insufficient stock! Required: ${formatNumber(required)}, Available: ${formatNumber(available)}`
            };
        }
        return { available: true, message: 'Stock available' };
    };

    // Calculator helpers
    window.calculateHolograms = function(bottles, cases) {
        const bottleCount = parseInt(bottles) || 0;
        const caseCount = parseInt(cases) || 0;
        return bottleCount * caseCount;
    };

    // AJAX helper for API calls
    window.apiCall = function(url, data, method = 'POST') {
        return fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: method !== 'GET' ? JSON.stringify(data) : null
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('API call failed:', error);
            throw error;
        });
    };

    // Local storage helpers
    window.saveToLocalStorage = function(key, data) {
        try {
            localStorage.setItem(key, JSON.stringify(data));
            return true;
        } catch (error) {
            console.error('Error saving to localStorage:', error);
            return false;
        }
    };

    window.getFromLocalStorage = function(key) {
        try {
            const data = localStorage.getItem(key);
            return data ? JSON.parse(data) : null;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return null;
        }
    };

    // Table sorting functionality
    window.sortTable = function(table, column, ascending = true) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));

        rows.sort((a, b) => {
            const aVal = a.cells[column].textContent.trim();
            const bVal = b.cells[column].textContent.trim();

            // Try to parse as numbers first
            const aNum = parseFloat(aVal.replace(/,/g, ''));
            const bNum = parseFloat(bVal.replace(/,/g, ''));

            if (!isNaN(aNum) && !isNaN(bNum)) {
                return ascending ? aNum - bNum : bNum - aNum;
            }

            // Fall back to string comparison
            return ascending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        });

        // Re-append sorted rows
        rows.forEach(row => tbody.appendChild(row));
    };

    // Print functionality
    window.printReport = function() {
        window.print();
    };

    // Export to CSV helper
    window.exportTableToCSV = function(table, filename = 'report.csv') {
        const rows = Array.from(table.querySelectorAll('tr'));
        const csv = rows.map(row => {
            const cells = Array.from(row.querySelectorAll('td, th'));
            return cells.map(cell => {
                const text = cell.textContent.trim();
                return `"${text.replace(/"/g, '""')}"`;
            }).join(',');
        }).join('\n');

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
    };

    // Initialize any data tables if present
    const dataTables = document.querySelectorAll('.data-table');
    dataTables.forEach(function(table) {
        // Add sorting capability to table headers
        const headers = table.querySelectorAll('th');
        headers.forEach(function(header, index) {
            if (!header.classList.contains('no-sort')) {
                header.style.cursor = 'pointer';
                header.addEventListener('click', function() {
                    const isAscending = !header.classList.contains('sort-desc');
                    
                    // Reset all other headers
                    headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
                    
                    // Set current header
                    header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
                    
                    // Sort the table
                    sortTable(table, index, isAscending);
                });
            }
        });
    });

    // Back to top button
    const backToTopButton = document.createElement('button');
    backToTopButton.innerHTML = '<i class="fas fa-chevron-up"></i>';
    backToTopButton.className = 'btn btn-primary position-fixed';
    backToTopButton.style.cssText = 'bottom: 20px; right: 20px; z-index: 1000; display: none; border-radius: 50%; width: 50px; height: 50px;';
    backToTopButton.addEventListener('click', function() {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    document.body.appendChild(backToTopButton);

    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopButton.style.display = 'block';
        } else {
            backToTopButton.style.display = 'none';
        }
    });
});

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + Enter to submit forms
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        const activeForm = document.activeElement.closest('form');
        if (activeForm) {
            const submitButton = activeForm.querySelector('button[type="submit"], input[type="submit"]');
            if (submitButton && !submitButton.disabled) {
                submitButton.click();
            }
        }
    }
});