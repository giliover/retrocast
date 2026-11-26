"""Keyboard playback help and bounded performance controls."""

class SettingsMixin:
    def draw_settings(self, width, bottom):
        c = self.session.config
        state = 'PAUSED' if self.session.video.paused else 'PLAY'
        self.txt(f'{state} | [SPACE] Pause  [C] SUB {"ON" if self.subtitle else "OFF"}  [↑/↓] VOL {round(self.volume*100)}%  [F] Fullscreen  [L] AUDIO {c.language.upper()}  [T] THEME  [I] LANG', 32, bottom+17, self.palette.accent, self.small, maxwidth=width-64)
        strict = c.priority == 'subtitle'
        performance = (
            ('quality', 'VIDEO: '+c.quality.upper()),
            ('priority', self.tr(c.priority)),
            ('fps', 'FPS: '+str(c.fps_limit or 'AUTO')),
            ('model', self.tr('model')+': '+c.model.upper()),
            ('delay_down', 'BUF −'),
            ('delay_up', 'BUF +'+str(c.delay)+'s'),
            ('whisper_retries' if strict else None, 'RETRY: '+str(c.whisper_retries if strict else 0)),
            ('whisper_timeout_down' if strict else None, '−'),
            ('whisper_timeout' if strict else None, 'WAIT: '+str(c.whisper_timeout if strict else 0)+'s'),
            ('whisper_timeout_up' if strict else None, '+'),
        )
        gap=4
        cell=max(1,(width-64-9*gap)//10)
        for i,(name,label) in enumerate(performance):
            x=32+i*(cell+gap)
            if name is None:
                self.rect((x,bottom+49,cell,34))
                self.txt(label,x+4,bottom+60,self.palette.muted,self.tiny,maxwidth=cell-8)
            else:
                self.button(name,label,(x,bottom+49,cell,34))
