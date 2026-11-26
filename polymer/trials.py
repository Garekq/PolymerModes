"""Планирование и оценка пользовательских измерений без прогнозирования свойств."""
import math

MEASURES = {
    'dimension_error': ('Абсолютное отклонение размера', 'мм'),
    'mass': ('Масса', 'г'),
    'wall_thickness': ('Толщина стенки', 'мм'),
    'warpage': ('Коробление', 'мм'),
    'tensile_strength': ('Прочность при растяжении', 'МПа'),
    'flexural_strength': ('Прочность при изгибе', 'МПа'),
    'moisture': ('Влагосодержание', '%'),
    'crystallinity': ('Степень кристалличности', '%'),
}
STEPS = {
    'flow': ('Стабильность экструзии', 'Одностенный образец; осмотрите дорожку и измерьте толщину стенки.'),
    'matrix': ('Температура и расход', 'Составьте матрицу 3 × 3; исключите несовместимые и непроверенные условия.'),
    'warpage': ('Коробление и адгезия', 'Измерьте коробление плоского образца и оцените адгезию.'),
    'dimensions': ('Размеры и поверхность', 'Измерьте калибровочный образец и зафиксируйте дефекты поверхности.'),
    'layers': ('Межслойное соединение', 'Сравните образцы с разной ориентацией по установленной методике.'),
    'mechanical': ('Механические испытания', 'При наличии оборудования испытайте образцы по выбранной методике.'),
    'repeat': ('Повторная проверка', 'Повторите выбранные условия и сопоставьте результаты с заданными критериями.'),
}
ORDERS = {
    'Сбалансированный': ('flow','matrix','warpage','dimensions','layers','mechanical','repeat'),
    'Межслойная прочность': ('flow','matrix','layers','mechanical','warpage','dimensions','repeat'),
    'Механическая прочность': ('flow','matrix','mechanical','layers','warpage','dimensions','repeat'),
    'Точность размеров': ('flow','matrix','dimensions','warpage','layers','mechanical','repeat'),
    'Минимальное коробление': ('flow','matrix','warpage','dimensions','layers','mechanical','repeat'),
    'Качество поверхности': ('flow','matrix','dimensions','warpage','layers','mechanical','repeat'),
    'Скорость изготовления': ('flow','matrix','dimensions','warpage','layers','mechanical','repeat'),
}

def plan(priority):
    if priority not in ORDERS: raise ValueError('Неизвестный приоритет изделия')
    return [dict(key=k,title=STEPS[k][0],description=STEPS[k][1]) for k in ORDERS[priority]]

def _value(raw,label,allow_zero=True):
    if raw is None or str(raw).strip() == '': return None
    try: value=float(str(raw).strip().replace(',','.'))
    except (TypeError,ValueError): raise ValueError(label+': требуется число')
    if not math.isfinite(value) or value < 0 or (not allow_zero and value == 0): raise ValueError(label+': требуется конечное неотрицательное число')
    return value

def evaluate(measurements,criteria):
    """Сравнение только заданных пользователем границ; незаданные критерии не считаются выполненными."""
    if set(measurements)-set(MEASURES) or set(criteria)-set(MEASURES): raise ValueError('Неизвестный показатель')
    rows=[]
    for key,(label,unit) in MEASURES.items():
        value=_value(measurements.get(key),label)
        bounds=criteria.get(key) or {}
        lo=_value(bounds.get('min'),label+' — минимум'); hi=_value(bounds.get('max'),label+' — максимум')
        if key in ('moisture','crystallinity') and any(x is not None and x>100 for x in (value,lo,hi)): raise ValueError(label+': значение не может превышать 100 %')
        if lo is not None and hi is not None and lo>hi: raise ValueError(label+': минимум больше максимума')
        if value is None and lo is None and hi is None: continue
        if lo is None and hi is None: status='критерий не задан'
        elif value is None: status='измерение отсутствует'
        elif (lo is not None and value<lo) or (hi is not None and value>hi): status='не соответствует'
        else: status='соответствует'
        rows.append(dict(key=key,label=label,unit=unit,value=value,min=lo,max=hi,status=status))
    if any(r['status']=='не соответствует' for r in rows): outcome='Есть несоответствия'
    elif not rows or any(r['status']!='соответствует' for r in rows): outcome='Недостаточно данных для оценки'
    else: outcome='Заданные критерии выполнены для введённых измерений'
    return {'rows':rows,'outcome':outcome,'disclaimer':'Оценены только заданные показатели одного протокола; подтверждение технологии, повторяемости и механических свойств требует соответствующих испытаний.'}

def confirm_repeats(calculation_id, calculation, records):
    """Проверяет локальную серию; не делает выводов за пределами заданных критериев."""
    from .slicer import export_guard, ProfileError
    if not calculation_id or not isinstance(calculation,dict): raise ValueError('Не указан исходный сохранённый расчёт.')
    try: export_guard(calculation['material'],calculation['printer'],calculation['parameters'])
    except (KeyError,TypeError,ValueError,ProfileError) as exc: raise ValueError('Невозможно подтвердить исходный режим: '+str(exc)) from exc
    if len(records)<2: raise ValueError('Нужны минимум два отдельных протокола повторных испытаний этого расчёта.')
    seen_ids=set(); seen_samples=set(); scope=None; criteria_signature=None; normalized=[]
    for record_id,trial in records:
        if record_id in seen_ids: raise ValueError('Один протокол нельзя учесть дважды.')
        seen_ids.add(record_id)
        if trial.get('calculation_id') != calculation_id or trial.get('calculation') != calculation: raise ValueError('Протокол относится к другому расчёту или его снимок изменён.')
        context=trial.get('context',{})
        for key,label in [('batch','партия материала'),('sample','образец и ориентация'),('sample_id','идентификатор образца'),('method','методика испытания'),('conditions','сушка и другие условия')]:
            if not isinstance(context.get(key),str) or not context[key].strip(): raise ValueError('В каждом протоколе необходимо указать: '+label+'.')
        sid=context['sample_id'].strip().casefold()
        if sid in seen_samples: raise ValueError('Идентификаторы повторных образцов должны различаться.')
        seen_samples.add(sid)
        current_scope=tuple(context[k].strip() for k in ('batch','sample','method','conditions'))
        if scope is None: scope=current_scope
        elif current_scope != scope: raise ValueError('Партия, описание и ориентация образцов, методика и условия должны совпадать во всех повторениях.')
        report=evaluate(trial.get('measurements',{}),trial.get('criteria',{}))
        rows=report['rows']
        if not rows or any(r['status']!='соответствует' for r in rows): raise ValueError('Все заданные показатели каждого повторения должны быть измерены и соответствовать критериям.')
        signature=tuple((r['key'],r['min'],r['max']) for r in rows)
        if criteria_signature is None: criteria_signature=signature
        elif signature != criteria_signature: raise ValueError('Показатели и критерии повторных испытаний должны совпадать.')
        normalized.append({'trial_id':record_id,'sample_id':context['sample_id'].strip(),'measurements':rows})
    return {'calculation_id':calculation_id,'calculation':calculation,'context':dict(zip(('batch','sample','method','conditions'),scope)), 'trials':normalized,'criteria':[{'key':key,'min':lo,'max':hi} for key,lo,hi in criteria_signature], 'status':'Подтверждено пользователем по указанным критериям', 'warning':'Отметка относится только к указанной партии, оборудованию, режиму, образцам, условиям, методике и измеренным критериям. Дополнительные условия не проверяются автоматически. Достаточность повторений и пригодность для ответственных изделий оценивает пользователь.'}
