"""Поля библиотечных профилей и происхождение значений без предположений об источнике."""
import copy
import math

ORIGINS=('справочный','введён пользователем','расчётный','экспериментальный')
COMMON=(('name','Название','','text'),('diameter','Диаметр филамента','мм','positive'),('source','Общий источник','','text'),('notes','Примечание','','text'))
MATERIAL=(('category','Категория материала','','text'),('manufacturer','Производитель','','text'),('brand','Марка','','text'),('density','Плотность','г/см³','positive'),('tg','Температура стеклования','°C','positive'),('melting_temperature','Температура плавления','°C','positive'),('structure','Структура полимера','','text'),('nozzle_min','Сопло: минимум','°C','positive'),('nozzle_max','Сопло: максимум','°C','positive'),('bed_min','Стол: минимум','°C','positive'),('bed_max','Стол: максимум','°C','positive'),('chamber_min','Камера: минимум','°C','positive'),('chamber_max','Камера: максимум','°C','positive'),('chamber_recommended','Нагрев камеры рекомендован','','bool'),('chamber_required','Нагрев камеры обязателен','','bool'),('drying_temperature','Температура сушки','°C','positive'),('drying_duration','Продолжительность сушки','ч','positive'),('moisture_limit','Влагосодержание: предел','%','percent'),('rheology','Реологические характеристики','','text'),('shrinkage','Усадка и кристаллизация','','text'),('thermal_expansion','Тепловое расширение','','text'),('print_recommendations','Рекомендации по печати','','text'),('brand_confirmed','Марка и паспорт подтверждены','','bool'),('orca_filament_template','Имя шаблона Orca','','text'))
PRINTER=(('model','Модель','','text'),('nozzle_diameter','Диаметр сопла','мм','positive'),('nozzle_material','Материал сопла','','text'),('extruder','Тип и характеристики экструдера','','text'),('nozzle_max','Предел сопла','°C','positive'),('bed_max','Предел стола','°C','positive'),('chamber_max','Предел камеры','°C','positive'),('heated_chamber','Активный нагрев камеры','','bool'),('qmax','Предельный расход Qmax','мм³/с','positive'),('qmax_material','Материал испытания Qmax','','text'),('qmax_nozzle_diameter','Сопло испытания Qmax','мм','positive'),('qmax_temperature','Температура испытания Qmax','°C','positive'),('speed_max','Предельная скорость','мм/с','positive'),('acceleration_max','Предельное ускорение','мм/с²','positive'),('build_volume','Рабочая область','','text'),('slicer','Поддерживаемый слайсер','','text'),('limitations','Дополнительные ограничения','','text'),('cura_definition','Идентификатор Cura','','text'),('orca_printer','Вариант принтера Orca','','text'),('orca_process_template','Шаблон процесса Orca','','text'),('orca_filament_template','Шаблон материала Orca','','text'))
CRITICAL={'name','category','manufacturer','brand','diameter','nozzle_min','nozzle_max','bed_min','bed_max','chamber_min','chamber_max','chamber_recommended','chamber_required','source'}

def fields(kind):
    if kind=='material': return COMMON+MATERIAL
    if kind=='printer': return COMMON+PRINTER
    raise ValueError('Неизвестный тип профиля')

def parse(raw,kind,label):
    if raw is None or str(raw).strip()=='': return None
    if kind=='text': return str(raw).strip()
    if kind=='bool':
        if isinstance(raw,bool): return raw
        val=str(raw).strip().lower()
        if val in ('да','true'): return True
        if val in ('нет','false'): return False
        raise ValueError(label+': выберите «Да», «Нет» или оставьте пустым')
    try: val=float(str(raw).strip().replace(',','.'))
    except (ValueError,TypeError): raise ValueError(label+': требуется число')
    if not math.isfinite(val) or (kind=='positive' and val<=0) or (kind=='percent' and (val<0 or val>100)): raise ValueError(label+': недопустимое число')
    return val

def apply_updates(kind,original,updates):
    """Применяет редактированные поля и сохраняет метаданные без назначения источников старым значениям."""
    result=copy.deepcopy(original); meta=copy.deepcopy(result.get('field_provenance') or {})
    if not isinstance(meta,dict): raise ValueError('Некорректные метаданные происхождения')
    schema={key:(label,typ) for key,label,_,typ in fields(kind)}
    if set(updates)-set(schema): raise ValueError('Неизвестное поле профиля')
    changed=set()
    for key,entry in updates.items():
        label,typ=schema[key]; val=parse(entry.get('value'),typ,label)
        origin=(entry.get('origin') or '').strip(); source=(entry.get('source') or '').strip()
        old=result.get(key)
        if val != old: changed.add(key)
        if val is None:
            if key in meta: changed.add(key)
            result[key]=None; meta.pop(key,None); continue
        if origin not in ORIGINS: raise ValueError(label+': укажите происхождение значения')
        if origin=='справочный' and not source: raise ValueError(label+': укажите источник справочного значения')
        evidence={'origin':origin,'source':source or None}
        if meta.get(key)!=evidence: changed.add(key)
        result[key]=val; meta[key]=evidence
    if not isinstance(result.get('name'),str) or not result['name'].strip(): raise ValueError('Укажите название профиля')
    for prefix in ('nozzle','bed','chamber'):
        low=result.get(prefix+'_min'); high=result.get(prefix+'_max')
        if low is not None and high is not None:
            try:
                if float(low)>float(high): raise ValueError(prefix+': нижняя граница больше верхней')
            except TypeError as exc: raise ValueError(prefix+': некорректные границы') from exc
    reset=kind=='material' and bool(changed & CRITICAL) and result.get('brand_confirmed') is True
    if reset:
        result['brand_confirmed']=False; meta.pop('brand_confirmed',None)
    result['field_provenance']=meta
    return result,reset

def reconcile_json(kind, original, data):
    """JSON-редактор не должен сохранять прежний источник изменённого значения."""
    if not isinstance(data,dict): raise ValueError('Профиль должен быть объектом JSON')
    result=copy.deepcopy(data); schema={key:(label,typ) for key,label,_,typ in fields(kind)}
    for key,(label,typ) in schema.items():
        if key in result: result[key]=parse(result[key],typ,label)
    if not result.get('name'): raise ValueError('Укажите название профиля')
    metadata=result.get('field_provenance') or {}
    if not isinstance(metadata,dict): raise ValueError('field_provenance должен быть объектом')
    changed_values={key for key in schema if result.get(key)!=original.get(key)}
    previous=original.get('field_provenance') if isinstance(original.get('field_provenance'),dict) else {}
    changed=changed_values | {key for key in schema if metadata.get(key)!=previous.get(key)}
    for key in changed_values: metadata.pop(key,None)
    for key,item in metadata.items():
        if not isinstance(item,dict) or item.get('origin') not in ORIGINS: raise ValueError('Некорректное происхождение поля '+str(key))
        if item['origin']=='справочный' and not str(item.get('source') or '').strip(): raise ValueError('Для справочного поля '+str(key)+' нужен источник')
    for prefix in ('nozzle','bed','chamber'):
        low=result.get(prefix+'_min'); high=result.get(prefix+'_max')
        if low is not None and high is not None and low>high: raise ValueError(prefix+': нижняя граница больше верхней')
    reset=kind=='material' and bool(changed & CRITICAL) and result.get('brand_confirmed') is True
    if reset: result['brand_confirmed']=False; metadata.pop('brand_confirmed',None)
    result['field_provenance']=metadata
    return result,reset
