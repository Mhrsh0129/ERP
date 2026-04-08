# 📊 JayShreeTraders ERP - Inventory Management

A user-friendly, clean web-based ERP system for complete inventory management, built for Jay Shree Traders. Now optimized for FastAPI and SQLite with Gemini AI integration.

## ✨ Features

- **📊 Dashboard**: Real-time overview of inventory statistics and recent activities.
- **📦 Incoming Stock Management**: Track purchases, supplier names, payments, and product photos.
- **📤 Outgoing Stock Management**: Generate sales bills on the fly (creates downloadable PDFs).
- **📋 Live Inventory**: Tracks stock in real-time.
- **💡 Smart AI Bill Scanner**: Upload images or capture handwritten bills with Gemini Vision API to auto-fill entry forms.
- **💰 Payment Tracking**: Keep detailed history of part payments for any purchase or sale.

## 🛠️ Technology Stack

- **Backend**: Python FastAPI & Pydantic.
- **Database**: SQLite (local database file).
- **Frontend**: HTML, CSS, JavaScript (Vanilla PWA).
- **AI**: Google Gemini Pro Vision API via google-generativeai.
- **PDF Generation**: jsPDF & autoTable.

## 📋 Prerequisites

- Python 3.10+
- Modern Web Browser (Chrome/Edge/Safari)

## 🚀 Installation & Setup

### 1. Requirements

Ensure you are in the project folder and the virtual environment is set up:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Use the `.env` file at the root of the project to set up your API keys and hosting URLs.
```env
GEMINI_API_KEY=your_gemini_vision_api_key
```

### 3. Start the Application

Navigate to the backend start folder and run the server:
```bash
cd backend/start
python run.py
```
*(This commands uvicorn to host the app on `http://127.0.0.1:5000`)*

### 4. Access the Application

Open your browser and navigate to:
**http://127.0.0.1:5000**

## 📖 Usage Guide

*   **Add Incoming Stock**: Go to incoming stock -> use the form or hit **Smart Scan Bill** to capture an image of the physical invoice.
*   **Add Outgoing Sale**: Go to outgoing stock -> add sale. Use the "View Bill" button to preview the modern invoice, complete with automated bank details and "Jay Shree Traders" headers, then download it as a PDF for sharing.
*   **Track Partial Payments**: Click the "History" (notebook) icon next to any incoming/outgoing record to log a partial cash pickup. It automatically updates the remaining balance.

## 📁 Project Structure

```
JayShreeTraders_Inventory/
├── backend/
│   ├── database/    # SQLite configuration
│   ├── model/       # SQLAlchemy tables / Pydantic schemas
│   ├── services/    # Business logic, image encoding, AI extraction
│   ├── start/       # Server startup script (run.py)
│   ├── vercel/      # Vercel deployment routes
│   └── main.py      # Core FastAPI app definition
├── frontend/        # Serves as Static Directory
│   ├── css/         # App styles
│   ├── js/          # Frontend Javascript, PWA service workers
│   ├── src/         # Typescript source code
│   └── *.html       # App views (Dashboard, Incoming, Outgoing)
├── .env             # Root env variables (Not committed)
├── requirements.txt # Python dependencies
└── vercel.json      # Cloud deployment configurations
```

---

**Made with ❤️ for Jay Shree Traders**