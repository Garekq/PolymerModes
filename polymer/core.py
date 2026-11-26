"""Расчёты: только инженерные приближения, не подтверждение технологии."""
import math

class InputError(ValueError):
    pass

def number(x, name, positive=True):
    try:
        v = float(x)
    except (ValueError, TypeError):
        raise InputError(f'{name}: требуется число')
    if not math.isfinite(v) or (positive and v <= 0):
        raise InputError(f'{name}: требуется конечное положительное число')
    return v

def flow(b, h, v):
    return number(b, 'Ширина') * number(h, 'Высота') * number(v, 'Скорость')

def filament_speed(q, diameter):
    return 4 * number(q, 'Расход') / (math.pi * number(diameter, 'Диаметр филамента') ** 2)

def transfer(b1, h1, v1, b2, h2):
    return flow(b1, h1, v1) / (number(b2, 'Новая ширина') * number(h2, 'Новая высота'))

def suggest_temperature(material, printer, kind):
    """Возвращает предложение и объяснение без предположений о неизвестных пределах."""
    if kind not in ('nozzle', 'bed'):
        raise ValueError('Неизвестный тип температуры')
    low, high, limit = (material.get(kind + '_min'), material.get(kind + '_max'), printer.get(kind + '_max'))
    try:
        low = number(low, 'Нижняя граница материала') if low is not None else None
        high = number(high, 'Верхняя граница материала') if high is not None else None
        limit = number(limit, 'Предел принтера') if limit is not None else None
    except InputError:
        return None, 'В профиле указан некорректный температурный предел. Проверьте данные материала и принтера.'
    if low is not None and high is not None and low > high:
        return None, 'Диапазон материала задан неверно: нижняя граница выше верхней. Исправьте профиль материала.'
    if low is not None and limit is not None and low > limit:
        return None, (f'Принтер допускает до {limit:g} °C, а материалу требуется не менее {low:g} °C. '
                      f'Не хватает {low-limit:g} °C; совместимый диапазон отсутствует.')
    missing = []
    if low is None or high is None: missing.append('диапазон температур материала')
    if limit is None: missing.append('предел температуры принтера')
    if missing:
        return None, 'Не указан ' + ' и '.join(missing) + '. Заполните профиль по документации материала и оборудования.'
    upper = min(high, limit)
    selected = (low + upper) / 2
    return selected, f'Предложено {selected:g} °C — середина пересечения {low:g}–{upper:g} °C.'

