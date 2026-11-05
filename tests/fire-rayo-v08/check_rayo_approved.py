#!/usr/bin/env python3
"""Verify the immutable approved V07 shader text is preserved in the extracted module."""
from pathlib import Path
import re
source=Path('tests/rayo-premium-v01/rayo-premium.js').read_text()
module=Path('vfx/approved/Genesis_Rayo_Helicoidal_V07.mjs').read_text()
for name in ('vertexGLSL','fragmentGLSL'):
    pattern=r'const '+name+r'=\x60([\s\S]*?)\x60;'
    orig=re.search(pattern,source)
    copy=re.search(pattern,module)
    assert orig and copy, name+' GLSL block missing'
    assert orig.group(1)==copy.group(1), name+' V07 APPROVED SHADER MODIFIED!'
assert 'const turns=3.15,steps=580;' in module
assert 'const ribbonHalfWidth=.020;' in module
assert 'Genesis_Rayo_Helice3D_V006_PresenceAt60' in module
print('GENESIS_V07_APPROVED_GLSL_UNCHANGED: vertex+fragment source byte-exact, helix geometry parameters preserved')
