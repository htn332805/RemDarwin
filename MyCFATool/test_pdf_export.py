import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from dashboard.pdf_exporter import PDFExporter

config_path = os.path.join(os.path.dirname(__file__), 'config', 'settings.yaml')

exporter = PDFExporter(config_path)

# Test overview
try:
    filename = exporter.generate_overview_pdf('AAPL', 'annual')
    print(f"Overview PDF generated: {filename}")
except Exception as e:
    print(f"Error generating overview PDF: {e}")

# Test Financial Statements
try:
    filename2 = exporter.generate_financial_statements_pdf('AAPL', 'annual')
    print(f"Financial Statements PDF generated: {filename2}")
except Exception as e:
    print(f"Error generating FS PDF: {e}")

# Test Valuation
try:
    filename3 = exporter.generate_valuation_pdf('AAPL', 'annual', 5, 3.0, 5.0, 6.0, 1.0)
    print(f"Valuation PDF generated: {filename3}")
except Exception as e:
    print(f"Error generating valuation PDF: {e}")

print("PDF export test completed.")