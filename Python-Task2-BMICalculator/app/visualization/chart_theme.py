"""Integrated navy/teal chart styling; no global pyplot state."""
from datetime import timedelta, timezone
import matplotlib.dates as mdates
from matplotlib.axes import Axes
from app.services.analytics_service import AnalyticsData

BACKGROUND='#0b1a23'  # Existing approved Task 05 card surface.
GRID='#253047'
TEXT='#F9FAFB'
MUTED='#9CA3AF'
TEAL='#14B8A6'
CYAN='#06B6D4'


def style_axes(ax: Axes, compact: bool = False) -> None:
    ax.clear();ax.set_axis_on();ax.set_facecolor(BACKGROUND)
    ax.figure.set_facecolor(BACKGROUND)
    for side,spine in ax.spines.items():
        spine.set_color(GRID)
        spine.set_visible(side in ('left','bottom'))
    ax.tick_params(colors=MUTED,labelsize=7 if compact else 9,length=0,pad=6)
    ax.grid(True,color=GRID,linewidth=.6,linestyle=':',alpha=.9)
    ax.set_axisbelow(True)
    locator=mdates.AutoDateLocator(minticks=2,maxticks=4 if compact else 6,tz=timezone.utc)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b\n%Y',tz=timezone.utc))
    ax.xaxis.get_offset_text().set_color(MUTED)
    ax.xaxis.get_offset_text().set_fontsize(7 if compact else 9)


def render_series(ax: Axes, data: AnalyticsData, values: tuple[float, ...],
                  ylabel: str, colour: str = TEAL, compact: bool = False) -> None:
    """Draw every stored point; equal timestamps are retained, not averaged/jittered."""
    style_axes(ax,compact)
    if not values:
        ax.set_axis_off()
        ax.text(.5,.55,'No measurements in this period',ha='center',va='center',
                color=TEXT,fontsize=9 if compact else 13,transform=ax.transAxes)
        ax.text(.5,.32,'Save a measurement or choose another period.',ha='center',
                color=MUTED,fontsize=8 if compact else 10,transform=ax.transAxes)
        return
    date_format='%d %b\n%H:%M' if data.dates[-1]-data.dates[0] < timedelta(days=2) else '%d %b\n%Y'
    ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format,tz=timezone.utc))
    line,=ax.plot(data.dates,values,color=colour,linewidth=1.6,
        linestyle='-' if len(values)>1 else 'None',marker='o',
        markersize=2 if len(values)>500 else (4 if compact else 5),
        markerfacecolor=colour,markeredgecolor=colour,markeredgewidth=.7,
        label='Recorded measurements',rasterized=len(values)>2000)
    line.get_path().should_simplify=False
    ax.set_ylabel(ylabel,color=MUTED,fontsize=8 if compact else 10)
    if not compact: ax.set_xlabel('Measurement date (UTC)',color=MUTED,fontsize=9)
    ax.margins(x=.05,y=.17)
    if data.dates[0] == data.dates[-1]:
        ax.set_xlim(data.dates[0]-timedelta(hours=12),data.dates[-1]+timedelta(hours=12))
    if len(values)==1 or compact:
        ax.annotate(f'{values[-1]:.2f}' if ylabel=='BMI' else f'{values[-1]:g} kg',
                    xy=(data.dates[-1],values[-1]),xytext=(-7,10),textcoords='offset points',
                    ha='right',color=TEXT,fontsize=8 if compact else 10)
    if len(data.dates)!=len(set(data.dates)):
        ax.text(.01,.98,'Equal-time markers may overlap; all records retained.',
                transform=ax.transAxes,va='top',color=MUTED,fontsize=7 if compact else 8)
