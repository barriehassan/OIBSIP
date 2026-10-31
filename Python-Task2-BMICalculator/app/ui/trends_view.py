"""Persistent Trends view: profile/period controls, embedded charts and neutral stats."""
import customtkinter as ctk
from app.core.validator import ValidationError
from app.database.errors import DatabaseError
from app.services.analytics_service import PERIODS, AnalyticsData, prepare_history
from .chart_widget import ChartWidget
from .controller import UIController
from .theme import CARD, BORDER, TEXT, MUTED, TEAL, TEAL_DARK, FONT


class TrendsView(ctk.CTkFrame):
    def __init__(self, master, controller: UIController, select_profile, on_error):
        super().__init__(master,fg_color='transparent')
        self.controller=controller;self.select_profile=select_profile;self.on_error=on_error
        self.period='All records';self.profile_map={};self.data=None
        self.grid_columnconfigure(0,weight=1);self.grid_rowconfigure(1,weight=1)
        header=self._card(self);header.grid(row=0,column=0,sticky='ew',pady=(0,12))
        header.grid_columnconfigure(0,weight=1)
        self._label(header,'Measurement Trends',24,bold=True).grid(row=0,column=0,sticky='w',padx=20,pady=(13,0))
        self.profile_label=self._label(header,'',12,MUTED)
        self.profile_label.grid(row=1,column=0,sticky='w',padx=20,pady=(2,14))
        self.profile_menu=ctk.CTkOptionMenu(header,values=['No profiles yet'],command=self._select,
            fg_color=CARD,button_color=TEAL_DARK,width=240,font=(FONT,13))
        self.profile_menu.grid(row=0,column=1,rowspan=2,padx=12)
        self.period_menu=ctk.CTkOptionMenu(header,values=list(PERIODS),command=self.set_period,
            fg_color=CARD,button_color=TEAL_DARK,width=175,font=(FONT,13))
        self.period_menu.set(self.period);self.period_menu.grid(row=0,column=2,rowspan=2,padx=(0,20))
        middle=ctk.CTkFrame(self,fg_color='transparent');middle.grid(row=1,column=0,sticky='nsew',pady=(0,12))
        middle.grid_rowconfigure(0,weight=1)
        for i in range(2):middle.grid_columnconfigure(i,weight=1,uniform='charts')
        bmi=self._card(middle);bmi.grid(row=0,column=0,sticky='nsew',padx=(0,6))
        weight=self._card(middle);weight.grid(row=0,column=1,sticky='nsew',padx=(6,0))
        for frame in (bmi,weight):frame.grid_columnconfigure(0,weight=1);frame.grid_rowconfigure(1,weight=1)
        self._label(bmi,'BMI over time',18,bold=True).grid(row=0,column=0,sticky='w',padx=18,pady=(14,6))
        self.threshold_toggle=ctk.CTkCheckBox(bmi,text='Adult reference lines',font=(FONT,11),width=155,
            fg_color=TEAL_DARK,hover_color=TEAL_DARK,command=self._threshold_changed)
        self.threshold_toggle.select();self.threshold_toggle.grid(row=0,column=1,padx=15,pady=(14,6))
        self._label(weight,'Weight over time',18,bold=True).grid(row=0,column=0,sticky='w',padx=18,pady=(14,6))
        self.bmi_chart=ChartWidget(bmi,'bmi',height=300)
        self.bmi_chart.grid(row=1,column=0,columnspan=2,sticky='nsew',padx=10,pady=(0,8))
        self.weight_chart=ChartWidget(weight,'weight',height=300)
        self.weight_chart.grid(row=1,column=0,sticky='nsew',padx=10,pady=(0,8))
        lower=ctk.CTkFrame(self,fg_color='transparent');lower.grid(row=2,column=0,sticky='ew')
        self.stat_values={}
        titles=('Latest BMI','Previous BMI','BMI Δ vs previous','Highest BMI','Lowest BMI','Average BMI',
                'Latest weight','Previous weight','Weight Δ vs previous','BMI Δ vs first','Weight Δ vs first','Total measurements')
        for i,title in enumerate(titles):
            col=i%6;row=i//6
            lower.grid_columnconfigure(col,weight=1,uniform='stats')
            item=self._card(lower);item.grid(row=row,column=col,sticky='ew',padx=4,pady=4)
            self._label(item,title,11,MUTED).pack(anchor='w',padx=12,pady=(12,3))
            value=self._label(item,'—',22,TEAL,bold=True);value.pack(anchor='w',padx=12,pady=(0,12))
            self.stat_values[title]=value
        self.footnote=self._label(self,'',11,MUTED)
        self.footnote.grid(row=3,column=0,sticky='w',padx=4,pady=(8,0))

    @staticmethod
    def _card(master):
        return ctk.CTkFrame(master,fg_color=CARD,border_color=BORDER,border_width=1,corner_radius=13)

    @staticmethod
    def _label(master,text,size,colour=TEXT,bold=False):
        return ctk.CTkLabel(master,text=text,text_color=colour,font=(FONT,size,'bold' if bold else 'normal'))

    def _select(self,name: str) -> None:
        self.select_profile(self.profile_map.get(name))

    def set_period(self,period: str) -> None:
        self.period=period;self.period_menu.set(period);self.refresh()

    def _threshold_changed(self) -> None:
        if self.data:self.bmi_chart.update_data(self.data,thresholds=bool(self.threshold_toggle.get()))

    def refresh(self, all_data: AnalyticsData | None = None) -> None:
        try:
            profiles=self.controller.profiles.list()
            self.profile_map={f'{p.name[:30]}  · #{p.id}':p.id for p in profiles}
            self.profile_menu.configure(values=list(self.profile_map) or ['No profiles yet'])
            selected=next((key for key,pid in self.profile_map.items() if pid==self.controller.profile_id),'No profiles yet')
            self.profile_menu.set(selected)
            self.profile_label.configure(text='Selected profile: '+selected)
            if all_data is None:
                data=self.controller.analytics.snapshot(self.controller.profile_id,self.period)
            else:
                data=prepare_history(all_data.records,all_data.profile_id,self.period,all_data.end)
            self.data=data
            self.bmi_chart.update_data(data,thresholds=bool(self.threshold_toggle.get()))
            self.weight_chart.update_data(data)
            stats=data.statistics;latest=stats.latest;previous=stats.previous
            def number(value,suffix='',signed=False):
                return '—' if value is None else (f'{value:+.2f}' if signed else f'{value:.2f}')+suffix
            values=(number(latest.bmi_value if latest else None),number(previous.bmi_value if previous else None),
                number(stats.bmi_change,signed=True),number(stats.highest_bmi),number(stats.lowest_bmi),number(stats.average_bmi),
                number(latest.weight_kg if latest else None,' kg'),number(previous.weight_kg if previous else None,' kg'),
                number(stats.weight_change,' kg',True),number(stats.bmi_change_from_first,signed=True),
                number(stats.weight_change_from_first,' kg',True),str(stats.count))
            for value,widget in zip(values,self.stat_values.values()):widget.configure(text=value)
            self.footnote.configure(text=f'{stats.count} measurements · {self.period} · UTC dates · Δ compares measurements within this period. Informational only; not medical advice.')
        except (ValidationError,DatabaseError) as error:
            # Clear the old profile immediately rather than leaving stale values on error.
            self.profile_label.configure(text='History unavailable for the selected profile.')
            self.data=prepare_history([],self.controller.profile_id)
            self.bmi_chart.clear(self.data);self.weight_chart.clear(self.data)
            for value in self.stat_values.values():value.configure(text='—')
            self.footnote.configure(text='History could not be loaded.')
            self.on_error(error)
