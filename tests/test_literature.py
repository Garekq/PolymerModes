import unittest
from polymer.literature import all_records,calculated_flow,transfer_demonstration
from polymer.core import InputError

class LiteratureTests(unittest.TestCase):
 def test_counts_and_sources(self):
  rows=all_records(); self.assertEqual(len(rows),29); self.assertEqual(len({r['id'] for r in rows}),29)
  self.assertEqual(sum(r['id'].startswith('doyle-') for r in rows),18)
  self.assertTrue(all(r['sources'] and r['origin'].startswith('эксперимент') for r in rows))
 def test_specific_publication(self):
  rows={r['id']:r for r in all_records()}; a=rows['doyle-13']; self.assertEqual(a['parameters']['during_print_annealer_C'],390); self.assertEqual(a['results']['porosity_percent'],10.8); self.assertIsNone(calculated_flow(a))
  self.assertEqual(rows['mccrickard-0-100']['results']['ultimate_tensile_strength_MPa'],94.5)
 def test_flow_and_transfer(self):
  row=next(r for r in all_records() if r['id']=='shrestha-seqens'); self.assertAlmostEqual(calculated_flow(row),.8); self.assertAlmostEqual(transfer_demonstration(row,.6,.2)['new_speed_mm_s'],.8/.12)
  missing=all_records()[0]
  with self.assertRaises(InputError): transfer_demonstration(missing,.4,.2)
if __name__=='__main__':unittest.main()
