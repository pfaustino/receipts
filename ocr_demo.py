import easyocr
import os
import re

class ReceiptScanner:
    def __init__(self, lang=['en']):
        self.reader = easyocr.Reader(lang)

    def scan(self, image_path):
        img_path = os.path.abspath(image_path)
        if not os.path.exists(img_path):
            return {"error": "Image not found"}

        print(f"Scanning {img_path}...")
        # detail=1 returns (bbox, text, prob)
        raw_results = self.reader.readtext(img_path)
        
        # Group text into lines based on Y-coordinate
        lines = self._group_into_lines(raw_results)
        
        # Extract data
        data = self._parse_lines(lines)
        return data

    def _group_into_lines(self, raw_results):
        """
        Groups OCR results into lines based on vertical usage.
        raw_results: list of (bbox, text, prob)
        bbox: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
        """
        # Sort by Y1 (top-left vertical coordinate)
        # We use the average Y of the top two points for sorting
        sorted_results = sorted(raw_results, key=lambda r: (r[0][0][1] + r[0][1][1]) / 2)
        
        lines = []
        current_line = []
        last_y = -1
        
        # Threshold for considering text on the same line (pixels)
        # This might need tuning based on image resolution
        y_threshold = 20 

        for bbox, text, prob in sorted_results:
            # Calculate center Y of this text block
            # y_center = (top_left_y + bottom_left_y) / 2
            y_center = (bbox[0][1] + bbox[3][1]) / 2
            
            if last_y == -1:
                current_line.append((bbox, text))
                last_y = y_center
            elif abs(y_center - last_y) < y_threshold:
                current_line.append((bbox, text))
                # Update last_y to average, or keep simpler?
                # Keeping simple for now
            else:
                # New line
                # Sort current line by X coordinate before saving
                current_line.sort(key=lambda item: item[0][0][0])
                # Join text with space
                full_line_text = " ".join([item[1] for item in current_line])
                lines.append(full_line_text)
                
                # Start new line
                current_line = [(bbox, text)]
                last_y = y_center
        
        # Append last line
        if current_line:
            current_line.sort(key=lambda item: item[0][0][0])
            full_line_text = " ".join([item[1] for item in current_line])
            lines.append(full_line_text)
            
        return lines

    def _parse_lines(self, lines):
        data = {
            "merchant": None,
            "date": None,
            "total": None,
            "items": []
        }
        
        # Regex Patterns
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}'
        ]
        
        # Price at end of line: "Milk 3.50"
        item_price_pattern = r'(.*?)\s+(\d+\.\d{2})$'

        # 1. Merchant (Heuristic: First significant text line)
        for line in lines:
            if len(line.strip()) > 3 and not any(char.isdigit() for char in line):
                data["merchant"] = line.strip()
                break
                
        # 2. Date
        for line in lines:
            for pat in date_patterns:
                match = re.search(pat, line, re.IGNORECASE)
                if match:
                    data["date"] = match.group(0)
                    break 
            if data["date"]: break

        # 3. Total
        for i, line in enumerate(lines):
            # Look for TOTAL strictly
            if "TOTAL" in line.upper() and "SUBTOTAL" not in line.upper():
                # Check for price in the same line "Total: 31.17"
                price_match = re.search(r'(\d+\.\d{2})', line)
                if price_match:
                     data["total"] = price_match.group(1)
                # Check next line "Total\n31.17"
                elif i + 1 < len(lines):
                     next_line = lines[i+1]
                     price_match = re.search(r'^\s*(\d+\.\d{2})\s*$', next_line)
                     if price_match:
                         data["total"] = price_match.group(1)
                break

        # 4. Items
        # Removed "TAX" so it appears as a line item
        skip_words = ["TOTAL", "SUBTOTAL", "CASH", "CHANGE", "DUE", "THANK", "DATE", "GROCERY"]
        
        for line in lines:
            # Skip metadata lines
            upper_line = line.upper()
            if any(w in upper_line for w in skip_words):
                continue
            if data["date"] and data["date"] in line:
                continue
            if data["merchant"] and data["merchant"] in line:
                continue
            if "----------------" in line:
                continue

            # Check if line ends with a price
            match = re.search(item_price_pattern, line)
            if match:
                name = match.group(1).strip()
                price = match.group(2)
                
                # Filter noise
                if len(name) > 1 and not re.match(r'^[0-9\W]+$', name):
                    data["items"].append({"name": name, "price": price})

        return data

if __name__ == "__main__":
    scanner = ReceiptScanner()
    result = scanner.scan("sample_receipt.png")
    
    print("-" * 30)
    print("Structured Receipt Data")
    print("-" * 30)
    print(f"Merchant: {result.get('merchant')}")
    print(f"Date:     {result.get('date')}")
    print(f"Total:    {result.get('total')}")
    print("\nitems:")
    for item in result.get('items', []):
        print(f"  - {item['name']:<20} {item['price']}")
