const API_BASE = '/api';

const API = {
    async get(endpoint: string) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`);
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            // Cast to Error so TypeScript knows it has a .message property
            return { success: false, error: (error as Error).message };
        }
    },

    async post(endpoint: string, data: unknown) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            return { success: false, error: (error as Error).message };
        }
    },

    async put(endpoint: string, data: unknown) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            return { success: false, error: (error as Error).message };
        }
    },

    async delete(endpoint: string) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, {
                method: 'DELETE'
            });
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            return { success: false, error: (error as Error).message };
        }
    }
};

function showAlert(message: string, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;

    const container = document.querySelector('.container');
    // Guard: only insert if container exists on this page
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
    }

    setTimeout(() => {
        alertDiv.style.opacity = '0';
        setTimeout(() => alertDiv.remove(), 300);
    }, 5000);
}

function formatDate(dateString: string) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatCurrency(amount: number) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(amount);
}

function confirmDelete(message = 'Are you sure you want to delete this item?') {
    return confirm(message);
}

function openModal(modalId: string) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

function closeModal(modalId: string) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

function resetForm(formId: string) {
    const form = document.getElementById(formId);
    if (form) {
        // Cast to HTMLFormElement so TypeScript knows it has a .reset() method
        (form as HTMLFormElement).reset();
        const preview = form.querySelector('.image-preview');
        if (preview) {
            // Cast to HTMLElement so TypeScript knows it has a .style property
            (preview as HTMLElement).style.display = 'none';
        }
    }
}

function handleImageUpload(input: HTMLInputElement, previewId: string) {
    const file = input.files?.[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
            const preview = document.getElementById(previewId) as HTMLImageElement | null;
            if (preview && e.target) {
                // Cast to HTMLImageElement so TypeScript knows it has a .src property
                preview.src = e.target.result as string;
                preview.style.display = 'block';
            }
        };
        reader.readAsDataURL(file);
    }
}

function imageToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            const result = reader.result;
            // result is string | ArrayBuffer — we know it's a string because we used readAsDataURL
            resolve((result as string).split(',')[1]);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });

    const closeBtns = document.querySelectorAll('.close-btn');
    closeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const modal = btn.closest('.modal');
            if (modal) {
                modal.classList.remove('active');
            }
        });
    });

    // Dark Mode Logic
    initTheme();
});

function initTheme() {
    const theme = localStorage.getItem('theme');
    if (theme === 'dark') {
        document.body.classList.add('dark-mode');
    }

    // Inject toggle button into nav
    const navList = document.querySelector('nav ul');
    if (navList) {
        const li = document.createElement('li');
        li.innerHTML = `
            <button onclick="toggleTheme()" class="btn" style="padding: 0 15px; min-width: auto; background: var(--bg-card); color: var(--text-main); border: 2px solid var(--border-color); height: 42px; font-size: 1.2rem;">
                ${document.body.classList.contains('dark-mode') ? '☀️' : '🌙'}
            </button>
        `;
        navList.appendChild(li);
    }
}

function toggleTheme() {
    const isDark = document.body.classList.toggle('dark-mode');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');

    // Update button icon
    const btn = document.querySelector('nav button[onclick="toggleTheme()"]');
    if (btn) {
        btn.innerHTML = isDark ? '☀️' : '🌙';
    }
}
