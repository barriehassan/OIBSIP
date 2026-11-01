"""Profile-specific dashboard composed from existing analytics and chart widgets."""
import customtkinter as ctk
from app.core.classification import CATEGORY_METADATA
from app.core.validator import ValidationError
from app.database.errors import DatabaseError
from app.services.analytics_service import PERIODS, prepare_history
from app.services.dashboard_service import DashboardService, describe_change
from .chart_widget import ChartWidget
from .trends_view import TrendsView
from .theme import CARD, MUTED, TEAL, TEAL_DARK, FONT

class DashboardView(ctk.CTkFrame):
    _card=staticmethod(TrendsView._card)
    _label=staticmethod(TrendsView._label)

    def __init__(self, master, controller, select_profile, on_error, open_calculator):
        super().__init__(master,fg_color='transparent')
        self.controller=controller;self.select_profile=select_profile;self.on_error=on_error
        self.service=DashboardService(controller.analytics);self.period='All records'
        self.profile_map={};self.data=None;self.all_time_count=0
        self.grid_columnconfigure(0,weight=1)
        header=self._card(self);header.grid(row=0,column=0,sticky='ew',pady=(0,12));header.grid_columnconfigure(0,weight=1)
        self._label(header,'Progress Dashboard',25,bold=True).grid(row=0,column=0,sticky='w',padx=20,pady=(14,0))
        self._label(header,'Understand your measurements over time.',13,MUTED).grid(row=1,column=0,sticky='w',padx=20,pady=(2,16))
        self.profile_menu=ctk.CTkOptionMenu(header,values=['No profiles yet'],command=self._select,
            fg_color=CARD,button_color=TEAL_DARK,width=230,font=(FONT,13))
        self.profile_menu.grid(row=0,column=1,rowspan=2,padx=12)
        self.period_menu=ctk.CTkOptionMenu(header,values=list(PERIODS),command=self.set_period,
            fg_color=CARD,button_color=TEAL_DARK,width=175,font=(FONT,13))
        self.period_menu.set(self.period);self.period_menu.grid(row=0,column=2,rowspan=2,padx=(0,20))
        summaries=ctk.CTkFrame(self,fg_color='transparent');summaries.grid(row=1,column=0,sticky='ew')
        self.values={};self.details={}
        titles=('Latest BMI','Latest Weight','BMI Change','Weight Change','Total Records','Last Measurement')
        for i,title in enumerate(titles):
            col=i%3;row=i//3;summaries.grid_columnconfigure(col,weight=1,uniform='cards')
            item=self._card(summaries);item.grid(row=row,column=col,sticky='nsew',padx=4,pady=4)
            self._label(item,title,12,MUTED).pack(anchor='w',padx=18,pady=(12,0))
            value=self._label(item,'—',25,TEAL,bold=True);value.pack(anchor='w',padx=18,pady=2)
            detail=self._label(item,'',11,MUTED);detail.pack(anchor='w',padx=18,pady=(0,12))
            self.values[title]=value;self.details[title]=detail
        self.state_label=self._label(self,'',12,MUTED);self.state_label.grid(row=2,column=0,sticky='w',padx=8,pady=8)
        middle=ctk.CTkFrame(self,fg_color='transparent');middle.grid(row=3,column=0,sticky='ew',pady=(0,12))
        for col in range(2):middle.grid_columnconfigure(col,weight=1,uniform='charts')
        for col,(kind,title) in enumerate([('bmi','BMI trend'),('weight','Weight trend · kg')]):
            item=self._card(middle);item.grid(row=0,column=col,sticky='nsew',padx=4)
            item.grid_columnconfigure(0,weight=1)
            self._label(item,title,18,bold=True).grid(row=0,column=0,sticky='w',padx=18,pady=(14,8))
            if kind=='bmi':
                self.threshold_toggle=ctk.CTkCheckBox(item,text='Adult reference lines',font=(FONT,11),
                    fg_color=TEAL_DARK,command=self._threshold_changed)
                self.threshold_toggle.select();self.threshold_toggle.grid(row=0,column=1,padx=16)
            chart=ChartWidget(item,kind,height=275);chart.grid(row=1,column=0,columnspan=2,sticky='ew',padx=10,pady=(0,8))
            setattr(self,kind+'_chart',chart)
        lower=self._card(self);lower.grid(row=4,column=0,sticky='ew',padx=4)
        self._label(lower,'Historical insights',18,bold=True).pack(anchor='w',padx=18,pady=(14,5))
        self.insights=self._label(lower,'',12,MUTED);self.insights.pack(anchor='w',padx=18,pady=(0,12))
        self._label(lower,'Recent measurements · selected period',15,bold=True).pack(anchor='w',padx=18,pady=(0,6))
        self.recent=self._label(lower,'',13,MUTED);self.recent.configure(justify='left',anchor='w')
        self.recent.pack(fill='x',padx=18,pady=(0,14))
        self.calculator_button=ctk.CTkButton(self,text='Open Calculator',command=open_calculator,fg_color=TEAL_DARK,height=38)
        self.calculator_button.grid(row=5,column=0,sticky='w',padx=4,pady=12)
        self._label(self,'All statistics describe the selected period unless marked all time. UTC dates. Informational use only.',11,MUTED).grid(row=6,column=0,sticky='w',padx=4)

    def _select(self,name):self.select_profile(self.profile_map.get(name))

    def set_period(self,period):
        self.period=period;self.period_menu.set(period);self.refresh()

    def _threshold_changed(self):
        if self.data:self.bmi_chart.update_data(self.data,thresholds=bool(self.threshold_toggle.get()))

    def refresh(self,all_data=None):
        try:
            profiles=self.controller.profiles.list()
            self.profile_map={f'{p.name[:28]}  · #{p.id}':p.id for p in profiles}
            self.profile_menu.configure(values=list(self.profile_map) or ['No profiles yet'])
            self.profile_menu.set(next((n for n,pid in self.profile_map.items() if pid==self.controller.profile_id),'No profiles yet'))
            snapshot=self.service.snapshot(self.controller.profile_id,self.period,all_data=all_data)
            self.all_time_count=snapshot.all_time_count;self.render(snapshot.selected)
        except (DatabaseError,ValidationError) as error:
            self.clear_unavailable()
            self.on_error(error)

    def clear_unavailable(self):
        self.all_time_count=0
        self.render(prepare_history([],self.controller.profile_id))
        for widget in self.values.values():widget.configure(text='—')
        self.state_label.configure(text='History unavailable. Try again before interpreting these values.')

    def render(self,data):
        self.data=data;s=data.statistics;r=s.latest
        from datetime import datetime,timezone
        def date(record):return datetime.fromisoformat(record.measured_at).astimezone(timezone.utc).strftime('%d %b %Y, %H:%M UTC')
        values=(f'{r.bmi_value:.2f}' if r else '—',f'{r.weight_kg:.2f} kg' if r else '—',
            f'{s.bmi_change:+.2f}' if s.bmi_change is not None else '—',
            f'{s.weight_change:+.2f} kg' if s.weight_change is not None else '—',str(s.count),date(r).split(',')[0] if r else '—')
        comparison='Latest vs previous in selected period'
        details=(f'{r.category.value} · {date(r)}' if r else 'No measurement in this period',
            date(r) if r else 'No measurement in this period',
            describe_change(s.bmi_change,'BMI points'),describe_change(s.weight_change,'kg'),
            f'{s.count} in period / {self.all_time_count} all time',date(r).split(', ')[1] if r else 'No saved date')
        for title,value,detail in zip(self.values,values,details):
            self.values[title].configure(text=value);self.details[title].configure(text=detail)
        self.values['Latest BMI'].configure(text_color=CATEGORY_METADATA[r.category].colour if r else TEAL)
        state=('No measurements recorded yet.' if not self.all_time_count else 'No measurements in this period.') if not r else (
            'One measurement available; no established trend.' if s.count==1 else comparison+' · '+self.period)
        self.state_label.configure(text=state)
        self.bmi_chart.update_data(data,thresholds=bool(self.threshold_toggle.get()));self.weight_chart.update_data(data)
        if r:
            self.insights.configure(text=f'BMI: highest {s.highest_bmi:.2f}  ·  lowest {s.lowest_bmi:.2f}  ·  average {s.average_bmi:.2f}'+
                f'    |    First {data.dates[0]:%d %b %Y}  ·  Latest {data.dates[-1]:%d %b %Y}')
            self.recent.configure(text='\n'.join(f'{date(record)}     |     {record.weight_kg:.2f} kg     |     BMI {record.bmi_value:.2f}     |     {record.category.value}' for record in reversed(data.records[-4:])))
        else:
            self.insights.configure(text='Statistics will appear after measurements are saved.')
            self.recent.configure(text='No records to display. Open Calculator to save a measurement.')
