// Service Worker Registration and PWA Install Prompt
// For Jay Shree Traders ERP

let deferredPrompt;
let installButton;

// Register Service Worker
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker
            .register('/service-worker.js')
            .then((registration) => {
                console.log('✅ Service Worker registered successfully:', registration.scope);

                // Check for updates periodically
                setInterval(() => {
                    registration.update();
                }, 60000); // Check every minute

                // Listen for updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;

                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            // New version available
                            showUpdateNotification();
                        }
                    });
                });
            })
            .catch((error) => {
                console.error('❌ Service Worker registration failed:', error);
            });
    });
}

// Handle PWA install prompt
window.addEventListener('beforeinstallprompt', (e) => {
    console.log('💾 Install prompt available');

    // Prevent the default mini-infobar
    e.preventDefault();

    // Store the event for later use
    deferredPrompt = e;

    // Show custom install button
    showInstallButton();
});

// Show install button in UI
function showInstallButton() {
    // Create install button if it doesn't exist
    if (!document.getElementById('pwa-install-btn')) {
        const nav = document.querySelector('nav');

        if (nav) {
            const installBtn = document.createElement('button');
            installBtn.id = 'pwa-install-btn';
            installBtn.className = 'install-app-btn';
            installBtn.innerHTML = '📱 Install App';
            installBtn.style.cssText = `
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        font-size: 18px;
        font-weight: 600;
        border-radius: 10px;
        cursor: pointer;
        margin-left: 15px;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
      `;

            installBtn.addEventListener('mouseenter', () => {
                installBtn.style.transform = 'translateY(-2px)';
                installBtn.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.4)';
            });

            installBtn.addEventListener('mouseleave', () => {
                installBtn.style.transform = 'translateY(0)';
                installBtn.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.3)';
            });

            installBtn.addEventListener('click', installApp);

            // Add to navigation
            nav.appendChild(installBtn);
            installButton = installBtn;
        }
    }
}

// Install the PWA
async function installApp() {
    if (!deferredPrompt) {
        console.log('❌ Install prompt not available');
        return;
    }

    // Show the install prompt
    deferredPrompt.prompt();

    // Wait for the user's response
    const { outcome } = await deferredPrompt.userChoice;

    console.log(`User response to install prompt: ${outcome}`);

    if (outcome === 'accepted') {
        console.log('✅ User accepted the install prompt');

        // Show success message
        showNotification('App installed successfully! 🎉', 'success');
    } else {
        console.log('❌ User dismissed the install prompt');
    }

    // Clear the deferred prompt
    deferredPrompt = null;

    // Hide install button
    if (installButton) {
        installButton.style.display = 'none';
    }
}

// Detect if app is already installed
window.addEventListener('appinstalled', () => {
    console.log('✅ PWA was installed');

    // Hide install button
    if (installButton) {
        installButton.style.display = 'none';
    }

    // Clear the deferredPrompt
    deferredPrompt = null;

    // Show success message
    showNotification('App installed successfully! You can now use it offline. 🎉', 'success');
});

// Check if running as installed PWA
function isRunningStandalone() {
    return (
        window.matchMedia('(display-mode: standalone)').matches ||
        window.navigator.standalone === true
    );
}

// Show update notification
function showUpdateNotification() {
    const updateBanner = document.createElement('div');
    updateBanner.id = 'update-banner';
    updateBanner.style.cssText = `
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: #2563eb;
    color: white;
    padding: 20px 30px;
    border-radius: 12px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    z-index: 10000;
    display: flex;
    align-items: center;
    gap: 20px;
    font-size: 18px;
    animation: slideDown 0.3s ease;
  `;

    updateBanner.innerHTML = `
    <span>🔄 New version available!</span>
    <button id="update-btn" style="
      background: white;
      color: #2563eb;
      border: none;
      padding: 10px 20px;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      font-size: 16px;
    ">Update Now</button>
    <button id="dismiss-update" style="
      background: transparent;
      color: white;
      border: 2px solid white;
      padding: 10px 20px;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      font-size: 16px;
    ">Later</button>
  `;

    document.body.appendChild(updateBanner);

    // Update button click
    document.getElementById('update-btn').addEventListener('click', () => {
        if (navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' });
        }
        window.location.reload();
    });

    // Dismiss button click
    document.getElementById('dismiss-update').addEventListener('click', () => {
        updateBanner.remove();
    });
}

// Generic notification function
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#2563eb'};
    color: white;
    padding: 20px 30px;
    border-radius: 12px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    z-index: 10000;
    font-size: 18px;
    font-weight: 600;
    animation: slideIn 0.3s ease;
    max-width: 400px;
  `;

    notification.textContent = message;
    document.body.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
  @keyframes slideDown {
    from {
      transform: translateX(-50%) translateY(-100px);
      opacity: 0;
    }
    to {
      transform: translateX(-50%) translateY(0);
      opacity: 1;
    }
  }
  
  @keyframes slideIn {
    from {
      transform: translateX(400px);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(400px);
      opacity: 0;
    }
  }
`;
document.head.appendChild(style);

// Log PWA status on load
window.addEventListener('load', () => {
    if (isRunningStandalone()) {
        console.log('✅ Running as installed PWA');
    } else {
        console.log('🌐 Running in browser');
    }
});

// Network status monitoring
window.addEventListener('online', () => {
    showNotification('✅ Back online!', 'success');
});

window.addEventListener('offline', () => {
    showNotification('📡 You are offline. Some features may be limited.', 'info');
});
