import pygame
from ...i18n import translate_status


class PanelsMixin:
    def draw(self):
        if self.video_fullscreen:
            self.draw_fullscreen_video()
            if self.help_open: self.draw_help(); pygame.display.flip()
            return
        w,h=self.screen.get_size()
        self.screen.fill(self.palette.bg)
        pygame.draw.rect(self.screen,self.palette.accent,(0,0,w,3))
        for y in range(0,h,5): pygame.draw.line(self.screen,self.palette.scanline,(0,y),(w,y))
        self.txt('RetroCast',22,17,self.palette.accent,self.large)
        self.txt('● '+self.tr('live') if self.session.running else '○ '+self.tr('standby'),w-130,25,self.palette.warning if self.session.running else self.palette.muted,self.small)
        # Header: fixed button gutters, input takes remaining space.
        self.rect((20,65,w-40,52))
        self.txt(self.tr('source'),30,82,self.palette.accent,self.small,maxwidth=105)
        self.url_box=pygame.Rect(145,76,max(100,w-177),30)
        self.rect(self.url_box,self.palette.black,self.palette.accent if self.url_active else self.palette.edge)
        display=self.url or self.tr('source_hint')
        self.txt(display[-max(10,(self.url_box.width-20)//10):],self.url_box.x+9,self.url_box.y+6,self.palette.text if self.url else self.palette.muted,self.small,maxwidth=self.url_box.width-18)
        self.txt(f"[F3] {self.tr('performance')}  [K] {self.tr('help')}  |  [ENTER] {self.tr('watch')}  [U] {self.tr('source')}  [H] {self.tr('history')}",20,128,self.palette.accent,self.small,maxwidth=w-40)
        video_w=max(320,int((w-58)*0.64)); right_x=video_w+38; right_w=w-right_x-20
        video=pygame.Rect(20,155,video_w,max(1,h-303))
        self.video_rect=video
        self.draw_video_region(video)
        self.rect((right_x,video.y,right_w,video.height))
        self.txt(self.tr('transcript').upper(),right_x+14,video.y+14,self.palette.accent,self.small,maxwidth=right_w-165)
        pygame.draw.line(self.screen,self.palette.edge,(right_x+12,video.y+43),(right_x+right_w-12,video.y+43))
        transcript_area=pygame.Rect(right_x+12,video.y+55,right_w-24,max(1,video.height-85))
        previous=self.screen.get_clip(); self.screen.set_clip(transcript_area)
        rows=self.session.lines
        self.transcript_page.page_size=min(30,max(1,transcript_area.height//20))
        if self.transcript_follow:
            self.transcript_page.page=self.transcript_page.pages(len(rows))-1
        for i,line in enumerate(self.transcript_page.view(rows)):
            self.txt(line,transcript_area.x,transcript_area.y+i*20,self.palette.text,self.small,maxwidth=transcript_area.width)
        self.screen.set_clip(previous)

        self.txt(self.transcript_page.label(len(rows))+(' '+self.tr('live' if self.transcript_follow else 'hold')),right_x+right_w-150,video.y+14,self.palette.accent,self.small)

        # Two rows: playback/appearance and processing settings.
        bottom=video.bottom+10
        self.rect((20,bottom,w-40,92))
        self.draw_settings(w,bottom)
        status=self.session.status or self.notice
        self.txt(translate_status(self.preferences.language,status),24,h-44,self.palette.warning if 'ERRO' in status or 'VIDEO:' in status else self.palette.muted,self.small,maxwidth=w-48)
        self.txt(f"[TAB] {self.tr('autocomplete')}  [X] {self.tr('stop')}  [S] {self.tr('save')}  [PgUp/PgDn] {self.tr('navigate')}  [END] {self.tr('live')}  [ESC] {self.tr('exit')}",24,h-26,self.palette.accent,self.small,maxwidth=w-48)
        self.draw_suggestions()
        if self.history_open: self.draw_history()
        if self.perf_visible: self.draw_performance()
        if self.help_open: self.draw_help()
        pygame.display.flip()


    def draw_performance(self):
        w,h=self.screen.get_size()
        width=min(510,w-40)
        panel=pygame.Rect(w-width-20,180,width,min(340,h-220))
        self.rect(panel,self.palette.panel,self.palette.accent)
        self.txt(self.tr('performance')+' [F3]',panel.x+12,panel.y+10,self.palette.accent,self.small)
        self.txt('Log: ~/.local/state/retrocast/performance.log',panel.x+12,panel.y+34,self.palette.muted,self.small,maxwidth=width-24)
        y=panel.y+62
        for name, metric in self.perf_metrics.items():
            if y>panel.bottom-24: break
            line=f"{name}: {self.tr('average')} {metric['avg_ms']:.1f}ms {self.tr('maximum')} {metric['max_ms']:.1f}ms n={metric['count']}"
            self.txt(line,panel.x+12,y,self.palette.text,self.small,maxwidth=width-24)
            y+=23
        for name, count in self.perf_counts.items():
            if y>panel.bottom-24: break
            self.txt(f'{name}: {count}',panel.x+12,y,self.palette.muted,self.small,maxwidth=width-24)
            y+=22


    def draw_suggestions(self):
        if not self.url_active or not self.show_suggestions or not self.suggestions:
            return
        width=self.url_box.width
        self.suggestions_page.page_size=5
        for i, item in enumerate(self.suggestions_page.view(self.suggestions)):
            absolute=self.suggestions_page.page*5+i
            rect=pygame.Rect(self.url_box.x, self.url_box.bottom+3+i*33, width, 32)
            selected=absolute==self.suggestion_idx
            self.rect(rect, self.palette.accent if selected else self.palette.panel, self.palette.accent if selected else self.palette.edge)
            self.txt(('> ' if selected else '  ')+({'RECENTE':self.tr('recent'),'YT CANAL':'YT '+self.tr('channel'),'TWITCH CANAL':'TWITCH '+self.tr('channel')}.get(item.label,item.label)),rect.x+8,rect.y+7,self.palette.black if selected else self.palette.accent,self.small,130)
            self.txt(item.url,rect.x+140,rect.y+7,self.palette.black if selected else self.palette.text,self.small,rect.width-150)
        if self.suggestions_page.pages(len(self.suggestions))>1:
            self.txt(f"{self.tr('page')} {self.suggestions_page.label(len(self.suggestions))}  [PgUp/PgDn]",self.url_box.x+6,self.url_box.bottom+3+5*33,self.palette.accent,self.small)


    def draw_history(self):
        w,h=self.screen.get_size()
        box=pygame.Rect(max(25,w//2-360),max(35,h//2-230),min(720,w-50),min(460,h-70))
        overlay=pygame.Surface((w,h),pygame.SRCALPHA); overlay.fill((*self.palette.black,185)); self.screen.blit(overlay,(0,0))
        self.rect(box,self.palette.panel,self.palette.accent)
        self.txt(self.tr('history').upper(),box.x+20,box.y+18,self.palette.accent,self.large)
        items=self.history_rows
        self.txt(f"[O] {self.tr('history_sort')}: {self.tr('history_order_fixed' if self.history_available_first else 'history_sort_recent')}",box.x+20,box.y+45,self.palette.muted,self.small,maxwidth=box.width-40)
        editing=self.history_search_active
        query=self.history_search_draft if editing else self.history_query
        search=pygame.Rect(box.x+18,box.y+65,box.width-36,30)
        self.rect(search,self.palette.black,self.palette.accent if editing else self.palette.edge)
        self.txt(f"[/] {self.tr('history_search')}: {query}{'_' if editing else ''}",search.x+8,search.y+6,self.palette.text,self.small,maxwidth=search.width-16)
        if not items:
            self.txt(self.tr('history_empty'),box.x+20,box.y+110,self.palette.muted,self.small,maxwidth=box.width-40)
        for i,url in enumerate(self.history_page.view(items)):
            rect=pygame.Rect(box.x+18,box.y+102+i*34,box.width-36,30)
            absolute=self.history_page.page*self.history_page.page_size+i
            selected=absolute==self.history_index
            self.rect(rect,self.palette.accent if selected else self.palette.black,self.palette.edge)
            state=self.history_status.state(url)
            color={'online':(40,210,90),'offline':(235,65,65),'checking':self.palette.warning,'unknown':self.palette.muted}[state]
            pygame.draw.circle(self.screen,self.palette.black,(rect.x+13,rect.centery),6)
            pygame.draw.circle(self.screen,color,(rect.x+13,rect.centery),4)
            label=self.tr('history_'+state)
            fg=self.palette.black if selected else self.palette.text
            label_width=self.small.size(label)[0]
            self.txt(label,rect.right-label_width-8,rect.y+6,fg,self.small)
            self.txt(f'{absolute+1:02d}  {url}',rect.x+25,rect.y+6,fg,self.small,max(0,rect.width-label_width-45))
        y=box.bottom-45
        self.txt((f"[ENTER] {self.tr('history_search')} [ESC] {self.tr('close')}" if editing else '[PgUp/PgDn] '+self.history_page.label(len(items))+f" [↑/↓] {self.tr('select')} [ENTER] {self.tr('open')} [ESC] {self.tr('close')}"),box.x+20,y+6,self.palette.accent,self.small,maxwidth=box.width-40)


