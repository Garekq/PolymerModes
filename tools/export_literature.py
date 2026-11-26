import json
from pathlib import Path
from polymer.literature import all_records
Path('data/literature_experiments.json').write_text(json.dumps(all_records(),ensure_ascii=False,indent=2),encoding='utf-8')
