from ...whisper_policy import WhisperPolicy, RETRIES, TIMEOUTS
from ...playback_policy import PRIORITIES, FPS_CHOICES
from ...sources import suggest, normalize_source, validate_source
from ...themes import get_theme, next_theme
from ...i18n import next_language


class ControlsMixin:
    def action(self,name):
        try:
            if name=='play':
                self.session.config.url=normalize_source(self.url)
                self.url=self.session.config.url
                validate_source(self.url)
                self.history.add(self.url)
                self.show_suggestions=False
                self.url_active=False
                self.session.start(); self.session.video.set_volume(self.volume); self.frame=None; self._scaled_frame=None; self._scaled_frame_key=None; self.transcript_page.reset(); self.transcript_follow=True
            elif name in ('delay_down','delay_up'):
                self.session.config.delay=max(10,min(120,self.session.config.delay+(5 if name=='delay_up' else -5)))
                self.session.video.set_delay(self.session.config.delay)
                self.frame=None
                self._scaled_frame=None
                self._scaled_frame_key=None
            elif name=='priority':
                config = self.session.config
                config.priority = PRIORITIES[(PRIORITIES.index(config.priority)+1)%len(PRIORITIES)]
                self.session.video.set_priority(config.priority)
            elif name in ('fps','fps_down','fps_up','fps_auto'):
                config = self.session.config
                index = FPS_CHOICES.index(config.fps_limit)
                if name == "fps_auto":
                    index = 0
                elif name == "fps":
                    index = (index+1)%len(FPS_CHOICES)
                elif name == "fps_down":
                    index = max(1, sum(fps < self.session.video.fps for fps in FPS_CHOICES)-1) if index == 0 else max(1,index-1)
                else:
                    index = FPS_CHOICES.index(60) if index == 0 else min(len(FPS_CHOICES)-1,index+1)
                config.fps_limit = FPS_CHOICES[index]
                self.session.video.set_fps_limit(config.fps_limit)
            elif name in ('whisper_retries','whisper_timeout','whisper_timeout_down','whisper_timeout_up'):
                config = self.session.config
                if config.priority != 'subtitle':
                    return
                if name == 'whisper_retries':
                    config.whisper_retries = RETRIES[(RETRIES.index(config.whisper_retries)+1)%len(RETRIES)]
                else:
                    config.whisper_timeout = TIMEOUTS[max(0,min(len(TIMEOUTS)-1,TIMEOUTS.index(config.whisper_timeout)+(-1 if name == "whisper_timeout_down" else 1)))]
                self.session.video.set_whisper_policy(WhisperPolicy(config.whisper_retries, config.whisper_timeout))
            elif name=='quality':
                qualities=('auto','1080p','720p','480p','360p')
                current=self.session.config.quality
                self.session.config.quality=qualities[(qualities.index(current)+1)%len(qualities)] if current in qualities else 'auto'
                self.session.status='VIDEO: '+self.session.config.quality.upper()+' (next WATCH)'
            elif name=='stop':
                self.session.close()
                self.frame=None
                self._scaled_frame=None
                self._scaled_frame_key=None
            elif name=='history':
                self.history_open=not self.history_open
                if self.history_open:
                    self.history_query=""; self.history_search_draft=""; self.history_search_active=False
                    self.resize_history_page()
                    self.refresh_history_order(reset=True)
                else: self.close_history()
            elif name=='history_close': self.close_history()
            elif name in ('trans_prev','trans_next','trans_live'):
                count=len(self.session.lines)
                if name=='trans_live':
                    self.transcript_page.page=self.transcript_page.pages(count)-1
                    self.transcript_follow=True
                else:
                    if self.transcript_follow:
                        self.transcript_page.page=self.transcript_page.pages(count)-1
                    self.transcript_page.move(-1 if name=='trans_prev' else 1,count)
                    self.transcript_follow=name=='trans_next' and self.transcript_page.page==self.transcript_page.pages(count)-1
            elif name=='save': self.session.save()
            elif name=='pause': self.session.video.toggle_pause()
            elif name=='sub':
                self.session.set_subtitles(not self.subtitle)
                self.subtitle=self.session.subtitles_enabled
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
            self.session.status='ERRO: '+type(exc).__name__


    def refresh_suggestions(self):
        self.suggestions=suggest(self.url, self.history.items)
        self.suggestion_idx=0
        self.suggestions_page.reset()
        self.show_suggestions=True


    def accept_suggestion(self):
        if not self.suggestions:
            return
        self.url=self.suggestions[self.suggestion_idx].url
        self.field_cursor("url").reset(self.url)
        self.show_suggestions=False


