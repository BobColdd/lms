"""
Certificate generator — St Francis Mercy Community Center
Clean, minimal, professional. A4 landscape.
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime

PAGE_W, PAGE_H = landscape(A4)

NAVY   = HexColor('#1a3a5c')
GOLD   = HexColor('#b8962e')
GREY   = HexColor('#4a4a4a')
LGREY  = HexColor('#888888')
LINE   = HexColor('#cccccc')


def _line(c, x1, y1, x2, y2, color=LINE, width=0.5):
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.line(x1, y1, x2, y2)


def generate_certificate(
    student_name: str,
    course_title: str,
    course_code: str,
    duration_months: int,
    completion_date: datetime,
    certificate_no: str,
    instructor_name: str = '',
    grade: str = '',
) -> BytesIO:

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    c.setTitle(f"Certificate – {student_name}")
    c.setAuthor("St Francis Mercy Community Center")

    W, H = PAGE_W, PAGE_H
    margin = 18 * mm

    # ── White background ──────────────────────────────────────────────────────
    c.setFillColor(white)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # ── Outer border — single clean navy rectangle ────────────────────────────
    c.setStrokeColor(NAVY)
    c.setLineWidth(3)
    c.rect(margin, margin, W - 2*margin, H - 2*margin, stroke=1, fill=0)

    # ── Inner border — thin gold line 5mm inside ──────────────────────────────
    pad = margin + 5*mm
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.8)
    c.rect(pad, pad, W - 2*pad, H - 2*pad, stroke=1, fill=0)

    # ── Top section: school identity ──────────────────────────────────────────
    top = H - margin - 13*mm

    # School name
    c.setFont('Helvetica-Bold', 15)
    c.setFillColor(NAVY)
    c.drawCentredString(W/2, top, 'ST FRANCIS MERCY COMMUNITY CENTER')

    # Thin gold rule under school name
    rule_y = top - 6*mm
    _line(c, pad + 8*mm, rule_y, W - pad - 8*mm, rule_y, GOLD, 0.8)

    # Location / contact
    c.setFont('Helvetica', 8.5)
    c.setFillColor(LGREY)
    c.drawCentredString(W/2, rule_y - 5*mm,
                        'Kiptere, Kericho County, Kenya   |   info@sfmcc.ac.ke')

    # ── Certificate heading ───────────────────────────────────────────────────
    heading_y = rule_y - 18*mm
    c.setFont('Helvetica-Bold', 22)
    c.setFillColor(NAVY)
    c.drawCentredString(W/2, heading_y, 'CERTIFICATE OF COMPLETION')

    # Decorative rule under heading: left line — diamond — right line
    ry = heading_y - 7*mm
    mid = W / 2
    rw = 90 * mm
    _line(c, mid - rw, ry, mid - 7, ry, GOLD, 1)
    _line(c, mid + 7, ry, mid + rw, ry, GOLD, 1)
    d = 5
    c.setFillColor(GOLD)
    p = c.beginPath()
    p.moveTo(mid, ry + d); p.lineTo(mid + d, ry)
    p.lineTo(mid, ry - d); p.lineTo(mid - d, ry); p.close()
    c.drawPath(p, fill=1, stroke=0)

    # ── Presented to ─────────────────────────────────────────────────────────
    presented_y = ry - 12*mm
    c.setFont('Helvetica', 10)
    c.setFillColor(GREY)
    c.drawCentredString(W/2, presented_y, 'This is to certify that')

    # ── Student name ──────────────────────────────────────────────────────────
    name_y = presented_y - 14*mm
    c.setFont('Helvetica-Bold', 28)
    c.setFillColor(NAVY)
    c.drawCentredString(W/2, name_y, student_name)

    # Underline for the name
    name_w = c.stringWidth(student_name, 'Helvetica-Bold', 28)
    _line(c, W/2 - name_w/2, name_y - 3*mm,
             W/2 + name_w/2, name_y - 3*mm, GOLD, 1)

    # ── Body copy ─────────────────────────────────────────────────────────────
    body_y = name_y - 14*mm
    c.setFont('Helvetica', 10)
    c.setFillColor(GREY)
    c.drawCentredString(W/2, body_y,
                        'has successfully completed the short course:')

    # Course title
    course_y = body_y - 11*mm
    c.setFont('Helvetica-Bold', 14)
    c.setFillColor(NAVY)
    c.drawCentredString(W/2, course_y, course_title)

    # Details line: code | duration | grade
    detail_parts = [f'Course Code: {course_code}',
                    f'Duration: {duration_months} Month{"s" if duration_months != 1 else ""}']
    if grade:
        detail_parts.append(f'Grade: {grade}')
    detail_y = course_y - 8*mm
    c.setFont('Helvetica', 9)
    c.setFillColor(LGREY)
    c.drawCentredString(W/2, detail_y, '   |   '.join(detail_parts))

    # Date
    date_y = detail_y - 9*mm
    c.setFont('Helvetica', 10)
    c.setFillColor(GREY)
    c.drawCentredString(W/2, date_y,
                        f'Awarded on  {completion_date.strftime("%d %B %Y")}')

    # ── Signature section ─────────────────────────────────────────────────────
    sig_y = margin + 24*mm          # signature line y
    sig_line_w = 52 * mm
    label_offset = -4.5 * mm
    name_offset  = -10 * mm
    role_offset  = -15 * mm

    positions = [
        (W * 0.22, instructor_name or '', 'Instructor / Trainer'),
        (W * 0.50, '',                    'Principal / Director'),
        (W * 0.78, '',                    'Official Stamp'),
    ]

    for (sx, sname, srole) in positions:
        # Signature line
        _line(c, sx - sig_line_w/2, sig_y,
                 sx + sig_line_w/2, sig_y, NAVY, 0.8)

        if sname:
            c.setFont('Helvetica-Bold', 9)
            c.setFillColor(NAVY)
            c.drawCentredString(sx, sig_y + name_offset, sname)

        c.setFont('Helvetica', 8)
        c.setFillColor(LGREY)
        c.drawCentredString(sx, sig_y + role_offset, srole)

    # Stamp circle — right position
    stamp_x = W * 0.78
    stamp_r = 16 * mm
    stamp_cy = sig_y + stamp_r - 4*mm
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.setFillColor(white)
    c.circle(stamp_x, stamp_cy, stamp_r, fill=1, stroke=1)
    c.setFont('Helvetica', 7)
    c.setFillColor(LINE)
    c.drawCentredString(stamp_x, stamp_cy + 2, 'OFFICIAL')
    c.drawCentredString(stamp_x, stamp_cy - 7, 'STAMP')

    # ── Thin separator above signatures ──────────────────────────────────────
    sep_y = sig_y + 8*mm
    _line(c, pad + 8*mm, sep_y, W - pad - 8*mm, sep_y, LINE, 0.5)

    # ── Footer: cert number ───────────────────────────────────────────────────
    footer_y = margin + 5*mm
    c.setFont('Helvetica', 7.5)
    c.setFillColor(LGREY)
    c.drawCentredString(W/2, footer_y,
                        f'Certificate No: {certificate_no}   |   '
                        f'St Francis Mercy Community Center, Kiptere, Kericho, Kenya')

    c.save()
    buf.seek(0)
    return buf
