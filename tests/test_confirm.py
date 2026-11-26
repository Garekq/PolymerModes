import copy, unittest
from polymer.trials import confirm_repeats

def fixture():
    material=dict(name='Тест PLA',brand_confirmed=True,diameter=1.75,nozzle_min=190,nozzle_max=230,bed_min=40,bed_max=70,chamber_recommended=False,chamber_required=False)
    printer=dict(name='Тестовый принтер',source='пользователь',diameter=1.75,nozzle_max=260,bed_max=100,heated_chamber=False,qmax=None)
    params=dict(nozzle=210,bed=60,chamber=None,diameter=.4,height=.2,width=.4,speed=20)
    calc=dict(material=material,printer=printer,parameters=params,result={'errors':[],'unknown':[]})
    def trial(sample): return {'calculation_id':42,'calculation':copy.deepcopy(calc),'context':{'batch':'A','sample':'куб XY','sample_id':sample,'method':'измерение штангенциркулем','conditions':'сушка по паспорту'},'measurements':{'warpage':'0.3'},'criteria':{'warpage':{'max':'0.5'}}}
    return calc,[(101,trial('1')),(102,trial('2'))]

class ConfirmTests(unittest.TestCase):
    def test_valid_repeat_scope(self):
        calc,records=fixture(); result=confirm_repeats(42,calc,records)
        self.assertEqual(result['context']['batch'],'A'); self.assertEqual(len(result['trials']),2)
        self.assertEqual(result['criteria'],[{'key':'warpage','min':None,'max':.5}])
    def test_missing_repetition_and_duplicate(self):
        calc,records=fixture()
        for recs in [records[:1],[records[0],records[0]]]:
            with self.assertRaises(ValueError): confirm_repeats(42,calc,recs)
        records[1][1]['context']['sample_id']='1'
        with self.assertRaises(ValueError): confirm_repeats(42,calc,records)
    def test_scope_criteria_and_failed_values(self):
        for alter in ('batch','conditions','sample','method','criteria','measurement','calculation','missing'):
            calc,records=fixture(); t=records[1][1]
            if alter in ('batch','conditions','sample','method'): t['context'][alter]='different'
            elif alter=='criteria': t['criteria']['warpage']['max']='0.6'
            elif alter=='measurement': t['measurements']['warpage']='0.8'
            elif alter=='calculation': t['calculation']['parameters']['speed']=30
            else: t['context']['sample_id']=''
            with self.subTest(alter=alter),self.assertRaises(ValueError): confirm_repeats(42,calc,records)
    def test_unsafe_calculation_blocked(self):
        for alteration in ('unknown','hot','conditional'):
            calc,records=fixture()
            if alteration=='unknown': calc['material']['brand_confirmed']=False
            elif alteration=='hot': calc['parameters']['nozzle']=400
            else: calc['printer']['source']='условная конфигурация'
            for _,t in records:t['calculation']=copy.deepcopy(calc)
            with self.subTest(alteration=alteration),self.assertRaises(ValueError): confirm_repeats(42,calc,records)

if __name__=='__main__': unittest.main()
