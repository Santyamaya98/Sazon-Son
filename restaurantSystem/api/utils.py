import cups
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime

def print_order_to_kitchen(order):
    """
    Print order to kitchen printer using CUPS
    This is for Linux/Raspberry Pi with CUPS installed
    """
    try:
        # Create PDF
        pdf_content = generate_order_pdf(order)
        
        # Connect to CUPS
        conn = cups.Connection()
        
        # Get available printers
        printers = conn.getPrinters()
        
        # Select kitchen printer (configure printer name)
        kitchen_printer = 'Kitchen_Printer'  # Change this to your printer name
        
        if kitchen_printer not in printers:
            # Use default printer if kitchen printer not found
            kitchen_printer = conn.getDefault()
        
        # Print the PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(pdf_content)
            tmp_file_path = tmp_file.name
        
        conn.printFile(kitchen_printer, tmp_file_path, f"Order_{order.order_number}", {})
        
        return True
        
    except Exception as e:
        # For testing without printer, just log
        print(f"Printing order {order.order_number}: {str(e)}")
        return False

def generate_order_pdf(order):
    """Generate PDF for order"""
    from io import BytesIO
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Header
    p.setFont("Helvetica-Bold", 20)
    p.drawString(100, 750, "SAZON & SON Cocina-Bar")
    
    # Order info
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, 700, f"Order #{order.order_number}")
    p.drawString(100, 680, f"Table: {order.table_number or 'N/A'}")
    p.drawString(100, 660, f"Time: {order.created_at.strftime('%H:%M')}")
    
    # Items
    p.setFont("Helvetica", 12)
    y = 620
    for item in order.items.all():
        p.drawString(100, y, f"{item.quantity}x {item.menu_item.name}")
        if item.notes:
            p.setFont("Helvetica-Oblique", 10)
            p.drawString(120, y-15, f"Note: {item.notes}")
            y -= 15
        p.setFont("Helvetica", 12)
        y -= 30
    
    # Notes
    if order.notes:
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, y-20, "Special notes:")
        p.setFont("Helvetica", 10)
        p.drawString(100, y-40, order.notes)
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer.read()

# Alternative for ESC/POS thermal printers
def print_to_thermal_printer(order):
    """
    Print to thermal printer using python-escpos
    Install: pip install python-escpos
    """
    from escpos.printer import Network, Usb
    
    try:
        # For network printer
        # printer = Network("192.168.1.100")  # Printer IP
        
        # For USB printer
        printer = Usb(0x04b8, 0x0202)  # Vendor and product ID
        
        # Print header
        printer.set(align='center', font='a', width=2, height=2)
        printer.text("SAZON & SON\n")
        printer.text("Cocina-Bar\n")
        
        printer.set(align='left', font='a', width=1, height=1)
        printer.text("-" * 32 + "\n")
        
        # Order info
        printer.text(f"Order: #{order.order_number}\n")
        printer.text(f"Table: {order.table_number or 'N/A'}\n")
        printer.text(f"Time: {order.created_at.strftime('%H:%M')}\n")
        printer.text("-" * 32 + "\n")
        
        # Items
        for item in order.items.all():
            printer.text(f"{item.quantity}x {item.menu_item.name}\n")
            if item.notes:
                printer.text(f"  -> {item.notes}\n")
        
        # Notes
        if order.notes:
            printer.text("-" * 32 + "\n")
            printer.text(f"Notes: {order.notes}\n")
        
        printer.text("-" * 32 + "\n")
        printer.text("\n\n")
        
        # Cut paper
        printer.cut()
        printer.close()
        
        return True
        
    except Exception as e:
        print(f"Error printing: {str(e)}")
        return False