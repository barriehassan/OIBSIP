"""Small local vector-style icons; no external fonts or downloads required."""
from PIL import Image, ImageDraw
import customtkinter as ctk


def icon(name: str, size: int = 22, colour: str = '#03d4ce') -> ctk.CTkImage:
    scale=4
    image=Image.new('RGBA',(size*scale,size*scale))
    d=ImageDraw.Draw(image)
    def line(points):d.line([(int(x*size*scale/24),int(y*size*scale/24)) for x,y in points],fill=colour,width=2*scale,joint='curve')
    def box(bounds):d.rounded_rectangle([int(n*size*scale/24) for n in bounds],radius=scale,outline=colour,width=2*scale)
    def ellipse(bounds):d.ellipse([int(n*size*scale/24) for n in bounds],outline=colour,width=2*scale)
    if name=='profile':
        ellipse((8,2,16,10));d.arc([int(n*size*scale/24) for n in (3,12,21,29)],180,360,fill=colour,width=2*scale);line([(3,21),(21,21)])
    elif name=='calculator':
        box((5,2,19,22));box((8,5,16,9))
        for x in (8,12,16):
            for y in (13,17):line([(x,y),(x,y+1)])
    elif name=='history':
        d.arc([int(n*size*scale/24) for n in (3,3,22,22)],210,530,fill=colour,width=2*scale)
        line([(2,4),(2,10),(8,10)]);line([(12,6),(12,12),(16,15)])
    elif name=='trends':line([(2,18),(8,10),(13,14),(21,5)]);line([(15,5),(21,5),(21,11)])
    elif name=='dashboard':
        for x,y in ((3,3),(14,3),(3,14),(14,14)):box((x,y,x+7,y+7))
    elif name=='reports':box((5,2,19,22));line([(9,8),(15,8)]);line([(9,12),(15,12)]);line([(9,16),(15,16)])
    elif name=='weight':box((4,8,20,22));ellipse((9,2,15,8))
    elif name=='trophy':
        line([(6,3),(18,3),(17,12),(12,16),(7,12),(6,3)]);line([(12,16),(12,21)]);line([(7,22),(17,22)])
        line([(6,5),(2,5),(3,11),(7,12)]);line([(18,5),(22,5),(21,11),(17,12)])
    elif name=='info':ellipse((2,2,22,22));line([(12,10),(12,18)]);line([(12,6),(12,7)])
    elif name=='bars':
        for x,h in ((3,8),(10,13),(17,20)):box((x,23-h,x+4,22))
    elif name=='reset':
        d.arc([int(n*size*scale/24) for n in (3,3,21,21)],200,510,fill=colour,width=2*scale);line([(2,3),(2,10),(9,10)])
    else:box((4,3,20,21))
    return ctk.CTkImage(light_image=image,dark_image=image,size=(size,size))
