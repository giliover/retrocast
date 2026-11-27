"""Keyboard-only navigation with explicit modal focus."""
import pygame as pg
from retro_live.history_order import order_history, DEFAULT_AVAILABLE_FIRST

ACTIONS = {
    pg.K_RETURN:'play', pg.K_SPACE:'pause', pg.K_UP:'vol_up',
    pg.K_DOWN:'vol_down', pg.K_x:'stop', pg.K_s:'save', pg.K_m:'model',
    pg.K_l:'lang', pg.K_t:'theme', pg.K_i:'ui_language', pg.K_c:'sub',
    pg.K_h:'history', pg.K_q:'quality', pg.K_p:'priority', pg.K_v:'fps',
    pg.K_LEFTBRACKET:'fps_down', pg.K_RIGHTBRACKET:'fps_up',
    pg.K_a:'fps_auto', pg.K_MINUS:'delay_down', pg.K_EQUALS:'delay_up',
    pg.K_r:'whisper_retries', pg.K_COMMA:'whisper_timeout_down',
    pg.K_PERIOD:'whisper_timeout_up', pg.K_PAGEUP:'trans_prev',
    pg.K_PAGEDOWN:'trans_next', pg.K_END:'trans_live',
}

class KeyboardMixin:
    def handle_key(self, event):
        key = event.key
        if getattr(self, 'help_open', False):
            if key in (pg.K_ESCAPE, pg.K_k): self.help_open=False
            elif key in (pg.K_PAGEUP,pg.K_PAGEDOWN,pg.K_UP,pg.K_DOWN):
                step=-1 if key in (pg.K_PAGEUP,pg.K_UP) else 1
                self.help_page=max(0,min(self.help_pages-1,self.help_page+step))
            return
        if key == pg.K_k and not self.url_active and not self.history_open:
            self.help_open=True; self.help_page=0; self.help_pages=1
            return
        if self.video_fullscreen:
            if key in (pg.K_ESCAPE, pg.K_F11, pg.K_f): self.action('fullscreen')
            elif key == pg.K_x: self.action('stop'); self.action('fullscreen')
            elif key in (pg.K_SPACE,pg.K_c,pg.K_UP,pg.K_DOWN): self.action(ACTIONS[key])
            return
        if self.history_open:
            if key == pg.K_ESCAPE: self.history_open=False
            elif key == pg.K_o:
                self.history_available_first=not getattr(self, 'history_available_first', DEFAULT_AVAILABLE_FIRST)
                self.refresh_history_order()
            elif key in (pg.K_UP,pg.K_DOWN,pg.K_PAGEUP,pg.K_PAGEDOWN,pg.K_HOME,pg.K_END):
                self.move_history(key)
            elif key == pg.K_RETURN and self.history_rows:
                self.url=self.history_rows[self.history_index]
                self.history_open=False; self.url_active=True; self.show_suggestions=False
            return
        if self.url_active:
            if key in (pg.K_PAGEUP,pg.K_PAGEDOWN) and not (self.show_suggestions and self.suggestions):
                self.url_active=False; self.show_suggestions=False
                self.action(ACTIONS[key]); return
            if key == pg.K_ESCAPE:
                self.url_active=False; self.show_suggestions=False
            elif key == pg.K_TAB:
                self.accept_suggestion()
            elif key in (pg.K_UP,pg.K_DOWN,pg.K_PAGEUP,pg.K_PAGEDOWN) and self.show_suggestions and self.suggestions:
                step={pg.K_UP:-1,pg.K_DOWN:1,pg.K_PAGEUP:-5,pg.K_PAGEDOWN:5}[key]
                self.suggestion_idx=max(0,min(len(self.suggestions)-1,self.suggestion_idx+step))
                self.suggestions_page.page=self.suggestion_idx//self.suggestions_page.page_size
            elif key == pg.K_RETURN:
                if self.show_suggestions and self.suggestions: self.accept_suggestion()
                else: self.action('play')
            elif key == pg.K_BACKSPACE:
                self.url=self.url[:-1]; self.refresh_suggestions()
            elif key == pg.K_v and event.mod & pg.KMOD_CTRL:
                self.paste_source()
            elif event.unicode and event.unicode.isprintable() and len(self.url)<2048:
                self.url+=event.unicode; self.refresh_suggestions()
            return
        if key == pg.K_ESCAPE: self.running=False
        elif key in (pg.K_F11,pg.K_f): self.action('fullscreen')
        elif key == pg.K_F3: self.perf_visible=not self.perf_visible
        elif key == pg.K_u: self.url_active=True; self.refresh_suggestions()
        elif key in ACTIONS: self.action(ACTIONS[key])

    def refresh_history_order(self, reset=False):
        previous=getattr(self, "history_rows", ())
        index=self.history_index
        selected=previous[index] if not reset and 0 <= index < len(previous) else None
        status=getattr(self, "history_status", None)
        self.history_rows=order_history(self.history.items, status.state if status else lambda _: "unknown", getattr(self, "history_available_first", DEFAULT_AVAILABLE_FIRST))
        self.history_index=self.history_rows.index(selected) if selected in self.history_rows else min(index, max(0,len(self.history_rows)-1))
        if reset: self.history_index=0
        self.history_page.page=self.history_index//self.history_page.page_size

    def move_history(self, key):
        size=self.history_page.page_size
        count=len(self.history_rows)
        if not count: return
        if key == pg.K_HOME: self.history_index=0
        elif key == pg.K_END: self.history_index=count-1
        else:
            step={pg.K_UP:-1,pg.K_DOWN:1,pg.K_PAGEUP:-size,pg.K_PAGEDOWN:size}[key]
            self.history_index=max(0,min(count-1,self.history_index+step))
        self.history_page.page=self.history_index//size

    def paste_source(self):
        root=None
        try:
            import tkinter
            root=tkinter.Tk(); root.withdraw()
            self.url=(self.url+root.clipboard_get())[:2048]
            self.refresh_suggestions()
        except Exception:
            self.notice=self.tr('clipboard')
        finally:
            if root is not None: root.destroy()
