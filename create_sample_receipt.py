from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random

def create_receipt():
    # Create a white image
    width = 400
    height = 600
    # Add some noise/texture to simulate paper
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)

    # Try to load a font, fallback to default
    try:
        # On Windows, arial.ttf should be standard
        font = ImageFont.truetype("arial.ttf", 20)
        header_font = ImageFont.truetype("arial.ttf", 30)
    except IOError:
        font = ImageFont.load_default()
        header_font = ImageFont.load_default()

    # Draw text
    draw.text((100, 20), "GROCERY STORE", font=header_font, fill='black')
    draw.text((120, 60), "123 Main St", font=font, fill='black')
    draw.text((120, 90), "Anytown, USA", font=font, fill='black')
    draw.text((120, 110), "Date: 02/08/2026", font=font, fill='black')
    draw.text((20, 140), "-"*40, font=font, fill='black')

    items = [
        ("Milk", "3.50"),
        ("Eggs", "2.99"),
        ("Bread", "4.25"),
        ("Apples", "5.10"),
        ("Chicken", "12.50")
    ]

    y = 160
    for item, price in items:
        draw.text((30, y), item, font=font, fill='black')
        draw.text((300, y), price, font=font, fill='black')
        y += 30

    draw.text((20, y), "-"*40, font=font, fill='black')
    y += 30
    
    subtotal = "28.34"
    tax = "2.83"
    total = "31.17"

    draw.text((30, y), "Subtotal", font=font, fill='black')
    draw.text((300, y), subtotal, font=font, fill='black')
    y += 30
    draw.text((30, y), "Tax (10%)", font=font, fill='black')
    draw.text((300, y), tax, font=font, fill='black')
    y += 30
    draw.text((30, y), "TOTAL", font=header_font, fill='black')
    draw.text((300, y), total, font=header_font, fill='black')
    
    y += 60
    draw.text((80, y), "Thank you for shopping!", font=font, fill='black')

    # Save the clean version
    image.save("sample_receipt_clean.png")

    # Add some distortion for "realism" (simple rotation and blur)
    image = image.rotate(random.uniform(-2, 2), expand=True, fillcolor='white')
    # Use GaussianBlur 1 to simulate slight out of focus
    # image = image.filter(ImageFilter.GaussianBlur(1))

    image.save("sample_receipt.png")
    print("sample_receipt.png created successfully.")

if __name__ == "__main__":
    create_receipt()
