import unittest
from retro_live.history_order import order_history
from test_keyboard_navigation import Harness, pg
from types import SimpleNamespace

class HistoryOrderTests(unittest.TestCase):
    def test_stable_partition(self):
        items=['a','b','c','d','e']
        states=dict(a='online', b='offline', c='checking', d='online', e='unknown')
        self.assertEqual(order_history(items,states.get,True),('d','a','e','c','b'))
        self.assertEqual(order_history(items,states.get,False),('e','d','c','b','a'))
    def test_selection_survives_reordering_and_enter(self):
        h=Harness(); states={'1':'online'}
        h.history_status=SimpleNamespace(state=lambda u:states.get(u,'offline'))
        h.key(pg.K_h); self.assertEqual(h.history_rows[0],'1'); h.key(pg.K_o); h.key(pg.K_DOWN); selected=h.history_rows[h.history_index]
        h.key(pg.K_o)
        self.assertEqual(h.history_rows[0],'1')
        self.assertEqual(h.history_rows[h.history_index],selected)
        states[selected]='online'; h.refresh_history_order()
        self.assertEqual(h.history_rows[h.history_index],selected)
        h.key(pg.K_RETURN); self.assertEqual(h.url,selected)
    def test_default_online_first(self):
        states={"old":"online", "new":"offline"}
        self.assertEqual(order_history(["old", "new"], states.get), ("old", "new"))
    def test_empty(self):
        h=Harness(); h.history.items=[]; h.key(pg.K_h); h.key(pg.K_o); h.key(pg.K_RETURN)
        self.assertEqual(h.history_rows,())
