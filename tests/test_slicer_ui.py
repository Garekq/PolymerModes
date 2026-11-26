import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from polymer.store import Store
from app import App

class SlicerUiTests(unittest.TestCase):
 def test_import_to_form_and_export_blocked(self):
  with tempfile.TemporaryDirectory() as d:
   store=Store(Path(d)/'test.db'); app=App(store)
   try:
    path=Path(d)/'source.json'; path.write_text(json.dumps({'type':'process','layer_height':'0.18','line_width':'0.42'}),encoding='utf8')
    with patch('app.filedialog.askopenfilename',return_value=str(path)): app.import_slicer()
    app.apply_slicer(); self.assertEqual(app.vars['height'].get(),'0.18'); self.assertEqual(app.vars['width'].get(),'0.42')
    with patch('app.filedialog.askopenfilename',return_value=str(path)),patch('app.messagebox.showerror') as err,patch('app.filedialog.asksaveasfilename') as save:
     app.export_slicer('Orca'); err.assert_called_once(); save.assert_not_called()
   finally: app.destroy(); store.db.close()
if __name__=='__main__':unittest.main()
