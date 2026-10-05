"""Build a minimal, reproducible public M2 package from the GitHub checkout."""
import argparse
import ast
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ALLOW=ROOT/'publication/TGI_M2_PUBLIC_MODULE_ALLOWLIST_V1.json'
ENTRIES=('tgi/__init__.py','tgi/source_bound_endpoint_transport.py',
         'tgi/source_bound_endpoint_transport_check.py',
         'tgi/source_bound_single_nmu_edit.py',
         'tgi/source_bound_single_nmu_edit_check.py',
         'tgi/phase_bound_response_atlas.py',
         'tgi/phase_bound_response_atlas_check.py')
SECRET_MARKERS=(b'pypi-',b'ghp_',b'-----BEGIN PRIVATE KEY-----')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def closure():
    seen=set();pending=list(ENTRIES)
    while pending:
        relative=pending.pop()
        if relative in seen:
            continue
        seen.add(relative)
        tree=ast.parse((ROOT/relative).read_text(encoding='utf8'))
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):
                if node.level==1 and node.module:
                    pending.append('tgi/'+node.module.split('.')[0]+'.py')
                elif node.level==0 and node.module and node.module.startswith('tgi.'):
                    pending.append('tgi/'+node.module.split('.')[1]+'.py')
            elif isinstance(node,ast.Import):
                for alias in node.names:
                    if alias.name.startswith('tgi.'):
                        pending.append('tgi/'+alias.name.split('.')[1]+'.py')
            elif isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and \
                    node.func.id in ('__import__','import_module'):
                raise RuntimeError(f'Dynamic import requires review: {relative}:{node.lineno}')
    return seen


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--version',default='0.2.0.dev12')
    args=parser.parse_args()
    output=args.output.resolve()
    if output.exists() or output.is_relative_to(ROOT):
        raise RuntimeError('Use a fresh output directory outside the checkout')
    frozen=json.loads(ALLOW.read_text(encoding='utf8'))
    modules=frozen['modules']
    if len(modules)!=45 or set(modules)!=closure() or \
       sorted(modules)!=modules or frozen['dynamic_import_call_lines']:
        raise RuntimeError('Frozen public module closure drift')
    stage=output/'stage';dist=output/'dist'
    (stage/'tgi').mkdir(parents=True)
    for relative in modules:
        source=ROOT/relative
        if source.parent!=ROOT/'tgi' or not source.is_file():
            raise RuntimeError(f'Invalid allowlisted module: {relative}')
        shutil.copy2(source,stage/relative)
    shutil.copy2(ROOT/'LICENSE',stage/'LICENSE')
    project=(ROOT/'pyproject.toml').read_text(encoding='utf8')
    if 'version = "0.2.0.dev0"' not in project:
        raise RuntimeError('Unexpected root project version')
    (stage/'pyproject.toml').write_text(project.replace(
        'version = "0.2.0.dev0"',f'version = "{args.version}"'),encoding='utf8')
    (stage/'README.md').write_text(
        '# TGI foundation M2\n\n'
        'Native NMU identity, source-bound response atlas, endpoint transport, '
        'and one-NMU substitution transport. Emylton Leunufna. '
        'No reuse allowed without permission.\n',encoding='utf8')
    (stage/'MANIFEST.in').write_text(
        'include README.md\ninclude LICENSE\nrecursive-include tgi *.py\n',
        encoding='utf8')
    expected=set(modules)|{'README.md','LICENSE','pyproject.toml','MANIFEST.in'}
    staged={p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}
    if staged!=expected:
        raise RuntimeError('Unexpected staged file')
    for path in stage.rglob('*'):
        if path.is_file() and any(marker in path.read_bytes() for marker in SECRET_MARKERS):
            raise RuntimeError(f'Credential marker in stage: {path.name}')
    dist.mkdir()
    for backend in ('build_wheel','build_sdist'):
        result=subprocess.run([sys.executable,'-c',
            f'from setuptools.build_meta import {backend}; '
            f'import sys; print({backend}(sys.argv[1]))',str(dist)],
            cwd=stage,capture_output=True,text=True)
        if result.returncode:
            raise RuntimeError(result.stdout+'\n'+result.stderr)
    wheel,=dist.glob('*.whl');sdist,=dist.glob('*.tar.gz')
    with zipfile.ZipFile(wheel) as archive:
        names=archive.namelist()
        selected={n for n in names if n.startswith('tgi/') and n.endswith('.py')}
        if selected!=set(modules) or any(
                sha(archive.read(n))!=sha((ROOT/n).read_bytes()) for n in modules):
            raise RuntimeError('Wheel module boundary mismatch')
    with tarfile.open(sdist,'r:gz') as archive:
        names=archive.getnames()
        selected={Path(n).relative_to(Path(n).parts[0]).as_posix()
                  for n in names if n.endswith('.py') and '/tgi/' in n}
        if selected!=set(modules):
            raise RuntimeError('Sdist module boundary mismatch')
    report={'version':args.version,'module_count':len(modules),
            'allowlist_sha256':sha(ALLOW.read_bytes()),
            'wheel_sha256':sha(wheel.read_bytes()),
            'sdist_sha256':sha(sdist.read_bytes())}
    (output/'BUILD_REPORT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report))


if __name__=='__main__':main()
