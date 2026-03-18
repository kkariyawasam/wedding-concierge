from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

os.makedirs("app/data/contracts", exist_ok=True)
path = "app/data/contracts/sample_contract.pdf"

c = canvas.Canvas(path, pagesize=letter)
text = c.beginText(40, 750)
text.setFont("Helvetica", 11)

lines = [
    "WEDDING CATERING AGREEMENT",
    "",
    "1) Deposit: Client will pay a 30% deposit within 7 days of signing.",
    "   Deposit is non-refundable after 14 days from signing.",
    "",
    "2) Cancellation: If canceled within 60 days of the event, client owes 50% of remaining balance.",
    "   If canceled within 30 days, client owes 100% of remaining balance.",
    "",
    "3) Overtime Fees: €200 per hour billed in 30-minute increments.",
    "",
    "4) Payment Schedule: Remaining balance due 14 days before event date.",
    "",
    "5) Minimum Guest Count: 80 guests minimum. Additional guests €85 per person.",
    "",
    "6) Force Majeure: Vendor not liable for events outside reasonable control.",
    "",
    "7) Additional Fees: Service charge 12% and travel fee €150 if outside city limits.",
]
for ln in lines:
    text.textLine(ln)

c.drawText(text)
c.showPage()
c.save()
print("Created:", path)