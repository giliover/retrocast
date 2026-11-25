import pygame


class PanelsMixin:
    def draw(self):
        if self.video_fullscreen:
            self.draw_fullscreen_video()
            return
        self.buttons.clear()
        w,h=self.screen.get_size()
        self.screen.fill(self.palette.bg)
        pygame.draw.rect(self.screen,self.palette.accent,(0,0,w,3))
        for y in range(0,h,5): pygame.draw.line(self.screen,self.palette.scanline,(0,y),(w,y))
        self.txt('RetroCast',22,17,self.palette.accent,self.large)
        self.txt('● LIVE' if self.session.running else '○ STANDBY',w-130,25,self.palette.warning if self.session.running else self.palette.muted,self.small)
        # Header: fixed button gutters, input takes remaining space.
        self.rect((20,65,w-40,52))
        self.txt(self.tr('source'),30,82,self.palette.accent,self.small,maxwidth=105)
        header_gap=12
        action_widths=(112,100,100)
        actions_total=sum(action_widths)+2*header_gap
        actions_x=w-32-actions_total
        self.url_box=pygame.Rect(145,76,max(100,actions_x-145-header_gap),30)
        self.rect(self.url_box,self.palette.black,self.palette.accent if self.url_active else self.palette.edge)
        display=self.url or 'twitch / youtube / @canal / URL'
        self.txt(display[-max(10,(self.url_box.width-20)//10):],self.url_box.x+9,self.url_box.y+6,self.palette.text if self.url else self.palette.muted,self.small,maxwidth=self.url_box.width-18)
        self.button('play',self.tr('watch'),(actions_x,76,action_widths[0],30),active=not self.session.running)
        self.button('stop',self.tr('stop'),(actions_x+action_widths[0]+header_gap,76,action_widths[1],30))
        self.button('save',self.tr('save'),(actions_x+action_widths[0]+action_widths[1]+2*header_gap,76,action_widths[2],30))
        self.button('history',self.tr('history'),(20,121,135,29))
        self.button('delay_down','- 5s',(170,121,75,29))
        self.txt(f'BUFFER {self.session.config.delay}s',255,128,self.palette.accent,self.small)
        self.button('delay_up','+ 5s',(365,121,75,29))
        self.button('quality','VIDEO: '+self.session.config.quality.upper(),(455,121,180,29))
        video_w=max(320,int((w-58)*0.64)); right_x=video_w+38; right_w=w-right_x-20
        video=pygame.Rect(20,158,video_w,max(220,h-305))
        self.video_rect=video
        self.draw_video_region(video)
        self.rect((right_x,158,right_w,video.height))
        self.txt(self.tr('transcript').upper(),right_x+14,172,self.palette.accent,self.small,maxwidth=right_w-165)
        pygame.draw.line(self.screen,self.palette.edge,(right_x+12,201),(right_x+right_w-12,201))
        transcript_area=pygame.Rect(right_x+12,213,right_w-24,video.height-85)
        previous=self.screen.get_clip(); self.screen.set_clip(transcript_area)
        key=(right_w, self._transcript_revision)
        if key != self._rows_key:
            self.transcript_rows=self.session.lines
            self._rows_key=key
        rows=self.transcript_rows
        self.transcript_page.page_size=min(30,max(1,transcript_area.height//20))
        if self.transcript_follow:
            self.transcript_page.page=self.transcript_page.pages(len(rows))-1
        for i,line in enumerate(self.transcript_page.view(rows)):
            self.txt(line,transcript_area.x,transcript_area.y+i*20,self.palette.text,self.small,maxwidth=transcript_area.width)
        self.screen.set_clip(previous)
        self.button('trans_prev','<', (right_x+right_w-135,166,26,27))
        self.txt(self.transcript_page.label(len(rows)),right_x+right_w-102,172,self.palette.accent,self.small)
        self.button('trans_next','>', (right_x+right_w-40,166,26,27))
        # Two dedicated rows, with consistent 12px spacing; no overlapping buttons.
        bottom=video.bottom+10
        self.rect((20,bottom,w-40,91))
        gap=12
        x=32
        for name,label,bw,active in (
            ('pause',self.tr('pause'),115,False),
            ('sub',self.tr('sub_on') if self.subtitle else self.tr('sub_off'),135,self.subtitle),
            ('vol_down','VOL -',90,False),
            ('vol_up','VOL +',90,False),
            ('fullscreen',self.tr('fullscreen'),150,False),
        ):
            self.button(name,label,(x,bottom+8,bw,34),active)
            x+=bw+gap
        self.txt(f'{round(self.volume*100)}%',x+3,bottom+16,self.palette.accent,self.small)
        # Settings on their own row to avoid the original overlap.
        options=[
            ('model',self.tr('model')+': '+self.session.config.model.upper()),
            ('lang',self.tr('speech')+': '+self.session.config.language.upper()),
            ('theme',self.tr('theme')+': '+self.preferences.theme.upper()),
            ('ui_language',self.tr('ui_lang')+': '+self.preferences.language.upper()),
        ]
        available=w-64
        option_width=(available-3*gap)//4
        for i,(name,label) in enumerate(options):
            self.button(name,label,(32+i*(option_width+gap),bottom+49,option_width,34))
        status=self.session.status or self.notice
        self.txt(status,24,h-44,self.palette.warning if 'ERRO' in status or 'VIDEO:' in status else self.palette.muted,self.small,maxwidth=w-48)
        self.txt(self.tr('hint'),24,h-26,self.palette.accent,self.small,maxwidth=w-48)
        self.draw_suggestions()
        if self.history_open: self.draw_history()
        if self.perf_visible: self.draw_performance()
        pygame.display.flip()


    def draw_performance(self):
        w,h=self.screen.get_size()
        width=min(510,w-40)
        panel=pygame.Rect(w-width-20,180,width,min(340,h-220))
        self.rect(panel,self.palette.panel,self.palette.accent)
        self.txt('PERFORMANCE [F3]',panel.x+12,panel.y+10,self.palette.accent,self.small)
        self.txt('Log: ~/.local/state/retrocast/performance.log',panel.x+12,panel.y+34,self.palette.muted,self.small,maxwidth=width-24)
        y=panel.y+62
        for name, metric in sorted(self.perf_metrics.items()):
            if y>panel.bottom-24: break
            line=f"{name}: avg {metric['avg_ms']:.1f}ms max {metric['max_ms']:.1f}ms n={metric['count']}"
            self.txt(line,panel.x+12,y,self.palette.text,self.small,maxwidth=width-24)
            y+=23
        for name, count in sorted(self.perf_counts.items()):
            if y>panel.bottom-24: break
            self.txt(f'{name}: {count}',panel.x+12,y,self.palette.muted,self.small,maxwidth=width-24)
            y+=22


    def draw_suggestions(self):
        self.suggestion_rects=[]
        if not self.url_active or not self.show_suggestions or not self.suggestions:
            return
        width=self.url_box.width
        self.suggestions_page.page_size=5
        for i, item in enumerate(self.suggestions_page.view(self.suggestions)):
            absolute=self.suggestions_page.page*5+i
            rect=pygame.Rect(self.url_box.x, self.url_box.bottom+3+i*33, width, 32)
            self.suggestion_rects.append((absolute,rect))
            selected=absolute==self.suggestion_idx
            self.rect(rect, self.palette.accent if selected else self.palette.panel, self.palette.accent if selected else self.palette.edge)
            self.txt(('> ' if selected else '  ')+item.label,rect.x+8,rect.y+7,self.palette.black if selected else self.palette.accent,self.small,130)
            self.txt(item.url,rect.x+140,rect.y+7,self.palette.black if selected else self.palette.text,self.small,rect.width-150)
        if self.suggestions_page.pages(len(self.suggestions))>1:
            self.txt(f"Pg {self.suggestions_page.label(len(self.suggestions))}  [PgUp/PgDn]",self.url_box.x+6,self.url_box.bottom+3+5*33,self.palette.accent,self.small)


    def draw_history(self):
        w,h=self.screen.get_size()
        box=pygame.Rect(max(25,w//2-360),max(35,h//2-230),min(720,w-50),min(460,h-70))
        overlay=pygame.Surface((w,h),pygame.SRCALPHA); overlay.fill((0,0,0,185)); self.screen.blit(overlay,(0,0))
        self.rect(box,self.palette.panel,self.palette.accent)
        self.txt(self.tr('history').upper(),box.x+20,box.y+18,self.palette.accent,self.large)
        items=list(reversed(self.history.items))
        self.history_page.page_size=min(9,max(1,(box.height-130)//34))
        self.history_rects=[]
        for i,url in enumerate(self.history_page.view(items)):
            rect=pygame.Rect(box.x+18,box.y+66+i*34,box.width-36,30)
            self.rect(rect,self.palette.black,self.palette.edge)
            self.txt(f'{self.history_page.page*self.history_page.page_size+i+1:02d}  {url}',rect.x+8,rect.y+6,self.palette.text,self.small,rect.width-15)
            self.history_rects.append((url,rect))
        y=box.bottom-45
        self.button('history_prev','<', (box.x+20,y,38,28))
        self.txt(self.history_page.label(len(items)),box.x+72,y+6,self.palette.accent,self.small)
        self.button('history_next','>', (box.x+135,y,38,28))
        self.button('history_close',self.tr('close'),(box.right-125,y,105,28))


