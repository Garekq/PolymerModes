import tempfile, unittest
from pathlib import Path
from polymer.store import Store
from app import App
from tkinter import ttk
from unittest.mock import patch

class TrialUiTests(unittest.TestCase):
    def test_save_and_read_structured_trial(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(Path(directory)/'test.db'); app=App(store)
            try:
                app.calculate(); app.refresh_history(); app.hist.selection_set(0); app.add_trial(); app.update_idletasks()
                dialog=next(w for w in app.winfo_children() if w.winfo_class()=='Toplevel')
                entries=[w for w in dialog.winfo_children() if isinstance(w,ttk.Entry)]
                entries[9].insert(0,'0.8'); entries[11].insert(0,'0.5') # warpage measured and maximum
                entries[24].insert(0,'Партия А')
                with patch('app.messagebox.showerror') as error:
                    next(w for w in dialog.winfo_children() if isinstance(w,ttk.Button) and w.cget('text')=='Сохранить протокол').invoke(); error.assert_not_called()
                record=store.all('trial')[0][2]
                self.assertEqual(record['assessment']['outcome'],'Есть несоответствия')
                self.assertEqual(record['context']['batch'],'Партия А')
                app.refresh_history(); app.hist.selection_clear(0,'end'); app.hist.selection_set(len(app.history)-1); app.show_history()
                self.assertIn('не соответствует',app.history_view.get('1.0','end'))
            finally: app.destroy(); store.db.close()

if __name__=='__main__': unittest.main()
