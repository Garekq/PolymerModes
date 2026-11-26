import unittest
from polymer.trials import evaluate, plan

class TrialTests(unittest.TestCase):
    def test_all_criteria_pass(self):
        r=evaluate({'warpage':'0,3','mass':'2'}, {'warpage':{'max':'0.5'},'mass':{'min':'1','max':'3'}})
        self.assertTrue(r['outcome'].startswith('Заданные критерии выполнены'))
        self.assertEqual([x['status'] for x in r['rows']],['соответствует','соответствует'])
    def test_missing_and_failed(self):
        r=evaluate({'warpage':'.8'}, {'warpage':{'max':'.5'},'mass':{'min':'1'}})
        self.assertEqual(r['outcome'],'Есть несоответствия')
        self.assertEqual({x['key']:x['status'] for x in r['rows']},{'mass':'измерение отсутствует','warpage':'не соответствует'})
        self.assertEqual(evaluate({'warpage':'.2'}, {})['outcome'],'Недостаточно данных для оценки')
        self.assertEqual(evaluate({}, {})['outcome'],'Недостаточно данных для оценки')
    def test_invalid(self):
        for values,criteria in [({'mass':'NaN'},{}),({'mass':'-1'},{}),({'moisture':'101'},{}),({}, {'mass':{'min':3,'max':2}})]:
            with self.assertRaises(ValueError): evaluate(values,criteria)
    def test_priorities_change_plan(self):
        dims=[x['key'] for x in plan('Точность размеров')]
        layers=[x['key'] for x in plan('Межслойная прочность')]
        self.assertLess(dims.index('dimensions'),dims.index('layers'))
        self.assertLess(layers.index('layers'),layers.index('dimensions'))
        self.assertEqual(dims[-1],'repeat')
        with self.assertRaises(ValueError): plan('неизвестно')

if __name__=='__main__': unittest.main()
