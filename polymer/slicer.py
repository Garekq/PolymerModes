"""Консервативный обмен явными значениями профилей; без переноса машинного G-code."""
import configparser
import io
import json
import math
import zipfile
from .core import analyze, number, InputError

class ProfileError(ValueError): pass

CURA_MAP={'material_print_temperature':'nozzle','material_bed_temperature':'bed','layer_height':'height','line_width':'width','speed_print':'speed'}
ORCA_PROCESS={'layer_height':'height','line_width':'width'}
ORCA_FILAMENT={'nozzle_temperature':'nozzle'}
PLATES={'hot_plate_temp','eng_plate_temp','textured_plate_temp','cool_plate_temp','textured_cool_plate_temp'}
LIMIT=2_000_000

def _numeric(raw):
    if isinstance(raw,list):
        if len(raw)!=1: return None
        raw=raw[0]
    if isinstance(raw,bool) or not isinstance(raw,(int,float,str)): return None
    try:
        val=float(raw)
        return val if math.isfinite(val) and val>0 else None
    except ValueError: return None

def read_cura(content):
    if len(content)>LIMIT: raise ProfileError('Архив профиля слишком велик')
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            info=z.infolist()
            if not info or len(info)>16 or sum(i.file_size for i in info)>LIMIT: raise ProfileError('Некорректный или слишком большой архив')
            if len({i.filename for i in info})!=len(info): raise ProfileError('Повторяющиеся имена контейнеров в архиве')
            containers=[]
            for item in info:
                if item.is_dir() or '/' in item.filename or '\\' in item.filename: raise ProfileError('Неожиданный путь в архиве')
                parser=configparser.ConfigParser(interpolation=None,strict=True)
                parser.read_string(z.read(item).decode('utf-8-sig'))
                if not parser.has_section('general') or not parser.has_section('metadata') or not parser.has_section('values'): raise ProfileError('Не хватает разделов контейнера Cura')
                if parser.get('metadata','type',fallback='')!='quality_changes': raise ProfileError('Поддерживаются только quality_changes профили Cura')
                if parser.get('general','version',fallback='')!='4': raise ProfileError('Поддерживается версия контейнера Cura 4')
                containers.append((item.filename,parser))
            return containers
    except (zipfile.BadZipFile, UnicodeDecodeError, configparser.Error, RuntimeError, KeyError) as e: raise ProfileError('Не удалось прочитать профиль Cura: '+str(e)) from e

def import_cura(content):
    containers=read_cura(content); candidates={}; skipped=[]
    for _,cfg in containers:
        for key,target in CURA_MAP.items():
            if cfg.has_option('values',key):
                v=_numeric(cfg['values'][key])
                if v is None: skipped.append(key+' (не число или выражение)')
                else: candidates.setdefault(target,[]).append(v)
    values={}
    for key,vals in candidates.items():
        if all(v==vals[0] for v in vals): values[key]=vals[0]
        else: skipped.append(key+' (разные значения в контейнерах)')
    return {'format':'Cura','values':values,'warnings':skipped+['Импортированы только явно заданные числовые значения; наследование и другие параметры не проверены.'], 'metadata':{'definitions':sorted({p.get('general','definition',fallback='') for _,p in containers})}}

def read_orca(content):
    if len(content)>LIMIT: raise ProfileError('JSON слишком велик')
    try: data=json.loads(content.decode('utf-8-sig'))
    except (UnicodeDecodeError,ValueError) as e: raise ProfileError('Некорректный JSON Orca: '+str(e)) from e
    if not isinstance(data,dict): raise ProfileError('Ожидался объект профиля Orca')
    kind=data.get('type')
    if not kind:
        if 'filament_settings_id' in data: kind='filament'
        elif 'print_settings_id' in data or 'process_settings_id' in data: kind='process'
    if kind=='print': kind='process'
    if kind not in ('process','filament'): raise ProfileError('Поддерживаются профили Orca процесса или материала, не принтера')
    return kind,data

