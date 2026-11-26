"""Условные геометрии в мм; не механические стандартные образцы."""
from pathlib import Path

def box(name,x,y,z):
    v=[(0,0,0),(x,0,0),(x,y,0),(0,y,0),(0,0,z),(x,0,z),(x,y,z),(0,y,z)]
    faces=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
    lines=['solid '+name]
    for f in faces:
        lines.extend([' facet normal 0 0 0','  outer loop']+['   vertex %s %s %s'%v[i] for i in f]+['  endloop',' endfacet'])
    lines.append('endsolid '+name); Path('models',name+'.stl').write_text('\n'.join(lines)+'\n',encoding='ascii')
box('cube_20mm',20,20,20)
box('warpage_plate_80x20x3mm',80,20,3)
