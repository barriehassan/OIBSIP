"""Approved Vitality Analytics desktop layout and service-backed interactions."""
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw
from app.core.classification import CATEGORY_METADATA
from app.core.validator import ValidationError
from app.database.errors import DatabaseError
from .controller import UIController
from .gauge import BMIGauge
from .icons import icon
from .chart_widget import ChartWidget
from .trends_view import TrendsView
from .dashboard_view import DashboardView
from .reports_view import ReportsView
from app.services.analytics_service import PERIODS, prepare_history
from .theme import BG, CARD, INNER, BORDER, TEXT, MUTED, TEAL, TEAL_DARK, CORAL, FONT

ASSETS = Path(__file__).resolve().parents[2] / 'assets'


def label(master, text: str, size: int = 14, colour: str = TEXT, bold: bool = False, **kwargs):
    return ctk.CTkLabel(master, text=text, text_color=colour,
                        font=(FONT,size,'bold' if bold else 'normal'), **kwargs)


def button(master, text: str, command, primary: bool = False, **kwargs):
    return ctk.CTkButton(master,text=text,command=command,corner_radius=9,
        fg_color='#009b9a' if primary else INNER,hover_color='#07565f' if primary else '#183340',
        border_width=1,border_color=TEAL if primary else BORDER,text_color=TEXT,
        font=(FONT,14,'bold' if primary else 'normal'),height=43,**kwargs)


def card(master):
    return ctk.CTkFrame(master,fg_color=CARD,border_color=BORDER,border_width=1,corner_radius=13)


def display_time(timestamp: str) -> str:
    return datetime.fromisoformat(timestamp).astimezone().strftime('%d %b %Y, %H:%M')


