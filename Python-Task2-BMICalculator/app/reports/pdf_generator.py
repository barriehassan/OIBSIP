"""Atomic local PDF export from immutable data; no Tk, SQL or network access."""
from io import BytesIO
import os
from pathlib import Path
import tempfile
from xml.sax.saxutils import escape
from datetime import timezone
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.pdfbase import pdfmetrics
from app.visualization.bmi_chart import render_bmi_chart
from app.visualization.weight_chart import render_weight_chart
from .report_models import ReportData, ReportError
from .report_styles import report_styles, NAVY, TEAL, PALE, MUTED, BORDER

DISCLAIMER=("Body Mass Index (BMI) is a screening measure, not a medical diagnosis. "
    "BMI does not directly measure body fat or account for all factors affecting an individual's health. "
    "This report is intended for general informational purposes.")


def chart_image(data, kind: str) -> BytesIO:
    """Reuse the Task 06 renderers, then apply a legible paper palette."""
    figure=Figure(figsize=(7.1,3.2),dpi=160)
    FigureCanvasAgg(figure)
    try:
        ax=figure.add_subplot(111)
        if kind=='bmi':render_bmi_chart(ax,data)
        else:render_weight_chart(ax,data)
        figure.set_facecolor('white');ax.set_facecolor('white')
        ax.tick_params(colors='#536475')
        ax.xaxis.label.set_color('#536475');ax.yaxis.label.set_color('#536475')
        for text in ax.texts:text.set_color('#263747')
        for spine in ax.spines.values():spine.set_color('#D5E0E6')
        ax.grid(True,color='#D5E0E6',linewidth=.6,linestyle=':')
        for line in ax.lines:
            if line.get_label()=='Recorded measurements':
                line.set_color('#087F8C');line.set_markerfacecolor('#087F8C');line.set_markeredgecolor('#087F8C')
        figure.subplots_adjust(left=.12,right=.95,bottom=.26,top=.94)
        stream=BytesIO();figure.savefig(stream,format='png',dpi=160,facecolor='white');stream.seek(0)
        return stream
    finally:
        figure.clear();figure.set_canvas(None)


