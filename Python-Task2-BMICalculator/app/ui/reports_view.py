"""Report controls and process-based export; Tk remains on its main thread."""
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from datetime import date
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from app.core.validator import ValidationError
from app.database.errors import DatabaseError
from app.reports.report_models import ReportOptions, ReportError, safe_filename
from app.reports.pdf_generator import generate_pdf
from app.services.report_service import ReportService
from app.services.analytics_service import PERIODS
from .trends_view import TrendsView
from .theme import CARD, INNER, MUTED, TEXT, TEAL, TEAL_DARK, CORAL, FONT, BORDER

class ReportsView(ctk.CTkFrame):
    _card=staticmethod(TrendsView._card)
    _label=staticmethod(TrendsView._label)

    def __init__(self, master, controller, select_profile, on_error):
        super().__init__(master,fg_color='transparent')
        self.controller=controller;self.select_profile=select_profile;self.on_error=on_error
        self.service=ReportService(controller.profiles,controller.history)
        self.profile_map={};self.executor=None;self.future=None;self._poll_job=None;self.closed=False
        self.export_profile=None;self.selected_profile_id=None
        self.grid_columnconfigure(0,weight=3,uniform='report');self.grid_columnconfigure(1,weight=2,uniform='report')
        header=self._card(self);header.grid(row=0,column=0,columnspan=2,sticky='ew',pady=(0,16));header.grid_columnconfigure(0,weight=1)
        self._label(header,'PDF Reports',25,bold=True).grid(row=0,column=0,sticky='w',padx=22,pady=(16,0))
        self._label(header,'Your measurements, clearly presented. Generated on your device.',13,MUTED).grid(row=1,column=0,sticky='w',padx=22,pady=(2,18))
        self.profile_menu=ctk.CTkOptionMenu(header,values=['No profiles yet'],command=self._select,
            fg_color=INNER,button_color=TEAL_DARK,width=250,font=(FONT,13))
        self.profile_menu.grid(row=0,column=1,rowspan=2,padx=22)
        form=self._card(self);form.grid(row=1,column=0,sticky='nsew',padx=(0,14));form.grid_columnconfigure(0,weight=1)
        self._label(form,'Create a measurement report',20,bold=True).grid(row=0,column=0,sticky='w',padx=24,pady=(22,14))
        self._label(form,'Report title',13,MUTED).grid(row=1,column=0,sticky='w',padx=24)
        self.title_entry=ctk.CTkEntry(form,height=44,fg_color=INNER,border_color=BORDER,font=(FONT,15))
        self.title_entry.insert(0,'BMI Measurement Summary');self.title_entry.grid(row=2,column=0,sticky='ew',padx=24,pady=(5,16))
        self._label(form,'Reporting period',13,MUTED).grid(row=3,column=0,sticky='w',padx=24)
        self.period_menu=ctk.CTkOptionMenu(form,values=[*PERIODS,'Custom dates'],command=self._period_changed,
            height=40,fg_color=INNER,button_color=TEAL_DARK,font=(FONT,14))
        self.period_menu.set('All records');self.period_menu.grid(row=4,column=0,sticky='ew',padx=24,pady=(5,12))
        dates=ctk.CTkFrame(form,fg_color='transparent');dates.grid(row=5,column=0,sticky='ew',padx=24)
        for col in range(2):dates.grid_columnconfigure(col,weight=1)
        self._label(dates,'From (YYYY-MM-DD, UTC)',12,MUTED).grid(row=0,column=0,sticky='w')
        self._label(dates,'Through (YYYY-MM-DD, UTC)',12,MUTED).grid(row=0,column=1,sticky='w',padx=(10,0))
        self.start_entry=ctk.CTkEntry(dates,height=38,fg_color=INNER,border_color=BORDER)
        self.end_entry=ctk.CTkEntry(dates,height=38,fg_color=INNER,border_color=BORDER)
        self.start_entry.grid(row=1,column=0,sticky='ew',padx=(0,10),pady=6)
        self.end_entry.grid(row=1,column=1,sticky='ew',padx=(10,0),pady=6)
        self.history_toggle=ctk.CTkCheckBox(form,text='Include measurement history',fg_color=TEAL_DARK,font=(FONT,14))
        self.history_toggle.select();self.history_toggle.grid(row=6,column=0,sticky='w',padx=24,pady=(18,12))
        self.charts_toggle=ctk.CTkCheckBox(form,text='Include BMI and weight charts',fg_color=TEAL_DARK,font=(FONT,14))
        self.charts_toggle.select();self.charts_toggle.grid(row=7,column=0,sticky='w',padx=24,pady=(0,20))
        self.generate_button=ctk.CTkButton(form,text='Choose location & Generate PDF',command=self.generate,
            height=48,fg_color=TEAL_DARK,hover_color='#087F8C',border_width=1,border_color=TEAL,font=(FONT,15,'bold'))
        self.generate_button.grid(row=8,column=0,sticky='ew',padx=24,pady=(8,16))
        self.status=self._label(form,'Choose a profile and reporting period.',12,MUTED)
        self.status.configure(wraplength=550,justify='left');self.status.grid(row=9,column=0,sticky='w',padx=24,pady=(0,24))
        form.bind('<Configure>',lambda e:self.status.configure(wraplength=max(250,e.width-48)))
        info=self._card(self);info.grid(row=1,column=1,sticky='nsew');info.grid_columnconfigure(0,weight=1)
        self._label(info,'NOMOLI FORGE',12,TEAL,bold=True).grid(row=0,column=0,sticky='w',padx=24,pady=(24,5))
        self._label(info,'BMI Measurement Summary',21,bold=True).grid(row=1,column=0,sticky='w',padx=24,pady=(0,16))
        self.summary=self._label(info,'',14,TEXT);self.summary.configure(justify='left',wraplength=380)
        self.summary.grid(row=2,column=0,sticky='w',padx=24,pady=(0,20))
        self._label(info,'Included in every report',15,bold=True).grid(row=3,column=0,sticky='w',padx=24,pady=(10,6))
        self._label(info,'Latest measurement and classification\nProgress summary and descriptive statistics\nAdult BMI reference categories\nLimitations and educational-use disclaimer',13,MUTED).grid(row=4,column=0,sticky='w',padx=24,pady=(0,22))
        note=self._label(info,'Exports stay local. PDFs are ordinary files and are not automatically encrypted. You choose where to save each report.\n\nStatistics use only the selected profile and period. Reports capture a snapshot when Generate is selected; later edits do not change the exported file.',13,MUTED)
        note.configure(wraplength=380,justify='left');note.grid(row=5,column=0,sticky='w',padx=24,pady=(0,24))
        info.bind('<Configure>',lambda e:(note.configure(wraplength=max(260,e.width-48)),self.summary.configure(wraplength=max(260,e.width-48))))
        for entry in (self.title_entry,self.start_entry,self.end_entry):
            entry.bind('<FocusOut>',lambda event:self.refresh())
        self._period_changed('All records')

    @property
    def busy(self):return self.future is not None

    def _select(self,name):self.select_profile(self.profile_map.get(name))

    def _period_changed(self,period):
        state='normal' if period=='Custom dates' else 'disabled'
        self.start_entry.configure(state=state);self.end_entry.configure(state=state)
        self.refresh()

    def options(self):
        period=self.period_menu.get();start=end=None
        if period=='Custom dates':
            try:start=date.fromisoformat(self.start_entry.get());end=date.fromisoformat(self.end_entry.get())
            except ValueError as error:raise ValidationError('Enter both dates as YYYY-MM-DD.') from error
        return ReportOptions(self.title_entry.get(),period,bool(self.history_toggle.get()),bool(self.charts_toggle.get()),start,end)

    def refresh(self,all_data=None):
        try:
            profiles=self.controller.profiles.list()
            self.profile_map={f'{p.name[:30]}  · #{p.id}':p.id for p in profiles}
            self.profile_menu.configure(values=list(self.profile_map) or ['No profiles yet'])
            self.profile_menu.set(next((n for n,pid in self.profile_map.items() if pid==self.controller.profile_id),'No profiles yet'))
            if self.selected_profile_id!=self.controller.profile_id and not self.busy:
                self.status.configure(text='Choose a profile and reporting period.',text_color=MUTED)
            self.selected_profile_id=self.controller.profile_id
            self.generate_button.configure(state='normal' if self.controller.profile_id is not None and not self.busy else 'disabled')
            if self.controller.profile_id is None:
                self.summary.configure(text='No profile selected.\nCreate a profile in Calculator or Profiles.');return
            try:
                data=self.service.prepare(self.controller.profile_id,self.options())
                self.summary.configure(text=f'{data.profile.name}\n\n{data.period_label}\n{len(data.analytics.records)} records in period\n{data.all_time_count} records all time\n\nDates and times are shown in UTC.')
            except ValidationError:
                self.summary.configure(text='Complete the report options and dates before generating.')
        except DatabaseError as error:
            self.summary.configure(text='Profile history unavailable.');self.generate_button.configure(state='disabled');self.on_error(error)

    def generate(self):
        if self.busy:return
        try:
            if self.controller.profile_id is None:raise ValidationError('Select a profile before exporting.')
            data=self.service.prepare(self.controller.profile_id,self.options())
            path=filedialog.asksaveasfilename(parent=self,title='Save BMI report',defaultextension='.pdf',
                filetypes=[('PDF document','*.pdf')],initialfile=safe_filename(data.profile.name,data.generated_at))
            if not path:return
            self.start_export(data,path)
        except (ValidationError,DatabaseError,ReportError) as error:
            self.status.configure(text=str(error),text_color=CORAL)

    def start_export(self,data,path):
        """Start one isolated renderer; polling and all widget updates stay in Tk."""
        if self.busy:raise ReportError('A report is already being generated.')
        try:
            if self.executor is None:self.executor=ProcessPoolExecutor(max_workers=1,mp_context=get_context('spawn'))
            self.future=self.executor.submit(generate_pdf,data,path,overwrite=Path(path).exists())
        except Exception as error:
            if self.executor:self.executor.shutdown(wait=False,cancel_futures=True);self.executor=None
            raise ReportError('The report worker could not start. Try again.') from error
        self.export_profile=data.profile.name
        self.generate_button.configure(state='disabled')
        self.status.configure(text=f'Generating report for {self.export_profile}… You can keep using the other pages.',text_color=TEAL)
        self._poll_job=self.after(100,self._poll)

    def _poll(self):
        self._poll_job=None
        if self.closed:return
        if not self.future.done():
            self._poll_job=self.after(100,self._poll);return
        try:
            path=self.future.result()
            self.status.configure(text=f'Saved report for {self.export_profile}:\n{path}',text_color=TEAL)
        except Exception as error:
            message=str(error) if isinstance(error,ReportError) else 'Report generation failed. No completed report was published. Try again.'
            self.status.configure(text=message,text_color=CORAL)
            if self.executor:self.executor.shutdown(wait=False,cancel_futures=True);self.executor=None
        finally:
            self.future=None
            self.generate_button.configure(state='normal' if self.controller.profile_id is not None else 'disabled')

    def destroy(self):
        self.closed=True
        if self._poll_job:self.after_cancel(self._poll_job);self._poll_job=None
        if self.executor:self.executor.shutdown(wait=False,cancel_futures=True);self.executor=None
        super().destroy()