def import_orca(content,plate_key='hot_plate_temp'):
    if plate_key not in PLATES: raise ProfileError('Неизвестная поверхность стола')
    kind,data=read_orca(content); mapping=ORCA_PROCESS if kind=='process' else dict(ORCA_FILAMENT,**{plate_key:'bed'})
    values={}; skipped=[]
    for key,target in mapping.items():
        if key in data:
            v=_numeric(data[key])
            if v is None: skipped.append(key+' (не число, процент или несколько значений)')
            else: values[target]=v
    warnings=['Импортированы только явные значения; скорость Orca по отдельным элементам не приравнивается к общей скорости. Наследование не раскрывается.']+skipped
    if data.get('inherits'): warnings.append('Родительский профиль не загружен: '+str(data['inherits']))
    return {'format':'OrcaSlicer '+kind,'values':values,'warnings':warnings,'metadata':{'compatible_printers':data.get('compatible_printers'),'inherits':data.get('inherits')}}

def export_guard(material,printer,p):
    if printer.get('source')=='условная конфигурация' or 'условный' in str(printer.get('name','')).lower(): raise ProfileError('Условный принтер предназначен только для демонстрации; экспорт заблокирован.')
    if material.get('brand_confirmed') is not True: raise ProfileError('Подтвердите марку и паспорт фактического материала в профиле.')
    if not isinstance(material.get('chamber_recommended'),bool) and not isinstance(material.get('chamber_required'),bool): raise ProfileError('Укажите требования материала к нагреву камеры.')
    try: result=analyze(material,printer,p)
    except (ValueError,TypeError) as e: raise ProfileError('Невозможно проверить параметры: '+str(e)) from e
    if result['errors'] or result['unknown']: raise ProfileError('Экспорт заблокирован: '+'; '.join(result['errors']+result['unknown']))
    if material.get('chamber_required') or material.get('chamber_recommended'):
        if printer.get('heated_chamber') is not True: raise ProfileError('Нужны сведения о подходящем активном нагреве камеры.')
        try:
            lo=number(material.get('chamber_min'),'Нижняя температура камеры материала')
            hi=number(material.get('chamber_max'),'Верхняя температура камеры материала')
            cap=number(printer.get('chamber_max'),'Предел камеры принтера')
            chamber=number(p.get('chamber'),'Температура камеры')
        except InputError as e: raise ProfileError('Необходимы данные камеры для материала и принтера: '+str(e)) from e
        if lo>hi or not lo<=chamber<=hi or chamber>cap: raise ProfileError('Температура камеры вне известных пределов материала или принтера.')
    return result

def export_cura(template,material,printer,p):
    export_guard(material,printer,p)
    ident=printer.get('cura_definition')
    if not isinstance(ident,str) or not ident.strip(): raise ProfileError('В профиле принтера укажите cura_definition целевого принтера.')
    containers=read_cura(template)
    globals_=[x for x in containers if not x[1].has_option('metadata','position')]
    extruders=[x for x in containers if x[1].has_option('metadata','position')]
    if len(globals_)!=1 or not extruders: raise ProfileError('Нужен шаблон Cura с одним глобальным контейнером и хотя бы одним экструдером.')
    positions=[cfg.get('metadata','position') for _,cfg in extruders]
    if any(not p.isdigit() for p in positions) or len(set(positions))!=len(positions) or '0' not in positions:
        raise ProfileError('Шаблон Cura должен содержать уникальные номера экструдеров, включая экструдер 0.')
    for _,cfg in containers:
        if cfg.get('general','definition',fallback='')!=ident: raise ProfileError('Шаблон Cura не соответствует cura_definition выбранного принтера.')
        if not cfg.get('metadata','quality_type',fallback='') or not cfg.get('metadata','setting_version',fallback=''): raise ProfileError('В шаблоне отсутствуют quality_type или setting_version.')
    if len({cfg.get('metadata','quality_type') for _,cfg in containers})!=1 or len({cfg.get('metadata','setting_version') for _,cfg in containers})!=1:
        raise ProfileError('Контейнеры Cura относятся к разным типам качества или версиям настроек.')
    name='PolymerModes PRELIMINARY'
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for fname,original in globals_+sorted(extruders,key=lambda pair:int(pair[1].get('metadata','position'))):
            cfg=configparser.ConfigParser(interpolation=None)
            cfg['general']={'version':'4','name':name,'definition':ident}
            cfg['metadata']={k:original['metadata'][k] for k in ('type','quality_type','setting_version','position','intent_category') if original.has_option('metadata',k)}
            cfg.add_section('values')
            global_keys={'layer_height','material_bed_temperature'}
            is_global=not cfg.has_option('metadata','position')
            is_first=cfg.get('metadata','position',fallback='')=='0'
            mapping={k:v for k,v in CURA_MAP.items() if (is_global and k in global_keys) or (is_first and k not in global_keys)}
            for key,param in mapping.items(): cfg['values'][key]=f'{float(p[param]):g}'
            out=io.StringIO(); cfg.write(out); z.writestr(fname,out.getvalue().encode('utf-8'))
    return buffer.getvalue()

