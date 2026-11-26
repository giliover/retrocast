import ast
import unittest
from pathlib import Path
from retro_live.i18n import MESSAGES, translate_status

class TranslationTests(unittest.TestCase):
    def test_static_ui_keys_exist_in_each_language(self):
        root=Path(__file__).resolve().parents[1]/'retro_live/ui'
        keys=set()
        for path in root.rglob('*.py'):
            tree=ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node,ast.Call) and node.args and isinstance(node.args[0],ast.Constant) and isinstance(node.args[0].value,str):
                    if (isinstance(node.func,ast.Attribute) and node.func.attr=='tr') or (isinstance(node.func,ast.Name) and node.func.id=='t'):
                        keys.add(node.args[0].value)
                if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SHORTCUTS' for t in node.targets):
                    keys.update(label for _,label in ast.literal_eval(node.value))
        for lang,messages in MESSAGES.items():
            self.assertFalse(keys-messages.keys(),lang)
    def test_status_localization(self):
        self.assertEqual(translate_status('pt','PLAYING | BUFFER 15s'),'REPRODUZINDO | BUFFER: 15s')
        self.assertEqual(translate_status('es','STOPPED'),'DETENIDO')
        self.assertEqual(translate_status('en','SALVO: /tmp/x'),'SAVED: /tmp/x')
    def test_full_labels(self):
        self.assertEqual(MESSAGES['pt']['retries'],'RETENTATIVAS')
        self.assertEqual(MESSAGES['es']['retries'],'REINTENTOS')
        self.assertEqual(MESSAGES['en']['buffer'],'BUFFER')