class BMIWindow(ctk.CTk):
    """Desktop view. All domain and persistence operations go through services."""
    def __init__(self, controller: UIController):
        ctk.set_appearance_mode('dark')
        super().__init__()
        self.controller = controller
        self.title('NOMOLI FORGE — BMI Insight')
        self.geometry('1440x1010')
        self.minsize(1240,860)
        self.configure(fg_color=BG)
        self.protocol('WM_DELETE_WINDOW', self.destroy)
        self.grid_columnconfigure(0,weight=1)
        self.grid_rowconfigure(2,weight=1)
        self.active_page = 'Calculator'
        self.trends_page = None
        self.dashboard_page = None
        self.reports_page = None
        self.preview_period = 'Last 6 months'
        self.profile_map: dict[str,int] = {}
        self.weight = tk.StringVar()
        self.height = tk.StringVar()
        self.status = tk.StringVar(value='Enter your height and weight to begin.')
        self._building = True
        self._hero_job = None
        self._hero_source = Image.open(ASSETS/'mountain_reference.png').convert('RGB') if (ASSETS/'mountain_reference.png').exists() else None
        self._nav()
        self._hero()
        self.viewport=ctk.CTkScrollableFrame(self,fg_color=BG,corner_radius=0,
            scrollbar_button_color=BORDER,scrollbar_button_hover_color=TEAL_DARK)
        self.viewport.grid(row=2,column=0,sticky='nsew',padx=(18,8),pady=(0,16))
        self.body = ctk.CTkFrame(self.viewport,fg_color='transparent',height=748)
        self.body.pack(fill='x',expand=True)
        self.body.grid_propagate(False)
        self.bind('<Configure>',self._resize_content,add='+')
        self.body.grid_rowconfigure(0,weight=1)
        self.body.grid_columnconfigure(0,weight=1)
        self.calculator = ctk.CTkFrame(self.body,fg_color='transparent')
        self.calculator.grid(row=0,column=0,sticky='nsew')
        self.calculator.grid_rowconfigure(0,weight=1)
        self.calculator.grid_columnconfigure(0,weight=35,uniform='main')
        self.calculator.grid_columnconfigure(1,weight=65,uniform='main')
        self._measurements()
        self._results()
        self.other_page = ctk.CTkFrame(self.body,fg_color='transparent')
        for var in (self.weight,self.height): var.trace_add('write', self._input_changed)
        self._building = False
        self.reload_profiles()
        self._render_result()
        self.refresh_summary()
        self.bind('<Return>',lambda event:self.calculate() if self.active_page=='Calculator' and self.focus_get() in (self.weight_entry,self.height_entry) else None)
        self.bind('<Escape>',lambda event:self.focus_set())

    def _nav(self) -> None:
        nav = ctk.CTkFrame(self,fg_color='#06131c',corner_radius=0,height=76,border_width=1,border_color=BORDER)
        nav.grid(row=0,column=0,sticky='ew',padx=8,pady=(8,0));nav.grid_propagate(False)
        nav.grid_rowconfigure(0,weight=1);nav.grid_columnconfigure(1,weight=1)
        brand = ctk.CTkFrame(nav,fg_color='transparent',width=435)
        brand.grid(row=0,column=0,sticky='nsw',padx=(18,8));brand.grid_propagate(False)
        mark = tk.Canvas(brand,width=34,height=44,bg='#06131c',highlightthickness=0)
        mark.place(x=0,y=15)
        mark.create_line(1,39,17,6,32,39,fill=TEAL,width=3)
        mark.create_line(8,39,19,18,25,39,fill='#75f4f0',width=2)
        label(brand,'NOMOLI',18,bold=True).place(x=45,y=15)
        label(brand,'FORGE',18,TEAL,bold=True).place(x=132,y=15)
        ctk.CTkFrame(brand,width=1,height=37,fg_color=BORDER).place(x=214,y=16)
        label(brand,'BMI Insight',20,bold=True).place(x=231,y=8)
        label(brand,'MEASURE   UNDERSTAND   PROGRESS',10,MUTED).place(x=231,y=36)
        links = ctk.CTkFrame(nav,fg_color='transparent');links.grid(row=0,column=1,sticky='ew')
        self.nav_buttons = {}
        self.nav_lines = {}
        for i,(name,icon_name) in enumerate([('Calculator','calculator'),('Profiles','profile'),('History','history'),('Trends','trends'),('Dashboard','dashboard'),('Reports','reports')]):
            links.grid_columnconfigure(i,weight=1)
            b = ctk.CTkButton(links,text=name,image=icon(icon_name,17,MUTED),compound='left',font=(FONT,13),height=45,
                fg_color='transparent',hover_color='#12323d',text_color=MUTED,corner_radius=4,
                command=lambda n=name:self.navigate(n))
            b.grid(row=0,column=i,sticky='ew',padx=2);self.nav_buttons[name]=b
            underline=ctk.CTkFrame(links,height=2,corner_radius=0,fg_color=BG)
            underline.grid(row=1,column=i,sticky='ew',padx=5)
            self.nav_lines[name]=underline
        controls = ctk.CTkFrame(nav,fg_color='transparent');controls.grid(row=0,column=2,padx=8)
        for text,command in [('−',self.iconify),('□',self.toggle_maximize),('×',self.destroy)]:
            ctk.CTkButton(controls,text=text,width=28,height=28,fg_color='transparent',hover_color='#23404a',font=(FONT,18),command=command).pack(side='left',padx=1)
        self._highlight_nav()

    def _resize_content(self,event) -> None:
        if event.widget is self and hasattr(self,'body'):
            self.body.configure(height=max(1050 if self.active_page=='Dashboard' else 748,event.height-262))

    def toggle_maximize(self) -> None:
        try:
            if self.state()=='zoomed': self.state('normal')
            else: self.state('zoomed')
        except tk.TclError:
            self.attributes('-zoomed',not bool(self.attributes('-zoomed')))

    def _hero(self) -> None:
        self.hero = tk.Canvas(self,height=155,bg=BG,highlightthickness=0)
        self.hero.grid(row=1,column=0,sticky='ew',padx=24)
        self.hero.bind('<Configure>',self._schedule_hero)

    def _schedule_hero(self,event=None) -> None:
        if self._hero_job is not None: self.after_cancel(self._hero_job)
        self._hero_job = self.after(45,self._draw_hero)

    def _draw_hero(self) -> None:
        self._hero_job = None
        w=max(1,self.hero.winfo_width());h=155
        self.hero.delete('all')
        if self._hero_source:
            art = self._hero_source.resize((w,h),Image.Resampling.LANCZOS).convert('RGBA')
            overlay = Image.new('RGBA',(w,h))
            draw = ImageDraw.Draw(overlay)
            # Dark edges integrate the supplied mountain crop with the hero text.
            for x in range(w):
                left=max(0,1-x/(w*.44));right=max(0,(x/w-.65)/.35)
                draw.line((x,0,x,h),fill=(5,19,27,int(235*max(left,right))))
            art = Image.alpha_composite(art,overlay)
            self._hero_photo=ImageTk.PhotoImage(art)
            self.hero.create_image(0,0,image=self._hero_photo,anchor='nw')
        self.hero.create_text(12,30,text='A  H E A L T H I E R  T O M O R R O W',anchor='w',fill=TEAL,font=(FONT,10,'bold'))
        self.hero.create_text(12,65,text='Small Inputs.',anchor='w',fill=TEXT,font=(FONT,32,'bold'))
        self.hero.create_text(12,106,text='Bigger Insights.',anchor='w',fill=TEAL,font=(FONT,34,'bold'))
        self.hero.create_text(w-28,58,text='“  More than a number —\na clearer view of your health.  ”',anchor='e',justify='left',fill=TEXT,font=(FONT,16,'italic'))
        self.hero.create_line(w-70,108,w-28,108,fill=TEAL,width=2)
        if not self._hero_source:
            self.hero.create_text(w/2,140,text='Reference mountain asset unavailable',fill=MUTED,font=(FONT,10))

    def _measurements(self) -> None:
        left = card(self.calculator);left.grid(row=0,column=0,sticky='nsew',padx=(0,14))
        left.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(left,text='',image=icon('profile',34)).grid(row=0,column=0,sticky='w',padx=22,pady=(18,0))
        label(left,'Profile & Measurements',20,bold=True).grid(row=0,column=0,sticky='w',padx=(70,10),pady=(18,0))
        label(left,'Enter your details to calculate your Body Mass Index (BMI).',12,MUTED,wraplength=350,justify='left').grid(row=1,column=0,sticky='w',padx=(25,18),pady=(4,26))
        ctk.CTkLabel(left,text='  Select Profile',image=icon('profile',20,MUTED),compound='left',text_color=TEXT,font=(FONT,14)).grid(row=2,column=0,sticky='w',padx=24)
        choices = ctk.CTkFrame(left,fg_color='transparent');choices.grid(row=3,column=0,sticky='ew',padx=24,pady=(8,10));choices.grid_columnconfigure(0,weight=1)
        self.profile_menu = ctk.CTkOptionMenu(choices,values=['No profiles yet'],command=self.choose_profile,
            fg_color=INNER,button_color=INNER,button_hover_color='#183340',dropdown_fg_color=INNER,
            dropdown_hover_color='#183340',text_color=TEXT,font=(FONT,14),height=48,dynamic_resizing=False)
        self.profile_menu.grid(row=0,column=0,sticky='ew',padx=(0,10))
        button(choices,'+  New Profile',self.new_profile,width=124).grid(row=0,column=1)
        ctk.CTkFrame(left,height=1,fg_color=BORDER).grid(row=4,column=0,sticky='ew',padx=24,pady=(14,20))
        note=ctk.CTkFrame(left,fg_color=INNER,corner_radius=10)
        note.grid(row=5,column=0,sticky='ew',padx=24,pady=(0,20))
        label(note,'ADULT BMI REFERENCE',11,TEAL,bold=True).pack(anchor='w',padx=15,pady=(12,2))
        label(note,'Age and gender are not collected.\nBMI is a reference, not a diagnosis.',13,MUTED,justify='left').pack(anchor='w',padx=15,pady=(0,12))
        self.height_entry=self._input_row(left,6,'Height',self.height,'cm')
        self.weight_entry=self._input_row(left,7,'Weight',self.weight,'kg')
        left.grid_rowconfigure(8,weight=1)
        self.feedback=label(left,'',13,MUTED,wraplength=370,justify='left',textvariable=self.status)
        self.feedback.grid(row=8,column=0,sticky='sw',padx=25,pady=(8,12))
        self.calculate_button=button(left,'Calculate BMI                     →',self.calculate,True,image=icon('calculator',22,'#ffffff'),compound='left')
        self.calculate_button.configure(height=55,font=(FONT,17,'bold'))
        self.calculate_button.grid(row=9,column=0,sticky='ew',padx=24,pady=(5,10))
        ctk.CTkButton(left,text='Reset',image=icon('reset',21,MUTED),compound='left',command=self.reset,fg_color='transparent',hover_color=INNER,
            text_color=MUTED,font=(FONT,14),height=36).grid(row=10,column=0,pady=(0,22))

    def _input_row(self,parent: ctk.CTkFrame,row: int,title: str,variable: tk.StringVar,unit: str) -> ctk.CTkEntry:
        line=ctk.CTkFrame(parent,fg_color='transparent');line.grid(row=row,column=0,sticky='ew',padx=24,pady=(0,20))
        line.grid_columnconfigure(1,weight=1)
        label(line,title,15).grid(row=0,column=0,sticky='w',padx=(0,25))
        entry=ctk.CTkEntry(line,textvariable=variable,height=54,font=(FONT,20,'bold'),fg_color=INNER,border_color=BORDER,corner_radius=9)
        entry.grid(row=0,column=1,sticky='ew');label(line,unit,13,MUTED).grid(row=0,column=2,padx=(10,0))
        return entry

    def _results(self) -> None:
        right=ctk.CTkFrame(self.calculator,fg_color='transparent');right.grid(row=0,column=1,sticky='nsew')
        right.grid_columnconfigure(0,weight=1)
        for row,weight in [(0,56),(1,16),(2,28)]:right.grid_rowconfigure(row,weight=weight,uniform='right')
        result=card(right);result.grid(row=0,column=0,sticky='nsew',pady=(0,12))
        result.grid_columnconfigure(0,weight=50,uniform='result');result.grid_columnconfigure(1,weight=50,uniform='result')
        result.grid_rowconfigure(1,weight=1)
        ctk.CTkLabel(result,text='  Your BMI Result',image=icon('bars',23),compound='left',font=(FONT,21,'bold'),text_color=TEXT).grid(row=0,column=0,sticky='nw',padx=20,pady=(14,0))
        self.calculated_label=label(result,'Not calculated yet',11,MUTED)
        self.calculated_label.grid(row=0,column=1,sticky='e',padx=20,pady=(18,0))
        self.gauge=BMIGauge(result);self.gauge.grid(row=1,column=0,sticky='nsew',padx=15,pady=(6,0))
        meaning=card(result);meaning.configure(fg_color=INNER)
        meaning.grid(row=1,column=1,sticky='nsew',padx=(7,20),pady=(16,10));meaning.grid_columnconfigure(0,weight=1)
        ctk.CTkLabel(meaning,text='   What this means',image=icon('info',24),compound='left',font=(FONT,15,'bold'),text_color=TEXT).grid(row=0,column=0,sticky='w',padx=18,pady=(18,8))
        self.interpretation=label(meaning,'',14,MUTED,wraplength=305,justify='left',anchor='nw')
        self.interpretation.grid(row=1,column=0,sticky='nsew',padx=18,pady=(0,15))
        meaning.bind('<Configure>',lambda event:self.interpretation.configure(wraplength=max(150,event.width-36)))
        scale=ctk.CTkFrame(result,fg_color='transparent');scale.grid(row=2,column=0,sticky='ew',padx=(20,6),pady=(6,15))
        for i,(name,rng,colour) in enumerate([('Underweight','< 18.5','#369ee5'),('Normal','18.5 – <25','#02c6aa'),('Overweight','25 – <30','#ffbc4b'),('Obese','≥ 30','#fb637b')]):
            scale.grid_columnconfigure(i,weight=1,uniform='scale')
            ctk.CTkFrame(scale,height=8,corner_radius=2,fg_color=colour).grid(row=0,column=i,sticky='ew',padx=2)
            label(scale,name,10).grid(row=1,column=i,pady=(3,0));label(scale,rng,10,MUTED).grid(row=2,column=i)
        self.save_button=button(result,'Save Result to Profile',self.save_result,True,image=icon('reports',20,'#ffffff'),compound='left')
        self.save_button.grid(row=2,column=1,sticky='ew',padx=(25,20),pady=(8,17))
        summaries=ctk.CTkFrame(right,fg_color='transparent');summaries.grid(row=1,column=0,sticky='nsew',pady=(0,12))
        self.summary_values=[];self.summary_details=[]
        for i,(icon_name,title) in enumerate([('weight','Latest Weight'),('trophy','Total Records'),('trends','Measurement Change')]):
            summaries.grid_columnconfigure(i,weight=1,uniform='summaries')
            item=card(summaries);item.configure(height=110);item.grid(row=0,column=i,sticky='nsew',padx=(0 if i==0 else 5,0 if i==2 else 5))
            ctk.CTkLabel(item,text='',image=icon(icon_name,27)).place(x=15,y=13)
            label(item,title,12).place(x=54,y=14)
            value=label(item,'—',25,bold=True);value.place(x=54,y=36)
            detail=label(item,'No saved measurements',10,MUTED);detail.place(x=54,y=72)
            self.summary_values.append(value);self.summary_details.append(detail)
        summaries.grid_rowconfigure(0,weight=1)
        trend=card(right);trend.grid(row=2,column=0,sticky='nsew');trend.grid_columnconfigure(0,weight=1);trend.grid_rowconfigure(2,weight=1)
        ctk.CTkLabel(trend,text='  Weight Trend Preview',image=icon('trends',23),compound='left',font=(FONT,16,'bold'),text_color=TEXT).grid(row=0,column=0,sticky='w',padx=20,pady=(13,0))
        self.trend_note=label(trend,'Saved measurements · UTC dates',11,MUTED)
        self.trend_note.grid(row=1,column=0,sticky='w',padx=42)
        controls=ctk.CTkFrame(trend,fg_color='transparent')
        controls.grid(row=0,column=1,rowspan=2,padx=14,pady=(10,0))
        self.preview_selector=ctk.CTkOptionMenu(controls,values=list(PERIODS),command=self.change_preview_period,
            fg_color=INNER,button_color=TEAL_DARK,font=(FONT,11),width=150,height=32)
        self.preview_selector.set(self.preview_period);self.preview_selector.pack(side='left',padx=(0,8))
        button(controls,'Trends →',lambda:self.navigate('Trends'),width=90).pack(side='left')
        self.preview_chart=ChartWidget(trend,'weight',compact=True,height=125)
        self.preview_chart.grid(row=2,column=0,columnspan=2,sticky='nsew',padx=16,pady=(2,10))

    def change_preview_period(self,period: str) -> None:
        self.preview_period=period;self.refresh_summary()

    def select_trends_profile(self,profile_id: int | None) -> None:
        try:
            self.controller.select(profile_id);self.reload_profiles();self.reset();self.refresh_summary()
        except (ValidationError,DatabaseError) as error:self.show_error(error)

    def _input_changed(self,*args) -> None:
        if self._building:return
        self.controller.invalidate()
        self._render_result()
        self.status.set('Inputs changed. Calculate BMI to see your result.')
        self.feedback.configure(text_color=MUTED)

    def _render_result(self) -> None:
        result=self.controller.result
        self.gauge.set_result(result)
        if result:
            metadata=CATEGORY_METADATA[result.category]
            self.interpretation.configure(text=f'Your BMI is {result.formatted_bmi}, in the {result.category.value} adult reference category.\n\n{metadata.explanation}\n\nBMI does not measure body fat directly and is not a diagnosis.',text_color=MUTED)
            self.calculated_label.configure(text='Calculated '+display_time(self.controller.calculated_at.isoformat()))
        else:
            self.interpretation.configure(text='Enter your height and weight, then calculate your BMI.\n\nYour result will use the four adult BMI reference categories.\n\nNo measurement is saved until you choose Save Result to Profile.')
            self.calculated_label.configure(text='Not calculated yet')
        self.save_button.configure(state='normal' if result and self.controller.profile_id is not None and self.controller.saved is None else 'disabled',
            text='✓   Result Saved' if self.controller.saved else 'Save Result to Profile')

    def calculate(self) -> None:
        try:
            self.controller.calculate(self.weight.get(),self.height.get())
            self.status.set('BMI calculated. Save it to your selected profile.' if self.controller.profile_id else 'BMI calculated. Create or select a profile to save measurements.')
            self.feedback.configure(text_color=TEAL)
        except (ValidationError,DatabaseError) as error:
            self.status.set(str(error));self.feedback.configure(text_color=CORAL)
        self._render_result()

    def save_result(self) -> None:
        try:
            self.controller.save();self.refresh_summary()
            self.status.set('Measurement saved to your profile.');self.feedback.configure(text_color=TEAL)
        except (ValidationError,DatabaseError) as error:
            self.status.set(str(error));self.feedback.configure(text_color=CORAL)
        self._render_result()

    def reset(self) -> None:
        self.weight.set('');self.height.set('');self.controller.invalidate()
        self._render_result();self.status.set('Enter your height and weight to begin.');self.feedback.configure(text_color=MUTED)
        self.height_entry.focus_set()

    def reload_profiles(self) -> None:
        try:
            profiles=self.controller.profiles.list()
            self.profile_map={f'{p.name if len(p.name)<=23 else p.name[:22]+"…"}  · #{p.id}':p.id for p in profiles}
            if self.controller.profile_id not in self.profile_map.values():
                self.controller.select(profiles[0].id if profiles else None)
            self.profile_menu.configure(values=list(self.profile_map) or ['No profiles yet'])
            selected=next((name for name,pid in self.profile_map.items() if pid==self.controller.profile_id),'No profiles yet')
            self.profile_menu.set(selected)
        except (ValidationError,DatabaseError) as error:self.show_error(error)

    def choose_profile(self,name: str) -> None:
        try:
            self.controller.select(self.profile_map.get(name))
            self.reset();self.refresh_summary()
        except (ValidationError,DatabaseError) as error:self.show_error(error)

    def refresh_summary(self) -> None:
        try:
            all_data=self.controller.analytics.snapshot(self.controller.profile_id)
            stats=all_data.statistics
            from .controller import Summary
            summary=Summary(stats.latest,stats.count,stats.weight_change_from_first,all_data.records[0].weight_kg if all_data.records else None)
            self.summary_values[0].configure(text=f'{summary.latest.weight_kg:g} kg' if summary.latest else '—')
            self.summary_details[0].configure(text=display_time(summary.latest.measured_at) if summary.latest else 'No saved measurements')
            self.summary_values[1].configure(text=str(summary.count))
            self.summary_details[1].configure(text='Total measurements')
            self.summary_values[2].configure(text=f'{summary.weight_change:+.1f} kg' if summary.weight_change is not None else '—',text_color=TEAL)
            self.summary_details[2].configure(text=f'From first: {summary.first_weight:g} kg' if summary.weight_change is not None else 'Save two measurements')
            preview=prepare_history(all_data.records,self.controller.profile_id,self.preview_period,all_data.end)
            self.preview_chart.update_data(preview)
            latest=preview.statistics.latest
            self.trend_note.configure(text=f'{len(preview.records)} records · Latest {latest.weight_kg:g} kg · UTC' if latest else 'No measurements in this period · UTC')
            if self.trends_page is not None:self.trends_page.refresh(all_data)
            if self.dashboard_page is not None:self.dashboard_page.refresh(all_data)
            if self.reports_page is not None:self.reports_page.refresh(all_data)
        except (ValidationError,DatabaseError) as error:
            for value,detail in zip(self.summary_values,self.summary_details):
                value.configure(text='—');detail.configure(text='History unavailable')
            self.preview_chart.clear(prepare_history([],self.controller.profile_id))
            self.trend_note.configure(text='History could not be loaded.')
            if self.trends_page is not None:self.trends_page.refresh(prepare_history([],self.controller.profile_id))
            if self.dashboard_page is not None:self.dashboard_page.clear_unavailable()
            if self.reports_page is not None:self.reports_page.refresh()
            self.show_error(error)

    def new_profile(self) -> None:
        dialog=ctk.CTkInputDialog(text='Profile name (up to 100 characters):',title='New Profile',fg_color=BG,button_fg_color=TEAL_DARK)
        name=dialog.get_input()
        if name is None:return
        try:
            self.controller.create_profile(name);self.reload_profiles();self.reset();self.refresh_summary()
            if self.active_page=='Profiles':self.navigate('Profiles')
        except (ValidationError,DatabaseError) as error:self.show_error(error)

    def rename_profile(self,profile_id: int) -> None:
        dialog=ctk.CTkInputDialog(text='New profile name:',title='Rename Profile',fg_color=BG,button_fg_color=TEAL_DARK)
        name=dialog.get_input()
        if name is None:return
        try:
            self.controller.profiles.rename(profile_id,name)
            self.reload_profiles();self.refresh_summary();self.navigate('Profiles')
        except (ValidationError,DatabaseError) as error:self.show_error(error)

    def delete_profile(self,profile_id: int) -> None:
        try:
            preview=self.controller.profiles.deletion_preview(profile_id)
            if not messagebox.askyesno('Delete Profile',f'Delete profile #{preview.profile.id} and all {preview.measurement_count} measurement(s)?\n\nThis cannot be undone.',parent=self):return
            self.controller.profiles.delete(profile_id,confirmed=True)
            self.reload_profiles();self.reset();self.refresh_summary();self.navigate('Profiles')
        except (ValidationError,DatabaseError) as error:self.show_error(error)

    def _highlight_nav(self) -> None:
        for name,b in self.nav_buttons.items():
            b.configure(text_color=TEAL if name==self.active_page else MUTED,
                        fg_color='transparent',image=icon('profile' if name=='Profiles' else name.lower(),17,TEAL if name==self.active_page else MUTED))
            self.nav_lines[name].configure(fg_color=TEAL if name==self.active_page else BG)

    def navigate(self,page: str) -> None:
        self.active_page=page;self._highlight_nav()
        self.body.configure(height=max(1050 if page=='Dashboard' else 748,self.winfo_height()-262))
        for view in (self.dashboard_page,self.reports_page):
            if view is not None:view.grid_remove()
        if page in ('Dashboard','Reports'):
            self.calculator.grid_remove();self.other_page.grid_remove()
            if self.trends_page is not None:self.trends_page.grid_remove()
            if page=='Dashboard':
                if self.dashboard_page is None:self.dashboard_page=DashboardView(self.body,self.controller,self.select_trends_profile,self.show_error,lambda:self.navigate('Calculator'))
                view=self.dashboard_page
            else:
                if self.reports_page is None:self.reports_page=ReportsView(self.body,self.controller,self.select_trends_profile,self.show_error)
                view=self.reports_page
            view.grid(row=0,column=0,sticky='nsew');view.refresh()
            self.viewport._parent_canvas.yview_moveto(0)
            return
        if self.trends_page is not None:self.trends_page.grid_remove()
        if page=='Trends':
            self.calculator.grid_remove();self.other_page.grid_remove()
            if self.trends_page is None:
                self.trends_page=TrendsView(self.body,self.controller,self.select_trends_profile,self.show_error)
            self.trends_page.grid(row=0,column=0,sticky='nsew')
            self.trends_page.refresh()
            self.viewport._parent_canvas.yview_moveto(0)
            return
        if page=='Calculator':
            self.other_page.grid_remove();self.calculator.grid();return
        self.calculator.grid_remove()
        for child in self.other_page.winfo_children():child.destroy()
        self.other_page.grid(row=0,column=0,sticky='nsew');self.other_page.grid_columnconfigure(0,weight=1);self.other_page.grid_rowconfigure(1,weight=1)
        header=card(self.other_page);header.grid(row=0,column=0,sticky='ew',pady=(0,12))
        label(header,page,24,bold=True).pack(side='left',padx=22,pady=18)
        if page=='Profiles':button(header,'+  New Profile',self.new_profile).pack(side='right',padx=20)
        if page=='History':
            choice=ctk.CTkOptionMenu(header,values=list(self.profile_map) or ['No profiles yet'],fg_color=INNER,button_color=TEAL_DARK,
                command=self._history_profile,width=230)
            choice.pack(side='right',padx=20)
            choice.set(next((name for name,pid in self.profile_map.items() if pid==self.controller.profile_id),'No profiles yet'))
        area=ctk.CTkScrollableFrame(self.other_page,fg_color=CARD,corner_radius=13,border_color=BORDER,border_width=1)
        area.grid(row=1,column=0,sticky='nsew');area.grid_columnconfigure(0,weight=1)
        try:
            if page=='Profiles':self._profiles_page(area)
            elif page=='History':self._history_page(area)
            else:
                label(area,f'{page} is planned for a later task.',24,bold=True).pack(pady=(65,15))
                label(area,'Your profiles and measurements are available in Calculator and History.\nDashboard and reporting remain planned features.',16,MUTED,justify='center').pack(pady=10)
                button(area,'Back to Calculator',lambda:self.navigate('Calculator')).pack(pady=25)
        except (ValidationError,DatabaseError) as error:self.show_error(error)

    def _profiles_page(self,area) -> None:
        profiles=self.controller.profiles.list()
        if not profiles:label(area,'No profiles yet. Create your first local profile to save measurements.',17,MUTED).pack(pady=60)
        for profile in profiles:
            row=card(area);row.pack(fill='x',padx=15,pady=8)
            label(row,f'{profile.name}  · #{profile.id}',16,bold=True,wraplength=500,justify='left').pack(side='left',padx=18,pady=18)
            button(row,'Delete',lambda pid=profile.id:self.delete_profile(pid),width=85).pack(side='right',padx=(5,15))
            button(row,'Rename',lambda pid=profile.id:self.rename_profile(pid),width=85).pack(side='right',padx=5)
            button(row,'Select',lambda pid=profile.id:self._select_from_page(pid),True,width=85).pack(side='right',padx=5)

    def _select_from_page(self,profile_id: int) -> None:
        try:
            self.controller.select(profile_id);self.reload_profiles();self.reset();self.refresh_summary();self.navigate('Calculator')
        except (ValidationError,DatabaseError) as error:self.show_error(error)

    def _history_profile(self,name: str) -> None:
        self.choose_profile(name);self.navigate('History')

    def _history_page(self,area) -> None:
        pid=self.controller.profile_id
        records=[] if pid is None else self.controller.history.history(pid)
        if not records:
            label(area,'No saved measurements for this profile.',18,MUTED).pack(pady=(60,12))
            button(area,'Calculate a measurement',lambda:self.navigate('Calculator')).pack(pady=12)
            return
        headings=ctk.CTkFrame(area,fg_color='transparent')
        headings.pack(fill='x',padx=15,pady=10)
        widths=(230,110,110,100,180,95)
        for i,(title,width) in enumerate(zip(('Measurement time (local)','Weight','Height','BMI','Category',''),widths)):
            headings.grid_columnconfigure(i,weight=1 if i==4 else 0,minsize=width)
            label(headings,title,13,MUTED,anchor='w').grid(row=0,column=i,sticky='w',padx=12)
        for record in reversed(records):
            row=card(area);row.pack(fill='x',padx=15,pady=5)
            values=(display_time(record.measured_at),f'{record.weight_kg:g} kg',f'{record.height_m*100:g} cm',record.formatted_bmi,record.category.value)
            for i,width in enumerate(widths):row.grid_columnconfigure(i,weight=1 if i==4 else 0,minsize=width)
            for i,value in enumerate(values):
                colour=CATEGORY_METADATA[record.category].colour if i==4 else TEXT
                label(row,value,14,colour,anchor='w').grid(row=0,column=i,sticky='w',padx=12,pady=15)
            button(row,'Delete',lambda rid=record.id:self.delete_measurement(rid),width=75).grid(row=0,column=5,padx=10,pady=8)

    def delete_measurement(self,record_id: int) -> None:
        try:
            if not messagebox.askyesno('Delete Measurement','Permanently delete this measurement?',parent=self):return
            self.controller.history.delete(self.controller.profile_id,record_id)
            if self.controller.saved is not None and self.controller.saved.id==record_id:
                self.controller.invalidate();self._render_result()
                self.status.set('Measurement deleted. Calculate a new result to save.')
            self.refresh_summary();self.navigate('History')
        except (ValidationError,DatabaseError) as error:self.show_error(error)

    def show_error(self,error: Exception) -> None:
        messagebox.showerror('BMI Insight',str(error),parent=self)

    def destroy(self) -> None:
        if self.reports_page is not None and self.reports_page.busy:
            messagebox.showinfo('Report in progress','Please wait for the PDF export to finish before closing BMI Insight.',parent=self)
            return
        if self._hero_job is not None:
            self.after_cancel(self._hero_job);self._hero_job=None
        if self._hero_source is not None:self._hero_source.close()
        super().destroy()
