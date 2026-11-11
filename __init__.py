import json
import subprocess
from .core import inspect_resources
from .motion import check_motion

def invoke(name, args):
    try:
        from .production import Production, TOOLS
        from .references import TOOLS as REF_TOOLS, References, run as run_reference
        if name in REF_TOOLS:
            from plugins.plugin_storage import plugin_data_dir
            return json.dumps(run_reference(References(plugin_data_dir('live2d-rigger')), name, args))
        if name in TOOLS:
            from plugins.plugin_storage import plugin_data_dir
            return json.dumps(getattr(Production(plugin_data_dir('live2d-rigger')),TOOLS[name][3])(**args))
        return json.dumps((check_motion if name == 'live2d_check_motion' else inspect_resources)(**args))
    except (ValueError, TypeError, OSError, UnicodeError, KeyError, RuntimeError, subprocess.TimeoutExpired) as exc:
        return json.dumps({'error': str(exc)})

def register(ctx):
    from .production import TOOLS
    for name,(description,props,required,method) in TOOLS.items():
        ctx.register_tool(name=name,toolset='live2d_rigger',schema={'name':name,'description':description,'parameters':{'type':'object','properties':props,'required':required,'additionalProperties':False}},handler=lambda args,_name=name,**kw:invoke(_name,args))
    from .references import TOOLS as REF_TOOLS
    for name,(description,props,required,_m) in REF_TOOLS.items():
        ctx.register_tool(name=name,toolset='live2d_rigger',schema={'name':name,'description':description,'parameters':{'type':'object','properties':props,'required':required,'additionalProperties':False}},handler=lambda args,_name=name,**kw:invoke(_name,args))
    if hasattr(ctx, 'register_skill'):
        from pathlib import Path
        ctx.register_skill('live2d-rigger', Path(__file__).parent / 'skills/live2d-rigger/SKILL.md', description='Create and rig editable Live2D characters from a brief through layered artwork, native authoring and motion review')
    ctx.register_tool(name='live2d_inspect_resources', toolset='live2d_rigger', schema={'name': 'live2d_inspect_resources',
        'description': 'Inspect model3.json references for missing or unsafe model, texture, physics, expression and motion resources. This does not inspect or render the rig.',
        'parameters': {'type': 'object', 'properties': {'model_path': {'type': 'string'}}, 'required': ['model_path'], 'additionalProperties': False}},
        handler=lambda args, **kwargs: invoke('live2d_inspect_resources', args))
    ctx.register_tool(name='live2d_check_motion', toolset='live2d_rigger', schema={'name': 'live2d_check_motion',
        'description': 'Check Cubism motion curve structure and compare targets with supplementary display-info IDs without rendering.',
        'parameters': {'type': 'object', 'properties': {'cdi_path': {'type': 'string'}, 'motion_path': {'type': 'string'}}, 'required': ['cdi_path', 'motion_path'], 'additionalProperties': False}},
        handler=lambda args, **kwargs: invoke('live2d_check_motion', args))
