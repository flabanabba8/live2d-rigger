"""Use an explicitly configured installed Umamo toolchain for a static layer export."""
import os
import shutil
import subprocess
from pathlib import Path


def toolchain(resources=None):
    resources = resources or {}
    java = resources.get('java') or os.environ.get('LIVE2D_JAVA') or (str(Path(os.environ['JAVA_HOME']) / 'bin/java') if os.environ.get('JAVA_HOME') else shutil.which('java'))
    compiler = resources.get('umamo_compiler_classpath') or os.environ.get('LIVE2D_UMAMO_COMPILER_CLASSPATH', '')
    runtime = resources.get('umamo_runtime_classpath') or os.environ.get('LIVE2D_UMAMO_RUNTIME_CLASSPATH', '')
    missing = []
    if not java or not Path(java).is_file(): missing.append('JDK 21 executable (set LIVE2D_JAVA or JAVA_HOME)')
    for key, value in [('LIVE2D_UMAMO_COMPILER_CLASSPATH', compiler), ('LIVE2D_UMAMO_RUNTIME_CLASSPATH', runtime)]:
        if not value or any(not Path(p).exists() for p in value.split(os.pathsep)): missing.append(key + ' (existing installed compiler/library paths)')
    if missing: raise ValueError('Umamo authoring is unavailable: set ' + '; '.join(missing))
    return java, compiler, runtime


def build(project, output, timeout=300, resources=None, prototype=False):
    java, compiler, runtime = toolchain(resources)
    classes = project / 'umamo-classes'
    classes.mkdir(exist_ok=True)
    source = Path(__file__).with_name('umamo_prototype.kt' if prototype else 'umamo_template.kt')
    log = project / 'umamo-build.log'
    with log.open('wb') as stream:
        command = [java, '-Xmx1g', '-cp', compiler, 'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler', '-no-stdlib', '-no-reflect', '-jvm-target', '21', '-classpath', runtime, '-d', str(classes), str(source)]
        if subprocess.run(command, stdout=stream, stderr=stream, timeout=timeout).returncode:
            raise RuntimeError('Umamo source compilation failed; see the private umamo-build.log')
        if subprocess.run([java, '-Xmx1g', '-cp', str(classes) + os.pathsep + runtime, ('org.umamo.cli.Umamo_prototypeKt' if prototype else 'org.umamo.cli.Umamo_templateKt'), str(project), str(output)], stdout=stream, stderr=stream, timeout=timeout).returncode:
            raise RuntimeError('Umamo export failed; see the private umamo-build.log')
    if prototype:add_hair_physics(output)


def add_hair_physics(output):
    """Add a small, explicitly experimental two-particle hair spring."""
    import json
    marker=output/'prototype-has-hair.txt'
    if not marker.exists() or marker.read_text().strip()!='true':
        marker.unlink(missing_ok=True)
        return
    marker.unlink()
    normal={'Minimum':-1.0,'Maximum':1.0,'Default':0.0}
    doc={
        'Version':3,
        'Meta':{'PhysicsSettingCount':1,'TotalInputCount':1,'TotalOutputCount':1,'VertexCount':2,
                'Fps':30.0,'EffectiveForces':{'Gravity':{'X':0.0,'Y':-1.0},'Wind':{'X':0.0,'Y':0.0}},
                'PhysicsDictionary':[{'Id':'HairBack','Name':'Experimental back hair'}]},
        'PhysicsSettings':[{'Id':'HairBack','Normalization':{'Position':normal,'Angle':{'Minimum':-10.0,'Maximum':10.0,'Default':0.0}},
            'Input':[{'Source':{'Target':'Parameter','Id':'ParamAngleZ'},'Weight':100.0,'Type':'Angle','Reflect':False}],
            'Output':[{'Destination':{'Target':'Parameter','Id':'ParamHairBack'},'VertexIndex':1,'Scale':1.0,'Weight':100.0,'Type':'Angle','Reflect':False}],
            'Vertices':[{'Position':{'X':0.0,'Y':0.0},'Mobility':1.0,'Delay':0.0,'Acceleration':1.0,'Radius':0.0},
                        {'Position':{'X':0.0,'Y':1.0},'Mobility':0.8,'Delay':0.2,'Acceleration':1.0,'Radius':1.0}]}]}
    target=output/'Model.physics3.json';target.write_text(json.dumps(doc,indent=2))
    model=output/'Model.model3.json';settings=json.loads(model.read_text());settings['FileReferences']['Physics']=target.name;model.write_text(json.dumps(settings,indent=2))