def _build_pdf(data: ReportData, target) -> None:
    styles=report_styles()
    supported=pdfmetrics.getFont('Insight').face.charToGlyph
    for value in (data.profile.name,data.options.title):
        if any(ord(c) not in supported for c in value):
            raise ReportError('The profile name or report title contains characters unavailable in the PDF font. Use a supported spelling for export.')
    def p(text,style='Body'):
        return Paragraph(escape(str(text)),styles[style])
    def heading(text):return p(text,'Section07')
    def table(rows,widths,header=False):
        cells=[[p(c,'Head07' if header and i==0 else 'Cell07') for c in row] for i,row in enumerate(rows)]
        result=Table(cells,colWidths=widths,repeatRows=1 if header else 0,hAlign='LEFT')
        commands=[('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),
            ('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
            ('LINEBELOW',(0,0),(-1,-1),.4,BORDER),('ROWBACKGROUNDS',(0,1 if header else 0),(-1,-1),[colors.white,PALE])]
        if header:commands.append(('BACKGROUND',(0,0),(-1,0),NAVY))
        result.setStyle(TableStyle(commands));return result
    def stamp(record):
        from datetime import datetime
        return datetime.fromisoformat(record.measured_at).astimezone(timezone.utc).strftime('%d %b %Y, %H:%M:%S UTC')
    width=A4[0]-84
    story=[p('NOMOLI FORGE  /  BMI INSIGHT','Small07'),Spacer(1,12),p(data.options.title,'Title07'),
        p('BMI Measurement Summary','Small07') if data.options.title!='BMI Measurement Summary' else Spacer(1,1),
        p('Profile: '+data.profile.name),p('Generated: '+data.generated_at.astimezone(timezone.utc).strftime('%d %b %Y, %H:%M UTC'),'Small07'),
        p('Reporting period: '+data.period_label,'Small07')]
    a=data.analytics;s=a.statistics;latest=s.latest
    if a.start and data.options.period!='Custom dates':
        story.append(p(f'UTC bounds: {a.start:%Y-%m-%d %H:%M} to {a.end:%Y-%m-%d %H:%M}','Small07'))
    story.append(heading('Latest BMI measurement'))
    if latest:
        story.append(table([['BMI / adult category',f'{latest.bmi_value:.2f}  /  {latest.category.value}'],
            ['Weight / height',f'{latest.weight_kg:.2f} kg  /  {latest.height_m:.3f} m'],
            ['Recorded',stamp(latest)]],[160,width-160]))
    else:story.append(p('No measurements recorded yet.' if not data.all_time_count else 'No measurements in the selected period.'))
    story.append(heading('Progress summary - selected period'))
    if latest:
        first=a.records[0]
        change='No previous measurement available.'
        story.append(table([['First / latest',stamp(first)+' / '+stamp(latest)],
            ['BMI change (latest vs first)',f'{s.bmi_change_from_first:+.2f} BMI points' if s.count>1 else change],
            ['Weight change (latest vs first)',f'{s.weight_change_from_first:+.2f} kg' if s.count>1 else change],
            ['BMI: minimum / average / maximum',f'{s.lowest_bmi:.2f} / {s.average_bmi:.2f} / {s.highest_bmi:.2f}'],
            ['Measurements',f'{s.count} in selected period / {data.all_time_count} all time']],[190,width-190]))
        if s.count==1:story.append(p('One measurement is available; it does not establish a trend.','Small07'))
    else:story.append(p(f'0 measurements in this period / {data.all_time_count} all time.'))
    story.extend([heading('General BMI information'),
        p('Adult categories: Underweight below 18.5; Normal 18.5 to below 25; Overweight 25 to below 30; Obese 30 and above. Classification uses the original unrounded BMI.'),
        p('This adult classification system is intended for adults aged 20 and older. Changes describe measurements; they do not determine whether a change is beneficial or harmful.','Small07'),
        heading('Limitations and privacy'),p(DISCLAIMER,'Small07'),
        p('Generated locally. This exported PDF is an ordinary file and is not automatically encrypted. All dates are UTC. Keep and share it thoughtfully.','Small07')])
    streams=[]
    try:
        if data.options.include_history:
            story.extend([PageBreak(),heading('Measurement history'),p(data.period_label+' - chronological order; record ID breaks timestamp ties.','Small07')])
            if a.records:
                rows=[['Date / time (UTC)','Weight (kg)','Height (m)','BMI','Category']]
                rows.extend([[stamp(r).replace(' UTC',''),f'{r.weight_kg:.2f}',f'{r.height_m:.3f}',f'{r.bmi_value:.2f}',r.category.value] for r in a.records])
                story.append(table(rows,[155,85,85,65,width-390],True))
                story.append(p('Display values are rounded; stored values retain full precision.','Small07'))
            else:story.append(p('No measurements in the selected period.'))
        if data.options.include_charts:
            story.extend([PageBreak(),heading('Measurement trends'),p(data.period_label+' - actual saved measurements only.','Small07')])
            if s.count<2:
                story.append(p('At least two measurements are needed for a trend comparison. '+('One measurement is shown in the summary.' if s.count else 'No measurements are available in this period.')))
            else:
                for kind,title in [('bmi','BMI over time'),('weight','Weight over time (kg)')]:
                    story.append(heading(title));stream=chart_image(a,kind);streams.append(stream)
                    story.append(Image(stream,width=width,height=width*3.2/7.1))
                story.append(p('Dashed BMI lines show adult reference thresholds, not personal targets. Equal-time points may overlap; every saved record is retained.','Small07'))
        def page_footer(canvas,doc):
            canvas.saveState();canvas.setStrokeColor(BORDER);canvas.line(42,39,A4[0]-42,39)
            canvas.setFont('Insight',7);canvas.setFillColor(MUTED)
            canvas.drawString(42,26,'NOMOLI FORGE  |  BMI Insight  |  Informational use')
            canvas.drawRightString(A4[0]-42,26,f'Page {doc.page}')
            canvas.restoreState()
        doc=SimpleDocTemplate(target,pagesize=A4,leftMargin=42,rightMargin=42,topMargin=38,bottomMargin=54,
            title=data.options.title,author='NOMOLI FORGE',pageCompression=1)
        doc.build(story,onFirstPage=page_footer,onLaterPages=page_footer)
    finally:
        for stream in streams:stream.close()


def generate_pdf(data: ReportData, output_path: str | Path, *, overwrite: bool = False) -> Path:
    """Publish only a complete PDF; an existing file survives any render failure.

    Run in a separate process from Tk when exporting interactively. A temporary
    file lives beside the destination and is always removed after success/failure.
    """
    temporary=None
    try:
        if not isinstance(data,ReportData) or type(overwrite) is not bool:
            raise ReportError('Report data or output options are invalid.')
        path=Path(output_path).expanduser()
        if path.suffix.lower()!='.pdf' or not path.parent.is_dir() or path.is_dir():
            raise ReportError('Choose a PDF filename in an existing writable folder.')
        if path.exists() and not overwrite:
            raise ReportError('That PDF already exists. Choose another filename or confirm replacement.')
        with tempfile.NamedTemporaryFile(prefix='.bmi-report-',suffix='.tmp',dir=path.parent,delete=False) as stream:
            temporary=Path(stream.name)
            _build_pdf(data,stream)
            stream.flush();os.fsync(stream.fileno())
        with temporary.open('rb') as stream:
            if stream.read(5)!=b'%PDF-':raise ReportError('The report could not be completed.')
        if overwrite:os.replace(temporary,path)
        else:
            os.link(temporary,path)  # exclusive publication; do not overwrite a raced-in file
            temporary.unlink()
        return path.resolve()
    except ReportError:
        raise
    except Exception as error:
        raise ReportError('The PDF could not be saved. Check the destination folder and available disk space, then try again.') from error
    finally:
        if temporary is not None:
            try:temporary.unlink(missing_ok=True)
            except OSError as error:
                raise ReportError('The temporary report file could not be removed from the destination folder. Check folder permissions.') from error
