"""Reusable Tk-embedded figure with explicit idle callback and figure cleanup."""
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from app.services.analytics_service import AnalyticsData
from app.visualization.bmi_chart import render_bmi_chart
from app.visualization.weight_chart import render_weight_chart
from app.visualization.chart_theme import BACKGROUND

class ChartWidget(ctk.CTkFrame):
    def __init__(self, master, kind: str, *, compact: bool = False, height: int = 260):
        super().__init__(master,fg_color=BACKGROUND,corner_radius=0,height=height)
        self.pack_propagate(False)
        self.kind=kind;self.compact=compact;self.closed=False;self.data=None
        self._fingerprint=None
        self.figure=Figure(figsize=(6,2.5),dpi=100,facecolor=BACKGROUND)
        self.figure.subplots_adjust(left=.09 if compact else .13,right=.95,
                                   bottom=.28 if compact else .24,top=.93)
        self.axes=self.figure.add_subplot(111)
        self.canvas=FigureCanvasTkAgg(self.figure,master=self)
        self.canvas.get_tk_widget().configure(bg=BACKGROUND,highlightthickness=0)
        self.canvas.get_tk_widget().pack(fill='both',expand=True)

    def update_data(self, data: AnalyticsData, *, thresholds: bool = True) -> None:
        if self.closed:return
        self.data=data
        fingerprint=(data.profile_id,data.period,data.records,thresholds)
        if fingerprint==self._fingerprint:return
        self._fingerprint=fingerprint
        if self.kind=='bmi':render_bmi_chart(self.axes,data,thresholds=thresholds)
        else:render_weight_chart(self.axes,data,compact=self.compact)
        self.canvas.draw_idle()

    def clear(self, data: AnalyticsData) -> None:
        self._fingerprint=None
        self.update_data(data)

    def destroy(self) -> None:
        if not self.closed:
            self.closed=True
            widget=self.canvas.get_tk_widget()
            # TkAgg schedules idle draws; cancel them before deleting Tcl commands.
            for name in ('_idle_draw_id','_event_loop_id'):
                callback=getattr(self.canvas,name,None)
                if callback:
                    widget.after_cancel(callback);setattr(self.canvas,name,None)
            widget.destroy()
            self.figure.clear()
            self.figure.set_canvas(None)
            self.data=None;self._fingerprint=None
        super().destroy()
