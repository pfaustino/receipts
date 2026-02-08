import os
import streamlit as st
from PIL import Image
import pandas as pd
import io
from ocr_demo import ReceiptScanner

# --- Page Config ---
st.set_page_config(page_title="Receipt Scanner", layout="wide")

st.title("🧾 Receipt Scanner & Parser")

# --- Authentication ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

def login():
    st.header("Log In")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Log In"):
        if username and password: # Simple check: allow any non-empty credential for now
            st.session_state.logged_in = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("Please enter a username and password.")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()

if not st.session_state.logged_in:
    login()
    st.stop() # Stop execution if not logged in

# --- Sidebar ---
st.sidebar.write(f"Logged in as: **{st.session_state.username}**")
if st.sidebar.button("Log Out"):
    logout()

st.write("Upload a receipt image to extract structured data.")

# --- Database Setup ---
DB_FILE = "receipts_db.csv"

def load_db():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Username", "Merchant", "Date", "Total", "Items"])

def save_to_db(username, merchant, date, total, items):
    df = load_db()
    # Flatten items to string
    items_str = "; ".join([f"{i['name']} ({i['price']})" for i in items])
    new_entry = pd.DataFrame([{
        "Username": username,
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
                        st.session_state.username,
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
st.subheader(f"📂 Receipt History ({st.session_state.username})")

if os.path.exists(DB_FILE):
    history_df = pd.read_csv(DB_FILE)
    
    # Filter by user if column exists
    if "Username" in history_df.columns:
        user_history = history_df[history_df["Username"] == st.session_state.username]
    else:
        # Backward compatibility for old DB (show nothing or everything? Better show nothing to stay safe)
        st.warning("Database format is old. Showing empty history. New saves will be visible.")
        user_history = pd.DataFrame()

    if not user_history.empty:
        st.dataframe(user_history, use_container_width=True)
        
        csv_bytes = user_history.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download My History (CSV)",
            data=csv_bytes,
            file_name=f"receipts_{st.session_state.username}.csv",
            mime="text/csv",
        )
    else:
        st.write("No history found for this user.")
else:
    st.write("No history yet.")
