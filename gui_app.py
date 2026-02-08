import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import threading
import os
import csv
from ocr_demo import ReceiptScanner

class ReceiptApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Receipt Scanner")
        self.root.geometry("900x700")
        
        # Initialize Scanner
        try:
            self.scanner = ReceiptScanner()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize OCR Engine:\n{e}")
            self.root.destroy()
            return

        self.current_image_path = None
        self.scan_results = None

        self._setup_ui()

    def _setup_ui(self):
        # Left Frame: Image
        left_frame = tk.Frame(self.root, width=400, bg="#f0f0f0")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Right Frame: Controls & Results
        right_frame = tk.Frame(self.root, width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # -- Left Side Content --
        self.lbl_image = tk.Label(left_frame, text="No Image Selected", bg="#ddd")
        self.lbl_image.pack(fill=tk.BOTH, expand=True)

        # -- Right Side Content --
        # Buttons
        btn_frame = tk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        btn_select = tk.Button(btn_frame, text="Select Receipt Image", command=self.load_image, height=2)
        btn_select.pack(fill=tk.X, pady=2)

        self.btn_scan = tk.Button(btn_frame, text="Scan Receipt", command=self.start_scan, height=2, bg="#4CAF50", fg="white", state=tk.DISABLED)
        self.btn_scan.pack(fill=tk.X, pady=2)

        # Results Area
        tk.Label(right_frame, text="Extracted Data:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(20, 5))
        
        self.txt_results = scrolledtext.ScrolledText(right_frame, height=20, font=("Consolas", 10))
        self.txt_results.pack(fill=tk.BOTH, expand=True)

        # Export Button
        self.btn_export = tk.Button(right_frame, text="Export to CSV", command=self.export_csv, state=tk.DISABLED)
        self.btn_export.pack(fill=tk.X, pady=10)
        
        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.statusbar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Receipt Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        
        if not file_path:
            return

        self.current_image_path = file_path
        self.status_var.set(f"Loaded: {os.path.basename(file_path)}")
        self.btn_scan.config(state=tk.NORMAL)
        self.scan_results = None
        self.btn_export.config(state=tk.DISABLED)
        self.txt_results.delete(1.0, tk.END)

        # Display Image (Resize to fit)
        try:
            img = Image.open(file_path)
            # Calculate resize ratio to fit in 400x600 box (approx)
            img.thumbnail((400, 600))
            self.tk_img = ImageTk.PhotoImage(img)
            self.lbl_image.config(image=self.tk_img, text="")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")

    def start_scan(self):
        if not self.current_image_path:
            return

        self.btn_scan.config(state=tk.DISABLED, text="Scanning... Please Wait")
        self.status_var.set("Scanning... (This may take a moment)")
        self.root.update()

        # Run in separate thread to keep UI responsive
        thread = threading.Thread(target=self.run_ocr)
        thread.start()

    def run_ocr(self):
        try:
            results = self.scanner.scan(self.current_image_path)
            # Schedule UI update on main thread
            self.root.after(0, self.display_results, results)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Scanning Error", str(e)))
            self.root.after(0, self.reset_scan_button)

    def display_results(self, results):
        self.scan_results = results
        self.reset_scan_button()
        self.status_var.set("Scan Complete")
        self.btn_export.config(state=tk.NORMAL)

        # Format output
        output = []
        output.append(f"MERCHANT: {results.get('merchant', 'Unknown')}")
        output.append(f"DATE:     {results.get('date', 'Unknown')}")
        output.append(f"TOTAL:    {results.get('total', 'Unknown')}")
        output.append("-" * 40)
        output.append("ITEMS:")
        for item in results.get('items', []):
            output.append(f"  {item['name']:<25} {item['price']}")
        
        self.txt_results.delete(1.0, tk.END)
        self.txt_results.insert(tk.END, "\n".join(output))

    def reset_scan_button(self):
        self.btn_scan.config(state=tk.NORMAL, text="Scan Receipt")

    def export_csv(self):
        if not self.scan_results:
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="Save Receipt Data"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write Header
                writer.writerow(["Merchant", "Date", "Item Name", "Item Price"])
                
                merchant = self.scan_results.get('merchant')
                date = self.scan_results.get('date')
                
                items = self.scan_results.get('items', [])
                if items:
                    for item in items:
                        writer.writerow([merchant, date, item['name'], item['price']])
                else:
                    # Write separate row if no items
                    writer.writerow([merchant, date, "", ""])
            
            messagebox.showinfo("Success", f"Data saved to {file_path}")
            self.status_var.set(f"Saved to {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = ReceiptApp(root)
    root.mainloop()
