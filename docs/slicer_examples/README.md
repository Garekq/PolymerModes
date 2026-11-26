# Демонстрационные соответствия параметров слайсеров

Это таблица для ручного изучения, не профиль и не разрешение на печать. Значения относятся к таблице 2 Shrestha et al. (2025), SEQENS IMPEKK-3D-F, CreatBot PEEK-300. Официальные исходники: [Cura](https://github.com/Ultimaker/Cura/blob/main/plugins/CuraProfileWriter/CuraProfileWriter.py), [Cura profiles](https://github.com/Ultimaker/Cura/wiki/Profiles-%26-Settings), [Orca process template](https://github.com/OrcaSlicer/OrcaSlicer/blob/main/resources/profiles_template/Template/process/process%20template.json), [Orca guide](https://github.com/OrcaSlicer/OrcaSlicer/wiki/how_to_create_profiles). Неизвестные настройки не заполнены. Ключи и единицы следует сверить с конкретной версией и машинным профилем.

| Параметр | Опубликовано | Cura возможное поле | Orca возможное поле |
|---|---:|---|---|
| Температура сопла | 400 °C | material_print_temperature | nozzle_temperature (filament) |
| Температура стола | 120 °C | material_bed_temperature | hot_plate_temp (если используется соответствующий тип поверхности) |
| Высота слоя | 0,1 мм | layer_height | layer_height |
| Ширина экструзии | 0,4 мм | line_width | line_width, уточнить назначение для отдельных линий |
| Скорость печати | 20 мм/с | speed_print | необходимо установить по видам линий вручную; единого точного соответствия нет |
| Заполнение | 100 % | infill_sparse_density | sparse_infill_density |
| Камера | 120 °C | зависит от определения машины | зависит от конфигурации машины |
| Сопло | 0,4 мм | конфигурация оборудования | конфигурация оборудования |

В статье Simplify3D, поэтому идентичность траекторий даже при совпадении чисел не доказана. Ключи могут иметь разные правила наследования и единицы; значения первого слоя, скорость отдельных элементов, вентилятор, G-code и машинная кинематика не заданы. Исходный файл Orca содержит значения и команды чужого примера: его не следует импортировать и применять к печати без полной настройки.

## Сторонний шаблон

`orca_official_process_template.json` получен из [OrcaSlicer](https://github.com/OrcaSlicer/OrcaSlicer/blob/main/resources/profiles_template/Template/process/process%20template.json) и используется только как тестовая фикстура. Условия OrcaSlicer AGPL-3.0 приведены в соседнем файле `ORCA_LICENSE.txt`. Это указание к стороннему файлу и не является объявлением лицензии всего проекта.
