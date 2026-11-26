import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from polymer.store import Store
from app import App

class ExtraUiTests(unittest.TestCase):
 def test_save_and_validation(self):
  with tempfile.TemporaryDirectory() as directory:
   store=Store(Path(directory)/'test.db'); app=App(store)
   try:
    app.extra_vars['fan_percent'].set('15'); app.extra_vars['orientation'].set('XY'); app.calculate()
    data=store.all('calculation')[0][2]
    self.assertEqual(data['additional_parameters'],{'fan_percent':15.0,'orientation':'XY'})
    self.assertIn('Ориентация изделия: XY',app.output.get('1.0','end'))
    app.extra_vars['fan_percent'].set('101')
    with patch('app.messagebox.showerror') as error: app.calculate(); error.assert_called_once()
    self.assertEqual(len(store.all('calculation')),1)
   finally: app.destroy(); store.db.close()

if __name__=='__main__':unittest.main()
