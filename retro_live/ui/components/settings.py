"""Read-only, localized keyboard hints."""

class SettingsMixin:
    def draw_settings(self, width, bottom):
        c=self.session.config
        t=self.tr
        strict=c.priority=='subtitle'
        state=t('paused' if self.session.video.paused else 'playing')
        playback=f"{state}  [{t('space')}] {t('pause_resume')}  [C] {t('sub_on' if self.subtitle else 'sub_off')}  [↑/↓] {t('volume')} {round(self.volume*100)}%  [F] {t('fullscreen')}"
        performance=f"[Q] {t('quality')}: {c.quality.upper()}  [P] {t(c.priority)}  [V] FPS: {c.fps_limit or t('auto')}  [M] {t('model')}: {c.model.upper()}  [-/=] {t('buffer')}: {c.delay}s"
        policy=f"[R] {t('retries')}: {c.whisper_retries if strict else 0}  [,/.] {t('timeout')}: {c.whisper_timeout if strict else 0:.1f}s"
        if not strict: policy+=f" ({t('off')})"
        # Two logical groups; wrap to two visual lines each as needed.
        appearance=f"[L] {t('speech')}: {t('auto') if c.language=='auto' else c.language.upper()}  [T] {t('theme')}: {t(self.preferences.theme)}  [I] {t('ui_lang')}: {self.preferences.language.upper()}"
        for i, line in enumerate((playback, appearance, performance, policy)):
            self.txt(line,32,bottom+7+i*20,self.palette.accent if i<2 else self.palette.text,self.tiny,maxwidth=width-64)
