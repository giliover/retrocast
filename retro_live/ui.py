"""Retro desktop-style pygame UI. No web server."""
import math
import time
from .performance import MONITOR, measure
import pygame
from .sources import suggest, normalize_source
from .history import SourceHistory
from .session import Session
from .themes import get_theme, next_theme
from .i18n import translate, next_language
from .preferences import Preferences
from .pagination import Paginator

# Visual inspirado na TUI enviada: verde fosforo, linhas e selecao invertida.
BG=(5,13,10); PANEL=(10,25,17); EDGE=(39,110,65); CYAN=(66,242,119)
CREAM=(180,245,185); MUTED=(91,152,108); ORANGE=(245,210,90); BLACK=(2,9,5)

class RetroUI:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('RetroCast')
        self.screen=pygame.display.set_mode((1180,800),pygame.RESIZABLE)
        self.clock=pygame.time.Clock()
        self.font=pygame.font.SysFont('dejavusansmono',17)
        self.small=pygame.font.SysFont('dejavusansmono',13)
        self.large=pygame.font.SysFont('dejavusansmono',25,bold=True)
        self.session=Session()
        self.preferences=Preferences()
        self.palette=get_theme(self.preferences.theme)
        self.url_active=False
        self.url=''
        self.volume=0.8
        self.video_fullscreen=False
        self._window_size=(1180,800)
        self.subtitle=True
        self.scroll=0
        self.frame=None
        self.frame_size=None
        self.running=True
        self.buttons={}
        self.notice=self.tr('ready')
        self.history=SourceHistory()
        self.suggestions=[]
        self.suggestion_idx=0
        self.suggestion_rects=[]
        self.show_suggestions=False
        self.history_open=False
        self.history_page=Paginator(page_size=9)
        self.suggestions_page=Paginator(page_size=5)
        self.transcript_page=Paginator(page_size=10)
        self.history_rects=[]
        self.transcript_rows=[]
        self.transcript_follow=True
        self.perf_visible=False
        self.perf_metrics={}
        self.perf_counts={}
        self._scaled_frame=None
        self._scaled_frame_key=None

    def tr(self, key):
        return translate(self.preferences.language, key)

    def txt(self, text, x,y, color=None, font=None, maxwidth=None):
        font=font or self.font
        color=self.palette.text if color is None else color
        if maxwidth:
            while text and font.size(text)[0]>maxwidth: text=text[:-2]+'…'
        self.screen.blit(font.render(text,True,color),(x,y))

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
            text_font=pygame.font.SysFont('dejavusansmono',11)
        if text_font.size(label)[0]>available:
            while label and text_font.size(label+'…')[0]>available:
                label=label[:-1]
            label+='…'
        text=text_font.render(label,True,self.palette.black if active else self.palette.text)
        self.screen.blit(text,text.get_rect(center=self.buttons[name].center))

    def wrap(self, text, max_width, font):
        result=[]; line=''
        for word in text.split():
            trial=(line+' '+word).strip()
            if font.size(trial)[0]>max_width and line:
                result.append(line); line=word
            else: line=trial
        if line: result.append(line)
        return result or ['']

    def toggle_video_fullscreen(self):
        """Fullscreen video-only mode, preserving the previous window dimensions."""
        if not self.video_fullscreen:
            self._window_size=self.screen.get_size()
            self.screen=pygame.display.set_mode((0,0),pygame.FULLSCREEN)
            self.video_fullscreen=True
        else:
            self.screen=pygame.display.set_mode(self._window_size,pygame.RESIZABLE)
            self.video_fullscreen=False
        self._scaled_frame_key=None
        self._scaled_frame=None
        self.buttons.clear()

    def draw_fullscreen_video(self):
        w,h=self.screen.get_size()
        self.screen.fill(self.palette.black)
        if self.frame:
            fw,fh=self.frame.get_size()
            scale=min(w/fw,h/fh)
            target=(max(1,int(fw*scale)),max(1,int(fh*scale)))
            key=(id(self.frame),target)
            if key!=self._scaled_frame_key:
                with measure('ui.video_scale'):
                    self._scaled_frame=pygame.transform.scale(self.frame,target)
                self._scaled_frame_key=key
            self.screen.blit(self._scaled_frame,self._scaled_frame.get_rect(center=(w//2,h//2)))
        else:
            self.txt(self.tr('nosignal'),max(20,w//2-80),h//2,self.palette.accent,self.large)
        if self.subtitle and self.session.lines:
            last=self.session.lines[-1].split('] ',1)[-1]
            lines=self.wrap(last,max(100,w-120),self.font)[-3:]
            line_height=28
            box_h=len(lines)*line_height+20
            box=pygame.Surface((max(1,w-80),box_h),pygame.SRCALPHA)
            box.fill((8,12,17,220))
            self.screen.blit(box,(40,h-box_h-35))
            for i,line in enumerate(lines):
                rendered=self.font.render(line,True,self.palette.text)
                self.screen.blit(rendered,rendered.get_rect(centerx=w//2,y=h-box_h-25+i*line_height))
        pygame.display.flip()

    def draw(self):
        if self.video_fullscreen:
            self.draw_fullscreen_video()
            return
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
        video_w=max(320,int((w-58)*0.64)); right_x=video_w+38; right_w=w-right_x-20
        video=pygame.Rect(20,158,video_w,max(220,h-305))
        self.rect(video,self.palette.black)
        if self.frame:
            fw,fh=self.frame.get_size()
            scale=min((video.width-4)/fw,(video.height-4)/fh)
            target=(max(1,int(fw*scale)),max(1,int(fh*scale)))
            key=(id(self.frame), target)
            if key != self._scaled_frame_key:
                with measure('ui.video_scale'):
                    self._scaled_frame=pygame.transform.scale(self.frame,target)
                self._scaled_frame_key=key
            self.screen.blit(self._scaled_frame,self._scaled_frame.get_rect(center=video.center))
        else:
            self.txt('[ '+self.tr('nosignal')+' ]',video.centerx-100,video.centery-25,self.palette.accent,self.large)
            self.txt('> '+self.tr('waiting'),video.centerx-115,video.centery+13,self.palette.muted,self.small)
        # Subtitles are drawn over video, including semi-transparent backing.
        if self.subtitle and self.session.lines:
            last=self.session.lines[-1].split('] ',1)[-1]
            subtitle_lines=self.wrap(last,video.width-75,self.font)[-3:]
            sh=18+len(subtitle_lines)*24
            surf=pygame.Surface((video.width-28,sh),pygame.SRCALPHA)
            surf.fill((8,12,17,220))
            self.screen.blit(surf,(video.x+14,video.bottom-sh-18))
            for i,line in enumerate(subtitle_lines):
                render=self.font.render(line,True,self.palette.text)
                self.screen.blit(render,render.get_rect(centerx=video.centerx,y=video.bottom-sh-10+i*24))
        self.rect((right_x,158,right_w,video.height))
        self.txt(self.tr('transcript').upper(),right_x+14,172,self.palette.accent,self.small,maxwidth=right_w-165)
        pygame.draw.line(self.screen,self.palette.edge,(right_x+12,201),(right_x+right_w-12,201))
        transcript_area=pygame.Rect(right_x+12,213,right_w-24,video.height-85)
        previous=self.screen.get_clip(); self.screen.set_clip(transcript_area)
        rows=[]
        for line in self.session.lines:
            rows.extend(self.wrap(line,right_w-40,self.small)); rows.append('')
        self.transcript_rows=rows
        self.transcript_page.page_size=max(1,transcript_area.height//20)
        if self.transcript_follow:
            self.transcript_page.page=self.transcript_page.pages(len(rows))-1
        for i,line in enumerate(self.transcript_page.view(rows)):
            self.txt(line,transcript_area.x,transcript_area.y+i*20,self.palette.text,self.small)
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

    def action(self,name):
        try:
            if name=='play':
                self.session.config.url=normalize_source(self.url)
                self.url=self.session.config.url
                self.history.add(self.url)
                self.show_suggestions=False
                self.url_active=False
                self.session.start(); self.scroll=0; self.frame=None; self.transcript_page.reset(); self.transcript_follow=True
            elif name=='stop': self.session.close()
            elif name=='history': self.history_open=not self.history_open; self.history_page.reset()
            elif name=='history_close': self.history_open=False
            elif name=='history_prev': self.history_page.move(-1,len(self.history.items))
            elif name=='history_next': self.history_page.move(1,len(self.history.items))
            elif name=='trans_prev': self.transcript_follow=False; self.transcript_page.move(-1,len(self.transcript_rows))
            elif name=='trans_next': self.transcript_page.move(1,len(self.transcript_rows)); self.transcript_follow=self.transcript_page.page==self.transcript_page.pages(len(self.transcript_rows))-1
            elif name=='save': self.session.save()
            elif name=='pause': self.session.video.toggle_pause()
            elif name=='sub': self.subtitle=not self.subtitle
            elif name=='fullscreen': self.toggle_video_fullscreen()
            elif name=='vol_down': self.volume=round(max(0,self.volume-0.05),2); self.session.video.set_volume(self.volume)
            elif name=='vol_up': self.volume=round(min(1,self.volume+0.05),2); self.session.video.set_volume(self.volume)
            elif name=='model':
                models=['tiny','base','small','medium']
                i=models.index(self.session.config.model) if self.session.config.model in models else 0
                self.session.config.model=models[(i+1)%len(models)]
                self.session.status=self.tr('changed_model')
            elif name=='lang':
                langs=['pt','en','es','auto']
                i=langs.index(self.session.config.language) if self.session.config.language in langs else 0
                self.session.config.language=langs[(i+1)%len(langs)]
                self.session.status=self.tr('changed_speech')
            elif name=='theme':
                self.preferences.theme=next_theme(self.preferences.theme)
                self.palette=get_theme(self.preferences.theme)
                self.preferences.save()
            elif name=='ui_language':
                self.preferences.language=next_language(self.preferences.language)
                self.notice=self.tr('ready')
                self.preferences.save()
        except Exception as exc:
            self.session.status='ERRO: '+str(exc)

    def refresh_suggestions(self):
        self.suggestions=suggest(self.url, self.history.items)
        self.suggestion_idx=0
        self.suggestions_page.reset()
        self.show_suggestions=True

    def accept_suggestion(self):
        if not self.suggestions:
            return
        self.url=self.suggestions[self.suggestion_idx].url
        self.show_suggestions=False

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
        self.history_page.page_size=max(1,(box.height-130)//34)
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

    def navigate_wheel(self, delta, pos):
        if self.history_open:
            self.history_page.move(-1 if delta>0 else 1,len(self.history.items))
        elif self.url_active and self.show_suggestions and self.url_box.x<=pos[0]<=self.url_box.right and self.url_box.bottom<=pos[1]<=self.url_box.bottom+200:
            self.suggestions_page.move(-1 if delta>0 else 1,len(self.suggestions))
            self.suggestion_idx=min(len(self.suggestions)-1,self.suggestions_page.page*self.suggestions_page.page_size) if self.suggestions else 0
        else:
            self.transcript_follow=False
            self.transcript_page.move(-1 if delta>0 else 1,len(self.transcript_rows))
            self.transcript_follow=self.transcript_page.page==self.transcript_page.pages(len(self.transcript_rows))-1

    def run(self):
        while self.running:
            frame_started=time.perf_counter()
            events_started=time.perf_counter()
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    self.running=False
                elif event.type==pygame.MOUSEBUTTONDOWN:
                    if self.video_fullscreen:
                        if event.button==1: self.action('fullscreen')
                        continue
                    if event.button==1:
                        selected=False
                        if self.history_open:
                            chosen=next((url for url,rect in self.history_rects if rect.collidepoint(event.pos)),None)
                            if chosen:
                                self.url=chosen; self.history_open=False; self.url_active=True
                                continue
                            for name in ('history_prev','history_next','history_close'):
                                if name in self.buttons and self.buttons[name].collidepoint(event.pos):
                                    self.action(name); break
                            continue
                        for i,rect in self.suggestion_rects:
                            if rect.collidepoint(event.pos):
                                self.suggestion_idx=i
                                self.accept_suggestion()
                                self.url_active=True
                                selected=True
                                break
                        if selected:
                            continue
                        self.url_active=self.url_box.collidepoint(event.pos)
                        self.show_suggestions=self.url_active
                        if self.url_active:
                            self.refresh_suggestions()
                        for name,rect in self.buttons.items():
                            if rect.collidepoint(event.pos):
                                self.action(name)
                                break
                    elif event.button in (4,5):
                        self.navigate_wheel(1 if event.button==4 else -1,event.pos)
                elif event.type==pygame.MOUSEWHEEL:
                    if self.video_fullscreen: continue
                    self.navigate_wheel(event.y,pygame.mouse.get_pos())
                elif event.type==pygame.KEYDOWN:
                    if event.key in (pygame.K_F11, pygame.K_f):
                        self.action('fullscreen')
                        continue
                    if self.video_fullscreen:
                        if event.key==pygame.K_ESCAPE: self.action('fullscreen')
                        elif event.key==pygame.K_SPACE: self.action('pause')
                        elif event.key==pygame.K_c: self.action('sub')
                        continue
                    if self.history_open:
                        if event.key==pygame.K_ESCAPE: self.history_open=False
                        elif event.key==pygame.K_PAGEUP: self.history_page.move(-1,len(self.history.items))
                        elif event.key==pygame.K_PAGEDOWN: self.history_page.move(1,len(self.history.items))
                        continue
                    if self.url_active:
                        if event.key==pygame.K_ESCAPE:
                            self.url_active=False
                            self.show_suggestions=False
                        elif event.key==pygame.K_TAB:
                            self.accept_suggestion()
                        elif event.key in (pygame.K_DOWN,pygame.K_UP) and self.suggestions:
                            delta=1 if event.key==pygame.K_DOWN else -1
                            self.suggestion_idx=(self.suggestion_idx+delta)%len(self.suggestions)
                            self.suggestions_page.page=self.suggestion_idx//self.suggestions_page.page_size
                        elif event.key in (pygame.K_PAGEUP,pygame.K_PAGEDOWN):
                            self.suggestions_page.move(-1 if event.key==pygame.K_PAGEUP else 1,len(self.suggestions))
                            self.suggestion_idx=min(len(self.suggestions)-1,self.suggestions_page.page*self.suggestions_page.page_size) if self.suggestions else 0
                        elif event.key==pygame.K_RETURN:
                            if self.show_suggestions and self.suggestions:
                                self.accept_suggestion()
                            else:
                                self.action('play')
                        elif event.key==pygame.K_BACKSPACE:
                            self.url=self.url[:-1]
                            self.refresh_suggestions()
                        elif event.key==pygame.K_v and event.mod & pygame.KMOD_CTRL:
                            try:
                                import tkinter
                                root=tkinter.Tk(); root.withdraw()
                                self.url+=root.clipboard_get(); root.destroy()
                                self.refresh_suggestions()
                            except Exception: pass
                        elif event.unicode and event.unicode.isprintable() and len(self.url)<2048:
                            self.url+=event.unicode
                            self.refresh_suggestions()
                    elif event.key==pygame.K_ESCAPE: self.running=False
                    elif event.key==pygame.K_RETURN: self.action('play')
                    elif event.key==pygame.K_SPACE: self.action('pause')
                    elif event.key==pygame.K_s: self.action('save')
                    elif event.key==pygame.K_m: self.action('model')
                    elif event.key==pygame.K_l: self.action('lang')
                    elif event.key==pygame.K_t: self.action('theme')
                    elif event.key==pygame.K_i: self.action('ui_language')
                    elif event.key==pygame.K_c: self.action('sub')
                    elif event.key==pygame.K_F3: self.perf_visible=not self.perf_visible
                    elif event.key==pygame.K_h: self.action('history')
                    elif event.key==pygame.K_PAGEUP: self.action('trans_prev')
                    elif event.key==pygame.K_PAGEDOWN: self.action('trans_next')
                    elif event.key==pygame.K_u:
                        self.url_active=True
                        self.refresh_suggestions()
            MONITOR.duration('ui.events', (time.perf_counter()-events_started)*1000)
            with measure('ui.session_poll'):
                self.session.poll()
            item=self.session.video.poll()
            if item:
                raw,size=item
                try:
                    with measure('ui.frame_upload'):
                        self.frame=pygame.image.frombuffer(raw,size,'RGB').copy()
                        MONITOR.increment('video.frames_presented_to_ui')
                except Exception as exc: self.session.status='FRAME: '+str(exc)
            with measure('ui.draw'):
                self.draw()
            self.clock.tick(30)
            MONITOR.duration('ui.frame_total', (time.perf_counter()-frame_started)*1000)
            MONITOR.increment('ui.frames')
            MONITOR.duration('ui.actual_fps', self.clock.get_fps())
            report=MONITOR.report_if_due()
            if report:
                self.perf_metrics,self.perf_counts=report
        self.session.close()
        pygame.quit()
