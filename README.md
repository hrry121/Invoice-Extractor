# 🧾 AI Invoice Extractor

An **AI-powered invoice extraction system** that goes beyond traditional OCR.  
It understands invoice structure and converts invoices into **business-ready Excel** and **developer-friendly JSON** formats in seconds.

---

## 🚀 Features

- Intelligent invoice understanding (not just text extraction)
- Extracts:
  - Vendor & customer details
  - Line items with calculations
  - Tax breakdowns
  - Payment terms
    
- Dual output formats:
  - 📊 **Excel** (accounting-ready)
  - 📄 **JSON** (API & automation-ready)
- Simple UI built with Streamlit

---

## 🛠️ Tech Stack

- **Google Gemini 2.5 Flash**
- **Python**
- **Streamlit**

---

## 📂 Project Structure

├── main.py # Streamlit application
├── requirements.txt # Python dependencies
├── .env # Environment variables
└── README.md

---

## 🔑 Setting Up Google Gemini API Key

This project uses **Google Gemini** via **Google AI Studio**.

### Step 1: Create an API Key
1. Go to **Google AI Studio**  
   👉 https://aistudio.google.com/
2. Sign in with your Google account
3. Click **Get API key**
4. Create a new API key
5. Copy the generated key

---

### Step 2: Create a `.env` File

In the root directory of the project, create a file named `.env`

⚠️ **Important**
- Do NOT commit `.env` to GitHub




