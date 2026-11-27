import unittest
from types import SimpleNamespace
from retro_live.ui.components.text_input import TextCursor
from test_keyboard_navigation import Harness, pg
from test_history_order import FakeStatus

class TextInputTests(unittest.TestCase):
    def test_insert_and_delete_in_middle(self):
        c=TextCursor(); c.reset('abc'); c.edit('abc','left')
        self.assertEqual(c.edit('abc','insert','X'),'abXc')
        self.assertEqual(c.edit('abXc','backspace'),'abc')
        self.assertEqual(c.edit('abc','delete'),'ab')
    def test_select_replace_and_clear(self):
        c=TextCursor(); c.reset('abc'); c.edit('abc','all')
        self.assertEqual(c.edit('abc','insert','z'),'z')
        self.assertEqual(c.edit('z','clear'),'')
        self.assertEqual(c.position,0)
    def test_bounds_and_viewport(self):
        c=TextCursor(); c.reset('abcdefgh')
        self.assertEqual(c.viewport('abcdefgh',4),('fgh',3))
        c.edit('abcdefgh','home'); self.assertEqual(c.viewport('abcdefgh',4),('abcd',0))
        self.assertEqual(c.edit('abcdefgh','insert','x',8),'abcdefgh')
    def test_search_clear_only_queries_on_enter(self):
        h=Harness(); h.history_status=FakeStatus(); h.key(pg.K_h); h.key(pg.K_SLASH)
        h.handle_key(SimpleNamespace(key=-1,mod=0,unicode='1')); h.key(pg.K_RETURN)
        h.key(pg.K_SLASH); h.handle_key(SimpleNamespace(key=pg.K_u,mod=pg.KMOD_CTRL,unicode=''))
        self.assertEqual(h.history_search_draft,''); self.assertEqual(len(h.history_status.requests),2)
        h.key(pg.K_RETURN); self.assertEqual(len(h.history_rows),12); self.assertEqual(len(h.history_status.requests),3)
    def test_url_keyboard_selection(self):
        h=Harness(); h.url='abc'; h.url_active=True; h.refresh_suggestions=lambda:None
        h.key(pg.K_HOME); h.handle_key(SimpleNamespace(key=-1,mod=0,unicode='x'))
        self.assertEqual(h.url,'xabc')
        h.handle_key(SimpleNamespace(key=pg.K_a,mod=pg.KMOD_CTRL,unicode='')); h.key(pg.K_DELETE)
        self.assertEqual(h.url,'')
