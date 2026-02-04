/**
 * Bill Scanner Module
 * AI-powered bill scanning using Gemini API
 */

class BillScanner {
    constructor() {
        this.modal = null;
        this.currentImage = null;
        this.currentImageData = null;
        this.onDataExtracted = null; // Callback function
        this.suggestedType = 'incoming'; // 'incoming' or 'outgoing'
    }

    /**
     * Initialize the scanner and open modal
     * @param {string} type - 'incoming' or 'outgoing'
     * @param {function} callback - Function to call with extracted data
     */
    open(type, callback) {
        this.suggestedType = type;
        this.onDataExtracted = callback;
        this.showModal();
    }

    /**
     * Show the scanner modal
     */
    showModal() {
        // Create modal if it doesn't exist
        if (!document.getElementById('billScannerModal')) {
            this.createModal();
        }

        this.modal = document.getElementById('billScannerModal');
        this.modal.classList.add('active');
        this.resetModal();
    }

    /**
     * Create the scanner modal HTML
     */
    createModal() {
        const modalHTML = `
            <div id="billScannerModal" class="modal">
                <div class="modal-content" style="max-width: 800px;">
                    <div class="modal-header">
                        <h2>📸 Smart Bill Scanner</h2>
                        <button class="close-btn" onclick="billScanner.close()">&times;</button>
                    </div>

                    <!-- Upload Section -->
                    <div id="uploadSection" class="scanner-section">
                        <p style="color: var(--text-secondary); margin-bottom: 20px;">
                            Upload or capture a bill image. The AI will automatically extract all data.
                        </p>
                        
                        <div style="display: flex; gap: 12px; margin-bottom: 20px;">
                            <button class="btn btn-primary" onclick="document.getElementById('billFileInput').click()">
                                📁 Upload Image
                            </button>
                            <button class="btn btn-secondary" onclick="document.getElementById('billCameraInput').click()">
                                📷 Take Photo
                            </button>
                        </div>

                        <input type="file" id="billFileInput" accept="image/*" style="display: none;" 
                               onchange="billScanner.handleFileSelect(event)">
                        <input type="file" id="billCameraInput" accept="image/*" capture="environment" style="display: none;" 
                               onchange="billScanner.handleFileSelect(event)">

                        <div class="alert" style="background: var(--primary-light); border: 1px solid var(--primary-color); margin-top: 16px;">
                            <strong>💡 Tips for best results:</strong>
                            <ul style="margin: 8px 0 0 20px; color: var(--text-secondary);">
                                <li>Use good lighting</li>
                                <li>Capture the entire bill</li>
                                <li>Keep the image clear and focused</li>
                                <li>Works with handwritten bills too!</li>
                            </ul>
                        </div>
                    </div>

                    <!-- Preview Section -->
                    <div id="previewSection" class="scanner-section" style="display: none;">
                        <h3>Preview</h3>
                        <img id="billPreview" style="max-width: 100%; border-radius: 8px; border: 2px solid var(--border-color); margin-bottom: 16px;">
                        
                        <div style="display: flex; gap: 12px;">
                            <button class="btn btn-primary" onclick="billScanner.processBill()">
                                🔍 Extract Data
                            </button>
                            <button class="btn btn-secondary" onclick="billScanner.resetModal()">
                                🔄 Choose Different Image
                            </button>
                        </div>
                    </div>

                    <!-- Loading Section -->
                    <div id="loadingSection" class="scanner-section" style="display: none; text-align: center;">
                        <div class="loading" style="padding: 60px 20px;">
                            <div style="font-size: 48px; margin-bottom: 16px;">🤖</div>
                            <h3>Analyzing Bill with AI...</h3>
                            <p style="color: var(--text-secondary);">This usually takes 2-5 seconds</p>
                            <div style="margin-top: 20px;">
                                <div class="spinner"></div>
                            </div>
                        </div>
                    </div>

                    <!-- Results Section -->
                    <div id="resultsSection" class="scanner-section" style="display: none;">
                        <h3 style="margin-bottom: 16px;">✅ Extracted Data</h3>
                        <div id="extractedDataPreview" style="background: var(--bg-body); padding: 20px; border-radius: 8px; margin-bottom: 16px;">
                            <!-- Filled dynamically -->
                        </div>

                        <div style="display: flex; gap: 12px;">
                            <button class="btn btn-success" onclick="billScanner.useExtractedData()">
                                ✓ Use This Data
                            </button>
                            <button class="btn btn-secondary" onclick="billScanner.resetModal()">
                                🔄 Scan Again
                            </button>
                        </div>
                    </div>

                    <!-- Error Section -->
                    <div id="errorSection" class="scanner-section" style="display: none;">
                        <div class="alert alert-error">
                            <strong>❌ Error</strong>
                            <p id="errorMessage"></p>
                        </div>
                        <button class="btn btn-primary" onclick="billScanner.resetModal()">
                            🔄 Try Again
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Add custom spinner CSS if not already present
        if (!document.getElementById('spinner-style')) {
            const spinnerStyle = document.createElement('style');
            spinnerStyle.id = 'spinner-style';
            spinnerStyle.textContent = `
                .spinner {
                    border: 4px solid var(--border-color);
                    border-top: 4px solid var(--primary-color);
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    animation: spin 1s linear infinite;
                    margin: 0 auto;
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                .scanner-section {
                    animation: fadeIn 0.3s ease-in;
                }
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
            `;
            document.head.appendChild(spinnerStyle);
        }
    }

    /**
     * Handle file selection
     */
    handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        // Validate file type
        if (!file.type.startsWith('image/')) {
            alert('Please select an image file');
            return;
        }

        // Validate file size (max 20MB)
        if (file.size > 20 * 1024 * 1024) {
            alert('Image size must be less than 20MB');
            return;
        }

        // Read and display image
        const reader = new FileReader();
        reader.onload = (e) => {
            this.currentImageData = e.target.result;
            document.getElementById('billPreview').src = this.currentImageData;
            this.showSection('previewSection');
        };
        reader.readAsDataURL(file);
    }

    /**
     * Process bill with AI
     */
    async processBill() {
        this.showSection('loadingSection');

        try {
            const response = await fetch('/api/scan-bill', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    image: this.currentImageData,
                    suggested_type: this.suggestedType
                })
            });

            const result = await response.json();

            if (result.success) {
                this.displayResults(result);
            } else {
                this.showError(result.error || 'Failed to process bill');
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        }
    }

    /**
     * Display extracted results
     */
    displayResults(result) {
        const data = result.data;
        const confidence = Math.round((result.confidence || 0.8) * 100);

        const previewHTML = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                ${this.renderField('Bill Type', result.bill_type === 'incoming' ? '📦 Incoming (Purchase)' : '📤 Outgoing (Sale)')}
                ${this.renderField('Product Name', data.product_name)}
                ${result.bill_type === 'incoming' ? this.renderField('Supplier', data.supplier_name) : ''}
                ${result.bill_type === 'outgoing' ? this.renderField('Customer', data.customer_name) : ''}
                ${this.renderField('Date', data.date)}
                ${this.renderField('Quantity', data.quantity ? `${data.quantity} ${data.unit || ''}` : null)}
                ${this.renderField('Price/Unit', data.price_per_unit ? `₹${data.price_per_unit}` : null)}
                ${this.renderField('Tax %', data.tax_percentage ? `${data.tax_percentage}%` : null)}
                ${this.renderField('Total Amount', data.total_amount ? `₹${data.total_amount}` : null)}
                ${this.renderField('GST Number', data.gst_number)}
                ${this.renderField('Invoice #', data.invoice_number)}
            </div>
            <div style="margin-top: 16px; padding: 12px; background: var(--success-bg); border-radius: 6px; text-align: center;">
                <strong>Confidence: ${confidence}%</strong>
                <p style="font-size: 13px; color: var(--text-secondary); margin-top: 4px;">
                    ${confidence >= 90 ? '✅ High confidence' : confidence >= 70 ? '⚠️ Medium - please review' : '❌ Low - manual verification needed'}
                </p>
            </div>
        `;

        document.getElementById('extractedDataPreview').innerHTML = previewHTML;
        this.extractedData = result;
        this.showSection('resultsSection');
    }

    /**
     * Render a data field
     */
    renderField(label, value) {
        if (!value) return '';
        return `
            <div style="padding: 12px; background: var(--bg-card); border-radius: 6px; border: 1px solid var(--border-color);">
                <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 4px;">${label}</div>
                <div style="font-weight: 600; color: var(--text-main);">${value}</div>
            </div>
        `;
    }

    /**
     * Use extracted data and close modal
     */
    useExtractedData() {
        if (this.onDataExtracted && this.extractedData) {
            this.onDataExtracted(this.extractedData);
            this.close();
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        this.showSection('errorSection');
    }

    /**
     * Show specific section, hide others
     */
    showSection(sectionId) {
        const sections = ['uploadSection', 'previewSection', 'loadingSection', 'resultsSection', 'errorSection'];
        sections.forEach(id => {
            document.getElementById(id).style.display = id === sectionId ? 'block' : 'none';
        });
    }

    /**
     * Reset modal to initial state
     */
    resetModal() {
        this.currentImageData = null;
        this.extractedData = null;
        document.getElementById('billFileInput').value = '';
        document.getElementById('billCameraInput').value = '';
        this.showSection('uploadSection');
    }

    /**
     * Close modal
     */
    close() {
        if (this.modal) {
            this.modal.classList.remove('active');
            setTimeout(() => this.resetModal(), 300);
        }
    }
}

// Create global instance
const billScanner = new BillScanner();
