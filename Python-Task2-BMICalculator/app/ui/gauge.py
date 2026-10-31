"""Responsive canvas gauge: display mapping does not alter BMI classification."""
import math
import tkinter as tk
from tkinter import font as tkfont
from app.core.models import BMIResult
from app.core.classification import CATEGORY_METADATA
from .theme import CARD, TEXT, MUTED, TEAL, FONT

# Segments match the reference ring; display saturates outside BMI 12–40.
SEGMENTS = ((12,18.5,"#369ee5"),(18.5,25,"#02bcae"),(25,30,"#ffbc4b"),(30,40,"#fb637b"))

def gauge_fraction(bmi: float) -> float:
    return max(0.0, min(1.0, (bmi-12)/28))

class BMIGauge(tk.Canvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, bg=CARD, highlightthickness=0, **kwargs)
        self.result: BMIResult | None = None
        self.bind('<Configure>', lambda _: self.draw())

    def set_result(self, result: BMIResult | None) -> None:
        self.result = result
        self.draw()

    def draw(self) -> None:
        self.delete('all')
        w,h = self.winfo_width(),self.winfo_height()
        if min(w,h)<10: return
        size = min(w-30,h-8)
        cx,cy = w/2,h/2+8
        radius = size/2-12
        box = (cx-radius,cy-radius,cx+radius,cy+radius)
        width = max(10,size*0.044)
        # Clockwise 270-degree sweep from lower left to lower right.
        for low,high,colour in SEGMENTS:
            start = 225 - gauge_fraction(low)*270
            extent = -(gauge_fraction(high)-gauge_fraction(low))*270 + 3
            self.create_arc(*box,start=start,extent=extent,style='arc',outline=colour,width=width)
        self.create_text(cx,cy-size*.16,text='BMI',fill=MUTED,font=(FONT,max(12,int(size*.06)),'bold'))
        value = self.result.formatted_bmi if self.result else '—'
        value_font = tkfont.Font(family=FONT,size=-max(25,int(size*.23)),weight='bold')
        measured = value_font.measure(value)
        if measured > size*.8:
            value_font.configure(size=-max(16,int(size*.23*size*.8/measured)))
        self._value_font = value_font
        self.create_text(cx,cy+size*.02,text=value,fill=TEXT,font=value_font,tags='bmi_value')
        category = self.result.category.value.upper() if self.result else 'AWAITING INPUT'
        colour = CATEGORY_METADATA[self.result.category].colour if self.result else TEAL
        if self.result:
            self.create_line(cx-48,cy+size*.23,cx+48,cy+size*.23,fill=colour,width=32,capstyle='round')
        self.create_text(cx,cy+size*.23,text=category,fill='#05131b' if self.result else colour,
                         font=(FONT,-max(12,int(size*.05)),'bold'))
        if self.result:
            angle = math.radians(225-gauge_fraction(self.result.bmi_value)*270)
            x,y = cx+radius*math.cos(angle),cy-radius*math.sin(angle)
            self.create_oval(x-8,y-8,x+8,y+8,fill=colour,outline='white',width=2)
