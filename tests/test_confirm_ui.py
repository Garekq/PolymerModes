import copy, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import tkinter as tk
from tkinter import ttk
from polymer.core import analyze
from polymer.store import Store
from app import App
from tests.test_confirm import fixture

class ConfirmUiTests(unittest.TestCase):
    def test_confirm_and_reload(self):
        with tempfile.TemporaryDirectory() as directory:
            db=Path(directory)/'db.sqlite'; store=Store(db); app=App(store)
            try:
                calc,records=fixture(); calc['result']=analyze(calc['material'],calc['printer'],calc['parameters'])
                store.save('calculation','Тестовый расчёт',calc); calc_id=store.all('calculation')[-1][0]
                for _,t in records:
                    t['calculation_id']=calc_id; t['calculation']=copy.deepcopy(calc); store.save('trial','Повтор',t)
                app.refresh_history(); app.hist.selection_set(0); app.confirm_series(); app.update_idletasks()
                dialog=next(w for w in app.winfo_children() if w.winfo_class()=='Toplevel')
                box=next(w for w in dialog.winfo_children() if isinstance(w,tk.Listbox)); box.selection_set(0,'end')
                with patch('app.messagebox.askyesno',return_value=True),patch('app.messagebox.showerror') as error:
                    next(w for w in dialog.winfo_children() if isinstance(w,ttk.Button)).invoke(); error.assert_not_called()
                saved=store.all('confirmation'); self.assertEqual(len(saved),1); self.assertEqual(saved[0][2]['calculation_id'],calc_id)
                app.refresh_history(); app.hist.selection_clear(0,'end'); app.hist.selection_set(len(app.history)-1); app.show_history()
                self.assertIn('Подтверждено пользователем',app.history_view.get('1.0','end'))
            finally: app.destroy(); store.db.close()
            reopened=Store(db)
            try:self.assertEqual(len(reopened.all('confirmation')),1)
            finally:reopened.db.close()

if __name__=='__main__': unittest.main()
