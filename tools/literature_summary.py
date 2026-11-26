from polymer.literature import all_records
r=[x for x in all_records() if x['id'].startswith('doyle-') and 'validation' not in x['id']]
for factor in ('nozzle_C','bed_C','chamber_C','speed_mm_s'):
 levels=sorted({x['parameters'][factor] for x in r})
 for level in levels:
  a=[x['results']['tensile_strength_MPa'] for x in r if x['parameters'][factor]==level]
  print(factor,level,sum(a)/len(a))
