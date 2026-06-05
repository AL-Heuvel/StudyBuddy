from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
import random


def maak_factuur(user):
    """Genereert een PDF factuur voor de gegeven gebruiker en geeft de PDF terug als bytes."""

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    breedte, hoogte = A4

    factuurnummer = f"SB-2026-{random.randint(1000, 9999)}"
    datum = datetime.now().strftime("%d-%m-%Y")

    # ── TITEL ──
    c.setFont("Helvetica-Bold", 36)
    c.drawString(40, hoogte - 70, "Factuur")

    # ── VAN ──
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, hoogte - 130, "Van")
    c.setFont("Helvetica", 10)
    c.drawString(150, hoogte - 130, "StudyBuddy B.V.")
    c.drawString(150, hoogte - 145, "Coolsingel 42, 3011 AD Rotterdam")

    # ── NAAR ──
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, hoogte - 180, "Naar")
    c.setFont("Helvetica", 10)
    c.drawString(150, hoogte - 180, user["username"])
    if user["email"]:
        c.drawString(150, hoogte - 195, user["email"])

    # ── FACTUURGEGEVENS ──
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, hoogte - 240, "Factuurnummer")
    c.drawString(200, hoogte - 240, "Factuurdatum")
    c.drawString(360, hoogte - 240, "Abonnement")
    c.setFont("Helvetica", 10)
    c.drawString(40, hoogte - 255, factuurnummer)
    c.drawString(200, hoogte - 255, datum)
    c.drawString(360, hoogte - 255, "Premium")

    # ── TABEL HEADER ──
    y = hoogte - 320
    c.setLineWidth(2)
    c.line(40, y + 15, breedte - 40, y + 15)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "Beschrijving")
    c.drawString(280, y, "Aantal")
    c.drawString(360, y, "Tarief")
    c.drawString(460, y, "Totaal")
    c.setLineWidth(0.5)
    c.line(40, y - 8, breedte - 40, y - 8)

    # ── TABEL REGELS ──
    regels = [
        ("StudyBuddy Premium abonnement", "1", "9,99 €", "9,99 €"),
        ("Extra gebruikerslicenties", "5", "4,50 €", "22,50 €"),
        ("Eenmalige setup-kosten", "1", "15,00 €", "15,00 €"),
    ]

    c.setFont("Helvetica", 10)
    y -= 35
    for beschrijving, aantal, tarief, totaal in regels:
        c.drawString(40, y, beschrijving)
        c.drawString(280, y, aantal)
        c.drawString(360, y, tarief)
        c.drawString(460, y, totaal)
        c.setStrokeColor(colors.HexColor("#eeeeee"))
        c.line(40, y - 10, breedte - 40, y - 10)
        y -= 30

    # ── TOTALEN ──
    y -= 10
    c.setFont("Helvetica", 10)
    c.drawString(360, y, "Subtotaal")
    c.drawString(460, y, "47,49 €")
    y -= 20
    c.drawString(360, y, "BTW (21%)")
    c.drawString(460, y, "9,97 €")
    y -= 25
    c.setFont("Helvetica-Bold", 11)
    c.drawString(360, y, "Totaalbedrag")
    c.drawString(460, y, "57,46 €")

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