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


