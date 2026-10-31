"""Mountain-glass desktop UI. Standard Tk widgets support both Tk 8.6 and Tk 9."""
from __future__ import annotations
import tkinter as tk
from tkinter import messagebox, font
from PIL import ImageTk
from app.core.password_generator import PasswordOptions, CHARACTER_SETS
from app.core.validator import DEFAULT_LENGTH, MIN_LENGTH, MAX_LENGTH, PasswordValidationError
from app.services.clipboard import copy_to_clipboard
from app.ui.controller import PasswordController
from app.ui.password_lab import PasswordLabView
from app.ui.glass import render_glass, WIDTH, HEIGHT

WHITE = '#F4F7FF'
MUTED = '#C0D1F1'
GREEN = '#3CE9B0'


class PasswordForgeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('NOMOLI FORGE | Password Forge')
        # Leave room for the Windows title bar and taskbar on laptop displays.
        width = min(1280, max(1000, self.winfo_screenwidth() - 80))
        height = min(800, max(680, self.winfo_screenheight() - 100))
        self.geometry(f'{width}x{height}')
        self.minsize(1000, 680)
        self.configure(bg='#13264F')
        families = {name.lower() for name in font.families(self)}
        self.ui_font = 'Segoe UI' if 'segoe ui' in families else 'Helvetica'
        self.mono_font = 'Consolas' if 'consolas' in families else 'Courier'
        self.controller = PasswordController()
        self.length_var = tk.IntVar(value=DEFAULT_LENGTH)
        self.numeric_length_var = tk.StringVar(value=str(DEFAULT_LENGTH))
        self.password_var = tk.StringVar()
        for name in ('uppercase', 'lowercase', 'digits', 'symbols', 'exclude'):
            setattr(self, name + '_var', tk.BooleanVar(value=True))
        self.auto_copy_var = tk.BooleanVar(value=False)
        self.show_password_var = tk.BooleanVar(value=False)
        self.show_history_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value='Choose your settings, then forge your first password.')
        self.strength = None
        self.last_options = None
        self.nav = 'Generate'
        self._size = (0, 0)
        self._pending = None
        self._focus = -1
        self.actions = []
        self.canvas = tk.Canvas(self, bg='#13264F', highlightthickness=0, takefocus=True)
        self.canvas.pack(fill='both', expand=True)
        self.password_entry = tk.Entry(self.canvas, textvariable=self.password_var,
            readonlybackground='#DDE8FF', fg='#102454', relief='flat', bd=0,
            insertbackground='#102454', state='readonly', show='*', exportselection=False)
        self.length_entry = tk.Entry(self.canvas, textvariable=self.numeric_length_var,
            bg='#284479', fg=WHITE, insertbackground=WHITE, justify='center', relief='flat', bd=0)
        self.lab = PasswordLabView(self)
        self.length_entry.bind('<Return>', self._on_length_entry)
        self.length_entry.bind('<FocusOut>', self._on_length_entry)
        self.canvas.bind('<Configure>', self._resize)
        self.canvas.bind('<Button-1>', self._click)
        self.canvas.bind('<B1-Motion>', self._drag)
        self.canvas.bind('<Motion>', self._hover)
        self.canvas.bind('<Tab>', self._tab)
        self.canvas.bind('<Shift-Tab>', lambda event: self._tab(event, -1))
        self.canvas.bind('<ISO_Left_Tab>', lambda event: self._tab(event, -1))
        self.canvas.bind('<Return>', self._activate)
        self.canvas.bind('<space>', self._activate)
        self.bind('<Control-g>', lambda event: self.lab.replace() if self.nav == 'Password Lab' else self._generate())
        self.bind('<Escape>', lambda event: self._hide())
        self.protocol('WM_DELETE_WINDOW', self._on_close)

    def _resize(self, event):
        if self._pending:
            self.after_cancel(self._pending)
        self._pending = self.after(100, lambda: self._draw(event.width, event.height))

    def _text(self, x, y, value, size=14, color=WHITE, bold=False, anchor='nw', width=0):
        # Negative pixel sizes avoid Tk 9's point-size parsing differences.
        return self.canvas.create_text(x*self.sx, y*self.sy, text=value,
            fill=color, font=(self.ui_font, -max(10, round(size*self.scale)), 'bold' if bold else 'normal'),
            anchor=anchor, width=width*self.sx if width else 0)

    def _rect(self, box, fill, outline='', radius=12):
        x1,y1,x2,y2=box
        points=[x1+radius,y1,x2-radius,y1,x2,y1,x2,y1+radius,x2,y2-radius,
                x2,y2,x2-radius,y2,x1+radius,y2,x1,y2,x1,y2-radius,x1,y1+radius,x1,y1]
        return self.canvas.create_polygon(*[v*(self.sx if i%2==0 else self.sy) for i,v in enumerate(points)],
            smooth=True, fill=fill, outline=outline, width=1)

    def _button(self, box, text, command, primary=False, subtle=False):
        self._rect(box, '#3760F4' if primary else ('#203D71' if subtle else '#DCE7FF'),
                   '#98B8FF' if primary else '#6383BB')
        x1,y1,x2,y2=box
        self._text((x1+x2)/2,(y1+y2)/2,text,14,WHITE if primary or subtle else '#183268',True,'center')
        self.actions.append((box,command,text))

    def _mountain(self, x, y, size):
        pts=[(0,.85),(.28,.28),(.4,.5),(.58,0),(1,.85),(.71,.66),(.57,.3),(.4,.72),(.29,.55)]
        self.canvas.create_polygon(*[v for px,py in pts for v in ((x+px*size)*self.sx,(y+py*size)*self.sy)], fill='#B8EEFF', outline='#E6F8FF')
        self.canvas.create_polygon((x+.58*size)*self.sx,y*self.sy,(x+.71*size)*self.sx,(y+.66*size)*self.sy,(x+size)*self.sx,(y+.85*size)*self.sy,fill='#8C85FF',outline='')

    def _draw(self, width=None, height=None):
        if self._pending:
            self.after_cancel(self._pending)
        self._pending=None
        width=width or self.canvas.winfo_width()
        height=height or self.canvas.winfo_height()
        if width < 10 or height < 10:
            return
        self.sx,self.sy=width/WIDTH,height/HEIGHT
        self.scale=min(self.sx,self.sy)
        if (width,height)!=self._size:
            self._image=ImageTk.PhotoImage(render_glass(width,height), master=self)
            self._size=(width,height)
        for item in self.canvas.find_all():
            if self.canvas.type(item) != 'window':
                self.canvas.delete(item)
        self.canvas.create_image(0,0,image=self._image,anchor='nw')
        self.actions=[]
        self._mountain(82,48,88)
        self._text(128,150,'NOMOLI FORGE',19,bold=True,anchor='center')
        self._text(128,178,'Password Forge',15,anchor='center')
        self._text(128,217,'Every Password,\nUniquely Forged.',12,MUTED,anchor='center')
        for i,(name,label) in enumerate((('Generate','＋  Generate'),('Password Lab','Password Lab'),('History','◷  History'),('Settings','⚙  Settings'),('About','ⓘ  About'))):
            self._button((34,282+i*64,222,332+i*64),label,lambda n=name:self._navigate(n),primary=self.nav==name,subtle=self.nav!=name)
        if self.nav == 'Password Lab':
            self._text(42,660,'EPHEMERAL INPUT',11,MUTED,True)
            self._text(42,696,'Ctrl+G  Replacement\nEsc  Hide passwords',11,MUTED)
        else:
            self._check((34,655,224,684),self.auto_copy_var,'Auto copy')
            self._text(42,696,'Ctrl+G  Generate\nEsc  Hide passwords',11,MUTED)
        self._text(42,768,'PRIVATE BY DESIGN',11,GREEN,True)
        self._text(42,796,'Offline generation.\nNo accounts. No cloud.',12,MUTED,width=170)
        self._text(270,39,'NOMOLI FORGE',38,bold=True)
        self._text(272,88,'Password Forge',27)
        self._text(274,130,'Every Password, Uniquely Forged.',17,MUTED)
        self._text(1400,58,'●  LOCAL & PRIVATE',12,GREEN,True,'ne')
        self._text(1400,87,'A stronger start to your digital life.',13,WHITE,False,'ne')
        if self.nav == 'Password Lab':
            for entry in (self.password_entry, self.length_entry):
                if hasattr(entry, '_canvas_item'):
                    self.canvas.itemconfigure(entry._canvas_item, state='hidden')
            self.lab.draw()
            return
        self._text(290,222,'Generated password',22,bold=True)
        self._rect((290,268,976,344),'#DDE8FF','#D4E5FF')
        self.password_entry.configure(font=(self.mono_font,-max(16,round(27*self.scale))),show='' if self.show_password_var.get() else '*')
        self._embed(self.password_entry,306,286,440,40)
        self._button((757,280,822,332),'Hide' if self.show_password_var.get() else 'Show',self._toggle_visibility)
        self._button((834,280,895,332),'Copy',self._copy)
        self._button((907,280,964,332),'New',self._generate)
        progress=self.strength.progress if self.strength else 0
        self._rect((294,359,876,368),'#6580B5',radius=4)
        color=GREEN if self.strength and self.strength.label=='Strong' else '#6CCBFF'
        if progress:
            self._rect((294,359,294+582*progress,368),color,radius=4)
        self._text(970,353,self.strength.label if self.strength else 'Ready',14,color,True,'ne')
        self._button((290,388,699,433),'✦  Generate Password',self._generate,primary=True)
        self._button((713,388,976,433),'Copy to Clipboard',self._copy)
        self._draw_strength()
        self._draw_settings()
        self._draw_history()
        self._text(288,851,self.status_var.get(),13,MUTED,width=1100)
        self._draw_focus()

    def _embed(self, entry, x, y, width, height):
        if not hasattr(entry, '_canvas_item'):
            entry._canvas_item=self.canvas.create_window(0,0,window=entry,anchor='nw')
        self.canvas.coords(entry._canvas_item,x*self.sx,y*self.sy)
        self.canvas.itemconfigure(entry._canvas_item,width=width*self.sx,height=height*self.sy,state='normal')
        self.canvas.tag_raise(entry._canvas_item)

    def _draw_strength(self):
        self._text(1042,222,'Password strength',21,bold=True)
        x1,y1,x2,y2=1044,281,1193,430
        self.canvas.create_oval(x1*self.sx,y1*self.sy,x2*self.sx,y2*self.sy,outline='#496797',width=13*self.scale)
        progress=self.strength.progress if self.strength else 0
        if progress:
            self.canvas.create_arc(x1*self.sx,y1*self.sy,x2*self.sx,y2*self.sy,start=90,extent=-359*progress,style='arc',outline=GREEN,width=13*self.scale)
        self._text(1118,349,self.strength.label if self.strength else 'Ready',20,GREEN,True,'center')
        self._text(1118,376,'estimated',11,MUTED,False,'center')
        options=self.last_options
        checks=[('Length '+str(options.length) if options else 'Length —',bool(options))]
        for key,label in [('uppercase','Uppercase'),('lowercase','Lowercase'),('digits','Numbers'),('symbols','Symbols')]:
            checks.append((label,bool(options and getattr(options,key))))
        for i,(label,enabled) in enumerate(checks):
            self._text(1220,278+29*i,('✓  ' if enabled else '–  ')+label,13,GREEN if enabled else MUTED)

    def _draw_settings(self):
        self._text(290,496,'Password settings',21,bold=True)
        self._text(290,539,'Password length',14,bold=True)
        self._text(754,541,'8 to 64 characters',12,MUTED,anchor='ne')
        self._rect((292,590,677,597),'#7290C6',radius=3)
        value=(self.length_var.get()-MIN_LENGTH)/(MAX_LENGTH-MIN_LENGTH)
        pos=292+385*value
        self._rect((292,590,max(295,pos),597),'#48BAFF',radius=3)
        self.canvas.create_oval((pos-9)*self.sx,584*self.sy,(pos+9)*self.sx,603*self.sy,fill='#4986FF',outline='#A6CEFF')
        self.length_entry.configure(font=(self.ui_font,-max(13,round(17*self.scale))))
        self._embed(self.length_entry,698,572,64,40)
        for i,(name,label) in enumerate([('uppercase','Uppercase letters (A–Z)'),('lowercase','Lowercase letters (a–z)'),('digits','Numbers (0–9)'),('symbols','Symbols (! @ # $ %)')]):
            self._check((292,625+i*33,760,653+i*33),getattr(self,name+'_var'),label)
        self._check((292,757,760,785),self.exclude_var,'Exclude lookalikes (0 O o 1 l I)')

    def _check(self, box, variable, label):
        x,y,_,_=box
        on=variable.get()
        self._rect((x,y,x+23,y+23),'#3C76F5' if on else '#203D71','#95B7ED',5)
        if on:self._text(x+11,y+10,'✓',18,WHITE,True,'center')
        self._text(x+35,y+2,label,14)
        self.actions.append((box,lambda:self._toggle(variable),label))

    def _draw_history(self):
        self._text(832,496,'Recent passwords',21,bold=True)
        self._button((1285,490,1396,528),'Clear all',self._clear_history,subtle=True)
        self._text(834,535,'LAST FIVE · MEMORY ONLY',10,MUTED,True)
        self._button((1150,530,1269,556),'Hide history' if self.show_history_var.get() else 'Reveal history',lambda:self._toggle(self.show_history_var),subtle=True)
        if not self.controller.history:
            self._text(1114,642,'Your next creation starts here.',18,anchor='center')
            self._text(1114,675,'Generate a password to begin your private history.',12,MUTED,anchor='center')
        for i,password in enumerate(self.controller.history):
            y=566+i*45
            self._rect((832,y,1396,y+38),'#284577','#6585B7')
            self._text(848,y+11,f'{i+1:02}',11,MUTED)
            text=password if self.show_history_var.get() else '*'*min(24,len(password))
            # Bound the rendered value; copying always uses the complete password.
            if len(text)>36:text=text[:33]+'…'
            self._text(886,y+8,text,15)
            self._button((1334,y+3,1390,y+35),'Copy',lambda p=password:self._copy_history_item(p),subtle=True)

    def _navigate(self, name):
        if self.nav == 'Password Lab' and name != 'Password Lab':
            self.lab.leave()
            if hasattr(self.lab, 'feedback') and hasattr(self.lab.feedback, '_canvas_item'):
                self.canvas.itemconfigure(self.lab.feedback._canvas_item, state='hidden')
        if name=='About':
            messagebox.showinfo('About Password Forge','NOMOLI FORGE · Password Forge\nEvery Password, Uniquely Forged.\n\nSecure local generation using Python secrets.\nHistory stays in memory. Clipboard contents can persist.\nStrength is an estimate, not a breach check.',parent=self)
            self._draw()
            return
        self.nav=name
        self._focus=-1
        self._draw()
        if name == 'Password Lab':
            self.lab.entry.focus_set()
        if name=='Settings':self.length_entry.focus_set()
        elif name=='History':self._status('Recent passwords stay in memory. Use Reveal history to inspect them.')

    def _toggle(self, var):
        var.set(not var.get())
        self._draw()

    def _on_length_entry(self, event=None):
        if self.nav == 'Password Lab':
            return
        try:
            number=int(self.numeric_length_var.get())
            if not MIN_LENGTH<=number<=MAX_LENGTH:raise ValueError
        except ValueError:
            self.numeric_length_var.set(str(self.length_var.get()))
            self._status('Choose a whole number from 8 to 64.')
            return
        self.length_var.set(number)
        self._draw()

    def _read_options(self):
        try:length=int(self.numeric_length_var.get())
        except ValueError as exc:raise PasswordValidationError('Enter a whole-number length.') from exc
        return PasswordOptions(length=length,**{n:getattr(self,n+'_var').get() for n in CHARACTER_SETS},exclude_ambiguous=self.exclude_var.get())

    def _generate(self):
        try:
            options=self._read_options()
            password,strength=self.controller.generate(options)
        except (PasswordValidationError,ValueError) as exc:
            self._status(str(exc))
            return
        self.password_var.set(password)
        self.strength=strength
        self.last_options=options
        self.length_var.set(options.length)
        self.show_password_var.set(False)
        if self.auto_copy_var.get():self._copy()
        else:self._status('Password forged locally. Copy it when you are ready.')

    def _toggle_visibility(self):
        self._toggle(self.show_password_var)

    def _hide(self):
        self.lab.visible = False
        self.lab.entry.configure(show='*')
        self.show_password_var.set(False)
        self.show_history_var.set(False)
        self._draw()

    def _copy(self):
        if not self.controller.current_password:
            self._status('Generate a password before copying.')
            return
        self._copy_history_item(self.controller.current_password)

    def _copy_history_item(self,password):
        self._status(copy_to_clipboard(password,self).message)

    def _status(self,message):
        self.status_var.set(message)
        self._draw()

    def _clear_history(self):
        self.controller.clear_history()
        self._status('History cleared. Your current password remains available above.')

    def _slider(self,x):
        length=round(MIN_LENGTH+(max(292,min(677,x))-292)/385*(MAX_LENGTH-MIN_LENGTH))
        self.length_var.set(length)
        self.numeric_length_var.set(str(length))
        self._draw()

    def _click(self,event):
        x,y=event.x/self.sx,event.y/self.sy
        self.canvas.focus_set()
        self._dragging=self.nav != 'Password Lab' and 282<=x<=688 and 575<=y<=612
        if self._dragging:
            self._slider(x)
            return
        for index,(box,command,_) in enumerate(self.actions):
            x1,y1,x2,y2=box
            if x1<=x<=x2 and y1<=y<=y2:
                self._focus=index
                command()
                return

    def _drag(self,event):
        if getattr(self,'_dragging',False):self._slider(event.x/self.sx)

    def _hover(self,event):
        if not hasattr(self,'sx'):return
        x,y=event.x/self.sx,event.y/self.sy
        self.canvas.configure(cursor='hand2' if any(a<=x<=c and b<=y<=d for (a,b,c,d),_,_ in self.actions) else '')

    def _tab(self,event,direction=1):
        if self.actions:
            next_focus=self._focus+direction
            if next_focus>=len(self.actions):
                self._focus=-1
                (self.lab.entry if self.nav == 'Password Lab' else self.length_entry).focus_set()
            elif next_focus<0:
                self._focus=len(self.actions)-1
                (self.lab.entry if self.nav == 'Password Lab' else self.password_entry).focus_set()
            else:
                self._focus=next_focus
                self._draw_focus()
        return 'break'

    def _draw_focus(self):
        self.canvas.delete('focus')
        if 0<=self._focus<len(self.actions) and self.focus_get() is self.canvas:
            box,_,label=self.actions[self._focus]
            a,b,c,d=box
            self.canvas.create_rectangle((a-3)*self.sx,(b-3)*self.sy,(c+3)*self.sx,(d+3)*self.sy,outline='#B8F4FF',width=2,tags='focus')

    def _activate(self,event):
        if 0<=self._focus<len(self.actions):self.actions[self._focus][1]()
        return 'break'

    def _on_close(self):
        self.lab.leave()
        self.password_var.set('')
        self.controller.close()
        self.actions.clear()  # Release copy callbacks holding temporary history values.
        if self._pending:self.after_cancel(self._pending)
        self.destroy()
