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
                self.session.start(); self.session.video.set_volume(self.volume); self._transcript_revision+=1; self.scroll=0; self.frame=None; self._scaled_frame=None; self._scaled_frame_key=None; self.transcript_page.reset(); self.transcript_follow=True
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
            elif name in ('fps','fps_down','fps_up'):
                config = self.session.config
                index = FPS_CHOICES.index(config.fps_limit)
                if name == "fps":
                    index = 0 if index else FPS_CHOICES.index(30)
                elif name == "fps_down":
                    index = max(1, sum(fps < self.session.video.fps for fps in FPS_CHOICES)-1) if index == 0 else max(1,index-1)
                else:
                    index = FPS_CHOICES.index(60) if index == 0 else min(len(FPS_CHOICES)-1,index+1)
                config.fps_limit = FPS_CHOICES[index]
                self.session.video.set_fps_limit(config.fps_limit)
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
            elif name=='history': self.history_open=not self.history_open; self.history_page.reset()
            elif name=='history_close': self.history_open=False
            elif name=='history_prev': self.history_page.move(-1,len(self.history.items))
            elif name=='history_next': self.history_page.move(1,len(self.history.items))
            elif name=='trans_prev': self.transcript_follow=False; self.transcript_page.move(-1,len(self.transcript_rows))
            elif name=='trans_next': self.transcript_page.move(1,len(self.transcript_rows)); self.transcript_follow=self.transcript_page.page==self.transcript_page.pages(len(self.transcript_rows))-1
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
        self.show_suggestions=False


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


