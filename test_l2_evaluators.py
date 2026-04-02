#!/usr/bin/env python3
"""Test all 11 new L2 evaluator functions for Kdenlive."""
import importlib.util
import os
import tempfile
import logging

logging.basicConfig(level=logging.CRITICAL)

spec = importlib.util.spec_from_file_location(
    'kdenlive',
    '/apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld/desktop_env/evaluators/metrics/kdenlive.py'
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

errors = []

def mk(xml):
    f = tempfile.NamedTemporaryFile(mode='w', suffix='.kdenlive', delete=False)
    f.write(xml)
    f.close()
    return f.name

def t(name, exp, act):
    if exp != act:
        errors.append(f'{name}: expected={exp}, got={act}')
        print(f'  X {name}: expected={exp}, got={act}')
    else:
        print(f'  OK {name}')


# === 1: check_kdenlive_clip_trim ===
print('=== clip_trim ===')
xml = '''<?xml version="1.0"?><mlt>
<profile frame_rate_num="30" frame_rate_den="1"/>
<producer id="p1"><property name="resource">/Videos/test.mp4</property></producer>
<playlist id="pl1"><entry producer="p1" in="60" out="240"/></playlist></mlt>'''
tmp = mk(xml)
t('trim_ok', 1.0, mod.check_kdenlive_clip_trim(tmp, {'source_file': 'test.mp4', 'in_time': 2.0, 'out_time': 8.0, 'tolerance': 0.5}))
t('trim_fail', 0.0, mod.check_kdenlive_clip_trim(tmp, {'source_file': 'test.mp4', 'in_time': 5.0, 'out_time': 10.0, 'tolerance': 0.5}))
os.unlink(tmp)

# === 2: check_kdenlive_transition ===
print('=== transition ===')
xml = '''<?xml version="1.0"?><mlt>
<transition id="t1"><property name="mlt_service">luma</property></transition></mlt>'''
tmp = mk(xml)
t('luma_found', 1.0, mod.check_kdenlive_transition(tmp, {'transition_type': 'luma'}))
t('composite_not', 0.0, mod.check_kdenlive_transition(tmp, {'transition_type': 'composite'}))
os.unlink(tmp)

xml2 = '''<?xml version="1.0"?><mlt>
<transition id="t1"><property name="mlt_service">qtblend</property></transition></mlt>'''
tmp2 = mk(xml2)
t('composite_qtblend', 1.0, mod.check_kdenlive_transition(tmp2, {'transition_type': 'composite'}))
os.unlink(tmp2)

# === 3: check_kdenlive_title_text ===
print('=== title_text ===')
xml = '''<?xml version="1.0"?><mlt>
<producer id="p1"><property name="mlt_service">kdenlivetitle</property>
<property name="xmldata">&lt;kdenlivetitle&gt;&lt;item&gt;&lt;content&gt;Hello World&lt;/content&gt;&lt;/item&gt;&lt;/kdenlivetitle&gt;</property>
</producer></mlt>'''
tmp = mk(xml)
t('title_found', 1.0, mod.check_kdenlive_title_text(tmp, {'expected_text': 'Hello World'}))
t('title_missing', 0.0, mod.check_kdenlive_title_text(tmp, {'expected_text': 'Goodbye'}))
os.unlink(tmp)

# === 4: check_kdenlive_clip_speed ===
print('=== clip_speed ===')
xml = '''<?xml version="1.0"?><mlt>
<chain id="c1"><property name="resource">2.000000:/Videos/test.mp4</property>
<property name="warp_speed">2.000000</property></chain></mlt>'''
tmp = mk(xml)
t('speed_2x', 1.0, mod.check_kdenlive_clip_speed(tmp, {'source_file': 'test.mp4', 'expected_speed': 2.0, 'tolerance': 0.1}))
t('speed_1x_fail', 0.0, mod.check_kdenlive_clip_speed(tmp, {'source_file': 'test.mp4', 'expected_speed': 1.0, 'tolerance': 0.1}))
os.unlink(tmp)

# Resource prefix format
xml2 = '''<?xml version="1.0"?><mlt>
<producer id="p1"><property name="resource">0.500000:/Videos/slow.mp4</property></producer></mlt>'''
tmp2 = mk(xml2)
t('speed_half', 1.0, mod.check_kdenlive_clip_speed(tmp2, {'source_file': 'slow.mp4', 'expected_speed': 0.5, 'tolerance': 0.1}))
os.unlink(tmp2)

# === 5: check_kdenlive_effect_applied ===
print('=== effect_applied ===')
xml = '''<?xml version="1.0"?><mlt>
<producer id="p1"><property name="resource">/Videos/test.mp4</property></producer>
<filter id="f1"><property name="mlt_service">box_blur</property></filter></mlt>'''
tmp = mk(xml)
t('blur_found', 1.0, mod.check_kdenlive_effect_applied(tmp, {'effect_service': ['box_blur', 'blur'], 'source_file': 'test.mp4'}))
t('sepia_not', 0.0, mod.check_kdenlive_effect_applied(tmp, {'effect_service': ['sepia'], 'source_file': 'test.mp4'}))
os.unlink(tmp)

# Test kdenlive_id matching
xml2 = '''<?xml version="1.0"?><mlt>
<filter id="f1"><property name="mlt_service">frei0r.something</property>
<property name="kdenlive_id">brightness</property></filter></mlt>'''
tmp2 = mk(xml2)
t('kdenlive_id', 1.0, mod.check_kdenlive_effect_applied(tmp2, {'effect_service': ['brightness']}))
os.unlink(tmp2)

# === 6: check_kdenlive_effect_param ===
print('=== effect_param ===')
xml = '''<?xml version="1.0"?><mlt>
<filter id="f1"><property name="mlt_service">affine</property>
<property name="rotate">90</property></filter></mlt>'''
tmp = mk(xml)
t('rotate_90', 1.0, mod.check_kdenlive_effect_param(tmp, {'effect_service': ['affine'], 'param_name': 'rotate', 'expected_value': 90, 'tolerance': 5}))
t('rotate_180_fail', 0.0, mod.check_kdenlive_effect_param(tmp, {'effect_service': ['affine'], 'param_name': 'rotate', 'expected_value': 180, 'tolerance': 5}))
os.unlink(tmp)

# Keyframe format
xml2 = '''<?xml version="1.0"?><mlt>
<filter id="f1"><property name="mlt_service">qtblend</property>
<property name="opacity">0=0.5</property></filter></mlt>'''
tmp2 = mk(xml2)
t('opacity_kf', 1.0, mod.check_kdenlive_effect_param(tmp2, {'effect_service': ['qtblend'], 'param_name': 'opacity', 'expected_value': 0.5, 'tolerance': 0.1}))
os.unlink(tmp2)

# === 7: check_kdenlive_audio_fade ===
print('=== audio_fade ===')
xml = '''<?xml version="1.0"?><mlt>
<filter id="f1"><property name="mlt_service">volume</property>
<property name="kdenlive_id">fadein</property></filter>
<filter id="f2"><property name="mlt_service">volume</property>
<property name="kdenlive_id">fadeout</property></filter></mlt>'''
tmp = mk(xml)
t('both_fades', 1.0, mod.check_kdenlive_audio_fade(tmp, {'fade_in': True, 'fade_out': True}))
os.unlink(tmp)

xml2 = '''<?xml version="1.0"?><mlt>
<filter id="f1"><property name="mlt_service">volume</property>
<property name="kdenlive_id">fadein</property></filter></mlt>'''
tmp2 = mk(xml2)
t('only_in', 1.0, mod.check_kdenlive_audio_fade(tmp2, {'fade_in': True, 'fade_out': False}))
t('need_out_fail', 0.0, mod.check_kdenlive_audio_fade(tmp2, {'fade_in': True, 'fade_out': True}))
os.unlink(tmp2)

# Keyframe-based volume fade
xml3 = '''<?xml version="1.0"?><mlt>
<filter id="f1"><property name="mlt_service">volume</property>
<property name="level">0=0.0
50=1.0</property></filter></mlt>'''
tmp3 = mk(xml3)
t('kf_fade_in', 1.0, mod.check_kdenlive_audio_fade(tmp3, {'fade_in': True, 'fade_out': False}))
os.unlink(tmp3)

# === 8: check_kdenlive_clip_split ===
print('=== clip_split ===')
xml = '''<?xml version="1.0"?><mlt>
<producer id="p1"><property name="resource">/Videos/test.mp4</property></producer>
<playlist id="pl1">
<entry producer="p1" in="0" out="149"/>
<entry producer="p1" in="150" out="299"/>
</playlist></mlt>'''
tmp = mk(xml)
t('split_2', 1.0, mod.check_kdenlive_clip_split(tmp, {'source_file': 'test.mp4', 'min_segments': 2}))
t('split_3_fail', 0.0, mod.check_kdenlive_clip_split(tmp, {'source_file': 'test.mp4', 'min_segments': 3}))
os.unlink(tmp)

# === 9: check_kdenlive_multi_track_composition ===
print('=== multi_track_composition ===')
xml = '''<?xml version="1.0"?><mlt>
<producer id="p1"><property name="resource">/Videos/main.mp4</property></producer>
<producer id="p2"><property name="resource">/Videos/overlay.mp4</property></producer>
<playlist id="pl1"><entry producer="p1" in="0" out="100"/></playlist>
<playlist id="pl2"><entry producer="p2" in="0" out="100"/></playlist>
<transition id="t1"><property name="mlt_service">qtblend</property></transition></mlt>'''
tmp = mk(xml)
t('pip_ok', 1.0, mod.check_kdenlive_multi_track_composition(tmp, {'main_file': 'main.mp4', 'overlay_file': 'overlay.mp4', 'require_transform': True}))
os.unlink(tmp)

# Same track - should fail
xml2 = '''<?xml version="1.0"?><mlt>
<producer id="p1"><property name="resource">/Videos/main.mp4</property></producer>
<producer id="p2"><property name="resource">/Videos/overlay.mp4</property></producer>
<playlist id="pl1"><entry producer="p1" in="0" out="100"/><entry producer="p2" in="0" out="100"/></playlist>
<transition id="t1"><property name="mlt_service">qtblend</property></transition></mlt>'''
tmp2 = mk(xml2)
t('same_track_fail', 0.0, mod.check_kdenlive_multi_track_composition(tmp2, {'main_file': 'main.mp4', 'overlay_file': 'overlay.mp4', 'require_transform': True}))
os.unlink(tmp2)

# === 10: check_kdenlive_clip_count ===
print('=== clip_count ===')
xml = '''<?xml version="1.0"?><mlt>
<producer id="p1"><property name="resource">/Videos/test.mp4</property></producer>
<playlist id="pl1">
<entry producer="p1" in="0" out="100"/>
<entry producer="p1" in="0" out="100"/>
<entry producer="p1" in="0" out="100"/>
</playlist></mlt>'''
tmp = mk(xml)
t('count_3', 1.0, mod.check_kdenlive_clip_count(tmp, {'source_file': 'test.mp4', 'min_count': 2}))
t('count_4_fail', 0.0, mod.check_kdenlive_clip_count(tmp, {'source_file': 'test.mp4', 'min_count': 4}))
os.unlink(tmp)

# === 11: check_kdenlive_clip_group ===
print('=== clip_group ===')
xml = '''<?xml version="1.0"?><mlt>
<playlist id="main_bin">
<property name="kdenlive:docproperties.groups">[{"type":"AVGroup","children":["1","2","3"]}]</property>
</playlist></mlt>'''
tmp = mk(xml)
t('group_found', 1.0, mod.check_kdenlive_clip_group(tmp, {'min_groups': 1, 'min_clips_in_group': 2}))
t('need_2_groups', 0.0, mod.check_kdenlive_clip_group(tmp, {'min_groups': 2, 'min_clips_in_group': 2}))
os.unlink(tmp)

# No groups
xml2 = '''<?xml version="1.0"?><mlt><playlist id="main_bin"></playlist></mlt>'''
tmp2 = mk(xml2)
t('no_groups', 0.0, mod.check_kdenlive_clip_group(tmp2, {'min_groups': 1, 'min_clips_in_group': 2}))
os.unlink(tmp2)


print()
if errors:
    print(f'FAILURES: {len(errors)}')
    for e in errors:
        print(f'  {e}')
else:
    print('ALL L2 EVALUATOR TESTS PASSED!')
