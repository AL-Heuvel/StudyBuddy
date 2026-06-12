from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
import random

# Prijzen per pakket (excl. BTW)
PAKKET_PRIJZEN = {
    "starter": ("Starter pakket - tot 1.000 views/maand", 49.00),
    "basis":   ("Basis pakket - tot 5.000 views/maand", 99.00),
    "premium": ("Premium pakket - tot 10.000 views/maand", 199.00),
}


def maak_advertentie_factuur(gegevens):
    """
    Genereert een PDF factuur voor een advertentie-aanvraag.
    gegevens is een dict met: bedrijf_naam, contactpersoon, email, views_pakket
    Geeft (pdf_bytes, factuurnummer) terug.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    breedte, hoogte = A4

    factuurnummer = f"SB-ADV-2026-{random.randint(1000, 9999)}"
    datum = datetime.now().strftime("%d-%m-%Y")

    pakket = gegevens.get("views_pakket", "starter").lower()
    pakket_omschrijving, prijs = PAKKET_PRIJZEN.get(pakket, PAKKET_PRIJZEN["starter"])

    btw = round(prijs * 0.21, 2)
    totaal = round(prijs + btw, 2)

    def euro(bedrag):
        return f"{bedrag:.2f} EUR".replace(".", ",")

    # ── TITEL ──
    c.setFont("Helvetica-Bold", 36)
    c.drawString(40, hoogte - 70, "Factuur")

    # ── VAN ──
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, hoogte - 130, "Van")
    c.setFont("Helvetica", 10)
    c.drawString(150, hoogte - 130, "StudyBuddy B.V.")
    c.drawString(150, hoogte - 145, "Coolsingel 42, 3011 AD Rotterdam")

    # ── NAAR (advertentie-gegevens) ──
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, hoogte - 185, "Naar")
    c.setFont("Helvetica", 10)
    c.drawString(150, hoogte - 185, gegevens.get("bedrijf_naam", ""))
    c.drawString(150, hoogte - 200, f"T.a.v. {gegevens.get('contactpersoon', '')}")
    c.drawString(150, hoogte - 215, gegevens.get("email", ""))

    # ── FACTUURGEGEVENS ──
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, hoogte - 260, "Factuurnummer")
    c.drawString(200, hoogte - 260, "Factuurdatum")
    c.drawString(360, hoogte - 260, "Pakket")
    c.setFont("Helvetica", 10)
    c.drawString(40, hoogte - 275, factuurnummer)
    c.drawString(200, hoogte - 275, datum)
    c.drawString(360, hoogte - 275, pakket.capitalize())

    # ── TABEL HEADER ──
    y = hoogte - 335
    c.setLineWidth(2)
    c.setStrokeColor(colors.black)
    c.line(40, y + 15, breedte - 40, y + 15)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "Beschrijving")
    c.drawString(300, y, "Aantal")
    c.drawString(380, y, "Tarief")
    c.drawString(470, y, "Totaal")
    c.setLineWidth(0.5)
    c.line(40, y - 8, breedte - 40, y - 8)

    # ── TABEL REGEL ──
    c.setFont("Helvetica", 10)
    y -= 35
    c.drawString(40, y, pakket_omschrijving)
    c.drawString(300, y, "1")
    c.drawString(380, y, euro(prijs))
    c.drawString(470, y, euro(prijs))
    c.setStrokeColor(colors.HexColor("#eeeeee"))
    c.line(40, y - 12, breedte - 40, y - 12)

    # ── TOTALEN ──
    y -= 45
    c.setFont("Helvetica", 10)
    c.drawString(380, y, "Subtotaal")
    c.drawString(470, y, euro(prijs))
    y -= 20
    c.drawString(380, y, "BTW (21%)")
    c.drawString(470, y, euro(btw))
    y -= 25
    c.setFont("Helvetica-Bold", 11)
    c.drawString(380, y, "Totaalbedrag")
    c.drawString(470, y, euro(totaal))

    # ── FOOTER ──
    c.setStrokeColor(colors.HexColor("#dddddd"))
    c.setLineWidth(0.5)
    c.line(40, 80, breedte - 40, 80)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(40, 65, "StudyBuddy B.V.")
    c.setFont("Helvetica", 8)
    c.drawString(40, 52, "Coolsingel 42, 3011 AD Rotterdam")
    c.drawString(40, 41, "BTW-nummer: NL123456789B01")
    c.drawString(250, 52, "Email: facturen@studybuddy.nl")
    c.drawString(250, 41, "IBAN: NL00 INGB 0000 0000 00")

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer.getvalue(), factuurnummer
