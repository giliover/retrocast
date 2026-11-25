"""Retro desktop-style pygame UI. No web server."""
from functools import lru_cache
import math
import time
from ..performance import MONITOR, measure
import pygame
from ..sources import suggest, normalize_source
from ..history import SourceHistory
from ..session import Session
from ..themes import get_theme, next_theme
from ..i18n import translate, next_language
from ..preferences import Preferences
from ..pagination import Paginator

# Visual inspirado na TUI enviada: verde fosforo, linhas e selecao invertida.
BG=(5,13,10); PANEL=(10,25,17); EDGE=(39,110,65); CYAN=(66,242,119)
CREAM=(180,245,185); MUTED=(91,152,108); ORANGE=(245,210,90); BLACK=(2,9,5)

from .components.primitives import PrimitivesMixin
from .components.video import VideoMixin
from .components.panels import PanelsMixin
from .components.controls import ControlsMixin

class RetroUI(PrimitivesMixin, VideoMixin, PanelsMixin, ControlsMixin):
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('RetroCast')
        self.screen=pygame.display.set_mode((1180,800),pygame.RESIZABLE)
        self.clock=pygame.time.Clock()
        self.font=pygame.font.SysFont('dejavusansmono',17)
        self.small=pygame.font.SysFont('dejavusansmono',13)
        self.tiny=pygame.font.SysFont('dejavusansmono',11)
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
        self._transcript_revision=0
        self._rows_key=None
        self._scaled_frame=None
        self._scaled_frame_key=None


    def run(self):
        self.draw()
        hover=None
        while self.running:
            # Block when idle; active video is sampled at up to 30 Hz.
            timeout=max(1, int(1000/self.session.video.fps)) if self.session.running else 1000
            first=pygame.event.wait(timeout) if timeout else pygame.event.wait()
            events=[first]
            for _ in range(63):
                event=pygame.event.poll()
                if event.type==pygame.NOEVENT: break
                events.append(event)
            dirty=False
            frame_started=time.perf_counter()
            events_started=time.perf_counter()
            for event in events:
                if event.type==pygame.MOUSEMOTION:
                    current=next((name for name,rect in self.buttons.items() if rect.collidepoint(event.pos)),None)
                    dirty=dirty or current!=hover
                    hover=current
                elif event.type!=pygame.NOEVENT:
                    dirty=True
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
                    if event.key==pygame.K_F11 or (event.key==pygame.K_f and not self.url_active):
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
                                self.url=(self.url+root.clipboard_get())[:2048]; root.destroy()
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
            if not self.running: break
            old_status=self.session.status
            old_caption=self.session.caption
            with measure('ui.session_poll'):
                changed=self.session.poll()
            if changed:
                self._transcript_revision+=1
            dirty=dirty or changed or old_status!=self.session.status or old_caption!=self.session.caption
            if self.session.running and self.session.video.position is None and self.frame is not None:
                self.frame=None; self._scaled_frame=None; self._scaled_frame_key=None; dirty=True
            item=self.session.video.poll() if self.session.running else None
            if item:
                raw,size=item
                try:
                    with measure('ui.frame_upload'):
                        self.frame=pygame.image.frombuffer(raw,size,'RGB').copy()
                        MONITOR.increment('video.frames_presented_to_ui')
                except Exception as exc: self.session.status='FRAME: '+type(exc).__name__
            if dirty or item:
                with measure('ui.draw'):
                    if not dirty and not self.video_fullscreen and not self.history_open and not self.show_suggestions and not self.perf_visible:
                        self.draw_video_region(self.video_rect)
                        pygame.display.update(self.video_rect)
                        MONITOR.increment('ui.partial_draws')
                    else:
                        self.draw()
                        MONITOR.increment('ui.full_draws')
                MONITOR.increment('ui.frames')
            if self.session.running:
                self.clock.tick(max(1, round(self.session.video.fps)))
            MONITOR.duration('ui.frame_total', (time.perf_counter()-frame_started)*1000)
            MONITOR.duration('ui.actual_fps', self.clock.get_fps())
            report=MONITOR.report_if_due()
            if report:
                self.perf_metrics,self.perf_counts=report
                if self.perf_visible: self.draw()
        self.session.close()
        pygame.quit()


