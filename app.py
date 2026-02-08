import streamlit as st
from PIL import Image
import pandas as pd
import io
from ocr_demo import ReceiptScanner

# Page Config
st.set_page_config(page_title="Receipt Scanner", layout="wide")

st.title("🧾 Receipt Scanner & Parser")
st.write("Upload a receipt image to extract structured data.")

# Initialize Scanner (Cached to avoid reloading model)
@st.cache_resource
def get_scanner():
    return ReceiptScanner()

try:
    scanner = get_scanner()
except Exception as e:
    st.error(f"Failed to load OCR engine: {e}")
    st.stop()

# Sidebar for Input
st.sidebar.header("Input Method")
input_method = st.sidebar.radio("Choose input:", ["Upload Image", "Use Camera"])

image_file = None

if input_method == "Upload Image":
    image_file = st.sidebar.file_uploader("Choose an image...", type=["jpg", "png", "jpeg"])
elif input_method == "Use Camera":
    image_file = st.sidebar.camera_input("Take a picture")

if image_file is not None:
    # Display Image based on source
    # Camera input already shows the image in the widget, but we can show it again or just process
    if input_method == "Upload Image":
        image = Image.open(image_file)
        st.sidebar.image(image, caption="Uploaded Receipt", use_container_width=True)

    # Convert to bytes for OCR
    # EasyOCR expects a file path or bytes/numpy array
    # We'll save it temporarily to disk to be safe with our existing class
    with open("temp_receipt.png", "wb") as f:
        f.write(image_file.getbuffer())

    with st.spinner("Scanning..."):
        try:
            # Run OCR
            results = scanner.scan("temp_receipt.png")
            
            # check for errors
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
                    # Reorder columns if needed
                    st.dataframe(df, use_container_width=True)
                    
                    # CSV Download
                    # Flatten data for CSV
                    csv_data = []
                    merchant = results.get('merchant')
                    date = results.get('date')
                    
                    for item in items:
                        csv_data.append({
                            "Merchant": merchant,
                            "Date": date,
                            "Item Name": item['name'],
                            "Price": item['price']
                        })
                    
                    csv_df = pd.DataFrame(csv_data)
                    csv_bytes = csv_df.to_csv(index=False).encode('utf-8')
                    
                    st.download_button(
                        label="Download Data as CSV",
                        data=csv_bytes,
                        file_name="receipt_data.csv",
                        mime="text/csv",
                    )
                else:
                    st.info("No line items detected.")
                    
        except Exception as e:
            st.error(f"An error occurred during scanning: {e}")

else:
    st.info("Please upload an image to begin.")
