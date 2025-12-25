from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai
import json
import pandas as pd
from io import BytesIO
import base64

# Configure Gemini API
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash')


def get_gemini_response(prompt, image_parts, user_query):
    """Generate response from Gemini model"""
    try:
        response = model.generate_content([prompt, user_query, image_parts[0]])
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"


def extract_structured_data(image_parts):
    """Extract structured invoice data as JSON"""
    prompt = """
    Analyze this invoice image and extract ALL information in JSON format.
    Return ONLY valid JSON with this structure:
    {
        "invoice_number": "",
        "date": "",
        "vendor_name": "",
        "vendor_address": "",
        "customer_name": "",
        "customer_address": "",
        "items": [
            {"description": "", "quantity": "", "unit_price": "", "total": ""}
        ],
        "subtotal": "",
        "tax": "",
        "total": "",
        "currency": "",
        "payment_terms": ""
    }
    If any field is not found, use empty string. Ensure proper JSON formatting.
    """
    try:
        response = model.generate_content([prompt, image_parts[0]])
        text = response.text.strip()
        
        # Clean the response
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        return json.loads(text)
    except Exception as e:
        st.error(f"Error extracting structured data: {str(e)}")
        return None


def draw_bounding_boxes(image, data):
    """Draw bounding boxes on detected invoice elements"""
    img = image.copy()
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    # Define colors for different elements
    colors = {
        "header": "#FF6B6B",
        "vendor": "#4ECDC4",
        "customer": "#45B7D1",
        "items": "#FFA07A",
        "totals": "#98D8C8"
    }
    
    # Simulate bounding boxes based on typical invoice layout
    # Header (Invoice number, date) - top 15%
    draw.rectangle([(10, 10), (width-10, int(height*0.15))], 
                   outline=colors["header"], width=3)
    draw.text((20, 15), "Header Info", fill=colors["header"])
    
    # Vendor info - left side, 15-35%
    draw.rectangle([(10, int(height*0.15)), (int(width*0.5), int(height*0.35))], 
                   outline=colors["vendor"], width=3)
    draw.text((20, int(height*0.16)), "Vendor", fill=colors["vendor"])
    
    # Customer info - right side, 15-35%
    draw.rectangle([(int(width*0.5)+10, int(height*0.15)), (width-10, int(height*0.35))], 
                   outline=colors["customer"], width=3)
    draw.text((int(width*0.5)+20, int(height*0.16)), "Customer", fill=colors["customer"])
    
    # Items table - middle section, 35-75%
    draw.rectangle([(10, int(height*0.35)), (width-10, int(height*0.75))], 
                   outline=colors["items"], width=3)
    draw.text((20, int(height*0.36)), "Items", fill=colors["items"])
    
    # Totals - bottom 25%
    draw.rectangle([(int(width*0.6), int(height*0.75)), (width-10, height-10)], 
                   outline=colors["totals"], width=3)
    draw.text((int(width*0.6)+10, int(height*0.76)), "Totals", fill=colors["totals"])
    
    return img


def input_image_setup(uploaded_file):
    """Process uploaded image file"""
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        image_parts = [{"mime_type": uploaded_file.type, "data": bytes_data}]
        return image_parts
    else:
        raise FileNotFoundError("No file uploaded")


