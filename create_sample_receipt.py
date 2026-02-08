from PIL import Image, ImageDraw, ImageFont
import random
import os

def create_receipt(index):
    # Data Pools
    merchants = ["GROCERY STORE", "TECH HAVEN", "CITY BOOKS", "COFFEE SPOT", "BURGER JOINT"]
    addresses = ["123 Main St", "456 Oak Ave", "789 Pine Rd", "321 Elm St", "654 Maple Dr"]
    dates = ["01/15/2026", "02/08/2026", "03/22/2026", "12/05/2025", "11/11/2025"]
    
    all_items = [
        ("Milk", 3.50), ("Eggs", 2.99), ("Bread", 4.25), ("Apples", 5.10), ("Chicken", 12.50),
        ("USB Cable", 8.99), ("Mouse", 15.50), ("Keyboard", 25.00), ("Monitor", 150.00),
        ("Novel", 12.99), ("Magazine", 5.99), ("Notebook", 3.50), ("Pen", 1.50),
        ("Latte", 4.50), ("Muffin", 3.00), ("Sandwich", 8.50), ("Tea", 3.00),
        ("Burger", 9.99), ("Fries", 3.99), ("Soda", 2.50), ("Shake", 4.50)
    ]

    # Random Selections
    merchant = random.choice(merchants)
    address = random.choice(addresses)
    date = random.choice(dates)
    
    # Select 3-6 random items
    num_items = random.randint(3, 6)
    selected_items = random.sample(all_items, num_items)

    # Create Image
    width = 400
    height = 600
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)

    # Fonts
    try:
        font = ImageFont.truetype("arial.ttf", 20)
        header_font = ImageFont.truetype("arial.ttf", 30)
    except IOError:
        font = ImageFont.load_default()
        header_font = ImageFont.load_default()

    # Draw Header
    draw.text((50, 20), merchant, font=header_font, fill='black')
    draw.text((100, 60), address, font=font, fill='black')
    draw.text((100, 90), "Anytown, USA", font=font, fill='black')
    draw.text((100, 110), f"Date: {date}", font=font, fill='black')
    draw.text((20, 140), "-"*40, font=font, fill='black')

    # Draw Items
    y = 170
    subtotal_val = 0.0
    
    for item_name, price in selected_items:
        draw.text((30, y), item_name, font=font, fill='black')
        draw.text((300, y), f"{price:.2f}", font=font, fill='black')
        subtotal_val += price
        y += 30

    draw.text((20, y), "-"*40, font=font, fill='black')
    y += 30
    
    tax_val = subtotal_val * 0.1
    total_val = subtotal_val + tax_val

    draw.text((30, y), "Subtotal", font=font, fill='black')
    draw.text((300, y), f"{subtotal_val:.2f}", font=font, fill='black')
    y += 30
    draw.text((30, y), "Tax (10%)", font=font, fill='black')
    draw.text((300, y), f"{tax_val:.2f}", font=font, fill='black')
    y += 30
    draw.text((30, y), "TOTAL", font=header_font, fill='black')
    draw.text((300, y), f"{total_val:.2f}", font=header_font, fill='black')
    
    y += 60
    draw.text((80, y), "Thank you for shopping!", font=font, fill='black')

    # Rotation/Noise
    image = image.rotate(random.uniform(-1, 1), expand=True, fillcolor='white')

    filename = f"sample_receipt_{index}.png"
    image.save(filename)
    print(f"Created {filename}")

if __name__ == "__main__":
    for i in range(1, 11):
        create_receipt(i)
