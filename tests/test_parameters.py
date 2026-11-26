import unittest
from polymer.parameters import parse,describe
class ParameterTests(unittest.TestCase):
    def test_optional_and_types(self):
        p=parse({'fan_percent':'0','walls':'2','first_layer_speed':'15,5','orientation':' XY ','infill_percent':''})
        self.assertEqual(p,{'first_layer_speed':15.5,'fan_percent':0.0,'walls':2,'orientation':'XY'})
        self.assertEqual(len(describe(p)),4)
    def test_invalid(self):
        for raw in ({'fan_percent':'101'}, {'infill_percent':'-1'}, {'walls':'1.2'}, {'walls':'0'}, {'first_layer_speed':'0'}, {'drying_temperature':'nan'}, {'wrong':'1'}):
            with self.subTest(raw=raw),self.assertRaises(ValueError): parse(raw)

if __name__=='__main__': unittest.main()
