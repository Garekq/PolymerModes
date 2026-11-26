"""Человекочитаемое представление данных без изменения исходных записей."""
from html import escape

PARAMS={'nozzle':('Температура сопла','°C'),'bed':('Температура стола','°C'),'chamber':('Температура камеры','°C'),'diameter':('Диаметр сопла','мм'),'height':('Высота слоя','мм'),'width':('Ширина линии','мм'),'speed':('Скорость печати','мм/с'),
'nozzle_C':('Температура сопла','°C'),'bed_C':('Температура стола','°C'),'chamber_C':('Температура камеры','°C'),'speed_mm_s':('Скорость печати','мм/с'),'height_mm':('Высота слоя','мм'),'width_mm':('Ширина линии','мм'),'nozzle_diameter_mm':('Диаметр сопла','мм'),'infill_percent':('Заполнение','%'),'raster':('Направление линий',''),'during_print_annealer_C':('Нагреватель при печати','°C'),'during_print_annealer_off':('Нагреватель при печати выключен',''),'orientation':('Ориентация печати',''),'extrusion_multiplier':('Коэффициент экструзии',''),'IR_heaters_C':('Температура ИК-нагревателей','°C')}
RESULTS={'tensile_strength_MPa':('Прочность при растяжении','МПа'),'tensile_strength_plus_minus_MPa':('Прочность: отклонение ±','МПа'),'tensile_strength_sd_MPa':('Прочность: стандартное отклонение','МПа'),'ultimate_tensile_strength_MPa':('Предел прочности при растяжении','МПа'),'ultimate_tensile_strength_sd_MPa':('Предел прочности: стандартное отклонение','МПа'),'modulus_MPa':('Модуль упругости','МПа'),'modulus_plus_minus_MPa':('Модуль: отклонение ±','МПа'),'modulus_sd_MPa':('Модуль: стандартное отклонение','МПа'),'crystallinity_fraction':('Доля кристалличности',''),'Tg_C':('Температура стеклования','°C'),'porosity_percent':('Пористость','%'),'porosity_plus_minus_percent':('Пористость: отклонение ±','%'),'tensile_n':('Число образцов на растяжение',''),'individual_result':('Результат отдельного опыта',''),'study_finding':('Вывод исследования','')}
PROFILE={'name':('Название',''),'category':('Категория',''),'nozzle_min':('Сопло: нижняя граница','°C'),'nozzle_max':('Сопло: верхняя граница','°C'),'bed_min':('Стол: нижняя граница','°C'),'bed_max':('Стол: верхняя граница','°C'),'diameter':('Диаметр филамента','мм'),'tg':('Температура стеклования','°C'),'chamber_recommended':('Нагрев камеры рекомендован',''),'chamber_required':('Нагрев камеры обязателен',''),'heated_chamber':('Активный нагрев камеры',''),'chamber_max':('Предел камеры','°C'),'qmax':('Предельный расход','мм³/с'),'brand_confirmed':('Марка подтверждена пользователем',''),'source':('Источник',''),'origin':('Происхождение',''),'notes':('Примечание','')}

def value(v,unit=''):
    if v is None: return 'Не указано'
    if isinstance(v,bool): return 'Да' if v else 'Нет'
    if isinstance(v,float): s=f'{v:.4f}'.rstrip('0').rstrip('.')
    else: s=str(v)
    return s+(' '+unit if unit else '')

def pairs(data,labels):
    return [('row', f'{labels.get(k,(k,""))[0]}:  {value(v,labels.get(k,(k,""))[1])}') for k,v in data.items()]

