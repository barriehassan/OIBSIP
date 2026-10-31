"""Non-interactive Agg rendering against actual temporary SQLite records."""
from datetime import datetime, timezone
import pytest
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from app.services.analytics_service import AnalyticsService
from app.visualization.bmi_chart import render_bmi_chart, REFERENCE_BOUNDARIES
from app.core.classification import classify_bmi, BMICategory

@pytest.mark.parametrize('count',[0,1,3])
def test_bmi_render_states(storage,count):
    _,profiles,save,history=storage
    p=profiles.create('Chart')
    for weight in [70,72,74][:count]:save.save(p.id,weight,1.75,datetime(2026,10,1,tzinfo=timezone.utc))
    data=AnalyticsService(history).snapshot(p.id)
    fig=Figure();canvas=FigureCanvasAgg(fig);ax=fig.add_subplot()
    render_bmi_chart(ax,data);canvas.draw()
    if count:
        assert list(ax.lines[0].get_ydata())==list(data.bmi_values)
        assert len(ax.lines[0].get_xdata())==count
        assert len(ax.lines)==4
        if count==1:assert ax.lines[0].get_linestyle()=='None'
        if count==3:assert any('all records retained' in t.get_text() for t in ax.texts)
        low,high=ax.get_ylim();assert low < min(data.bmi_values) <= max(data.bmi_values) < high
    else:
        assert len(ax.lines)==0
        assert any('No measurements' in t.get_text() for t in ax.texts)
    fig.clear()


def test_optional_thresholds_and_outlier_axis(storage):
    _,profiles,save,history=storage;p=profiles.create('Wide')
    save.save(p.id,500,.3)
    data=AnalyticsService(history).snapshot(p.id)
    fig=Figure();FigureCanvasAgg(fig);ax=fig.add_subplot()
    render_bmi_chart(ax,data,thresholds=False)
    assert len(ax.lines)==1 and ax.get_ylim()[1]>data.bmi_values[0]
    render_bmi_chart(ax,data,thresholds=True)
    assert [line.get_ydata()[0] for line in ax.lines[1:]]==list(REFERENCE_BOUNDARIES)
    assert [classify_bmi(x) for x in REFERENCE_BOUNDARIES]==[BMICategory.NORMAL,BMICategory.OVERWEIGHT,BMICategory.OBESE]
    fig.canvas.draw();fig.clear()