def export_orca(template,material,printer,p,plate_key='hot_plate_temp'):
    export_guard(material,printer,p)
    target=printer.get('orca_printer')
    if not isinstance(target,str) or not target.strip(): raise ProfileError('В профиле принтера укажите orca_printer — точное имя варианта Orca.')
    if plate_key not in PLATES: raise ProfileError('Неизвестная поверхность стола')
    kind,data=read_orca(template)
    compat=data.get('compatible_printers')
    if data.get('compatible_printers_condition'): raise ProfileError('Условие совместимости шаблона не проверяется программой.')
    if compat is not None and (not isinstance(compat,list) or target not in compat): raise ProfileError('Шаблон не указывает выбранный вариант принтера.')
    if data.get('instantiation')=='false': raise ProfileError('Шаблон не является выбираемым профилем.')
    if not isinstance(data.get('name'),str) or not data['name'].strip(): raise ProfileError('В шаблоне не указано имя профиля; его доступность необходимо проверить в Orca.')
    if not isinstance(data.get('inherits'),str) or not data['inherits'].strip(): raise ProfileError('В шаблоне не указан родительский профиль; его доступность необходимо проверить в Orca.')
    version=data.get('version')
    if not isinstance(version,str) or len(version.split('.')) not in (3,4) or not all(x.isdigit() for x in version.split('.')): raise ProfileError('Используйте пользовательский шаблон Orca с указанной версией профиля, сохранённый в целевом слайсере.')
    if compat is None and printer.get('orca_process_template' if kind=='process' else 'orca_filament_template') != data['name']:
        raise ProfileError('Подтвердите имя целевого шаблона в профиле принтера (orca_process_template или orca_filament_template).')
    if kind=='filament':
        expected=material.get('orca_filament_template')
        identity=data.get('name') or (data.get('filament_settings_id') or [None])[0]
        if not expected or expected!=identity: raise ProfileError('В профиле материала укажите orca_filament_template с точным названием шаблона этого материала.')
    # Не копируем параметры движения, G-code и чужие технологические значения из шаблона.
    metadata=['inherits','filament_id','version','is_custom_defined']
    out={k:data[k] for k in metadata if k in data}
    out.update({'name':'PolymerModes PRELIMINARY','from':'User'})
    if kind=='process':
        out['print_settings_id']='PolymerModes PRELIMINARY'
        for key,param in ORCA_PROCESS.items(): out[key]=f'{float(p[param]):g}'
    else:
        out['filament_settings_id']=['PolymerModes PRELIMINARY']
        out['nozzle_temperature']=[f'{float(p["nozzle"]):g}']; out[plate_key]=[f'{float(p["bed"]):g}']
    return json.dumps(out,ensure_ascii=False,indent=2).encode('utf-8')
