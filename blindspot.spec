# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build specification for compiling standalone BlindSpot executables.
Produces a single, self-contained binary for Windows (blindspot.exe), macOS, and Linux.
"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

project_root = Path(SPECPATH)
src_root = project_root / 'src' / 'blindspot'

datas = []

# Collect knowledge playbooks
for md_file in (src_root / 'knowledge').rglob('*.md'):
    rel_path = md_file.relative_to(project_root)
    datas.append((str(md_file), str(rel_path.parent)))

# Collect bundled agent skills
for skill_file in (src_root / 'skills').rglob('*.md'):
    rel_path = skill_file.relative_to(project_root)
    datas.append((str(skill_file), str(rel_path.parent)))

# Collect web templates / static files
for html_file in src_root.rglob('*.html'):
    rel_path = html_file.relative_to(project_root)
    datas.append((str(html_file), str(rel_path.parent)))

datas += collect_data_files('litellm')
datas += collect_data_files('playwright')

hiddenimports = [
    'blindspot',
    'blindspot.cli',
    'blindspot.core',
    'blindspot.core.session',
    'blindspot.tools',
    'blindspot.knowledge',
    'blindspot.ai',
    'blindspot.browser',
    'blindspot.execution',
    'blindspot.reporting',
    'blindspot.reporting.sarif',
    'blindspot.mcp',
    'blindspot.web',
    'litellm',
    'litellm.llms',
    'litellm.llms.openai',
    'litellm.llms.anthropic',
    'rich',
    'rich.console',
    'rich.table',
    'rich.panel',
    'pydantic',
    'playwright',
    'typer',
    'fastapi',
    'uvicorn',
]

a = Analysis(
    [str(src_root / 'cli.py')],
    pathex=[str(project_root / 'src')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='blindspot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
