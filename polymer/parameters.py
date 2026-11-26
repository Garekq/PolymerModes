"""Дополнительные условия: ввод пользователя, не переносятся в слайсер автоматически."""
import math

# key, label, unit, kind, lower bound, upper bound
FIELDS = (
 ('first_layer_speed','Скорость первого слоя','мм/с','positive',None,None),
 ('outer_wall_speed','Скорость внешней стенки','мм/с','positive',None,None),
 ('inner_wall_speed','Скорость внутренних стенок','мм/с','positive',None,None),
 ('infill_speed','Скорость заполнения','мм/с','positive',None,None),
 ('flow_factor','Коэффициент подачи','×','positive',None,None),
 ('acceleration','Ускорение печати','мм/с²','positive',None,None),
 ('retract_distance','Длина ретракта','мм','nonnegative',None,None),
 ('retract_speed','Скорость ретракта','мм/с','nonnegative',None,None),
 ('fan_percent','Интенсивность обдува','%','nonnegative',0,100),
 ('infill_percent','Плотность заполнения','%','nonnegative',0,100),
 ('walls','Количество стенок','шт.','integer',1,None),
 ('min_layer_time','Минимальное время слоя','с','nonnegative',None,None),
 ('drying_temperature','Температура сушки','°C','positive',None,None),
 ('drying_duration','Продолжительность сушки','ч','positive',None,None),
 ('infill_type','Тип заполнения','','text',None,None),
 ('orientation','Ориентация изделия','','text',None,None),
 ('bed_adhesion','Адгезия к столу','','text',None,None),
)

def parse(raw):
    known={field[0] for field in FIELDS}
    if set(raw)-known: raise ValueError('Неизвестный дополнительный параметр')
    result={}
    for key,label,unit,kind,low,high in FIELDS:
        value=raw.get(key,'')
        if value is None or str(value).strip()=='': continue
        if kind=='text': result[key]=str(value).strip(); continue
        try: value=float(str(value).strip().replace(',','.'))
        except (ValueError,TypeError): raise ValueError(label+': требуется число')
        if not math.isfinite(value) or (kind=='positive' and value<=0) or (kind in ('nonnegative','integer') and value<0): raise ValueError(label+': недопустимое число')
        if (low is not None and value<low) or (high is not None and value>high): raise ValueError(label+': значение вне допустимых границ ввода')
        if kind=='integer' and not value.is_integer(): raise ValueError(label+': требуется целое число')
        result[key]=int(value) if kind=='integer' else value
    return result

def describe(values):
    return [(label,values[key],unit) for key,label,unit,*_ in FIELDS if key in values]
