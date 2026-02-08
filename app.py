import streamlit as st
from PIL import Image
import pandas as pd
import io
from ocr_demo import ReceiptScanner

import os

# --- Page Config ---
st.set_page_config(page_title="Receipt Scanner", layout="wide")

st.title("🧾 Receipt Scanner & Parser")
st.write("Upload a receipt image to extract structured data.")

# --- Database Setup ---
DB_FILE = "receipts_db.csv"

def load_db():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Merchant", "Date", "Total", "Items"])

def save_to_db(merchant, date, total, items):
    df = load_db()
    # Flatten items to string for simple storage
    items_str = "; ".join([f"{i['name']} ({i['price']})" for i in items])
    new_entry = pd.DataFrame([{
        "Merchant": merchant,
        "Date": date,
        "Total": total,
        "Items": items_str
    }])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

# --- Initialize Session State ---
if "scan_results" not in st.session_state:
    st.session_state.scan_results = None
if "last_image_id" not in st.session_state:
    st.session_state.last_image_id = None

# --- OCR Engine ---
@st.cache_resource
def get_scanner():
    return ReceiptScanner()

try:
    scanner = get_scanner()
except Exception as e:
    st.error(f"Failed to load OCR engine: {e}")
    st.stop()

# --- Input Section ---
st.subheader("1. Digitize Receipt")

# Input Method Selection
input_method = st.radio("Choose input method:", ["Upload Image", "Use Camera"], horizontal=True)

image_file = None

if input_method == "Upload Image":
    image_file = st.file_uploader("Choose an image...", type=["jpg", "png", "jpeg"])
elif input_method == "Use Camera":
    image_file = st.camera_input("Take a picture")

# Detect Image Change
if image_file:
    # Use size + name as a simple unique ID for the file
    file_id = f"{image_file.name}-{image_file.size}"
    if file_id != st.session_state.last_image_id:
        st.session_state.last_image_id = file_id
        st.session_state.scan_results = None # Reset results

if image_file is not None:
    # --- Preview Section ---
    st.subheader("2. Preview & Scan")
    
    # Display Image based on source
    if input_method == "Upload Image":
        col1, col2 = st.columns([1, 2])
        with col1:
             image = Image.open(image_file)
             st.image(image, caption="Uploaded Receipt", use_container_width=True)
    
    # Run Scan if not already done
    if st.session_state.scan_results is None:
        # Save temp
        with open("temp_receipt.png", "wb") as f:
            f.write(image_file.getbuffer())

        with st.spinner("Scanning..."):
            try:
                results = scanner.scan("temp_receipt.png")
                st.session_state.scan_results = results
            except Exception as e:
                st.error(f"An error occurred during scanning: {e}")

    # Display Results
    results = st.session_state.scan_results
    
    if results:
        if "error" in results:
            st.error(results["error"])
        else:
            st.success("Scan Complete!")

            # Layout: Metrics & Table
            col1, col2, col3 = st.columns(3)
            col1.metric("Merchant", results.get('merchant', 'Unknown'))
            col2.metric("Date", results.get('date', 'Unknown'))
            col3.metric("Total", results.get('total', 'Unknown'))

            st.subheader("Line Items")
            items = results.get('items', [])
            
            if items:
                df = pd.DataFrame(items)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No line items detected.")
            
            # --- Actions ---
            st.subheader("3. Actions")
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.button("💾 Save to Database", type="primary"):
                    save_to_db(
                        results.get('merchant'),
                        results.get('date'),
                        results.get('total'),
                        items
                    )
                    st.toast("Receipt saved to database!", icon="✅")

else:
    st.info("Please upload an image to begin.")

# --- History Section ---
st.markdown("---")
st.subheader("📂 Receipt History")

if os.path.exists(DB_FILE):
    history_df = pd.read_csv(DB_FILE)
    st.dataframe(history_df, use_container_width=True)
    
    csv_bytes = history_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download All History (CSV)",
        data=csv_bytes,
        file_name="all_receipts.csv",
        mime="text/csv",
    )
else:
    st.write("No history yet.")
