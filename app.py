import csv, html, json, tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from polymer.core import analyze, transfer, matrix, InputError, suggest_temperature
from polymer.store import Store
from polymer.literature import all_records, calculated_flow, transfer_demonstration
from polymer import presentation as view
from polymer import slicer
from polymer import trials as trial_tools
from polymer import parameters as extra_parameters
from polymer import profiles as profile_tools

class App(tk.Tk):
    def __init__(self, store=None):
        super().__init__(); self.title('Подбор режимов высокотемпературной FFF-печати'); self.geometry('1180x760'); self.minsize(900,600)
        self.store=store or Store(); self.result=None; self.payload=None
        style=ttk.Style(self)
        if 'clam' in style.theme_names(): style.theme_use('clam')
        style.configure('.',font=('Segoe UI',10),background='#f2f6f9',foreground='#253b4d')
        style.configure('TButton',padding=(10,7))
        style.configure('TNotebook.Tab',padding=(14,9))
        style.map('TNotebook.Tab',background=[('selected','#ffffff')],foreground=[('selected','#126b80')])
        self.tabs=ttk.Notebook(self); self.tabs.pack(fill='both',expand=True)
        self.calc=ttk.Frame(self.tabs,padding=12); self.tabs.add(self.calc,text='Подбор и перенос')
        self.extra=ttk.Frame(self.tabs,padding=12); self.tabs.add(self.extra,text='Доп. параметры')
        self.library=ttk.Frame(self.tabs,padding=12); self.tabs.add(self.library,text='Библиотека')
        self.trials=ttk.Frame(self.tabs,padding=12); self.tabs.add(self.trials,text='Испытания')
        self.exchange=ttk.Frame(self.tabs,padding=12); self.tabs.add(self.exchange,text='Cura / OrcaSlicer')
        self.literature=ttk.Frame(self.tabs,padding=12); self.tabs.add(self.literature,text='Литературные данные')
        self.help=ttk.Frame(self.tabs,padding=12); self.tabs.add(self.help,text='Справка')
        self.build_calc(); self.build_extra(); self.build_library(); self.build_history(); self.build_exchange(); self.build_literature(); self.build_help(); self.refresh()
    def build_extra(self):
        ttk.Label(self.extra,text='Дополнительные условия режима',font=('Segoe UI',15,'bold')).pack(anchor='w')
        ttk.Label(self.extra,text='Неизвестные значения оставьте пустыми. Они сохраняются в расчёте как данные пользователя, но не проверяются на совместимость и не передаются в профиль слайсера.',wraplength=1050).pack(anchor='w',pady=(6,12))
        frame=ttk.Frame(self.extra); frame.pack(fill='both',expand=True); self.extra_vars={}
        for index,(key,label,unit,*_) in enumerate(extra_parameters.FIELDS):
            column=(index//9)*2; row=index%9
            ttk.Label(frame,text=label+(f', {unit}' if unit else '')).grid(row=row,column=column,sticky='w',padx=(0,8),pady=8)
            variable=tk.StringVar(); self.extra_vars[key]=variable; ttk.Entry(frame,textvariable=variable,width=22).grid(row=row,column=column+1,sticky='w',padx=(0,30),pady=8)
    def build_calc(self):
        left=ttk.Frame(self.calc); left.pack(side='left',fill='y',padx=(0,12)); right=ttk.Frame(self.calc); right.pack(side='left',fill='both',expand=True)
        self.sel={}
        for i,(key,label) in enumerate([('material','Материал'),('printer','Целевой принтер'),('source','Исходный принтер')]):
            ttk.Label(left,text=label).grid(row=i,column=0,sticky='w'); box=ttk.Combobox(left,state='readonly',width=40); box.grid(row=i,column=1,sticky='ew',pady=3); self.sel[key]=box
        self.vars={}
        fields=[('nozzle','Сопло, °C',''),('bed','Стол, °C',''),('chamber','Камера, °C',''),('diameter','Диаметр сопла, мм','0.4'),('height','Высота слоя, мм','0.2'),('width','Ширина линии, мм','0.4'),('speed','Скорость, мм/с','20'),('old_height','Исходная высота, мм','0.2'),('old_width','Исходная ширина, мм','0.4'),('old_speed','Исходная скорость, мм/с','20'),('q_levels','Уровни Q, мм³/с через ;','1;2;3')]
        for i,(key,label,initial) in enumerate(fields,3):
            ttk.Label(left,text=label).grid(row=i,column=0,sticky='w'); v=tk.StringVar(value=initial); ttk.Entry(left,textvariable=v,width=20).grid(row=i,column=1,sticky='w',pady=2); self.vars[key]=v
        pr=3+len(fields); ttk.Label(left,text='Приоритет').grid(row=pr,column=0,sticky='w'); self.priority=ttk.Combobox(left,state='readonly',values=['Сбалансированный','Межслойная прочность','Механическая прочность','Точность размеров','Минимальное коробление','Качество поверхности','Скорость изготовления']); self.priority.current(0); self.priority.grid(row=pr,column=1,sticky='w')
        for j,(title,cmd) in enumerate([('Предложить температуры',self.suggest),('Проверить и сохранить',self.calculate),('Перенести расход',self.do_transfer),('Матрица 3 × 3',self.do_matrix),('План испытаний по приоритету',self.show_plan),('Экспорт отчёта / JSON / CSV',self.export)]): ttk.Button(left,text=title,command=cmd).grid(row=pr+1+j,column=0,columnspan=2,sticky='ew',pady=2)
        ttk.Label(right,text='Результат и ограничения',font=('Segoe UI',13,'bold')).pack(anchor='w',pady=(0,8)); self.output=self.readable_text(right)
        self.render(self.output,[('title','Начните с выбора материала'),('note','Примеры материалов не являются данными предприятия. Сначала подтвердите паспорт партии и заполните профиль.')])
    def build_library(self):
        top=ttk.Frame(self.library); top.pack(fill='x'); self.kind=ttk.Combobox(top,state='readonly',values=['Материалы','Принтеры']); self.kind.current(0); self.kind.pack(side='left'); self.kind.bind('<<ComboboxSelected>>',lambda e:self.refresh_list())
        for title,cmd in [('Изменить поля',lambda:self.edit_profile_fields(False)),('Новый по полям',lambda:self.edit_profile_fields(True)),('JSON',self.load_profile),('Новый JSON',self.new_profile),('Сохранить JSON',self.save_profile),('Удалить',self.delete_profile)]: ttk.Button(top,text=title,command=cmd).pack(side='left',padx=2)
        frame=ttk.Frame(self.library); frame.pack(fill='both',expand=True,pady=8); self.listbox=tk.Listbox(frame,width=42,font=('Segoe UI',10),borderwidth=0,selectbackground='#d7edf1',selectforeground='#124f60'); self.listbox.pack(side='left',fill='y',padx=(0,10)); self.listbox.bind('<<ListboxSelect>>',lambda e:self.preview_profile())
        self.profile_tabs=ttk.Notebook(frame); self.profile_tabs.pack(side='left',fill='both',expand=True)
        preview=ttk.Frame(self.profile_tabs); edit=ttk.Frame(self.profile_tabs)
        self.profile_tabs.add(preview,text='Просмотр'); self.profile_tabs.add(edit,text='Редактирование JSON')
        self.profile_view=self.readable_text(preview); self.editor=tk.Text(edit,wrap='none',font=('Consolas',10)); self.editor.pack(fill='both',expand=True); self.edit_id=None
        ttk.Label(self.library,text='Выберите профиль и нажмите «Изменить поля». Неизвестные значения оставляйте пустыми; JSON доступен для расширенного редактирования.').pack(anchor='w')
    def edit_profile_fields(self,new=False):
        kind=self.kind_key(); chosen=self.listbox.curselection()
        if not new and not chosen: return messagebox.showwarning('Профиль не выбран','Выберите профиль в библиотеке.')
        ident=None if new else self.items[chosen[0]][0]
        original={} if new else self.items[chosen[0]][2]
        dialog=tk.Toplevel(self); dialog.title('Поля профиля материала' if kind=='material' else 'Поля профиля принтера'); dialog.transient(self); dialog.geometry('930x690'); dialog.minsize(750,550)
        ttk.Label(dialog,text='Выберите поле, укажите значение, происхождение и при необходимости источник. Пустое значение означает «неизвестно».',wraplength=870).pack(anchor='w',padx=12,pady=8)
        holder=ttk.Frame(dialog); holder.pack(fill='both',expand=True,padx=12)
        tree=ttk.Treeview(holder,columns=('value','origin'),show='tree headings',height=12,selectmode='browse')
        tree.heading('#0',text='Характеристика'); tree.heading('value',text='Значение'); tree.heading('origin',text='Происхождение')
        tree.column('#0',width=290,stretch=True); tree.column('value',width=220,stretch=True); tree.column('origin',width=180,stretch=True)
        scroll=ttk.Scrollbar(holder,orient='vertical',command=tree.yview); tree.configure(yscrollcommand=scroll.set); scroll.pack(side='right',fill='y'); tree.pack(side='left',fill='both',expand=True)
        editor=ttk.Frame(dialog); editor.pack(fill='x',padx=12,pady=8); editor.columnconfigure(1,weight=1)
        title=tk.StringVar(value='Выберите поле'); value=tk.StringVar(); origin=tk.StringVar(); source=tk.StringVar()
        ttk.Label(editor,textvariable=title,font=('Segoe UI',10,'bold')).grid(row=0,column=0,columnspan=2,sticky='w',pady=3)
        ttk.Label(editor,text='Значение').grid(row=1,column=0,sticky='w'); inputbox=ttk.Entry(editor,textvariable=value); inputbox.grid(row=1,column=1,sticky='ew',pady=2)
        ttk.Label(editor,text='Происхождение').grid(row=2,column=0,sticky='w'); originbox=ttk.Combobox(editor,textvariable=origin,state='readonly',values=('',)+profile_tools.ORIGINS); originbox.grid(row=2,column=1,sticky='ew',pady=2)
        ttk.Label(editor,text='Источник').grid(row=3,column=0,sticky='w'); ttk.Entry(editor,textvariable=source).grid(row=3,column=1,sticky='ew',pady=2)
        ttk.Label(editor,text='Для логических полей введите «Да» или «Нет». Для справочных значений источник обязателен.').grid(row=4,column=0,columnspan=2,sticky='w',pady=4)
        schema={key:(label,unit,typ) for key,label,unit,typ in profile_tools.fields(kind)}; pending={}; active=[None]; baseline=[None]
        metadata=original.get('field_provenance') or {}
        if not isinstance(metadata,dict): metadata={}
        def shown(v): return '' if v is None else 'Да' if v is True else 'Нет' if v is False else str(v)
        for key,(label,unit,typ) in schema.items():
            item=metadata.get(key) if isinstance(metadata.get(key),dict) else {}
            tree.insert('', 'end',iid=key,text=label+(f', {unit}' if unit else ''),values=(shown(original.get(key)),item.get('origin') or 'не указано'))
        def commit_current():
            key=active[0]
            if key is None:return
            current=(value.get(),origin.get(),source.get())
            if current!=baseline[0]:
                pending[key]={'value':current[0],'origin':current[1],'source':current[2]}
                tree.set(key,'value',current[0]); tree.set(key,'origin',current[1] or 'не указано')
        def selected(event=None):
            selection=tree.selection()
            if not selection:return
            key=selection[0]
            if key==active[0]:return
            commit_current(); active[0]=key; label,unit,typ=schema[key]; title.set(label+(f', {unit}' if unit else ''))
            item=metadata.get(key) if isinstance(metadata.get(key),dict) else {}
            entry=pending.get(key,{'value':shown(original.get(key)),'origin':item.get('origin') or '', 'source':item.get('source') or ''})
            value.set(entry['value']); origin.set(entry['origin']); source.set(entry['source']); baseline[0]=(value.get(),origin.get(),source.get())
        tree.bind('<<TreeviewSelect>>',selected)
        def save():
            commit_current()
            try:
                data,reset=profile_tools.apply_updates(kind,original,pending)
                self.store.save(kind,data['name'],data,ident); dialog.destroy(); self.refresh()
                messagebox.showinfo('Профиль сохранён','Профиль сохранён.'+(' После изменения данных материала подтверждение марки сброшено; повторно проверьте паспорт и подтвердите его отдельным действием.' if reset else ''))
            except (ValueError,TypeError) as exc: messagebox.showerror('Ошибка профиля',str(exc),parent=dialog)
        ttk.Button(dialog,text='Сохранить профиль',command=save).pack(pady=(0,10))
    def build_history(self):
        top=ttk.Frame(self.trials); top.pack(fill='x');
        for title,cmd in [('Обновить',self.refresh_history),('Открыть запись',self.show_history),('Добавить испытание',self.add_trial),('Подтвердить по повторам',self.confirm_series),('Экспорт',self.export_trial)]: ttk.Button(top,text=title,command=cmd).pack(side='left',padx=3)
        frame=ttk.Frame(self.trials); frame.pack(fill='both',expand=True,pady=8)
        self.hist=tk.Listbox(frame,width=48,font=('Segoe UI',10),borderwidth=0,selectbackground='#d7edf1',selectforeground='#124f60'); self.hist.pack(side='left',fill='y',padx=(0,10)); self.hist.bind('<<ListboxSelect>>',lambda e:self.show_history())
        self.history_view=self.readable_text(frame)
    def build_exchange(self):
        self.imported_profile=None
        bar=ttk.Frame(self.exchange); bar.pack(fill='x',pady=(0,8))
        ttk.Label(bar,text='Поверхность стола Orca:').pack(side='left')
        self.orca_plate=ttk.Combobox(bar,state='readonly',width=26,values=['hot_plate_temp','eng_plate_temp','textured_plate_temp','cool_plate_temp','textured_cool_plate_temp']); self.orca_plate.current(0); self.orca_plate.pack(side='left',padx=6)
        actions=ttk.Frame(self.exchange); actions.pack(fill='x',pady=(0,10))
        for label,action in [('Импорт профиля',self.import_slicer),('Перенести данные в подбор',self.apply_slicer),('Экспорт Cura',lambda:self.export_slicer('Cura')),('Экспорт Orca',lambda:self.export_slicer('Orca'))]: ttk.Button(actions,text=label,command=action).pack(side='left',padx=(0,5))
        self.exchange_view=self.readable_text(self.exchange)
        self.render(self.exchange_view,[('title','Обмен со слайсерами'),('note','Импорт считывает только явно заданные параметры. Для экспорта нужен профиль-шаблон целевого принтера и подтверждённые данные материала и оборудования.'),('row','Подробности: docs/ОБМЕН_СЛАЙСЕРАМИ.md'),('warn','Проверены отдельные сценарии Cura 5.14.0 и Orca 2.5.2; совместимость других конфигураций и версий требует проверки.')])
    def import_slicer(self):
        path=filedialog.askopenfilename(filetypes=[('Профили Cura и Orca','*.curaprofile *.json'),('Все файлы','*.*')])
        if not path:return
        self.imported_profile=None
        try:
            with open(path,'rb') as f: data=f.read(slicer.LIMIT+1)
            result=slicer.import_cura(data) if path.lower().endswith('.curaprofile') else slicer.import_orca(data,self.orca_plate.get())
            self.imported_profile=result
            blocks=[('title','Импорт: '+result['format']),('note','Импорт не подтверждает пригодность режима для выбранного принтера.'),('heading','Найденные параметры')]+view.pairs(result['values'],view.PARAMS)
            if not result['values']: blocks.append(('warn','Поддерживаемые явные числовые параметры не найдены.'))
            blocks += [('heading','Ограничения')]+[('warn','• '+s) for s in result['warnings']]
            self.render(self.exchange_view,blocks)
        except (OSError,slicer.ProfileError) as e: messagebox.showerror('Ошибка импорта',str(e))
    def apply_slicer(self):
        if not self.imported_profile or not self.imported_profile['values']: return messagebox.showwarning('Нет данных','Сначала импортируйте профиль с поддерживаемыми параметрами.')
        for key,val in self.imported_profile['values'].items(): self.vars[key].set(f'{val:g}')
        self.tabs.select(self.calc)
        self.render(self.output,[('title','Параметры загружены'),('note','Перенесены только явно указанные параметры; остальные поля сохранены. Выберите фактический материал и принтер, проверьте все значения и нажмите «Проверить и сохранить».'),('warn','Импортированный профиль не подтверждает безопасность и совместимость.')]+view.pairs(self.imported_profile['values'],view.PARAMS))
    def export_slicer(self,kind):
        types=[('Профиль Cura','*.curaprofile')] if kind=='Cura' else [('Профиль Orca','*.json')]
        template=filedialog.askopenfilename(title='Выберите шаблон целевой конфигурации '+kind,filetypes=types)
        if not template:return
        try:
            with open(template,'rb') as f: data=f.read(slicer.LIMIT+1)
            material,printer=self.selected(); params=self.params()
            output=slicer.export_cura(data,material,printer,params) if kind=='Cura' else slicer.export_orca(data,material,printer,params,self.orca_plate.get())
            path=filedialog.asksaveasfilename(title='Сохранить предварительный профиль',defaultextension='.curaprofile' if kind=='Cura' else '.json',filetypes=types)
            if not path:return
            from pathlib import Path
            if Path(path).resolve()==Path(template).resolve(): raise slicer.ProfileError('Нельзя перезаписывать исходный шаблон; выберите другое имя.')
            with open(path,'wb') as f:f.write(output)
            self.render(self.exchange_view,[('title','Предварительный профиль сохранён'),('row','Файл:  '+path),('warn','Проверьте импорт в используемую версию и конфигурацию слайсера. Перед печатью проверьте наследуемые настройки, температуры первого слоя, камеру, скорости и совместимость оборудования.'),('note','Экспортируются только поддерживаемые параметры; настройки оборудования и G-code не переносятся из шаблона. Orca: скорость по видам линий и температура камеры остаются на проверку пользователю.')])
        except (OSError,ValueError,TypeError,slicer.ProfileError) as e: messagebox.showerror('Экспорт заблокирован',str(e))
    def build_literature(self):
        self.litdata=all_records()
        bar=ttk.Frame(self.literature); bar.pack(fill='x')
        ttk.Label(bar,text='Литературные экспериментальные данные: сторонние опыты, не паспорта материалов и не собственные испытания').pack(side='left')
        ttk.Button(bar,text='Обновить выбор',command=self.show_literature).pack(side='right')
        ttk.Button(bar,text='Демонстрация переноса Q',command=self.literature_transfer).pack(side='right')
        frame=ttk.Frame(self.literature); frame.pack(fill='both',expand=True,pady=8)
        listframe=ttk.Frame(frame); listframe.pack(side='left',fill='y',padx=(0,10))
        self.litlist=tk.Listbox(listframe,width=48,font=('Segoe UI',10),borderwidth=0,selectbackground='#d7edf1',selectforeground='#124f60'); self.litlist.pack(side='left',fill='y')
        listscroll=ttk.Scrollbar(listframe,orient='vertical',command=self.litlist.yview); listscroll.pack(side='right',fill='y'); self.litlist.configure(yscrollcommand=listscroll.set)
        self.litout=self.readable_text(frame)
        for rec in self.litdata: self.litlist.insert('end',rec['id']+' | '+rec['category']+' | '+rec['material'][:35])
        self.litlist.bind('<<ListboxSelect>>',lambda event:self.show_literature())
        self.litlist.selection_set(0); self.show_literature()
    def current_literature(self):
        selected=self.litlist.curselection()
        return self.litdata[selected[0]] if selected else None
    def show_literature(self):
        rec=self.current_literature()
        if rec is None:return
        q=calculated_flow(rec)
        self.render(self.litout,view.literature(rec,q))
    def literature_transfer(self):
        rec=self.current_literature()
        if rec is None:return
        if calculated_flow(rec) is None:return messagebox.showwarning('Недостаточно данных','Публикация не содержит установленную ширину линии; расход не вычислен.')
        width=simpledialog.askfloat('Условный перенос','Новая ширина линии, мм:',minvalue=0.001)
        if width is None:return
        height=simpledialog.askfloat('Условный перенос','Новая высота слоя, мм:',minvalue=0.001)
        if height is None:return
        try:
            result=transfer_demonstration(rec,width,height)
            messagebox.showinfo('Только расчёт',f"Исходный расчётный расход: {result['source_flow_mm3_s']:.2f} мм³/с\nНовая расчётная скорость: {result['new_speed_mm_s']:.2f} мм/с\n\n{result['warning']}")
        except Exception as e: messagebox.showerror('Ошибка',str(e))
    def build_help(self):
        text=tk.Text(self.help,wrap='word'); text.pack(fill='both',expand=True)
        text.insert('1.0','''ИНЖЕНЕРНЫЙ ИНСТРУМЕНТ ДЛЯ ПРЕДВАРИТЕЛЬНОЙ ОЦЕНКИ

1. В библиотеке скопируйте или измените профиль под фактическую партию, внесите диаметр и ссылку на паспорт. brand_confirmed=true означает подтверждение пользователем; это не экспериментальная проверка режима.
2. Выберите целевой принтер. Задайте температуру, размеры линии и скорость или нажмите «Предложить температуры». Это середины пересечения диапазонов, а не готовая технология.
3. Для переноса введите параметры исходного режима и новую геометрию. Программа пересчитает только скорость по сохранению расхода. Экспериментальное подтверждение на целевом принтере обязательно.
4. Проверьте результат, сохраните отчёт и составьте матрицу 3×3 с обоснованными уровнями расхода. Сведения об испытаниях вводятся вручную в историю.

Q≈b·h·v, мм³/с; скорость филамента vf≈4Q/(πd²), мм/с. Реальная форма сечения отличается от прямоугольника. Qmax должен относиться к конкретному материалу, температуре и соплу. Сохранение Q не сохраняет структуру и свойства.

На вкладке «Cura / OrcaSlicer» доступны ограниченный импорт и экспорт на основе шаблона целевого принтера. Проверены отдельные сценарии Cura 5.14.0 и Orca 2.5.2; подробности и ограничения см. в docs/ОБМЕН_СЛАЙСЕРАМИ.md. G-code создаётся только слайсером.'''); text.configure(state='disabled')
    def refresh(self):
        self.materials=self.store.all('material'); self.printers=self.store.all('printer')
        for key,items in [('material',self.materials),('printer',self.printers),('source',self.printers)]:
            box=self.sel[key]; old=box.current(); box['values']=[x[1] for x in items]; box.current(old if 0<=old<len(items) else 0)
        self.refresh_list(); self.refresh_history()
    def kind_key(self): return 'material' if self.kind.current()==0 else 'printer'
    def readable_text(self,parent):
        frame=ttk.Frame(parent); frame.pack(fill='both',expand=True)
        text=tk.Text(frame,wrap='word',font=('Segoe UI',10),bg='#ffffff',fg='#253b4d',relief='flat',padx=20,pady=16,spacing1=2,spacing3=4,cursor='arrow')
        scroll=ttk.Scrollbar(frame,orient='vertical',command=text.yview); text.configure(yscrollcommand=scroll.set); scroll.pack(side='right',fill='y'); text.pack(side='left',fill='both',expand=True)
        for tag,options in {'title':{'font':('Segoe UI',17,'bold'),'foreground':'#17384b','spacing3':10},'heading':{'font':('Segoe UI',11,'bold'),'foreground':'#176a7a','spacing1':12,'spacing3':6},'metric':{'font':('Segoe UI',12,'bold'),'foreground':'#126b80'},'error':{'foreground':'#ad303a','font':('Segoe UI',10,'bold')},'warn':{'foreground':'#9a6200'},'good':{'foreground':'#14745a','font':('Segoe UI',10,'bold')},'note':{'foreground':'#596f80'},'link':{'foreground':'#176a9c'}}.items(): text.tag_configure(tag,**options)
        text.configure(state='disabled'); return text
    def render(self,widget,blocks):
        widget.configure(state='normal'); widget.delete('1.0','end')
        for tag,text in blocks: widget.insert('end',text+'\n',tag)
        widget.configure(state='disabled'); widget.see('1.0')
    def preview_profile(self):
        selection=self.listbox.curselection()
        if selection: self.render(self.profile_view,view.profile(self.items[selection[0]][2]))
    def refresh_list(self):
        self.items=self.store.all(self.kind_key()); self.listbox.delete(0,'end')
        for _,name,_ in self.items: self.listbox.insert('end',name)
        self.edit_id=None
    def load_profile(self):
        s=self.listbox.curselection()
        if not s: return
        self.edit_id,_,data=self.items[s[0]]; self.editor.delete('1.0','end'); self.editor.insert('1.0',json.dumps(data,ensure_ascii=False,indent=2))
        self.profile_tabs.select(1)
    def new_profile(self):
        self.edit_id=None; self.editor.delete('1.0','end'); self.editor.insert('1.0',json.dumps({'name':'Новый профиль','source':'введено пользователем','origin':'введено пользователем'},ensure_ascii=False,indent=2))
        self.profile_tabs.select(1)
    def save_profile(self):
        try:
            data=json.loads(self.editor.get('1.0','end')); original=next((row[2] for row in self.items if row[0]==self.edit_id),{})
            data,reset=profile_tools.reconcile_json(self.kind_key(),original,data)
            self.store.save(self.kind_key(),data['name'],data,self.edit_id); self.refresh(); messagebox.showinfo('Сохранено','Профиль сохранён. Происхождение изменённых полей необходимо указать заново.'+(' Подтверждение марки сброшено: повторно сверьте паспорт.' if reset else ''))
        except Exception as e: messagebox.showerror('Ошибка профиля',str(e))
    def delete_profile(self):
        s=self.listbox.curselection()
        if s and messagebox.askyesno('Удаление','Удалить выбранный профиль?'): self.store.delete(self.items[s[0]][0]); self.refresh()
    def selected(self): return self.materials[self.sel['material'].current()][2],self.printers[self.sel['printer'].current()][2]
    def params(self):
        p={}
        for k in ('nozzle','bed','chamber','diameter','height','width','speed'):
            raw=self.vars[k].get().strip().replace(',','.'); p[k]=float(raw) if raw else None
        return p
    def suggest(self):
        m,pr=self.selected()
        blocks=[('title','Предложение температур'),('row','Материал:  '+m.get('name','Не указано')),('row','Принтер:  '+pr.get('name','Не указано'))]
        for key,label in [('nozzle','Сопло'),('bed','Стол')]:
            proposed,explanation=suggest_temperature(m,pr,key)
            self.vars[key].set(f'{proposed:g}' if proposed is not None else '')
            blocks.extend([('heading',label),('metric' if proposed is not None else 'warn',explanation)])
        blocks.append(('note','Предложенные значения предварительные. Проверьте остальные ограничения кнопкой «Проверить и сохранить» и подтвердите режим испытаниями.'))
        self.render(self.output,blocks)
    def calculate(self):
        try:
            m,pr=self.selected(); p=self.params(); extra=extra_parameters.parse({key:var.get() for key,var in self.extra_vars.items()}); r=analyze(m,pr,p); self.result=r; self.payload={'material':m,'printer':pr,'parameters':p,'additional_parameters':extra,'additional_parameters_origin':'введено пользователем','priority':self.priority.get(),'result':r,'status':'предварительный расчёт; не результат испытаний'}
            self.store.save('calculation',f"{m['name']} / {pr['name']}",self.payload)
            self.render(self.output,view.calculation(self.payload))
        except Exception as e: messagebox.showerror('Ошибка ввода',str(e))
    def do_transfer(self):
        try:
            old_width=float(self.vars['old_width'].get().replace(',','.')); old_height=float(self.vars['old_height'].get().replace(',','.')); old_speed=float(self.vars['old_speed'].get().replace(',','.'))
            v=transfer(old_width,old_height,old_speed,float(self.vars['width'].get().replace(',','.')),float(self.vars['height'].get().replace(',','.')))
            m,target=self.selected(); source=self.printers[self.sel['source'].current()][2]; params=self.params(); params['speed']=v; result=analyze(m,target,params); self.vars['speed'].set(f'{v:.3f}')
            blocks=[('title','Предварительный расчёт переноса'),('row','Исходный принтер: '+source.get('name','не указан')),('row','Целевой принтер: '+target.get('name','не указан')),('metric',f'Расчётная скорость: {v:.3f} мм/с'),('row',f'Исходный расчётный расход: {old_width*old_height*old_speed:.3f} мм³/с')]
            for key,label,unit in [('diameter','Диаметр филамента','мм'),('nozzle_max','Предел сопла','°C'),('bed_max','Предел стола','°C'),('heated_chamber','Активный нагрев камеры','')]:
                blocks.append(('row',f"{label}: источник {source.get(key) if source.get(key) is not None else 'неизвестно'} → цель {target.get(key) if target.get(key) is not None else 'неизвестно'} {unit}"))
            blocks.append(('heading','Проверка целевого принтера'))
            blocks += [('error','• '+s) for s in result['errors']]+[('warn','• '+s) for s in result['unknown']+result['warnings']]
            blocks.append(('warn','Исходный режим не подтверждён этой операцией. Температурная история, диаметр исходного сопла, охлаждение и подача автоматически не перенесены. Для сохранения результата нажмите «Проверить и сохранить».'))
            self.render(self.output,blocks)
        except Exception as e: messagebox.showerror('Ошибка ввода',str(e))
    def do_matrix(self):
        try:
            m,pr=self.selected(); levels=[float(x.replace(',','.')) for x in self.vars['q_levels'].get().split(';')]; rows=matrix(m,pr,self.params(),levels)
            self.render(self.output,view.matrix_view(rows))
        except Exception as e: messagebox.showerror('Ошибка матрицы',str(e))
    def show_plan(self):
        steps=trial_tools.plan(self.priority.get())
        blocks=[('title','План испытаний'),('row','Приоритет:  '+self.priority.get()),('warn','Порядок — организационная рекомендация, а не прогноз свойств. Работайте только в подтверждённом техническом окне.')]
        for i,step in enumerate(steps,1): blocks.extend([('heading',f"{i}. {step['title']}"),('row',step['description'])])
        blocks.append(('note','Зафиксируйте партию, сушку, сопло, ориентацию, методику и неизменяемые условия. Критерии устанавливает пользователь до испытаний.'))
        self.render(self.output,blocks)
    def display(self,value): self.output.delete('1.0','end'); self.output.insert('1.0',value)
    def export(self):
        if not self.payload: return messagebox.showwarning('Нет расчёта','Сначала выполните проверку.')
        path=filedialog.asksaveasfilename(defaultextension='.html',filetypes=[('HTML отчёт','*.html'),('JSON диагностика','*.json'),('CSV параметры','*.csv')])
        if not path:return
        try:
            if path.lower().endswith('.json'):
                with open(path,'w',encoding='utf-8') as f: json.dump(self.payload,f,ensure_ascii=False,indent=2)
            elif path.lower().endswith('.csv'):
                with open(path,'w',encoding='utf-8-sig',newline='') as f:
                    w=csv.writer(f,delimiter=';'); w.writerow(['Параметр','Значение','Статус']); w.writerows((k,v,'введён пользователем') for k,v in self.payload['parameters'].items())
                    w.writerows((k,v,'дополнительно введён пользователем; не проверено') for k,v in self.payload.get('additional_parameters',{}).items())
            else:
                with open(path,'w',encoding='utf-8') as f: f.write(view.html_report(view.calculation(self.payload)))
            messagebox.showinfo('Сохранено','Сохранён диагностический файл, не нативный профиль слайсера.')
        except Exception as e: messagebox.showerror('Ошибка',str(e))
    def refresh_history(self):
        self.history=self.store.all('calculation')+self.store.all('trial')+self.store.all('confirmation'); self.hist.delete(0,'end')
        for id,name,data in self.history:self.hist.insert('end',f'{id}: {name}')
    def show_history(self):
        s=self.hist.curselection()
        if s:
            data=self.history[s[0]][2]
            if data.get('status')=='Подтверждено пользователем по указанным критериям':
                blocks=self.confirmation_blocks(data)
            elif 'calculation' in data:
                blocks=self.trial_blocks(data)
            else: blocks=view.calculation(data)
            self.render(self.history_view,blocks)
    def add_trial(self):
        selected=self.hist.curselection()
        if not selected: return messagebox.showwarning('Нет расчёта','Выберите сохранённый расчёт в списке истории.')
        source_id,_,source=self.history[selected[0]]
        if 'calculation' in source: return messagebox.showwarning('Нужен расчёт','Выберите расчёт, а не протокол испытания.')
        dialog=tk.Toplevel(self); dialog.title('Протокол испытания'); dialog.transient(self); dialog.geometry('900x730')
        ttk.Label(dialog,text='Фактические измерения и критерии задаёт пользователь. Пустое поле означает отсутствие данных.',wraplength=850).grid(row=0,column=0,columnspan=4,sticky='w',padx=10,pady=8)
        for col,label in enumerate(('Показатель','Измерено','Минимум','Максимум')): ttk.Label(dialog,text=label).grid(row=1,column=col,sticky='w',padx=8)
        variables={}
        for row,(key,(label,unit)) in enumerate(trial_tools.MEASURES.items(),2):
            ttk.Label(dialog,text=f'{label}, {unit}').grid(row=row,column=0,sticky='w',padx=8,pady=3)
            variables[key]=[tk.StringVar() for _ in range(3)]
            for col,v in enumerate(variables[key],1): ttk.Entry(dialog,textvariable=v,width=17).grid(row=row,column=col,padx=8,pady=3)
        fields={}
        for row,(key,label) in enumerate([('batch','Партия материала'),('sample','Тип образца и ориентация'),('method','Методика испытания'),('conditions','Сушка и прочие условия'),('observations','Дефекты и наблюдения'),('sample_id','Уникальный номер образца')],10):
            ttk.Label(dialog,text=label).grid(row=row,column=0,sticky='w',padx=8,pady=3); fields[key]=tk.StringVar(); ttk.Entry(dialog,textvariable=fields[key],width=55).grid(row=row,column=1,columnspan=3,sticky='ew',padx=8,pady=3)
        def save():
            try:
                measurements={k:v[0].get() for k,v in variables.items()}; criteria={k:{'min':v[1].get(),'max':v[2].get()} for k,v in variables.items()}
                assessment=trial_tools.evaluate(measurements,criteria)
                if not assessment['rows'] and not fields['observations'].get().strip(): raise ValueError('Добавьте хотя бы одно измерение, критерий или наблюдение.')
                data={'calculation_id':source_id,'calculation':source,'measurements':measurements,'criteria':criteria,'assessment':assessment,'context':{k:v.get().strip() for k,v in fields.items()},'origin':'экспериментальные данные пользователя'}
                self.store.save('trial','Испытание: '+source['material']['name'],data); dialog.destroy(); self.refresh_history()
            except (ValueError,KeyError) as e: messagebox.showerror('Ошибка протокола',str(e),parent=dialog)
        ttk.Button(dialog,text='Сохранить протокол',command=save).grid(row=16,column=0,columnspan=4,pady=12)
    def trial_blocks(self,data):
        blocks=[('title','Результат испытания'),('note','Данные, введённые пользователем')]
        if 'assessment' in data:
            a=data['assessment']; blocks.append(('heading',a['outcome']))
            for row in a['rows']:
                val='нет данных' if row['value'] is None else f"{row['value']:g} {row['unit']}"
                low='—' if row['min'] is None else f"{row['min']:g}"; high='—' if row['max'] is None else f"{row['max']:g}"
                blocks.append(('error' if row['status']=='не соответствует' else 'row',f"{row['label']}: {val}; критерий {low}–{high} {row['unit']} — {row['status']}"))
            blocks.append(('warn',a['disclaimer']))
            for key,label in [('batch','Партия'),('sample','Образец и ориентация'),('sample_id','Номер образца'),('method','Методика'),('conditions','Условия'),('observations','Наблюдения')]: blocks.append(('row',label+': '+(data.get('context',{}).get(key) or 'не указано')))
        else: blocks.append(('row',data.get('observations','Не указано')))
        return blocks+view.calculation(data['calculation'])
    def export_trial(self):
        selected=self.hist.curselection()
        if not selected or 'calculation' not in self.history[selected[0]][2]: return messagebox.showwarning('Нет протокола','Выберите результат испытания в истории.')
        data=self.history[selected[0]][2]; path=filedialog.asksaveasfilename(defaultextension='.html',filetypes=[('HTML отчёт','*.html'),('JSON протокол','*.json')])
        if not path:return
        try:
            with open(path,'w',encoding='utf-8') as f:
                if path.lower().endswith('.json'): json.dump(data,f,ensure_ascii=False,indent=2,allow_nan=False)
                else: f.write(view.html_report(self.confirmation_blocks(data) if data.get('status')=='Подтверждено пользователем по указанным критериям' else self.trial_blocks(data)))
        except (OSError,ValueError) as e: messagebox.showerror('Ошибка экспорта',str(e))
    def confirm_series(self):
        selected=self.hist.curselection()
        if not selected: return messagebox.showwarning('Нет расчёта','Выберите исходный расчёт в истории.')
        calc_id,_,calculation=self.history[selected[0]]
        if 'calculation' in calculation: return messagebox.showwarning('Нужен расчёт','Выберите исходный расчёт, а не протокол или подтверждение.')
        records=[(i,name,data) for i,name,data in self.store.all('trial') if data.get('calculation_id')==calc_id]
        if len(records)<2: return messagebox.showwarning('Недостаточно данных','Для этого расчёта нужно не менее двух отдельных протоколов. Ранее созданные протоколы без привязки к расчёту не учитываются.')
        dialog=tk.Toplevel(self); dialog.title('Подтверждение по повторениям'); dialog.transient(self); dialog.geometry('750x440')
        ttk.Label(dialog,text='Выберите не менее двух протоколов с разными образцами. Совпадение партии, условий, методики и критериев будет проверено.',wraplength=710).pack(anchor='w',padx=12,pady=10)
        box=tk.Listbox(dialog,selectmode='extended',height=10,exportselection=False); box.pack(fill='both',expand=True,padx=12)
        for ident,name,data in records:
            context=data.get('context',{}); box.insert('end',f"{ident}: образец {context.get('sample_id') or 'не указан'} | партия {context.get('batch') or 'не указана'} | {data.get('assessment',{}).get('outcome','нет оценки')}")
        def confirm():
            try:
                selected_records=[(records[i][0],records[i][2]) for i in box.curselection()]
                result=trial_tools.confirm_repeats(calc_id,calculation,selected_records)
                if not messagebox.askyesno('Подтверждение пользователем','Подтверждаете, что образцы получены при отдельных повторных печатях, измерения достоверны, а серия достаточна для указанных критериев и условий?',parent=dialog): return
                self.store.save('confirmation','Подтверждение: '+calculation['material']['name'],result); dialog.destroy(); self.refresh_history()
            except (ValueError,KeyError) as exc: messagebox.showerror('Подтверждение невозможно',str(exc),parent=dialog)
        ttk.Button(dialog,text='Проверить и подтвердить',command=confirm).pack(pady=12)
    def confirmation_blocks(self,data):
        blocks=[('title',data['status']),('warn',data['warning']),('heading','Область подтверждения')]
        for key,label in [('batch','Партия'),('sample','Тип образца и ориентация'),('method','Методика'),('conditions','Условия')]: blocks.append(('row',label+': '+data['context'][key]))
        blocks.append(('heading','Повторные испытания'))
        for record in data['trials']:
            blocks.append(('row',f"Протокол № {record['trial_id']}; образец {record['sample_id']}"))
            for r in record['measurements']:
                lo='—' if r['min'] is None else f"{r['min']:g}"; hi='—' if r['max'] is None else f"{r['max']:g}"
                blocks.append(('row',f"{r['label']}: {r['value']:g} {r['unit']}; критерий {lo}–{hi} {r['unit']}"))
        calc_blocks=view.calculation(data['calculation'])
        calc_blocks=[(tag,'Исходный расчёт; пользовательское подтверждение ограничено указанными выше критериями и условиями.' if text=='Предварительный расчёт. Результат не подтверждён печатью и испытаниями.' else text) for tag,text in calc_blocks]
        return blocks+calc_blocks

if __name__=='__main__': App().mainloop()
