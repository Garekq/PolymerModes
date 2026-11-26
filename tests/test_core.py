import unittest, tempfile
from pathlib import Path
from polymer.core import *
from polymer.store import Store, MATERIALS, PRINTERS

class CoreTests(unittest.TestCase):
 def setUp(self):
  self.m=dict(MATERIALS[5],brand_confirmed=True); self.pr=dict(PRINTERS[1]); self.p=dict(nozzle=365,bed=150,diameter=.4,height=.2,width=.4,speed=20)
 def test_formulas(self):
  self.assertAlmostEqual(flow(.4,.2,20),1.6); self.assertAlmostEqual(transfer(.4,.2,20,.6,.3),8.8888889); self.assertAlmostEqual(filament_speed(1.6,1.75),.6652,places=3)
 def test_valid(self): self.assertEqual(analyze(self.m,self.pr,self.p)['status'],'предварительно')
 def test_ultimaker(self):
  r=analyze(self.m,PRINTERS[0],self.p); self.assertEqual(r['status'],'несовместимо'); self.assertTrue(any('диаметр' in e.lower() for e in r['errors']))
 def test_unknown(self): self.assertEqual(analyze(MATERIALS[0],self.pr,self.p)['status'],'недостаточно данных')
 def test_temperature_suggestions(self):
  value,reason=suggest_temperature(self.m,self.pr,'nozzle'); self.assertEqual(value,365); self.assertIn('350–380',reason)
  value,reason=suggest_temperature(self.m,PRINTERS[0],'nozzle'); self.assertIsNone(value); self.assertIn('70 °C',reason)
  value,reason=suggest_temperature(self.m,PRINTERS[0],'bed'); self.assertIsNone(value); self.assertIn('40 °C',reason)
  value,reason=suggest_temperature(MATERIALS[0],self.pr,'nozzle'); self.assertIsNone(value); self.assertIn('диапазон температур материала',reason)
  value,reason=suggest_temperature(self.m,dict(self.pr,nozzle_max=None),'nozzle'); self.assertIsNone(value); self.assertIn('предел температуры принтера',reason)
  value,reason=suggest_temperature(dict(self.m,nozzle_min=390,nozzle_max=350),self.pr,'nozzle'); self.assertIsNone(value); self.assertIn('задан неверно',reason)
  value,reason=suggest_temperature(self.m,dict(self.pr,nozzle_max=370),'nozzle'); self.assertEqual(value,360)
 def test_qmax(self):
  self.pr.update(qmax=1,qmax_material=self.m['name'],qmax_nozzle_diameter=.4,qmax_temperature=365); r=analyze(self.m,self.pr,self.p); self.assertEqual(r['status'],'несовместимо'); self.assertAlmostEqual(r['vmax_qmax'],12.5)
  self.pr['qmax_temperature']=360; r=analyze(self.m,self.pr,self.p); self.assertEqual(r['status'],'предварительно'); self.assertIsNone(r['vmax_qmax']); self.assertTrue(any('Qmax не применён' in x for x in r['warnings']))
  self.pr['qmax']=None; self.assertIsNone(analyze(self.m,self.pr,self.p)['vmax_qmax'])
  for invalid in (0, -1, float('nan')):
   self.pr['qmax']=invalid
   with self.assertRaises(InputError): analyze(self.m,self.pr,self.p)
 def test_nonfinite(self):
  for v in [float('nan'),float('inf'),0,-1]:
   with self.assertRaises(InputError): flow(.4,.2,v)
 def test_matrix(self):
  rows=matrix(self.m,self.pr,self.p,[1,2,3]); self.assertEqual(len(rows),9); self.assertEqual(rows[0]['temperature'],350)
 def test_material_families(self):
  for i in (3,4,5,6):
   m=dict(MATERIALS[i],brand_confirmed=True,diameter=1.75); p=dict(self.p,nozzle=m['nozzle_min'],bed=m['bed_min']); self.assertEqual(analyze(m,self.pr,p)['status'],'предварительно')
 def test_store(self):
  with tempfile.TemporaryDirectory() as d:
   s=Store(Path(d)/'db.sqlite'); s.save('trial','test',{'x':1}); self.assertEqual(s.all('trial')[0][2]['x'],1); s.db.close(); t=Store(Path(d)/'db.sqlite'); self.assertEqual(len(t.all('trial')),1); t.db.close()
if __name__=='__main__':unittest.main()