def analyze(material, printer, p):
    errors, unknown, warnings = [], [], []
    for key, label in [('nozzle_min','нижняя температура сопла материала'),('nozzle_max','верхняя температура сопла материала'),('bed_min','нижняя температура стола материала'),('bed_max','верхняя температура стола материала'),('diameter','диаметр филамента материала')]:
        if material.get(key) is None: unknown.append('Неизвестна ' + label)
    for key, label in [('nozzle_max','предел сопла принтера'),('bed_max','предел стола принтера'),('diameter','диаметр филамента принтера')]:
        if printer.get(key) is None: unknown.append('Неизвестен ' + label)
    for low, high, label in [('nozzle_min','nozzle_max','сопла'),('bed_min','bed_max','стола')]:
        if material.get(low) is not None and material.get(high) is not None and material[low] > material[high]:
            errors.append('Некорректный диапазон ' + label)
    for typ, label in [('nozzle','Сопло'),('bed','Стол')]:
        lo, hi, limit = material.get(typ+'_min'), material.get(typ+'_max'), printer.get(typ+'_max')
        if lo is not None and limit is not None and lo > limit:
            errors.append(f'{label}: не хватает {lo-limit:g} °C до нижней границы материала')
        value = p.get(typ)
        if value is not None:
            value = number(value, label)
            if lo is not None and value < lo or hi is not None and value > hi:
                errors.append(f'{label}: {value:g} °C вне диапазона материала')
            if limit is not None and value > limit: errors.append(f'{label}: превышен предел принтера')
        else: unknown.append(f'Не задана температура: {label.lower()}')
    md, pd = material.get('diameter'), printer.get('diameter')
    if md is not None and pd is not None and abs(md-pd) > 0.1: errors.append(f'Диаметр филамента {md:g} и принтера {pd:g} мм несовместимы')
    if material.get('chamber_recommended') and printer.get('heated_chamber') is False:
        warnings.append('Производитель рекомендует нагреваемую камеру; её отсутствие требует оценки и не подтверждает пригодность')
    if material.get('chamber_required') and printer.get('heated_chamber') is not True:
        errors.append('Для материала требуется активный нагрев камеры')
    if printer.get('heated_chamber') is None: unknown.append('Неизвестно наличие нагрева камеры')
    if p.get('chamber') is not None:
        chamber = number(p['chamber'], 'Температура камеры')
        if printer.get('heated_chamber') is False: errors.append('Задана температура камеры, но активный нагрев отсутствует')
        cap=printer.get('chamber_max')
        if cap is None: unknown.append('Неизвестен предел температуры камеры принтера')
        elif chamber > number(cap, 'Предел камеры принтера'): errors.append('Температура камеры превышает предел принтера')
        lo,hi=material.get('chamber_min'),material.get('chamber_max')
        if lo is None or hi is None: warnings.append('Диапазон камеры материала не указан; пригодность температуры камеры не проверена')
        elif chamber < number(lo,'Нижняя температура камеры материала') or chamber > number(hi,'Верхняя температура камеры материала'): errors.append('Температура камеры вне диапазона материала')
    if not material.get('brand_confirmed'): unknown.append('Марка и паспорт реального филамента не подтверждены')
    q = flow(p.get('width'), p.get('height'), p.get('speed'))
    nozzle = number(p.get('diameter'), 'Диаметр сопла')
    h, b = number(p.get('height'), 'Высота'), number(p.get('width'), 'Ширина')
    if h > nozzle: errors.append('Высота слоя больше диаметра сопла')
    if b < h: warnings.append('Ширина линии меньше высоты слоя; проверьте геометрию')
    qmax = printer.get('qmax')
    vmax = None
    if qmax is None: warnings.append('Qmax для данных условий неизвестен; производительность экструдера не проверена')
    else:
        qmax=number(qmax,'Qmax')
        try:
            q_nozzle=number(printer.get('qmax_nozzle_diameter'),'Диаметр сопла испытания Qmax')
            q_temp=number(printer.get('qmax_temperature'),'Температура испытания Qmax')
            matches=(printer.get('qmax_material') == material.get('name') and bool(printer.get('qmax_material')) and abs(q_nozzle-nozzle)<1e-6 and p.get('nozzle') is not None and abs(q_temp-number(p['nozzle'],'Температура сопла'))<1e-6)
        except InputError: matches=False
        if matches:
            vmax=qmax/(b*h)
            if q > qmax: errors.append(f'Расход {q:.2f} превышает Qmax {qmax:g} мм³/с для заданных условий')
            warnings.append('Qmax указан пользователем для совпадающих материала, сопла и температуры; подтвердите условия его измерения')
        else: warnings.append('Qmax не применён: не указаны или не совпадают материал, диаметр сопла и температура его измерения; производительность не проверена')
    warnings.append('Расчёт не учитывает форму валика, скольжение и тепловую историю; нужна калибровка')
    return {'errors':errors, 'unknown':unknown, 'warnings':warnings, 'q':q, 'vmax_qmax':vmax, 'filament_speed': filament_speed(q, md) if md else None, 'k':h/nozzle, 'status':'несовместимо' if errors else 'недостаточно данных' if unknown else 'предварительно'}

def matrix(material, printer, p, q_levels):
    lo, hi = material.get('nozzle_min'), material.get('nozzle_max')
    if lo is None or hi is None: raise InputError('Нужен диапазон температуры материала')
    if len(q_levels) != 3: raise InputError('Нужны три уровня расхода')
    out = []
    for temp in [lo, (lo+hi)/2, hi]:
        for q in q_levels:
            x = dict(p, nozzle=temp, speed=number(q,'Расход')/(number(p.get('width'),'Ширина')*number(p.get('height'),'Высота')))
            result = analyze(material,printer,x)
            out.append({'temperature':temp,'q':float(q),'speed':x['speed'],'status':result['status'],'reasons':result['errors']+result['unknown']})
    return out
