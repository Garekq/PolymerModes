import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from tkinter import ttk
from polymer.store import Store
from app import App

class ProfileUiTests(unittest.TestCase):
 def test_create_view_and_reload(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'db.sqlite'; store=Store(path); app=App(store)
   try:
    app.edit_profile_fields(True); app.update()
    dialog=next(w for w in app.winfo_children() if w.winfo_class()=='Toplevel')
    holder=next(w for w in dialog.winfo_children() if isinstance(w,ttk.Frame) and any(isinstance(x,ttk.Treeview) for x in w.winfo_children()))
    tree=next(w for w in holder.winfo_children() if isinstance(w,ttk.Treeview))
    editor=next(w for w in dialog.winfo_children() if isinstance(w,ttk.Frame) and any(isinstance(x,ttk.Combobox) for x in w.winfo_children()))
    entries=[w for w in editor.winfo_children() if isinstance(w,ttk.Entry) and not isinstance(w,ttk.Combobox)]
    comb=next(w for w in editor.winfo_children() if isinstance(w,ttk.Combobox))
    tree.selection_set('name'); app.update(); entries[0].insert(0,'Мой материал'); comb.set('введён пользователем')
    tree.selection_set('diameter'); app.update(); entries[0].delete(0,'end'); entries[0].insert(0,'1,75'); comb.set('справочный'); entries[1].insert(0,'паспорт партии')
    with patch('app.messagebox.showinfo'),patch('app.messagebox.showerror') as error:
     next(w for w in dialog.winfo_children() if isinstance(w,ttk.Button)).invoke(); error.assert_not_called()
    profile=store.all('material')[-1][2]; self.assertEqual(profile['diameter'],1.75); self.assertEqual(profile['field_provenance']['diameter']['source'],'паспорт партии')
    app.listbox.selection_set(app.listbox.size()-1); app.preview_profile(); self.assertIn('паспорт партии',app.profile_view.get('1.0','end')); self.assertNotIn('field_provenance:',app.profile_view.get('1.0','end'))
   finally:app.destroy(); store.db.close()
   reopened=Store(path)
   try:self.assertEqual(reopened.all('material')[-1][2]['name'],'Мой материал')
   finally:reopened.db.close()

if __name__=='__main__':unittest.main()
