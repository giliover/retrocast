import unittest
from retro_live.history_order import order_history
from test_keyboard_navigation import Harness, pg
from types import SimpleNamespace

class FakeStatus:
    def __init__(self):
        self.states={}; self.pending=set(); self.requests=[]
    def state(self,url): return self.states.get(url,'unknown')
    def cancel_queued(self): pass
    def prune(self,history): pass
    def request(self,rows,force=False): self.requests.append(tuple(rows)); self.pending=set(rows)

class HistoryOrderTests(unittest.TestCase):
    def test_stable_partition(self):
        items=['a','b','c','d','e']
        states=dict(a='online', b='offline', c='checking', d='online', e='unknown')
        self.assertEqual(order_history(items,states.get,True),('d','a','e','c','b'))
        self.assertEqual(order_history(items,states.get,False),('e','d','c','b','a'))
    def test_selection_survives_reordering_and_enter(self):
        h=Harness(); h.history_status=FakeStatus(); h.key(pg.K_h)
        self.assertEqual(h.history_status.requests,[('11','10','9','8','7')])
        h.key(pg.K_DOWN); selected=h.history_rows[h.history_index]
        h.history_status.states['7']='online'; h.history_status.pending.clear(); h.apply_history_results()
        self.assertEqual(h.history_rows[0],'7'); self.assertEqual(h.history_rows[h.history_index],selected)
        h.key(pg.K_RETURN); self.assertEqual(h.url,selected)
    def test_default_online_first(self):
        states={'old':'online','new':'offline'}
        self.assertEqual(order_history(['old','new'],states.get),('old','new'))
    def test_empty(self):
        h=Harness(); h.history.items=[]; h.key(pg.K_h); h.key(pg.K_RETURN)
        self.assertEqual(h.history_rows,())
    def test_page_only_and_no_request_on_selection(self):
        h=Harness(); h.history_status=FakeStatus(); h.key(pg.K_h); h.key(pg.K_DOWN)
        self.assertEqual(len(h.history_status.requests),1)
        h.key(pg.K_PAGEDOWN)
        self.assertEqual(h.history_status.requests[-1],('6','5','4','3','2'))
        h.history_status.pending.clear(); h.apply_history_results(); h.apply_history_results()
        self.assertEqual(len(h.history_status.requests),2)
        self.assertEqual(len(set(h.history_rows)),12)
    def test_search_all_history_on_enter_only(self):
        h=Harness(); h.history_status=FakeStatus(); h.key(pg.K_h); h.key(pg.K_SLASH)
        h.handle_key(SimpleNamespace(key=-1,mod=0,unicode='0'))
        self.assertEqual(len(h.history_status.requests),1)
        h.key(pg.K_RETURN)
        self.assertEqual(h.history_rows,('10','0'))
        self.assertEqual(h.history_status.requests[-1],('10','0'))
        h.key(pg.K_SLASH); h.key(pg.K_BACKSPACE); h.key(pg.K_RETURN)
        self.assertEqual(len(h.history_rows),12)
    def test_reopen_requests_current_page(self):
        h=Harness(); h.history_status=FakeStatus(); h.key(pg.K_h); h.key(pg.K_ESCAPE); h.key(pg.K_h)
        self.assertEqual(len(h.history_status.requests),2)

    def test_toggle_preserves_selection_and_requests_only_page(self):
        h=Harness(); h.history_status=FakeStatus(); h.history_status.states['7']='online'
        h.key(pg.K_h)
        self.assertEqual(h.history_rows[0],'7')
        h.key(pg.K_o)
        self.assertFalse(h.history_available_first)
        self.assertEqual(h.history_rows,tuple(str(i) for i in range(11,-1,-1)))
        self.assertEqual(h.history_rows[h.history_index],'7')
        self.assertEqual(h.history_status.requests[-1],('11','10','9','8','7'))
        h.history_status.pending.clear(); h.apply_history_results()
        self.assertEqual(h.history_rows[0],'11')
        h.key(pg.K_o)
        self.assertTrue(h.history_available_first)
        self.assertEqual(h.history_rows[0],'7')
        self.assertEqual(len(h.history_status.requests),3)

    def test_o_is_search_text_when_editing(self):
        h=Harness(); h.history_status=FakeStatus(); h.key(pg.K_h); h.key(pg.K_SLASH)
        h.handle_key(SimpleNamespace(key=pg.K_o,mod=0,unicode='o'))
        self.assertEqual(h.history_search_draft,'o')
        self.assertEqual(len(h.history_status.requests),1)
