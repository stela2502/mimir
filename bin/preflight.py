#!/usr/bin/env python3
"""Read-only Mimir dataset manifest validation; standard library only."""
import argparse, csv, os, re, shutil, subprocess, sys
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--samples',required=True)
p.add_argument('--outdir',required=True)
p.add_argument('--profile',default='local')
p.add_argument('--sc-analyse',default='sc-analyse')
p.add_argument('--image',default='')
p.add_argument('--check-runtime',action='store_true')
a=p.parse_args()
errors=[]; warnings=[]
def err(msg): errors.append(msg)
def warn(msg): warnings.append(msg)
manifest=Path(a.samples).expanduser()
if not manifest.is_file(): err(f'Manifest missing: {manifest}')
else:
 with manifest.open(newline='') as fh:
  reader=csv.DictReader(fh,delimiter='\t')
  required={'dataset','input','mode','annotations','split_by'}
  if not reader.fieldnames or not required.issubset(reader.fieldnames): err(f'Manifest requires columns: {", ".join(sorted(required))}')
  else:
   seen=set(); rows=list(reader)
   if not rows: err('Manifest has no datasets')
   for line,r in enumerate(rows,2):
    name=(r['dataset'] or '').strip(); mode=(r['mode'] or '').strip().lower()
    inp=(r['input'] or '').strip(); ann=(r['annotations'] or '').strip()
    if not re.fullmatch('[A-Za-z0-9_-]+',name): err(f'Line {line}: invalid dataset identifier {name!r}')
    if name in seen: err(f'Line {line}: duplicate dataset {name!r}')
    seen.add(name)
    if mode not in ('gex','existing'): err(f'{name}: mode must be gex or existing')
    if not Path(inp).is_absolute(): err(f'{name}: input must be absolute: {inp}')
    elif not Path(inp).exists(): err(f'{name}: input missing: {inp}')
    elif mode=='existing' and (not Path(inp).is_file() or not inp.endswith('.h5ad')): err(f'{name}: existing mode requires an .h5ad file')
    elif mode=='gex' and not (Path(inp).is_dir() or inp.endswith('.h5ad')): warn(f'{name}: GEX input format needs confirmation: {inp}')
    if ann:
     if not Path(ann).is_absolute(): err(f'{name}: annotation TSV path must be absolute: {ann}')
     elif not Path(ann).is_file(): err(f'{name}: annotation TSV missing: {ann}')
    print(f'  {name}: {mode} {inp}')
out=Path(a.outdir).expanduser()
if not out.is_absolute(): err(f'Output directory must be absolute: {out}')
if out.exists() and not out.is_dir(): err(f'Output destination is not a directory: {out}')
parent=out if out.is_dir() else next((x for x in out.parents if x.exists()),None)
if parent and not os.access(parent,os.W_OK): err(f'No write permission on output parent: {parent}')
if a.check_runtime:
 if 'apptainer' in a.profile or 'slurm' in a.profile:
  if not shutil.which('apptainer'): err('apptainer not found in PATH')
  if not a.image: err('No container image configured')
  if a.image and a.image.endswith('.sif') and not Path(a.image).is_file(): err(f'Container SIF missing: {a.image}')
 else:
  binary=shutil.which(a.sc_analyse) or (a.sc_analyse if Path(a.sc_analyse).is_file() else None)
  if not binary: err(f'sc-analyse not found: {a.sc_analyse}')
  else:
   try:
    result=subprocess.run([binary,'--help'],capture_output=True,text=True,timeout=15)
    if result.returncode: err(f'sc-analyse --help exited {result.returncode}')
    for command in ('gex','annotate','split'):
     if not re.search(r'^\s*'+command+r'\s',result.stdout,re.M): err(f'sc-analyse lacks subcommand {command}')
   except Exception as e: err(f'Cannot execute sc-analyse: {e}')
for w in warnings: print('WARNING:',w,file=sys.stderr)
for e in errors: print('ERROR:',e,file=sys.stderr)
print(f'PREFLIGHT: {len(errors)} error(s), {len(warnings)} warning(s)')
sys.exit(1 if errors else 0)