def calculation(payload):
    r=payload['result']; p=payload['parameters']; m=payload['material']; printer=payload['printer']
    status=r['status']; tag='error' if status=='несовместимо' else 'warn' if status=='недостаточно данных' else 'good'
    out=[('title','Результат проверки'),(tag,status.upper()),('note','Предварительный расчёт. Результат не подтверждён печатью и испытаниями.'),('heading','Материал и оборудование'),('row','Материал:  '+m.get('name','Не указано')),('row','Принтер:  '+printer.get('name','Не указано')),('row','Приоритет:  '+payload.get('priority','Не указано')),('heading','Расчётные показатели'),('metric','Объёмный расход ≈ '+value(r.get('q'),'мм³/с')),('row','Скорость подачи филамента ≈ '+value(r.get('filament_speed'),'мм/с')),('row','Относительная высота слоя:  '+value(r.get('k'))),('heading','Введённые параметры')]+pairs(p,PARAMS)
    out.insert(10,('row','Предельная скорость по Qmax ≈ '+value(r.get('vmax_qmax'),'мм/с') if r.get('vmax_qmax') is not None else 'Предельная скорость по Qmax: данных недостаточно'))
    for key,title,kind in [('errors','Причины несовместимости','error'),('unknown','Недостающие данные','warn'),('warnings','Замечания и ограничения','note')]:
        if r.get(key): out.append(('heading',title)); out.extend((kind,'• '+str(x)) for x in r[key])
    if payload.get('additional_parameters'):
        from .parameters import describe
        out += [('heading','Дополнительные условия'),('warn','Данные пользователя: совместимость этих значений автоматически не проверяется и в слайсер они не передаются.')]
        out += [('row',f'{label}: {item} {unit}'.strip()) for label,item,unit in describe(payload['additional_parameters'])]
    return out

def literature(rec,q=None):
    out=[('title','Литературный эксперимент'),('note','Данные сторонних исследователей · не собственное испытание'),('heading','Исследование и образец'),('row','Запись:  '+rec['id']),('row','Исследование:  '+rec['study']),('row','Материал:  '+rec['material']),('row','Принтер:  '+rec['printer']),('row','Образец:  '+rec['specimen']),('heading','Опубликованные параметры печати')]+pairs(rec['parameters'],PARAMS)
    out += [('heading','Опубликованные результаты')]+pairs(rec['results'],RESULTS)
    out += [('heading','Расчёт программы'),('metric','Объёмный расход ≈ '+value(q,'мм³/с') if q is not None else 'Объёмный расход: недостаточно данных'),('note','Это инженерное приближение, не измеренный исследователями расход.'),('heading','Примечание'),('row',rec.get('notes','Не указано')),('heading','Источники')]+[('link',url) for url in rec['sources']]
    return out

def profile(data):
    from .profiles import fields
    names={key:(label,unit) for kind in ('material','printer') for key,label,unit,_ in fields(kind)}
    metadata=data.get('field_provenance') if isinstance(data.get('field_provenance'),dict) else {}
    out=[('title','Профиль'),('note','Данные профиля требуют проверки по фактическому оборудованию или партии. Общий источник профиля не приписывается отдельным полям автоматически.')]
    for key,val in data.items():
        if key=='field_provenance':continue
        label,unit=names.get(key,PROFILE.get(key,(key,'')))
        out.append(('row',f'{label}:  {value(val,unit)}'))
        if val is not None:
            meta=metadata.get(key) if isinstance(metadata.get(key),dict) else {}
            provenance=meta.get('origin') or 'не указано'; source=meta.get('source') or 'не указан'
            out.append(('note',f'  Происхождение: {provenance}; источник: {source}'))
    return out

def matrix_view(rows):
    out=[('title','Матрица испытаний 3 × 3'),('note','Предварительные сочетания. Недостаток данных не означает допустимость.')]
    for i,row in enumerate(rows,1):
        status=row['status']; tag='error' if status=='несовместимо' else 'warn' if status=='недостаточно данных' else 'good'
        out += [('heading',f'Опыт {i} · сопло {value(row["temperature"],"°C")} · расход {value(row["q"],"мм³/с")}'),(tag,status.capitalize()),('row','Расчётная скорость:  '+value(row['speed'],'мм/с'))]
        out += [('note','• '+reason) for reason in row.get('reasons',[])]
    return out

def plain(blocks): return '\n'.join(text for _,text in blocks)

def html_report(blocks):
    style='body{font:16px Segoe UI,Arial,sans-serif;color:#25374a;max-width:900px;margin:48px auto;padding:0 24px;line-height:1.5} h1{font-size:30px;color:#102840} h2{font-size:19px;margin-top:28px;border-bottom:1px solid #d9e3eb;padding-bottom:6px} p{margin:8px 0}.error{color:#ad303a}.warn{color:#9a6200}.good{color:#19745b}.metric{font-weight:700;color:#146a80;font-size:20px}.note{color:#566a7d}'
    body=[]
    for tag,text in blocks:
        element='h1' if tag=='title' else 'h2' if tag=='heading' else 'p'
        body.append(f'<{element} class="{escape(tag)}">{escape(text)}</{element}>')
    return '<!doctype html><html lang="ru"><meta charset="utf-8"><title>Диагностический отчёт</title><style>'+style+'</style><body>'+''.join(body)+'</body></html>'
