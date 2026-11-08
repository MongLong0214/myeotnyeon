from pathlib import Path
import subprocess,json
O=Path('research/format_v4/missing_axes_work')
for v in ['H_GaGKQp17k','w_LJ_GQObic','C1eXfwC7uAw','_qQK1LZpyJI','N18']:
 paths=sorted((O/v).glob('*.jpg'));res=subprocess.run(['research/format_v4/extol_all/ocr',*map(str,paths)],capture_output=True,text=True,check=True);(O/f'{v}_ocr.json').write_text(res.stdout);print(v,len(paths),flush=True)
