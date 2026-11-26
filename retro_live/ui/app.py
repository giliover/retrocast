import logging
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
from .components.settings import SettingsMixin
from .components.keyboard import KeyboardMixin
from .components.help import HelpMixin

class RetroUI(PrimitivesMixin, VideoMixin, PanelsMixin, ControlsMixin, SettingsMixin, KeyboardMixin, HelpMixin):
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
        self.frame=None
        self.frame_size=None
        self.running=True
        self.notice=self.tr('ready')
        self.history=SourceHistory()
        self.suggestions=[]
        self.suggestion_idx=0
        self.show_suggestions=False
        self.history_open=False
        self.history_page=Paginator(page_size=9)
        self.suggestions_page=Paginator(page_size=5)
        self.transcript_page=Paginator(page_size=10)
        self.history_index=0
        self.transcript_follow=True
        self.perf_visible=False
        self.help_open=False
        self.help_page=0
        self.help_pages=1
        self.perf_metrics={}
        self.perf_counts={}
        self._scaled_frame=None
        self._scaled_frame_key=None


    def run(self):
        pygame.event.set_blocked([pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL])
        self.draw()
        while self.running:
            # Block when idle; active video is sampled at the selected FPS cap.
            timeout=max(1, int(1000/self.session.video.presentation_fps)) if self.session.running else 1000
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
                if event.type==pygame.QUIT:
                    self.running=False
                elif event.type==pygame.KEYDOWN:
                    self.handle_key(event)
                    dirty=True
                elif event.type in (pygame.VIDEORESIZE, pygame.WINDOWEXPOSED):
                    dirty=True
            MONITOR.duration('ui.events', (time.perf_counter()-events_started)*1000)
            if not self.running: break
            old_status=self.session.status
            old_caption=self.session.caption
            with measure('ui.session_poll'):
                changed=self.session.poll()
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
            # Animate at 10 Hz even when the media clock is frozen.
            spinner_tick = int(time.monotonic()*10) if self.session.running and self.session.video.whisper_waiting else None
            animate = spinner_tick != getattr(self, '_spinner_tick', None)
            self._spinner_tick = spinner_tick
            if dirty or item or animate:
                with measure('ui.draw'):
                    if not dirty and not self.video_fullscreen and not self.history_open and not self.show_suggestions and not self.perf_visible and not self.help_open:
                        self.draw_video_region(self.video_rect)
                        pygame.display.update(self.video_rect)
                        MONITOR.increment('ui.partial_draws')
                    else:
                        self.draw()
                        MONITOR.increment('ui.full_draws')
                MONITOR.increment('ui.frames')
            if self.session.running:
                self.clock.tick(max(1, round(self.session.video.presentation_fps)))
            MONITOR.duration('ui.frame_total', (time.perf_counter()-frame_started)*1000)
            MONITOR.duration('ui.actual_fps', self.clock.get_fps())
            report=MONITOR.report_if_due()
            if report:
                if self.session.running:
                    logging.getLogger("retrocast.application").info("subtitle_ui enabled=%s caption_present=%s fullscreen=%s frame_present=%s", self.subtitle, bool(self.session.caption), self.video_fullscreen, self.frame is not None)
                self.perf_metrics,self.perf_counts=report
                if self.perf_visible: self.draw()
        self.session.close()
        pygame.quit()


