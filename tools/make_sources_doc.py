from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pathlib import Path
text=Path('docs/SOURCES.md').read_text(encoding='utf-8-sig').splitlines()
doc=Document(); section=doc.sections[0]; section.top_margin=Cm(2); section.bottom_margin=Cm(2); section.left_margin=Cm(2.5); section.right_margin=Cm(2)
normal=doc.styles['Normal']; normal.font.name='Calibri'; normal.font.size=Pt(11); normal.paragraph_format.space_after=Pt(7)
for name in ['Title','Heading 1']:
 s=doc.styles[name]; s.font.name='Calibri'; s.font.color.rgb=RGBColor(0,0,0)
style=doc.styles['Title']; ppr=style.element.get_or_add_pPr(); borders=OxmlElement('w:pBdr'); bottom=OxmlElement('w:bottom'); bottom.set(qn('w:val'),'nil'); borders.append(bottom); ppr.append(borders)
doc.add_paragraph('Источники и литература для разработки программы подбора режимов 3D печати',style='Title')
doc.add_paragraph('Перечень включает источники, использованные при разработке прототипа, методики, обмена профилями и организации испытаний. Критерии оценки устанавливает пользователь. Карточки поставщика могут меняться; для применения необходимо сверить документацию конкретной партии. Дата обращения 26 ноября 2026 года.')
for line in text:
 if line and line[0].isdigit():
  p=doc.add_paragraph(line); p.paragraph_format.keep_together=True
  if line.startswith(('8. ', '15. ', '23. ')): p.paragraph_format.page_break_before=True
doc.save('docs/Источники_и_литература.docx')


