"""BMI-over-time chart using stored, unrounded BMI values."""
from matplotlib.axes import Axes
from app.services.analytics_service import AnalyticsData
from .chart_theme import render_series, MUTED

REFERENCE_BOUNDARIES=(18.5,25.0,30.0)

def render_bmi_chart(ax: Axes, data: AnalyticsData, *, thresholds: bool = True) -> None:
    render_series(ax,data,data.bmi_values,'BMI')
    if thresholds and data.records:
        for value in REFERENCE_BOUNDARIES:
            ax.axhline(value,color=MUTED,linewidth=.7,linestyle='--',alpha=.65)
            ax.text(.99,value,f'{value:g} reference',transform=ax.get_yaxis_transform(),
                    ha='right',va='bottom',color=MUTED,fontsize=8)
        # Matplotlib autoscales over both actual values and optional references.
        ax.relim();ax.autoscale_view()
