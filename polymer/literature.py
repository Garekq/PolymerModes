"""Published third-party experiments; null means not extracted/unknown, never assumed."""
from copy import deepcopy
from .core import flow, transfer, InputError

DOYLE='https://doi.org/10.3390/polym17111444'
ZENODO='https://zenodo.org/records/14864777'
SHRESTHA='https://doi.org/10.1002/mame.202500076'
MCCRICKARD='https://doi.org/10.3390/polym18010113'
REVIEW='https://doi.org/10.3390/polym12081665'
# Table 1: nozzle, bed, chamber, speed, during-print annealer (not post-anneal).
CONDITIONS=[(420,100,80,15,390),(455,100,80,15,None),(420,150,80,15,None),(455,150,80,15,390),(420,100,100,15,None),(455,100,100,15,390),(420,150,100,15,390),(455,150,100,15,None),(420,100,80,60,None),(455,100,80,60,390),(420,150,80,60,390),(455,150,80,60,None),(420,100,100,60,390),(455,100,100,60,None),(420,150,100,60,None),(455,150,100,60,390)]
# Table 2: reported values and ± as published; do not assume uncertainty type absent explicit statement.
RESULTS=[(79,7,2800,200,.23,158.8,2.6,1.0),(77,1,2730,60,.27,159.8,.21,.12),(85,2,2970,60,.25,160.8,.5,.2),(91,2,3020,60,.26,161.2,.9,.3),(72,5,2600,200,.22,158.4,.5,.2),(84,5,2970,90,.26,159.5,3,1.1),(86,3,3050,90,.27,161.1,.4,.2),(87.7,1.1,3300,600,.26,160.7,2.2,1.0),(73,2,2700,200,.20,158.3,.46,.07),(77,2,2700,50,.24,159.7,3.8,1.1),(79,3,2870,60,.24,160.9,1,.3),(88.7,1.4,3130,40,.23,160.8,2.7,.5),(72,4,2600,120,.24,159.6,10.8,1.4),(81,4,3010,90,.23,159.3,.7,.2),(75,2,2710,30,.25,160.9,2.8,.5),(86.7,1.4,3010,40,.26,161.1,1.6,.3)]

