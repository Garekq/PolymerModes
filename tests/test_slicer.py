import io, json, unittest, zipfile
from pathlib import Path
from polymer import slicer
from polymer.store import MATERIALS, PRINTERS

def cura_template():
 b=io.BytesIO()
 with zipfile.ZipFile(b,'w') as z:
  for name,position in [('global',None),('extruder','0')]:
   meta='type = quality_changes\nquality_type = normal\nsetting_version = 25\n'+('position = '+position+'\n' if position else '')
   z.writestr(name,'[general]\nversion = 4\nname = User\ndefinition = target_printer\n[metadata]\n'+meta+'[values]\nmaterial_print_temperature = 360\nmachine_start_gcode = M999\n')
 return b.getvalue()

def orca_template(kind):
 d={'type':kind,'name':'Verified material template','inherits':'Target parent','from':'system','instantiation':'true','compatible_printers':['Target 0.4'],'filament_start_gcode':['M999'],'version':'2.3.0.0'}
 return json.dumps(d).encode()

class SlicerTests(unittest.TestCase):
 def setUp(self):
  self.material=dict(MATERIALS[5],brand_confirmed=True,chamber_min=70,chamber_max=130,orca_filament_template='Verified material template')
  self.printer=dict(PRINTERS[1],name='Target',source='пользователь',cura_definition='target_printer',orca_printer='Target 0.4')
  self.p={'nozzle':365,'bed':150,'chamber':100,'diameter':.4,'height':.2,'width':.4,'speed':20}
 def test_cura_roundtrip_and_strip(self):
  data=slicer.export_cura(cura_template(),self.material,self.printer,self.p); result=slicer.import_cura(data)
  self.assertEqual(result['values'],{k:self.p[k] for k in ('nozzle','bed','height','width','speed')}); self.assertNotIn(b'M999',data)
  with zipfile.ZipFile(io.BytesIO(data)) as z:
   self.assertNotIn(b'machine_start_gcode',b''.join(z.read(n) for n in z.namelist()))
   self.assertIn(b'material_bed_temperature = 150',z.read('global'))
   self.assertNotIn(b'material_bed_temperature',z.read('extruder'))
 def test_orca_roundtrip_and_strip(self):
  for kind,fields in [('process',('height','width')),('filament',('nozzle','bed'))]:
   data=slicer.export_orca(orca_template(kind),self.material,self.printer,self.p); result=slicer.import_orca(data)
   self.assertEqual(result['values'],{k:self.p[k] for k in fields}); self.assertNotIn(b'M999',data)
 def test_real_orca_252_templates(self):
  base=Path('tests/fixtures')
  process=(base/'orca252_process.json').read_bytes()
  self.assertEqual(slicer.import_orca(process)['values']['height'],.18)
  printer=dict(self.printer,orca_process_template='Polymer Test Source')
  generated=slicer.export_orca(process,self.material,printer,self.p)
  profile=json.loads(generated)
  self.assertEqual(profile['version'],'2.8.0.16'); self.assertEqual(profile['from'],'User'); self.assertNotIn('type',profile)
  self.assertEqual(profile['inherits'],'0.20mm Standard @BBL A1')
  filament=(base/'orca252_filament.json').read_bytes()
  self.assertEqual(slicer.import_orca(filament)['values'],{'nozzle':213.0,'bed':61.0})
 def test_cura_two_extruders(self):
  source=cura_template(); b=io.BytesIO()
  with zipfile.ZipFile(io.BytesIO(source)) as orig,zipfile.ZipFile(b,'w') as out:
   for entry in orig.infolist(): out.writestr(entry.filename,orig.read(entry.filename))
   out.writestr('second',orig.read('extruder').replace(b'position = 0',b'position = 1'))
  data=slicer.export_cura(b.getvalue(),self.material,self.printer,self.p)
  with zipfile.ZipFile(io.BytesIO(data)) as result:
   self.assertIn('second',result.namelist()); self.assertNotIn(b'material_print_temperature',result.read('second'))
 def test_real_cura_514_template(self):
  source=Path('tests/fixtures/cura514_ultimaker3.curaprofile').read_bytes()
  self.assertEqual(slicer.import_cura(source)['metadata']['definitions'],['ultimaker3'])
  printer=dict(self.printer,cura_definition='ultimaker3')
  data=slicer.export_cura(source,self.material,printer,self.p)
  self.assertEqual(slicer.import_cura(data)['values'],{k:self.p[k] for k in ('nozzle','bed','height','width','speed')})
  with zipfile.ZipFile(io.BytesIO(data)) as result:
   self.assertEqual(len(result.namelist()),3)
 def test_guard_conditions(self):
  with self.assertRaisesRegex(slicer.ProfileError,'Экспорт заблокирован'): slicer.export_cura(cura_template(),self.material,dict(self.printer,nozzle_max=280),self.p)
  with self.assertRaisesRegex(slicer.ProfileError,'камер'): slicer.export_cura(cura_template(),self.material,dict(self.printer,chamber_max=None),self.p)
  with self.assertRaisesRegex(slicer.ProfileError,'условн|Условн'): slicer.export_cura(cura_template(),self.material,PRINTERS[1],self.p)
  with self.assertRaisesRegex(slicer.ProfileError,'cura_definition'): slicer.export_cura(cura_template(),self.material,dict(self.printer,cura_definition='different'),self.p)
 def test_absent_inheritance_and_wrong_printer(self):
  bad=json.loads(orca_template('process')); bad['inherits']=''
  with self.assertRaises(slicer.ProfileError): slicer.export_orca(json.dumps(bad).encode(),self.material,self.printer,self.p)
  bad=json.loads(orca_template('process')); bad['compatible_printers']=['Different']
  with self.assertRaises(slicer.ProfileError): slicer.export_orca(json.dumps(bad).encode(),self.material,self.printer,self.p)
 def test_import_uncertainty(self):
  d={'type':'print','inherits':'parent','layer_height':'0.2','line_width':'120%','outer_wall_speed':'35'}
  result=slicer.import_orca(json.dumps(d).encode()); self.assertEqual(result['values'],{'height':.2}); self.assertTrue(result['warnings'])
  d={'type':'filament','nozzle_temperature':['350','360']}; self.assertNotIn('nozzle',slicer.import_orca(json.dumps(d).encode())['values'])
 def test_invalid_input(self):
  with self.assertRaises(slicer.ProfileError): slicer.import_cura(b'not zip')
  with self.assertRaises(slicer.ProfileError): slicer.import_orca(b'[]')
 def test_official_orca_template_import(self):
  data=Path('docs/slicer_examples/orca_official_process_template.json').read_bytes()
  result=slicer.import_orca(data)
  self.assertEqual(result['format'],'OrcaSlicer process'); self.assertEqual(result['values']['height'],.2); self.assertEqual(result['values']['width'],.42)
if __name__=='__main__':unittest.main()
