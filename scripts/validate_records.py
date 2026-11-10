#!/usr/bin/env python3
"""Check project maintenance files without running business code or experiments."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from urllib.parse import unquote, urlsplit

REQUIRED = (
    'README.md', 'AGENTS.md', 'TASKMEMORY.md', '.gitignore',
    'scripts/README.md', 'scripts/validate_records.py', 'docs/README.md',
    'docs/PROJECT_MAP.md', 'docs/PROJECT_MEMORY.md', 'docs/REPRODUCTION.md',
    'docs/RECORD_SPEC.md', 'docs/GIT_WORKFLOW.md', 'docs/RESPONSE_STYLE.md',
    'docs/design/README.md', 'docs/reports/README.md', 'docs/provenance/README.md',
    'docs/archive/README.md', 'docs/registry/README.md', 'generated_artifacts/README.md',
)
FIELDS = {
    'datasets': 'id title source evidence status',
    'runs': 'id title dataset_ids kind output_uri code config evidence status',
    'evaluations': 'id title run_ids definition output_uri evaluator evidence status',
    'sites': 'id title run_ids evaluation_ids output_uri evidence status',
}
LINKS = {'dataset_ids': 'datasets', 'run_ids': 'runs', 'evaluation_ids': 'evaluations', 'parent_run_ids': 'runs'}
STATUSES = {'planned', 'running', 'completed', 'failed', 'interrupted', 'paused'}
LOCAL_DIRS = {'data', 'datasets', 'weights', 'checkpoints', 'outputs', 'results', 'runs', 'logs', 'generated_artifacts'}
DATA_ENDINGS = ('.npy', '.npz', '.pkl', '.pickle', '.parquet', '.arrow', '.h5', '.hdf5', '.pt', '.pth', '.ckpt', '.safetensors', '.onnx', '.gif', '.mp4', '.webm', '.zip', '.tar', '.tar.gz', '.tgz', '.log')


def local_data_path(path):
    text = path.as_posix().lower()
    if text == 'generated_artifacts/readme.md':
        return False
    return bool(path.parts and path.parts[0] in LOCAL_DIRS) or text.endswith(DATA_ENDINGS) or '.tfrecord' in text


def inside(root, path):
    try:
        path.resolve().relative_to(root)
        return True
    except ValueError:
        return False


def git_check(root, errors, warnings):
    git = shutil.which('git')
    if not git:
        warnings.append('Git unavailable: ignore behavior and tracked-data checks NOT performed.')
        return {'ignore_rules': 'not_checked', 'tracked_data': 'not_checked'}
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
    ignored = ['data/raw.csv', 'datasets/records.json', 'weights/model.bin', 'checkpoints/model.bin',
               'outputs/result.csv', 'results/result.json', 'runs/x/metrics.json', 'logs/stdout.txt',
               'generated_artifacts/task/receipt.json', 'sample.npz', 'model.ckpt', 'movie.gif', 'delivery.zip', '.env']
    allowed = ['README.md', 'AGENTS.md', 'TASKMEMORY.md', 'scripts/validate_records.py',
               'docs/provenance/task/manifest.json', 'docs/reports/result.md', 'generated_artifacts/README.md', '.env.example']
    # Simulate Git rules in a disposable repository; never initialize the user's project.
    with tempfile.TemporaryDirectory(prefix='maintenance-ignore-') as directory:
        temp = Path(directory)
        shutil.copy2(root / '.gitignore', temp / '.gitignore')
        subprocess.run([git, '-C', str(temp), 'init', '--quiet'], env=env, check=True, capture_output=True)
        for name in ignored + allowed:
            p = subprocess.run([git, '-C', str(temp), 'check-ignore', '--no-index', '--verbose', '-z', '--stdin'],
                               input=name + '\0', env=env, capture_output=True, text=True)
            expected = name in ignored
            fields = p.stdout.split('\0')
            # Explicit ! exceptions also return 0: inspect the matched pattern.
            actual_ignored = bool(p.stdout) and len(fields) >= 4 and not fields[2].startswith('!')
            if p.returncode not in (0, 1) or actual_ignored != expected:
                errors.append(f'Git ignore mismatch: {name} (expected ignored={expected})')
    probe = subprocess.run([git, '-C', str(root), 'rev-parse', '--show-toplevel'], env=env, capture_output=True, text=True)
    tracked = 'not_checked_no_repository'
    if probe.returncode == 0:
        p = subprocess.run([git, '-C', str(root), 'ls-files', '-z', '--', '.'], env=env, capture_output=True, check=True)
        names = [os.fsdecode(n) for n in p.stdout.split(b'\0') if n]
        for name in names:
            if local_data_path(Path(name)):
                errors.append(f'Experiment data/media already tracked by Git: {name}')
        tracked = f'checked_{len(names)}_files_in_project_scope'
    else:
        warnings.append('Project has no Git repository: tracked files not checked; ignore rules still tested.')
    return {'ignore_rule_probes': len(ignored) + len(allowed), 'tracked_data': tracked}


def validate(root):
    errors, warnings = [], []
    for name in REQUIRED:
        if not (root / name).is_file():
            errors.append(f'Missing required file: {name}')
    # Only read documentation, not large output trees or historical data.
    docs = sorted((root / 'docs').rglob('*.md'))
    documents = [root / n for n in ['README.md', 'AGENTS.md', 'TASKMEMORY.md', 'scripts/README.md', 'generated_artifacts/README.md']] + docs
    links_checked = 0
    for document in documents:
        if not document.is_file():
            continue
        text = re.sub(r'^```[^\n]*\n.*?^```\s*$', '', document.read_text(encoding='utf-8'), flags=re.M | re.S)
        for match in re.finditer(r'!?\[[^\]]*\]\((<[^>]+>|[^\s)]+)(?:\s+"[^\"]*")?\)', text):
            target = match.group(1).strip('<>')
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            path = document.parent / unquote(parsed.path)
            links_checked += 1
            if not inside(root, path) or not path.exists():
                errors.append(f'Broken or out-of-project link in {document.relative_to(root)}: {target}')
    records, kinds = {}, {}
    for kind, fields in FIELDS.items():
        path = root / 'docs/registry' / (kind + '.json')
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(payload, dict) or payload.get('schema') != 'project_maintenance_v1' or not isinstance(payload.get('records'), list):
                raise ValueError('Expected project_maintenance_v1 with records list')
        except (OSError, ValueError) as exc:
            errors.append(f'Cannot read {kind} registry: {exc}')
            continue
        for row in payload['records']:
            if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id'].strip():
                errors.append(f'{kind}: nonempty string id required')
                continue
            ident = row['id']
            if ident in records:
                errors.append(f'Duplicate registry id: {ident}')
                continue
            records[ident], kinds[ident] = row, kind
            missing = set(fields.split()) - row.keys()
            if missing:
                errors.append(f'{ident}: missing fields {sorted(missing)}')
            if not isinstance(row.get('status'), str) or row['status'] not in STATUSES:
                errors.append(f'{ident}: invalid status')
    evidence_checked = 0
    for ident, row in records.items():
        for field, kind in LINKS.items():
            values = row.get(field, [])
            if not isinstance(values, list):
                errors.append(f'{ident}: {field} must be a list')
                continue
            for ref in values:
                if not isinstance(ref, str) or kinds.get(ref) != kind:
                    errors.append(f'{ident}: invalid {field} reference {ref!r}')
        evidence = row.get('evidence')
        if not isinstance(evidence, list) or not evidence:
            errors.append(f'{ident}: nonempty evidence list required')
            continue
        for item in evidence:
            if not isinstance(item, dict) or not isinstance(item.get('path'), str) or not isinstance(item.get('sha256'), str):
                errors.append(f'{ident}: evidence requires path and sha256 strings')
                continue
            relative = Path(item['path'])
            path = root / relative
            if relative.is_absolute() or not inside(root, path) or local_data_path(relative) or not path.is_file():
                errors.append(f'{ident}: evidence must be an existing, project-relative metadata file: {relative}')
                continue
            if path.stat().st_size > 8 * 1024 * 1024:
                errors.append(f'{ident}: evidence exceeds 8 MiB metadata limit: {relative}')
                continue
            expected = item['sha256']
            if not re.fullmatch('[0-9a-f]{64}', expected) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                errors.append(f'{ident}: evidence SHA mismatch: {relative}')
            evidence_checked += 1
        if kinds[ident] == 'sites':
            site_runs = row.get('run_ids', [])
            for ref in row.get('evaluation_ids', []) if isinstance(row.get('evaluation_ids', []), list) else []:
                evaluation = records.get(ref) if isinstance(ref, str) else None
                needed = evaluation.get('run_ids', []) if evaluation else []
                if isinstance(needed, list) and isinstance(site_runs, list) and any(r not in site_runs for r in needed):
                    errors.append(f'{ident}: evaluation {ref} uses undeclared runs')
    active, done = set(), set()

    def visit(ident):
        if ident in active:
            errors.append(f'Parent-run cycle: {ident}')
            return
        if ident in done:
            return
        active.add(ident)
        parents = records[ident].get('parent_run_ids', [])
        for ref in parents if isinstance(parents, list) else []:
            if isinstance(ref, str) and kinds.get(ref) == 'runs':
                visit(ref)
        active.remove(ident)
        done.add(ident)

    for ident in records:
        visit(ident)
    git_result = {}
    if (root / '.gitignore').is_file():
        try:
            git_result = git_check(root, errors, warnings)
        except (OSError, subprocess.SubprocessError) as exc:
            errors.append(f'Git safety check failed: {exc}')
    return {'status': 'failed' if errors else 'passed', 'root': str(root), 'documents_checked': len(documents),
            'local_links_checked': links_checked, 'registry_records': len(records), 'evidence_files_checked': evidence_checked,
            'git': git_result, 'warnings': warnings, 'errors': errors,
            'scope': 'Maintenance structure, relative file links (not anchors), registry references and metadata SHA, common Git ignore rules and tracked data paths. No business/experiment/browser validation, external fetches, secret detection or proof of exclusion of every data format.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    result = validate(args.root.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
