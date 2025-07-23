from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch

def create_test_w2():
    c = canvas.Canvas("test_files/w2_2023.pdf", pagesize=letter)
    width, height = letter

    # Add W-2 form content
    c.setFont("Helvetica", 12)
    
    # Employer information
    c.drawString(1*inch, height - 1*inch, "Employer's name, address, and ZIP code")
    c.drawString(1*inch, height - 1.2*inch, "ACME Corporation")
    c.drawString(1*inch, height - 1.4*inch, "123 Business Ave")
    c.drawString(1*inch, height - 1.6*inch, "San Francisco, CA 94105")
    
    # Employee information
    c.drawString(1*inch, height - 2*inch, "Employee's SSN")
    c.drawString(1*inch, height - 2.2*inch, "123-45-6789")
    
    # Wages and tax information
    c.drawString(1*inch, height - 3*inch, "Wages, tips, other comp.")
    c.drawString(3*inch, height - 3*inch, "100,000.00")
    
    c.drawString(1*inch, height - 3.5*inch, "Federal income tax withheld")
    c.drawString(3*inch, height - 3.5*inch, "25,000.00")
    
    # Save the PDF
    c.save()

if __name__ == "__main__":
    create_test_w2() 