import json
from .core import inspect_resources
from .motion import check_motion

def invoke(name, args):
    try:
        return json.dumps((check_motion if name == 'live2d_check_motion' else inspect_resources)(**args))
    except (ValueError, TypeError, OSError, UnicodeError, KeyError) as exc:
        return json.dumps({'error': str(exc)})

def register(ctx):
    ctx.register_tool(name='live2d_inspect_resources', toolset='live2d_rig_doctor', schema={'name': 'live2d_inspect_resources',
        'description': 'Inspect model3.json references for missing or unsafe model, texture, physics, expression and motion resources. This does not inspect or render the rig.',
        'parameters': {'type': 'object', 'properties': {'model_path': {'type': 'string'}}, 'required': ['model_path'], 'additionalProperties': False}},
        handler=lambda args, **kwargs: invoke('live2d_inspect_resources', args))
    ctx.register_tool(name='live2d_check_motion', toolset='live2d_rig_doctor', schema={'name': 'live2d_check_motion',
        'description': 'Check Cubism motion curve structure and compare targets with supplementary display-info IDs without rendering.',
        'parameters': {'type': 'object', 'properties': {'cdi_path': {'type': 'string'}, 'motion_path': {'type': 'string'}}, 'required': ['cdi_path', 'motion_path'], 'additionalProperties': False}},
        handler=lambda args, **kwargs: invoke('live2d_check_motion', args))
