"""Weight line chart and compact calculator preview."""
from matplotlib.axes import Axes
from app.services.analytics_service import AnalyticsData
from .chart_theme import render_series, CYAN


def render_weight_chart(ax: Axes, data: AnalyticsData, *, compact: bool = False) -> None:
    render_series(ax,data,data.weight_values,'Weight (kg)',colour=CYAN,compact=compact)
