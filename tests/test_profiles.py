import unittest
from polymer.profiles import apply_updates,reconcile_json
from polymer.store import MATERIALS

class ProfileTests(unittest.TestCase):
 def test_field_sources_and_unknown_legacy(self):
  p,reset=apply_updates('material',{'name':'PEI','nozzle_min':350}, {'nozzle_max':{'value':'380','origin':'справочный','source':'паспорт партии'}})
  self.assertEqual(p['nozzle_max'],380); self.assertEqual(p['field_provenance']['nozzle_max']['source'],'паспорт партии')
  self.assertNotIn('nozzle_min',p['field_provenance']); self.assertFalse(reset)
  with self.assertRaises(ValueError):apply_updates('material',{'name':'PEI'}, {'nozzle_max':{'value':'380','origin':'справочный','source':''}})
 def test_reset_confirmation_on_critical_change(self):
  original={'name':'PEI','diameter':1.75,'brand_confirmed':True,'field_provenance':{'diameter':{'origin':'справочный','source':'old'}}}
  p,reset=apply_updates('material',original,{'diameter':{'value':'2.85','origin':'введён пользователем','source':''}})
  self.assertTrue(reset); self.assertFalse(p['brand_confirmed']); self.assertEqual(p['field_provenance']['diameter']['origin'],'введён пользователем')
  self.assertEqual(original['diameter'],1.75)
  p,reset=apply_updates('material',p,{'brand_confirmed':{'value':'Да','origin':'введён пользователем','source':''}})
  self.assertTrue(p['brand_confirmed']); self.assertFalse(reset)
 def test_json_stale_provenance_and_ranges(self):
  old={'name':'PEI','diameter':1.75,'brand_confirmed':True,'field_provenance':{'diameter':{'origin':'справочный','source':'old'}}}
  new=dict(old,diameter=2.85)
  p,reset=reconcile_json('material',old,new)
  self.assertTrue(reset); self.assertFalse(p['brand_confirmed']); self.assertNotIn('diameter',p['field_provenance'])
  for bad in ({'nozzle_min':400,'nozzle_max':300},{'nozzle_min':'nan'},{'brand_confirmed':'maybe'},{'moisture_limit':101}):
   with self.subTest(bad=bad),self.assertRaises(ValueError):reconcile_json('material',{},dict(name='x',**bad))
 def test_empty_and_preserve_unknown_fields(self):
  p,_=apply_updates('printer',{'name':'A','custom':{'x':1},'qmax':2}, {'qmax':{'value':'','origin':'','source':''}})
  self.assertIsNone(p['qmax']); self.assertEqual(p['custom'],{'x':1})
  with self.assertRaises(ValueError):apply_updates('printer',{'name':'A'}, {'qmax':{'value':'3','origin':'','source':''}})

if __name__=='__main__':unittest.main()
