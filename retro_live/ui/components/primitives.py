from functools import lru_cache
import pygame
from ...i18n import translate


class PrimitivesMixin:
    def tr(self, key):
        return translate(self.preferences.language, key)


    @lru_cache(maxsize=512)
    def render_text(self, font, text, color):
        return font.render(text, True, color)


    def txt(self, text, x,y, color=None, font=None, maxwidth=None):
        text = str(text)[:2048]
        font=font or self.font
        color=self.palette.text if color is None else color
        if maxwidth is not None and font.size(text)[0]>maxwidth:
            if maxwidth<font.size('…')[0]: return
            lo, hi = 0, len(text)
            while lo < hi:
                mid = (lo+hi+1)//2
                if font.size(text[:mid]+'…')[0] <= maxwidth: lo=mid
                else: hi=mid-1
            text=text[:lo]+'…'
        self.screen.blit(self.render_text(font,text,color),(x,y))


    def rect(self, box, fill=None, border=None, radius=3):
        fill=self.palette.panel if fill is None else fill
        border=self.palette.edge if border is None else border
        pygame.draw.rect(self.screen,fill,box,border_radius=radius)
        pygame.draw.rect(self.screen,border,box,1,border_radius=radius)


    def button(self, name, label, rect, active=False):
        self.buttons[name]=pygame.Rect(rect)
        mouse=pygame.mouse.get_pos()
        hover=self.buttons[name].collidepoint(mouse)
        fill=self.palette.accent if active else (self.palette.edge if hover else self.palette.panel)
        self.rect(rect,fill,self.palette.accent if hover or active else self.palette.edge)
        font=self.small
        # Fit labels inside their hit targets without silently clipping text.
        available=max(8,self.buttons[name].width-16)
        text_font=font
        if font.size(label)[0]>available:
            text_font=self.tiny
        if text_font.size(label)[0]>available:
            while label and text_font.size(label+'…')[0]>available:
                label=label[:-1]
            label+='…'
        text=self.render_text(text_font,label,self.palette.black if active else self.palette.text)
        self.screen.blit(text,text.get_rect(center=self.buttons[name].center))


    @lru_cache(maxsize=4096)
    def wrap(self, text, max_width, font):
        result=[]; line=''
        for word in text.split():
            trial=(line+' '+word).strip()
            if font.size(trial)[0]>max_width and line:
                result.append(line); line=word
            else: line=trial
        if line: result.append(line)
        return result or ['']