def make_records():
 records=[]
 for i,((nozzle,bed,chamber,speed,anneal),(strength,serr,modulus,merr,xc,tg,por,perr)) in enumerate(zip(CONDITIONS,RESULTS),1):
  records.append(dict(id=f'doyle-{i:02}', origin='эксперимент сторонних исследователей',study='Doyle et al. 2025, Table 1–2', material='PEEK EVONIK INFINAM 9359 F', category='PEEK', printer='CreatBot PEEK-300', specimen='ISO 527-2 тип 1BA, печать XY; DMTA 30×10×3 мм', parameters={'nozzle_C':nozzle,'bed_C':bed,'chamber_C':chamber,'speed_mm_s':speed,'height_mm':.2,'width_mm':None,'nozzle_diameter_mm':None,'infill_percent':100,'raster': '±45° между слоями','during_print_annealer_C':anneal,'during_print_annealer_off':anneal is None},results={'tensile_strength_MPa':strength,'tensile_strength_plus_minus_MPa':serr,'modulus_MPa':modulus,'modulus_plus_minus_MPa':merr,'crystallinity_fraction':xc,'Tg_C':tg,'porosity_percent':por,'porosity_plus_minus_percent':perr,'tensile_n':5},sources=[DOYLE,ZENODO],notes='Table 2; ± передано как в публикации. Не установлены ширина линии и сопло. Температура 390 °C относится к нагревателю при печати, а не температуре камеры или последующему отжигу.'))
 for i,(nozzle,bed,chamber,speed,strength,serr,mod,moderr) in enumerate([(440,150,100,15,91.4,.8,2900,200),(430,100,100,15,80.5,.8,2740,90)],1):
  records.append(dict(id=f'doyle-validation-{i}',origin='эксперимент сторонних исследователей',study='Doyle et al. 2025, Table 3–4',material='PEEK EVONIK INFINAM 9359 F',category='PEEK',printer='CreatBot PEEK-300',specimen='ISO 527-2 тип 1BA, XY',parameters={'nozzle_C':nozzle,'bed_C':bed,'chamber_C':chamber,'speed_mm_s':speed,'height_mm':.2,'width_mm':None,'nozzle_diameter_mm':None,'infill_percent':100,'during_print_annealer_off':True},results={'tensile_strength_MPa':strength,'tensile_strength_sd_MPa':serr,'modulus_MPa':mod,'modulus_sd_MPa':moderr},sources=[DOYLE],notes='Проверка модели авторов; не проверка нашей модели прочности.'))
 for ident,category,brand,nozzle,bed in [('seqens','PEKK','SEQENS IMPEKK-3D-F (60/40)',400,120),('pekk-c','PEKK','3DXTECH ThermaX PEKK-C (70/30)',400,120),('vestakeep','PEEK','EVONIK VESTAKEEP i4 3DF-T',440,140)]:
  records.append(dict(id='shrestha-'+ident,origin='эксперимент сторонних исследователей',study='Shrestha et al. 2025, Tables 1–2',material=brand,category=category,printer='CreatBot PEEK-300',specimen='DMA: 30×15×3 мм; сжатие: цилиндр Ø12,7×25,4 мм',parameters={'nozzle_C':nozzle,'bed_C':bed,'chamber_C':120,'speed_mm_s':20,'height_mm':.1,'width_mm':.4,'nozzle_diameter_mm':.4,'infill_percent':100,'raster':'±45°','orientation':'XY','extrusion_multiplier':1},results={'individual_result':None,'study_finding':'PEKK 3DA после отжига: кристалличность до 27%; результат зависит от условий отжига и не относится автоматически к остальным материалам' if ident=='seqens' else None},sources=[SHRESTHA],notes='Параметры печати из таблицы 2; данные отдельных режимов отжига и испытаний не оцифрованы.'))
 ratios=['100/0','80/20','70/30','60/40','50/50','40/60','20/80','0/100']
 strength=[(74.5,4.04),(75.6,2.4),(70.4,6.4),(70.9,2.4),(58.4,6.2),(82.6,5),(80.3,5.8),(94.5,5.97)]
 modulus=[(1428,41.8),(1338,40.9),(1198,65.9),(1112,38.3),(1039,78.4),(1280,43.5),(1238,36.7),(1342,32.2)]
 for ratio,(s,sd),(e,ed) in zip(ratios,strength,modulus):
  category='PEEK' if ratio=='100/0' else 'PEI' if ratio=='0/100' else 'PEEK/PEI смесь'
  records.append(dict(id='mccrickard-'+ratio.replace('/','-'),origin='эксперимент сторонних исследователей',study='McCrickard et al. 2026, Tables 2 and 5',material=f'PEEK/PEI {ratio} мас.%; лабораторный филамент: VESTAKEEP 2000FP / ULTEM 1010P200',category=category,printer='SpiderBot 4.0 HT',specimen='ISO 527-2 тип 5A',parameters={'nozzle_C':380,'bed_C':180,'chamber_C':75,'IR_heaters_C':450,'speed_mm_s':30,'height_mm':.2,'width_mm':None,'nozzle_diameter_mm':None,'infill_percent':100},results={'ultimate_tensile_strength_MPa':s,'ultimate_tensile_strength_sd_MPa':sd,'modulus_MPa':e,'modulus_sd_MPa':ed,'tensile_n':5},sources=[MCCRICKARD],notes='Из порошка изготовлен филамент; температуры IR-нагревателей и камеры различаются. Значения относятся к композициям исследования, а не к коммерческим катушкам.'))
 return records

RECORDS=make_records()
def all_records(): return deepcopy(RECORDS)
def calculated_flow(record):
 p=record['parameters']
 if any(p.get(k) is None for k in ('width_mm','height_mm','speed_mm_s')): return None
 return flow(p['width_mm'],p['height_mm'],p['speed_mm_s'])
def transfer_demonstration(record,new_width,new_height):
 p=record['parameters']
 if calculated_flow(record) is None: raise InputError('В статье не установлена ширина линии; расчёт расхода невозможен')
 return {'source_flow_mm3_s':calculated_flow(record),'new_speed_mm_s':transfer(p['width_mm'],p['height_mm'],p['speed_mm_s'],new_width,new_height),'origin':'расчётный','warning':'Условное сохранение расхода: оборудование, ограничения и свойства не подтверждены.'}
