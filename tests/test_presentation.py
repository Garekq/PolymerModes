import unittest
from polymer.presentation import calculation,literature,html_report,plain
from polymer.literature import all_records
from polymer.core import analyze

class PresentationTests(unittest.TestCase):
 def test_readable_unknown_and_source(self):
  record=all_records()[0]; text=plain(literature(record))
  self.assertIn('Литературный эксперимент',text); self.assertIn('Ширина линии:  Не указано',text)
  self.assertIn(record['sources'][0],text); self.assertNotIn('"nozzle_C"',text)
 def test_html_escapes_and_retains_status(self):
  p={'material':{'name':'<материал>'},'printer':{'name':'Принтер'},'priority':'Точность','parameters':{'nozzle':350},'result':{'status':'несовместимо','q':1.2,'filament_speed':None,'k':.5,'errors':['Сопло превышает предел'],'unknown':[],'warnings':[]}}
  page=html_report(calculation(p)); self.assertIn('НЕСОВМЕСТИМО',page); self.assertIn('Сопло превышает предел',page); self.assertIn('&lt;материал&gt;',page); self.assertNotIn('<материал>',page)
if __name__=='__main__':unittest.main()
