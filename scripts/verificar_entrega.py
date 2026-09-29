"""Check packaging and evidence integrity, not live AWS or security posture."""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors = []
required = [
    'README.md', 'docs/ENTREGA_FINAL.md', 'docs/clasificacion_hallazgo.md',
    'docs/respuesta_incidente.md', 'docs/evidencia_produccion.md',
    'docs/declaracion_ia.md', 'docs/correo_confirmacion.md',
    'reportes/pipeline_bloqueado.txt', 'reportes/pipeline_verde.txt',
    'reportes/pipeline_bloqueado_metadata.txt', 'reportes/aws/cierre_qa.txt',
    'reportes/sbom_cyclonedx.json', 'infra/main.tf', 'infra/README.md',
]
for name in required:
    if not (ROOT/name).is_file(): errors.append('Missing: '+name)
for name, word in [('pipeline_bloqueado.txt','BLOQUEADO'), ('pipeline_verde.txt','PERMITIDO')]:
    path=ROOT/'reportes'/name
    if path.exists() and word not in path.read_text(encoding='utf-8-sig'):
        errors.append('Missing verdict: '+name)
for record in json.loads((ROOT/'reportes/manifest_evidencias.json').read_text()):
    path=ROOT/record['published']
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=record['published_sha256']:
        errors.append('Evidence hash mismatch: '+record['published'])
for record in json.loads((ROOT/'docs/capturas/manifest.json').read_text()):
    path=ROOT/'docs/capturas'/record['file']
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=record['sha256']:
        errors.append('Screenshot hash mismatch: '+record['file'])
for folder in [ROOT,ROOT/'docs',ROOT/'reportes',ROOT/'infra',ROOT/'entrega',ROOT/'pipeline']:
    for doc in folder.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8-sig')):
            if '://' in target or target.startswith('#'): continue
            target=target.split('#',1)[0]
            if target and not (doc.parent/target).exists(): errors.append('Broken link: '+str(doc.relative_to(ROOT))+' -> '+target)
if errors:
    print('\n'.join(errors)); sys.exit(1)
print('OK: required files, evidence hashes, screenshot hashes and local document links.')
print('Scope: packaging only. Does not certify live AWS, Word submission or presentation.')
