import json
import subprocess
from .core import inspect_resources
from .motion import check_motion

SETUP = ('First-use interview and environment scan. Without answers: returns what this computer has (JDK, Umamo and image tools on PATH, GPU, which image-service keys exist as yes/no), suggestions for image generation (hosted services with price, free tier, transparent-background and reference-edit support; local models that fit the GPU), cutout tools with licences, and rigging toolchains with their limits (Cubism FREE caps, Umamo alpha status, Inochi2D/nijigenerate), whether the built-in knowledge looks out of date (offering online research only if the user says yes), and the questions to ask. With answers: saves them, including the image, cutout and rigging routes the user picked. The plugin never picks for the user. Generates nothing, installs nothing, sends nothing. live2d_begin_model and live2d_build_model return the interview until it is answered.',
         {'answers': {'type': 'object', 'description': 'character (text), source (own art|ai generated|existing model|official sample), use (personal|vtubing|game|commercial), small_scale (true|false|null), allow_upload (bool), budget_usd (number), has (text), image_route, cutout_route, rig_route (the ids the user picked).'}, 'knowledge_updates': {'type': 'array', 'maxItems': 100, 'items': {'type': 'object'}, 'description': 'Only after the user said yes to online research: facts you verified on primary pages. Each item: id (from the wiki tables), field, value, source (https page), date (the day you read it). Saved as dated overrides; the shipped catalog is unchanged.'}}, [])
GATED = ('live2d_begin_model', 'live2d_build_model')


SETTING_KEYS = ('java', 'umamo_classpath_file', 'render_python', 'viewer_dir', 'authoring_command', 'motion_command')


def owner_settings(ctx):
    """The plugin settings only the owner can set; the model cannot change them through tool arguments."""
    get = getattr(ctx, 'get_config', None)
    out = {}
    for key in SETTING_KEYS:
        try:
            value = get(key) if get else None
        except Exception:
            value = None
        if value: out[key] = value
    return out


def invoke(name, args, ctx=None):
    try:
        if name == 'live2d_setup' or name in GATED:
            from plugins.plugin_storage import plugin_data_dir
            from . import resources as R
            root = plugin_data_dir('live2d-rigger')
            if name == 'live2d_setup':
                return json.dumps(R.apply_setup(root, R.survey(root, owner_settings=owner_settings(ctx)), args.get('answers'), args.get('knowledge_updates')))
            profile = R.load_profile(root)
            if profile is None or not all(profile.get(k) for k in R.ROUTE_KEYS):
                return json.dumps({**R.interview(root, R.survey(root, owner_settings=owner_settings(ctx))), 'next': 'Do not pick the routes for the user. Run the interview first (live2d_setup), then repeat this call.'})
        from .production import Production, TOOLS
        from .references import TOOLS as REF_TOOLS, References, run as run_reference
        if name in REF_TOOLS:
            from plugins.plugin_storage import plugin_data_dir
            return json.dumps(run_reference(References(plugin_data_dir('live2d-rigger')), name, args))
        if name in TOOLS:
            from plugins.plugin_storage import plugin_data_dir
            return json.dumps(getattr(Production(plugin_data_dir('live2d-rigger'),owner_settings(ctx)),TOOLS[name][3])(**args))
        if name in ('live2d_check_motion', 'live2d_inspect_resources') and 'own_root' in args: raise ValueError('own_root is not a tool argument')
        return json.dumps((check_motion if name == 'live2d_check_motion' else inspect_resources)(**args))
    except (ValueError, TypeError, OSError, UnicodeError, KeyError, RuntimeError, subprocess.TimeoutExpired) as exc:
        return json.dumps({'error': str(exc)})

def register(ctx):
    from .production import TOOLS
    for name,(description,props,required,method) in TOOLS.items():
        ctx.register_tool(name=name,toolset='live2d_rigger',schema={'name':name,'description':description,'parameters':{'type':'object','properties':props,'required':required,'additionalProperties':False}},handler=lambda args,_name=name,**kw:invoke(_name,args,ctx))
    from .references import TOOLS as REF_TOOLS
    for name,(description,props,required,_m) in REF_TOOLS.items():
        ctx.register_tool(name=name,toolset='live2d_rigger',schema={'name':name,'description':description,'parameters':{'type':'object','properties':props,'required':required,'additionalProperties':False}},handler=lambda args,_name=name,**kw:invoke(_name,args,ctx))
    ctx.register_tool(name='live2d_setup', toolset='live2d_rigger', schema={'name': 'live2d_setup', 'description': SETUP[0], 'parameters': {'type': 'object', 'properties': SETUP[1], 'required': SETUP[2], 'additionalProperties': False}},
                      handler=lambda args, **kwargs: invoke('live2d_setup', args, ctx))
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
