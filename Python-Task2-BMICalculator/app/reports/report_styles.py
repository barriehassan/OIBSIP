"""Print-friendly navy/teal typography, independent of desktop styling."""
from pathlib import Path
from matplotlib import get_data_path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

NAVY=colors.HexColor('#0B1220')
TEAL=colors.HexColor('#087F8C')
PALE=colors.HexColor('#EDF7F7')
MUTED=colors.HexColor('#536475')
BORDER=colors.HexColor('#D5E0E6')

def report_styles():
    """Embed Matplotlib's bundled DejaVu fonts for portable, searchable output."""
    fonts=Path(get_data_path())/'fonts'/'ttf'
    for name,file in [('Insight','DejaVuSans.ttf'),('Insight-Bold','DejaVuSans-Bold.ttf')]:
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name,str(fonts/file)))
    pdfmetrics.registerFontFamily('Insight',normal='Insight',bold='Insight-Bold',italic='Insight',boldItalic='Insight-Bold')
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle('Body',fontName='Insight',fontSize=9,leading=14,textColor=NAVY,spaceAfter=7,splitLongWords=True))
    styles.add(ParagraphStyle('Title07',parent=styles['Body'],fontName='Insight-Bold',fontSize=24,leading=29,spaceAfter=12))
    styles.add(ParagraphStyle('Section07',parent=styles['Body'],fontName='Insight-Bold',fontSize=13,leading=18,textColor=TEAL,spaceBefore=15,spaceAfter=9,keepWithNext=True))
    styles.add(ParagraphStyle('Small07',parent=styles['Body'],fontSize=8,leading=12,textColor=MUTED))
    styles.add(ParagraphStyle('Cell07',parent=styles['Body'],fontSize=8,leading=12,spaceAfter=0))
    styles.add(ParagraphStyle('Head07',parent=styles['Cell07'],fontName='Insight-Bold',textColor=colors.white))
    return styles
