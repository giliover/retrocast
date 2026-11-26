import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import re
import unittest
from retro_live.pagination import Paginator
from retro_live.ring import Ring

# Exercise the actual keyboard dispatcher without requiring a graphical display.
root=Path(__file__).resolve().parents[1]/'retro_live/ui/components'
source=(root/'keyboard.py').read_text()
pg=SimpleNamespace(**{name:i for i,name in enumerate(sorted(set(re.findall(r'pg\.(K\w+)',source))),1)})
spec=importlib.util.spec_from_file_location('keyboard_under_test',root/'keyboard.py')
keyboard=importlib.util.module_from_spec(spec)
with patch.dict('sys.modules', {'pygame':pg}):
    spec.loader.exec_module(keyboard)

# Load controls with its actual relative imports but without importing UI __init__.
spec=importlib.util.spec_from_file_location('retro_live.ui.components.controls',root/'controls.py')
controls=importlib.util.module_from_spec(spec)
spec.loader.exec_module(controls)

class Harness(keyboard.KeyboardMixin, controls.ControlsMixin):
    def __init__(self):
        self.video_fullscreen=False; self.history_open=False; self.url_active=False
        self.show_suggestions=False; self.suggestions=[]; self.history_index=0
        self.history_page=Paginator(page_size=5); self.suggestions_page=Paginator(page_size=5)
        self.history=SimpleNamespace(items=[str(i) for i in range(12)])
        self.session=SimpleNamespace(lines=Ring(2000))
        for i in range(35): self.session.lines.append(str(i))
        self.transcript_page=Paginator(page_size=10); self.transcript_follow=True
    def key(self,key): self.handle_key(SimpleNamespace(key=key,mod=0,unicode=''))

class KeyboardTests(unittest.TestCase):
    def test_page_up_from_live(self):
        h=Harness(); h.key(pg.K_PAGEUP)
        self.assertEqual(h.transcript_page.page,2); self.assertFalse(h.transcript_follow)
        h.key(pg.K_PAGEUP); self.assertEqual(h.transcript_page.page,1)
        h.key(pg.K_PAGEDOWN); self.assertEqual(h.transcript_page.page,2)
        h.key(pg.K_PAGEDOWN); self.assertTrue(h.transcript_follow)
    def test_url_focus_without_suggestions(self):
        h=Harness(); h.url_active=True; h.key(pg.K_PAGEUP)
        self.assertFalse(h.url_active); self.assertEqual(h.transcript_page.page,2)
    def test_end_returns_live(self):
        h=Harness(); h.key(pg.K_PAGEUP); h.key(pg.K_END)
        self.assertTrue(h.transcript_follow); self.assertEqual(h.transcript_page.page,3)
    def test_history_selection(self):
        h=Harness(); h.key(pg.K_h); h.key(pg.K_PAGEDOWN); h.key(pg.K_DOWN)
        h.key(pg.K_RETURN); self.assertEqual(h.url,'5'); self.assertFalse(h.history_open)
    def test_suggestions_own_pagination(self):
        h=Harness(); h.url_active=True; h.show_suggestions=True; h.suggestions=list(range(12)); h.suggestion_idx=0
        h.key(pg.K_PAGEDOWN); self.assertEqual(h.suggestion_idx,5); self.assertTrue(h.transcript_follow)
    def test_performance_key_map(self):
        for key,action in [(pg.K_p,'priority'),(pg.K_q,'quality'),(pg.K_v,'fps'),(pg.K_a,'fps_auto'),(pg.K_r,'whisper_retries'),(pg.K_COMMA,'whisper_timeout_down'),(pg.K_PERIOD,'whisper_timeout_up')]:
            h=Harness(); calls=[]; h.action=calls.append; h.key(key); self.assertEqual(calls,[action])

    def test_help_modal_isolated_navigation(self):
        h=Harness(); h.key(pg.K_k); self.assertTrue(h.help_open)
        h.help_pages=3; h.key(pg.K_PAGEDOWN); self.assertEqual(h.help_page,1)
        h.key(pg.K_PAGEDOWN); h.key(pg.K_PAGEDOWN); self.assertEqual(h.help_page,2)
        self.assertTrue(h.transcript_follow)
        h.key(pg.K_ESCAPE); self.assertFalse(h.help_open)
        h.key(pg.K_PAGEUP); self.assertFalse(h.transcript_follow)
    def test_help_key_in_url_is_text(self):
        h=Harness(); h.url_active=True; h.url=''; h.refresh_suggestions=lambda:None
        h.handle_key(SimpleNamespace(key=pg.K_k,mod=0,unicode='k'))
        self.assertEqual(h.url,'k'); self.assertFalse(getattr(h,'help_open',False))
    def test_help_in_fullscreen(self):
        h=Harness(); h.video_fullscreen=True; h.key(pg.K_k); self.assertTrue(h.help_open)
        h.key(pg.K_ESCAPE); self.assertFalse(h.help_open); self.assertTrue(h.video_fullscreen)