def convert_to_excel(data):
    """Convert extracted data to Excel file"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Invoice details
        details_df = pd.DataFrame([{
            'Invoice Number': data.get('invoice_number', ''),
            'Date': data.get('date', ''),
            'Vendor': data.get('vendor_name', ''),
            'Customer': data.get('customer_name', ''),
            'Subtotal': data.get('subtotal', ''),
            'Tax': data.get('tax', ''),
            'Total': data.get('total', ''),
            'Currency': data.get('currency', '')
        }])
        details_df.to_excel(writer, sheet_name='Invoice Details', index=False)
        
        # Items
        if data.get('items'):
            items_df = pd.DataFrame(data['items'])
            items_df.to_excel(writer, sheet_name='Line Items', index=False)
    
    output.seek(0)
    return output


# Streamlit UI
st.set_page_config(page_title="Invoice Extractor", page_icon="🧾", layout="wide")

st.title("🧾 Invoice Extractor ")
st.markdown("**Advanced invoice analysis with visualization and data export**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Features")
    show_boxes = st.checkbox("Show Detection Zones", value=True)
    extract_table = st.checkbox("Extract as Table", value=True)
    
    st.markdown("---")
    st.header("💡 Example Questions")
    st.markdown("""
    - What is the total amount?
    - List all items with prices
    - Who is the vendor?
    - Extract payment terms
    - What's the invoice date?
    """)
    
    st.markdown("---")
    st.header("📊 Export Options")
    st.info("Extract data to view as table or download as Excel")

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📤 Upload Invoice")
    uploaded_file = st.file_uploader(
        "Choose an invoice image", 
        type=["jpg", "jpeg", "png"],
        help="Upload a clear image of your invoice"
    )
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        
        if show_boxes:
            st.image(image, caption="Original Invoice", use_container_width=True)
        else:
            st.image(image, caption="Uploaded Invoice", use_container_width=True)

with col2:
    st.subheader("🤖 AI Analysis")
    
    if uploaded_file:
        # Quick extract button
        if st.button("🔍 Quick Extract All Data", type="primary"):
            with st.spinner("🔄 Analyzing invoice..."):
                try:
                    image_data = input_image_setup(uploaded_file)
                    extracted_data = extract_structured_data(image_data)
                    
                    if extracted_data:
                        st.success("✅ Extraction complete!")
                        
                        # Display key info
                        st.markdown("### 📋 Key Information")
                        key_cols = st.columns(3)
                        with key_cols[0]:
                            st.metric("Invoice #", extracted_data.get('invoice_number', 'N/A'))
                        with key_cols[1]:
                            st.metric("Date", extracted_data.get('date', 'N/A'))
                        with key_cols[2]:
                            st.metric("Total", f"{extracted_data.get('currency', '')} {extracted_data.get('total', 'N/A')}")
                        
                        # Store in session state
                        st.session_state['extracted_data'] = extracted_data
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # Custom query
        st.markdown("---")
        user_input = st.text_input(
            "Or ask a specific question:", 
            placeholder="e.g., What are the payment terms?"
        )
        
        if st.button("Ask Question"):
            if user_input:
                with st.spinner("🔄 Getting answer..."):
                    try:
                        image_data = input_image_setup(uploaded_file)
                        system_prompt = """You are an expert invoice analyzer. 
                        Provide accurate, concise answers based on the invoice image."""
                        response = get_gemini_response(system_prompt, image_data, user_input)
                        st.write(response)
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

# Detection Zones Visualization
if uploaded_file and show_boxes:
    st.markdown("---")
    st.subheader("🎯 Detection Zones")
    st.info("Color-coded regions show where different invoice elements are typically located")
    
    image = Image.open(uploaded_file)
    boxed_image = draw_bounding_boxes(image, {})
    st.image(boxed_image, caption="Invoice with Detection Zones", use_container_width=True)
    
    # Legend
    legend_cols = st.columns(5)
    with legend_cols[0]:
        st.markdown("🟥 **Header**")
    with legend_cols[1]:
        st.markdown("🟦 **Vendor**")
    with legend_cols[2]:
        st.markdown("🟨 **Customer**")
    with legend_cols[3]:
        st.markdown("🟧 **Items**")
    with legend_cols[4]:
        st.markdown("🟩 **Totals**")

# Data Table View
if 'extracted_data' in st.session_state and extract_table:
    st.markdown("---")
    st.subheader("📊 Extracted Data")
    
    data = st.session_state['extracted_data']
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📄 Summary", "🛒 Line Items", "📥 Export"])
    
    with tab1:
        summary_data = {
            "Field": ["Invoice Number", "Date", "Vendor", "Customer", "Subtotal", "Tax", "Total", "Currency"],
            "Value": [
                data.get('invoice_number', 'N/A'),
                data.get('date', 'N/A'),
                data.get('vendor_name', 'N/A'),
                data.get('customer_name', 'N/A'),
                data.get('subtotal', 'N/A'),
                data.get('tax', 'N/A'),
                data.get('total', 'N/A'),
                data.get('currency', 'N/A')
            ]
        }
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
    
    with tab2:
        if data.get('items'):
            items_df = pd.DataFrame(data['items'])
            st.dataframe(items_df, use_container_width=True)
        else:
            st.info("No line items extracted")
    
    with tab3:
        st.markdown("### Download Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # JSON download
            json_str = json.dumps(data, indent=2)
            st.download_button(
                label="📄 Download JSON",
                data=json_str,
                file_name="invoice_data.json",
                mime="application/json"
            )
        
        with col2:
            # Excel download
            excel_file = convert_to_excel(data)
            st.download_button(
                label="📊 Download Excel",
                data=excel_file,
                file_name="invoice_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# Footer
st.markdown("---")
st.markdown("**🤖 Powered by Google Gemini 2.5 Flash** | Built with Streamlit")