# Проверенные источники и литература

Дата обращения: 26.11.2026. Источники относятся к данным и выводам, использованным в файлах проекта. Коммерческие карточки изменяются; перед использованием проверить паспорт партии.

1. UltiMaker. Ultimaker 3 User Manual, v1.4, раздел 2.2. https://um-support-files.ultimaker.com/manuals/user-manual/UM3/Ultimaker%203%20-%20User%20manual%20EN%20v1.4.pdf — параметры оборудования.
2. 3DXTECH. ThermaX PEEK. https://www.3dxtech.com/products/thermax-peek-1 — справочный диапазон печати; есть расхождение с FAQ и таблицей сушки.
3. 3DXTECH. ThermaX PEKK-A. https://www.3dxtech.com/products/pekk-a — диапазон печати и Tg.
4. 3DXTECH. ThermaX PEI 9085. https://www.3dxtech.com/products/thermax-pei-9085 — диапазон печати и аморфность.
5. 3DXTECH. ThermaX PEI 1010. https://www.3dxtech.com/products/thermax-pei-1010 — диапазон печати и Tg.
6. 3DXTECH. Filament Drying Instructions. https://www.3dxtech.com/pages/filament-drying-instructions — общая таблица сушки; сравнить с карточкой партии.
7. 3DXTECH. Frequently Asked Questions. https://www.3dxtech.com/pages/frequently-asked-questions — обнаружено расхождение температур PEEK с карточкой продукта.
8. UltiMaker. CuraProfileReader, исходный код. https://github.com/Ultimaker/Cura/blob/main/plugins/CuraProfileReader/CuraProfileReader.py — разбор и обновление профиля; отдельный сценарий импорта проверен в Cura 5.14.0.
9. UltiMaker. Settings Glossary. https://github.com/Ultimaker/Cura/wiki/Settings-Glossary — взаимосвязь профилей и конфигураций Cura.
10. OrcaSlicer. Исходный код. https://github.com/OrcaSlicer/OrcaSlicer — исходный код проекта; отдельные сценарии проверены в OrcaSlicer 2.5.2.
11. ISO. ISO 15512:2019 Plastics — Determination of water content. https://www.iso.org/standard/73834.html — область применения методов; по состоянию на просмотр стандарт опубликован, готовится новая редакция.
12. ASTM. D638-22 Standard Test Method for Tensile Properties of Plastics. https://store.astm.org/standards/d638/1000 — направление выбора методики растяжения; полный текст и соответствие конкретного образца не проверены.
13. Crystallization and microstructure effects on interlayer performance and ductility of Polyetherketoneketone in open-chamber fused filament fabrication. Materials Today Communications, 2025, 49, 114253. https://doi.org/10.1016/j.mtcomm.2025.114253 — PEKK-C; не распространять количественные результаты на другие марки без проверки.
14. Rodzeń K. и др. Improvement of the layer-layer adhesion in FFF 3D printed PEEK/carbon fibre composites. Composites Part A, 2021, 149, 106532. https://doi.org/10.1016/j.compositesa.2021.106532 — влияние условий и кристаллизации на межслойное соединение композита; не свойства чистого PEEK.
15. Doyle L., García-Molleja J., Fernández-Blázquez J. P., González C. Unraveling the Print–Structure–Property Relationships in the FFF of PEEK. Polymers. 2025;17:1444. https://doi.org/10.3390/polym17111444 — условия опытов и результаты.
16. Doyle L. и соавт. Raw Experimental data for Unraveling the Print-Structure-Property Relationships in FFF of PEEK, Zenodo, v1. https://zenodo.org/records/14864777 — матрица тех же 16 опытов, а не отдельное исследование. Большие исходные томограммы не скачивались.
17. Shrestha и соавт. Thermo-Mechanical and Structural Characterization of Isothermally Annealed 3D Printed Pseudo-Amorphous Polyetherketoneketone. Macromolecular Materials and Engineering. 2025;310:2500076. https://doi.org/10.1002/mame.202500076 — составы и режимы печати, исследование отжига.
18. McCrickard C., Boyd A., Rodzen K., Archer E., Manzoor F., Ullah J. PEEK/PEI Polymer Blends for Fused Filament Fabrication: Processing, Properties, and Printability. Polymers. 2026;18:113. https://doi.org/10.3390/polym18010113 — филаменты, изготовленные исследователями, и таблицы испытаний.
19. Zanjanijam A. R., Major I., Lyons J. G., Lafont U., Devine D. M. Fused Filament Fabrication of PEEK: A Review of Process-Structure-Property Relationships. Polymers. 2020;12:1665. https://doi.org/10.3390/polym12081665 — обзор, не отдельный набор собственных опытов.
20. OrcaSlicer. How to create profiles. https://github.com/OrcaSlicer/OrcaSlicer/wiki/how_to_create_profiles — структура профилей и наследование.
21. OrcaSlicer. Официальный шаблон процесса. https://github.com/OrcaSlicer/OrcaSlicer/blob/main/resources/profiles_template/Template/process/process%20template.json — структура файла; не готовый профиль эксперимента.
22. UltiMaker. Profiles & Settings. https://github.com/Ultimaker/Cura/wiki/Profiles-%26-Settings — контейнеры профиля и зависимость от оборудования.
23. UltiMaker. Cura fdmprinter.def.json. https://github.com/Ultimaker/Cura/blob/main/resources/definitions/fdmprinter.def.json — наименования параметров и расположение настроек стола и сопла.
24. UltiMaker. Setting Properties. https://github.com/Ultimaker/Cura/wiki/Setting-Properties — области действия настроек Cura.
25. OrcaSlicer. Пример профиля материала. https://github.com/OrcaSlicer/OrcaSlicer/blob/main/resources/profiles/Flashforge/filament/Flashforge%20ASA%20Basic%20%40FF%20AD5X.json — структура JSON и совместимость с принтером.
26. OrcaSlicer. Release v2.5.2. https://github.com/OrcaSlicer/OrcaSlicer/releases/tag/v2.5.2 — переносимая сборка, использованная для проверки интерфейса.
27. OrcaSlicer. PresetBundle.cpp, v2.5.2. https://github.com/OrcaSlicer/OrcaSlicer/blob/v2.5.2/src/libslic3r/PresetBundle.cpp — проверка версии и наследования при импорте профилей.
28. UltiMaker. Cura release 5.14.0. https://github.com/Ultimaker/Cura/releases/tag/5.14.0 — тестовая сборка Cura.

