"""Theme-aware, keyboard-only help overlay with bounded pagination."""
import pygame

SHORTCUTS=(
 ('ENTER','watch'), ('U','edit_source'), ('TAB','autocomplete'), ('CTRL+V','paste'), ('←/→','move_cursor'), ('HOME/END','cursor_edges'), ('CTRL+A','select_text'), ('CTRL+U','clear_field'), ('DEL/BACKSPACE','delete_text'),
 ('H','history'), ('O (H)','history_sort_help'), ('/ (H)','history_search_help'), ('SPACE','pause_resume'), ('↑/↓','volume'), ('C','toggle_sub'),
 ('F/F11','fullscreen'), ('X','stop'), ('S','save'), ('L','speech'), ('T','theme'), ('I','ui_lang'),
 ('PgUp/PgDn','navigate'), ('END','return_live'), ('Q','quality'), ('P','priority'), ('V','fps'),
 ('[/]','fps_adjust'), ('A','auto'), ('-/=','buffer_adjust'), ('R','retries'), (',/.','timeout_adjust'),
 ('F3','performance'), ('K','help'), ('ESC','close'),
)

class HelpMixin:
    def draw_help(self):
        w,h=self.screen.get_size()
        width=max(1,min(720,w-24)); height=max(1,min(620,h-24))
        box=pygame.Rect((w-width)//2,(h-height)//2,width,height)
        self.rect(box,self.palette.panel,self.palette.accent)
        self.txt(self.tr('shortcuts'),box.x+12,box.y+12,self.palette.accent,self.font,maxwidth=width-24)
        size=max(1,min(23,(height-94)//22))
        pages=(len(SHORTCUTS)+size-1)//size
        self.help_page=max(0,min(self.help_page,pages-1))
        self.help_pages=pages
        for i,(key,label) in enumerate(SHORTCUTS[self.help_page*size:(self.help_page+1)*size]):
            y=box.y+45+i*22
            self.txt('['+(self.tr('space') if key=='SPACE' else key)+']',box.x+12,y,self.palette.accent,self.small,maxwidth=min(135,width//3))
            self.txt(self.tr(label),box.x+min(155,width//3+16),y,self.palette.text,self.small,maxwidth=width-min(155,width//3+16)-12)
        self.txt(f"[PgUp/PgDn] {self.tr('page')} {self.help_page+1}/{pages}  [K/ESC] {self.tr('close')}",box.x+12,box.bottom-28,self.palette.muted,self.small,maxwidth=width-24)
