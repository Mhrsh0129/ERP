# 📊 Jay Shree Traders - Inventory Management System

A user-friendly, senior-friendly web-based ERP system for inventory management with MySQL database integration.

## ✨ Features

- **📊 Dashboard**: Overview of inventory statistics and recent activities
- **📦 Incoming Stock Management**: Track purchases from suppliers
- **📤 Outgoing Stock Management**: Track sales to customers
- **📋 Live Inventory**: Real-time stock levels with low stock alerts
- **🔍 Search & Filter**: Easy search functionality across all modules
- **📸 Product Photos**: Upload and manage product images
- **💰 Payment Tracking**: Track payment types (Cash, UPI, Cheque) and dates

## 🎨 Senior-Friendly Design

- **Large Fonts**: Minimum 18px font size for easy reading
- **Big Buttons**: Minimum 60px height buttons for easy clicking
- **High Contrast**: Clear, readable color scheme
- **Simple Navigation**: Only 3-4 main menu items
- **Confirmation Dialogs**: Always confirms before deleting
- **Clear Feedback**: Large success/error messages

## 🛠️ Technology Stack

- **Backend**: Python FastAPI & Pydantic
- **Database**: MySQL (using PyMySQL and cryptography)
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **Styling**: Custom CSS with accessibility focus

## 📋 Prerequisites

- Python 3.8 or higher
- MySQL Server 5.7 or higher
- Web browser (Chrome, Firefox, Edge recommended)

## 🚀 Installation & Setup

### 1. Database Setup

The database `jay_shree_traders` should already be created with the following tables:
- `incoming_stock`
- `outgoing_stock`
- `live_inventory`

### 2. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure Environment Variables

The `.env` file is already configured with your database credentials:
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=@Maha2004
DB_NAME=jay_shree_traders
DB_PORT=3306
API_PORT=8000
```

### 4. Start the Application

```bash
cd backend
python run.py
```

The server will start API endpoints on `http://localhost:8000`. You will need to open the HTML files directly in your browser or serve them with a simple HTTP server (like `python -m http.server 5000` in the `frontend` folder).

### 5. Access the Application

Open your web browser and navigate directly to your local frontend files:
- **Dashboard**: `frontend/index.html`
- **Incoming Stock**: `frontend/incoming-stock.html`
- **Outgoing Stock**: `frontend/outgoing-stock.html`
- **Live Inventory**: `frontend/inventory.html`

## 📖 Usage Guide

### Adding Incoming Stock

1. Click on "📦 Incoming Stock" in the navigation
2. Click the "➕ Add New Stock" button
3. Fill in the form:
   - Product Name (required)
   - Supplier Name (required)
   - Purchase Date (required)
   - Amount (required)
   - Payment Type (required)
   - Payment Date (optional)
   - Delivery Date (optional)
   - Product Photo (optional)
4. Click "✓ Add Stock"

### Adding Outgoing Stock (Sales)

1. Click on "📤 Outgoing Stock" in the navigation
2. Click the "➕ Add New Sale" button
3. Fill in the form with customer and sale details
4. Click "✓ Add Sale"

### Viewing Inventory

1. Click on "📋 Live Inventory" in the navigation
2. View current stock levels
3. Check low stock alerts at the bottom

### Editing Records

1. Find the record in the table
2. Click the "✏️ Edit" button
3. Update the information
4. Click "✓ Update"

### Deleting Records

1. Find the record in the table
2. Click the "🗑️ Delete" button
3. Confirm the deletion when prompted

### Searching

Use the search box at the top of each page to filter records by product name, supplier, or customer name.

## 📁 Project Structure

```
JayShreeTraders_Inventory/
├── backend/
│   ├── app/                      # Main FastAPI application
│   │   ├── core/                 # Database config 
│   │   ├── models/               # Database models and queries
│   │   ├── routers/              # API endpoints
│   │   ├── schemas/              # Pydantic data validation
│   │   ├── utils/                # AI Scanning integration
│   │   └── main.py               # Application entrypoint
│   ├── requirements.txt          # Python dependencies
│   └── run.py                    # Server runner script
├── frontend/                     # Static frontend files
│   ├── css/
│   │   └── styles.css            # Senior-friendly styling
│   ├── js/                       # Client-side scripts
│   │   ├── app.js          
│   │   ├── bill-scanner.js 
│   │   └── sw-register.js
│   ├── index.html                # Dashboard page
│   ├── incoming-stock.html       # Incoming stock management
│   ├── outgoing-stock.html       # Outgoing stock management
│   ├── inventory.html            # Live inventory view
│   ├── manifest.json             # PWA properties
│   └── service-worker.js         # Offline capabilities
├── Architecture.txt              # Detailed architecture breakdown
├── .env                          # Environment variables
├── .gitignore                    # Git ignore file
└── README.md                     # This file
```

## 🔒 Security Notes

- The `.env` file contains sensitive database credentials
- Never commit `.env` to version control
- Change default passwords in production
- Use HTTPS in production environments

## 🐛 Troubleshooting

### Database Connection Failed

- Verify MySQL server is running
- Check credentials in `.env` file
- Ensure database `jay_shree_traders` exists

### Port Already in Use

- Change `API_PORT` in `.env` file
- Or stop the process using port 8000

### Images Not Uploading

- Check file size (max 16MB for LONGBLOB)
- Ensure file is a valid image format
- Check browser console for errors

## 📞 Support

For issues or questions, please contact the system administrator.

## 📝 License

This project is proprietary software for Jay Shree Traders.

---

**Made with ❤️ for easy inventory management**
