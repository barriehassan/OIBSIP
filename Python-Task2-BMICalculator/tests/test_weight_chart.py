from datetime import datetime, timedelta, timezone
import pytest
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from app.services.analytics_service import AnalyticsService
from app.visualization.weight_chart import render_weight_chart

@pytest.mark.parametrize('count',[0,1,4])
@pytest.mark.parametrize('compact',[False,True])
def test_weight_chart(storage,count,compact):
    _,profiles,save,history=storage;p=profiles.create('Weight')
    now=datetime.now(timezone.utc)
    for i in range(count):save.save(p.id,70+i,1.75,now-timedelta(days=count-i))
    data=AnalyticsService(history).snapshot(p.id)
    fig=Figure();canvas=FigureCanvasAgg(fig);ax=fig.add_subplot()
    render_weight_chart(ax,data,compact=compact);canvas.draw()
    if count:
        assert tuple(ax.lines[0].get_ydata())==data.weight_values
        assert len(ax.lines[0].get_xdata())==count
        assert ax.get_ylabel()=='Weight (kg)'
        if compact or count==1:assert any(f'{data.weight_values[-1]:g} kg' in t.get_text() for t in ax.texts)
    else:assert len(ax.lines)==0
    fig.clear()


def test_large_history_keeps_every_record(storage):
    from dataclasses import replace
    from app.services.analytics_service import prepare_history
    _,profiles,save,_=storage;p=profiles.create('Large');record=save.save(p.id,70,1.75)
    records=[replace(record,id=i+1,weight_kg=70+i/10000) for i in range(3000)]
    data=prepare_history(records,p.id)
    fig=Figure();FigureCanvasAgg(fig);ax=fig.add_subplot()
    render_weight_chart(ax,data)
    assert len(ax.lines[0].get_ydata())==3000
    assert not ax.lines[0].get_path().should_simplify
    fig.canvas.draw();fig.clear()
