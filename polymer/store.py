"""Локальное хранение записей. Исходные справочные профили не заменяют паспорт партии."""
import json, os, sqlite3
from pathlib import Path

URL='https://www.3dxtech.com/products/'
def material(name, category, low, high, bedlow, bedhigh, url, diameter=None, tg=None):
    return dict(name=name, category=category, nozzle_min=low, nozzle_max=high, bed_min=bedlow, bed_max=bedhigh, diameter=diameter, tg=tg, chamber_recommended=True, chamber_required=False, brand_confirmed=False, source=url, origin='справочный; для конкретной партии не подтверждён', notes='Режим сушки уточнить по паспорту партии: данные страниц производителя расходятся.')

MATERIALS=[
 material('PEEK — марка неизвестна','PEEK',None,None,None,None,''),
 material('PEKK — марка неизвестна','PEKK',None,None,None,None,''),
 material('PEI — марка неизвестна','PEI',None,None,None,None,''),
 material('3DXTECH ThermaX PEEK — пример','PEEK',400,480,140,180,URL+'thermax-peek-1'),
 material('3DXTECH ThermaX PEKK-A — пример','PEKK',345,375,120,140,URL+'pekk-a',tg=162),
 material('3DXTECH ThermaX PEI 9085 — пример','PEI',350,380,140,160,URL+'thermax-pei-9085',1.75,186),
 material('3DXTECH ThermaX PEI 1010 — пример','PEI',370,390,120,160,URL+'thermax-pei-1010',tg=217),
]
PRINTERS=[dict(name='Ultimaker 3 штатный',diameter=2.85,nozzle_max=280,bed_max=100,heated_chamber=False, chamber_max=None,qmax=None,source='https://um-support-files.ultimaker.com/manuals/user-manual/UM3/Ultimaker%203%20-%20User%20manual%20EN%20v1.4.pdf',notes='Одно сопло: 215×215×200 мм; два экструдера. Print core и длительный режим уточнить.'),dict(name='Условный высокотемпературный — НЕ реальное оборудование',diameter=1.75,nozzle_max=450,bed_max=170,heated_chamber=True,chamber_max=150,qmax=None,source='условная конфигурация',notes='Для демонстрации алгоритма; паспорт реального принтера не заменяет.')]

def default_path():
    root=Path(os.getenv('LOCALAPPDATA') or Path.home())/'PolymerModes'
    root.mkdir(parents=True,exist_ok=True)
    return root/'polymer.sqlite3'

class Store:
    def __init__(self,path=None):
        self.db=sqlite3.connect(str(path or default_path()))
        self.db.execute('CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY, kind TEXT NOT NULL, name TEXT NOT NULL, data TEXT NOT NULL, created TEXT DEFAULT CURRENT_TIMESTAMP)')
        if not self.db.execute('SELECT 1 FROM records WHERE kind="seed"').fetchone():
            for m in MATERIALS: self.save('material',m['name'],m)
            for p in PRINTERS: self.save('printer',p['name'],p)
            self.save('seed','seed',{})
        self.db.commit()
    def save(self,kind,name,data,id=None):
        s=json.dumps(data,ensure_ascii=False,allow_nan=False)
        if id: self.db.execute('UPDATE records SET name=?,data=? WHERE id=? AND kind=?',(name,s,id,kind))
        else: self.db.execute('INSERT INTO records(kind,name,data) VALUES (?,?,?)',(kind,name,s))
        self.db.commit()
    def all(self,kind):
        return [(i,n,json.loads(d)) for i,n,d in self.db.execute('SELECT id,name,data FROM records WHERE kind=? ORDER BY id',(kind,))]
    def delete(self,id):
        self.db.execute('DELETE FROM records WHERE id=?',(id,)); self.db.commit()
