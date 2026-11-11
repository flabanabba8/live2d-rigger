"""Own complete model-production projects; use real selected authoring/render toolchains."""
import hashlib,json,os,re,shutil,signal,subprocess,uuid
from pathlib import Path
from .core import inspect_resources

IDENT=re.compile(r'^[0-9a-f]{32}$')
AGENTS={'codex','claude','gemini','hermes'}
def save(path,value):
    tmp=path.with_name(uuid.uuid4().hex+'.tmp')
    with os.fdopen(os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w')as f:json.dump(value,f,indent=2)
    tmp.replace(path)
def digest(path):
    with Path(path).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()

class Production:
    def __init__(self,root):self.root=Path(root)/'model-projects';self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
    def load(self,model_id):
        if not isinstance(model_id,str)or not IDENT.fullmatch(model_id):raise ValueError('Invalid model production ID')
        p=self.root/model_id
        if p.is_symlink()or not(p/'model-project.json').is_file():raise ValueError('Model project not found')
        return p,json.loads((p/'model-project.json').read_text())
    def begin(self,name,brief,resources=None):
        if not isinstance(name,str)or not name.strip()or len(name)>120 or not isinstance(brief,str)or not brief.strip()or len(brief)>12000:raise ValueError('Supply a character name and complete bounded brief')
        if resources is not None and(not isinstance(resources,dict)or len(json.dumps(resources))>12000):raise ValueError('Resource choices must be a bounded non-secret object')
        ident=uuid.uuid4().hex;p=self.root/ident;p.mkdir(mode=0o700);(p/'layers').mkdir();(p/'src').mkdir();data={'model_id':ident,'name':name,'brief':brief,'resources':resources or{},'layers':[],'rig_file':None,'phase':'design','accepted':False};save(p/'model-project.json',data)
        return {**data,'project_path':str(p),'next_steps':['Use the active host and native MAIN-session image tools to design complete editable parts, including hidden backing regions.','Review/import complete layers; author an executable rig using the selected real producer’s API, not guessed coefficients from another character.','Build through a real authoring toolchain; inspect compiled resources, run actual Core/domain checks and render motion.','Deliver source/layers, rig, native editable/runtime exports and reviewed animation. No physical camera/VTS/tracking or installation is authorized automatically.'],'notice':'Production started; no model has been generated or rigged yet.'}
    def layer(self,model_id,name,role,source_path,review_note,x=None,y=None):
        p,data=self.load(model_id)
        if any(l['name']==name for l in data['layers']):raise ValueError('Layer names must be unique within a model; use a stable role name such as Eye_L_Iris')
        if(x is None)!=(y is None)or any(v is not None and(type(v)is not int or abs(v)>100000)for v in(x,y)):raise ValueError('Give both integer x and y placement offsets, or neither for a full shared-canvas layer')
        if len(data['layers'])>=160:raise ValueError('Split this production part; layer limit160')
        if not all(isinstance(v,str)and v.strip()and len(v)<=2000 for v in(name,role,review_note)):raise ValueError('Name, complete-part role and actual main-session review note are required')
        source=Path(source_path).expanduser()
        if source.is_symlink()or source.suffix.lower()!='.png'or any(x in source.parts for x in('.ssh','.aws','.gnupg','.env')):raise ValueError('Choose a reviewed regular PNG, not private configuration')
        if not source.is_file()or source.stat().st_size>32*1024**2:raise ValueError('Select a bounded PNG layer')
        from PIL import Image
        with Image.open(source)as image:
            if image.mode!='RGBA':raise ValueError('Model layers need actual RGBA transparency')
            size=image.size;image.verify()
        full=[l['dimensions']for l in data['layers']if l.get('offset')is None]
        if x is None and full and list(size)!=list(full[0]):raise ValueError('Full-canvas layers must share one canvas size (%s); give x and y offsets for cropped parts'%full[0])
        dest=p/'layers'/(uuid.uuid4().hex+'.png');before=source.stat();shutil.copyfile(source,dest);dest.chmod(0o600);after=source.stat()
        if(before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns):dest.unlink();raise ValueError('Layer changed during import')
        row={'name':name,'role':role,'path':str(dest.relative_to(p)),'dimensions':size,'offset':None if x is None else[x,y],'sha256':digest(dest),'review_note':review_note};data['layers'].append(row);data['phase']='artwork';save(p/'model-project.json',data);return row
    def rig(self,model_id,source,filename='ModelRig.kt'):
        p,data=self.load(model_id)
        if not data['layers']:raise ValueError('Create/review actual complete parts before authoring the rig')
        if not isinstance(filename,str)or Path(filename).name!=filename or Path(filename).suffix not in('.kt','.json','.py'):raise ValueError('Use a simple rig source filename for the selected authoring toolchain')
        if not isinstance(source,str)or not source.strip()or len(source)>400000:raise ValueError('Supply executable rig source from the actual selected authoring contract')
        out=p/'src'/filename
        if out.exists():out=out.with_name(out.stem+'-'+uuid.uuid4().hex[:6]+out.suffix)
        out.write_text(source);out.chmod(0o600);data.update(rig_file=str(out.relative_to(p)),phase='rig_authored');save(p/'model-project.json',data);return {'rig_source':str(out),'phase':data['phase'],'notice':'Source saved, not proof of a compiled or usable rig. Build and inspect actual output next.'}
    def command(self,p,argv,output,timeout_seconds=300):
        if not isinstance(argv,list)or not argv or len(argv)>100 or not all(isinstance(x,str)and len(x)<=8000 for x in argv):raise ValueError('Select a trusted native authoring/render command argument array')
        if Path(argv[0]).name.lower().removesuffix('.exe')in AGENTS or any(Path(x).name=='agent.sh'for x in argv):raise ValueError('Use a real authoring/render toolchain, not another agent session')
        if not any('{project}'in x for x in argv)or not any('{output}'in x for x in argv):raise ValueError('Selected toolchain arguments need explicit {project} and {output} paths')
        if type(timeout_seconds)is not int or not 1<=timeout_seconds<=900:raise ValueError('Choose a1–900second bounded operation')
        actual=[x.replace('{project}',str(p)).replace('{output}',str(output))for x in argv];log=p/(uuid.uuid4().hex+'-tool.log');env={k:v for k,v in os.environ.items()if k in('PATH','HOME','JAVA_HOME','LANG','LC_ALL','SystemRoot','TEMP','TMP','TMPDIR')}
        with log.open('wb')as stream:
            log.chmod(0o600);proc=subprocess.Popen(actual,cwd=p,env=env,stdin=subprocess.DEVNULL,stdout=stream,stderr=stream,start_new_session=os.name!='nt')
            try:proc.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                if os.name!='nt':os.killpg(proc.pid,signal.SIGKILL)
                else:proc.kill()
                proc.wait(timeout=5);raise RuntimeError('Owned native toolchain timed out; no automatic reroll or agent fallback')from None
        if proc.returncode:raise RuntimeError('Selected native authoring/render operation failed; private diagnostics retained')
    def build(self,model_id,command_argv,timeout_seconds=300):
        p,data=self.load(model_id)
        if not data['rig_file']:raise ValueError('Author the actual rig first')
        for layer in data['layers']:
            if digest(p/layer['path'])!=layer['sha256']:raise ValueError('Reviewed layer changed; re-establish the artwork contract')
        output=p/('build-'+uuid.uuid4().hex[:8]);output.mkdir();self.command(p,command_argv,output,timeout_seconds)
        models=list(output.rglob('*.model3.json'))
        if len(models)!=1:raise ValueError('The native producer must emit one actual Cubism model3.json package; no model placeholder accepted')
        if models[0].is_symlink()or not models[0].resolve().is_relative_to(output.resolve()):raise ValueError('Native model package must remain inside its build directory')
        report=inspect_resources(str(models[0]))
        if report['issues']or any(x['status']!='present'for x in report['resources']):raise ValueError('Native model package has unsafe or missing resources; no compiled success claimed')
        settings=json.loads(models[0].read_text());moc=models[0].parent/settings['FileReferences']['Moc']
        with moc.open('rb')as f:magic=f.read(4)
        if magic!=b'MOC3':raise ValueError('The selected producer did not emit native MOC3 bytes')
        data.update(phase='compiled_needs_core_and_motion_review',build_root=str(output.relative_to(p)),model_path=str(models[0].relative_to(p)),moc_sha256=digest(moc),native_editable_documents=[str(x.relative_to(p))for x in output.rglob('*.cmo3')],resource_report=report);save(p/'model-project.json',data)
        return {'model_id':model_id,'model_path':str(models[0]),'moc_sha256':data['moc_sha256'],'native_editable_documents':data['native_editable_documents'],'phase':data['phase'],'notice':'Native output package is present; its header/reference checks do not prove MOC3 validity or Core/appearance/human-motion acceptance. Inspect domains and render through the real SDK; original layers and executable rig source are retained separately.'}
    def motion(self,model_id,command_argv,timeout_seconds=300):
        p,data=self.load(model_id)
        if not data.get('model_path'):raise ValueError('Compile a native model before motion review')
        output=p/('motion-'+uuid.uuid4().hex[:8]);output.mkdir();self.command(p,command_argv,output,timeout_seconds);videos=list(output.rglob('*.mp4'))
        if not videos:raise ValueError('Selected renderer produced no motion video; no animation success inferred')
        probe=shutil.which('ffprobe');decoder=shutil.which('ffmpeg')
        if not probe or not decoder:raise ValueError('Motion review requires selected installed ffprobe and ffmpeg; output retained, no success inferred')
        for video in videos:
            if video.is_symlink()or not video.resolve().is_relative_to(output.resolve())or not video.stat().st_size:raise ValueError('Renderer output must be a nonempty regular video in its own output directory')
            checked=subprocess.run([probe,'-v','error','-select_streams','v:0','-show_entries','stream=width,height:format=duration','-of','json',str(video)],capture_output=True,timeout=15)
            try:metadata=json.loads(checked.stdout);duration=float(metadata['format']['duration']);stream=metadata['streams'][0]
            except (ValueError,KeyError,IndexError):raise ValueError('Renderer output is not a measured motion video')from None
            if checked.returncode or not 0<duration<=900 or not stream.get('width')or not stream.get('height'):raise ValueError('Renderer output failed motion metadata checks')
            decoded=subprocess.run([decoder,'-v','error','-xerror','-i',str(video),'-map','0:v:0','-an','-f','null','-'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=60)
            if decoded.returncode:raise ValueError('Renderer video failed full frame decoding; output retained for diagnosis')
        data.update(phase='motion_review_pending',motion_videos=[str(x.relative_to(p))for x in videos]);save(p/'model-project.json',data)
        return {'model_id':model_id,'videos':[str(x)for x in videos],'phase':data['phase'],'notice':'Inspect actual frames/motion in the MAIN session and report remaining issues. No physical camera, tracking or VTS installation was performed by this workflow.'}
    def status(self,model_id):return self.load(model_id)[1]

    # ---- existing models: work on a copy, never on the user's original ----
    def open_existing(self,name,model_path,viewer_dir=None,render_python=None):
        if not isinstance(name,str)or not name.strip()or len(name)>120:raise ValueError('Give the character a name')
        source=Path(str(model_path)).expanduser()
        if source.is_dir()and not source.is_symlink():
            found=sorted(source.glob('*.model3.json'))
            if len(found)!=1:raise ValueError('Give the .model3.json file, or a folder holding exactly one')
            source=found[0]
        if not source.name.endswith('.model3.json')or not source.is_file()or source.is_symlink():raise ValueError('Give the FULL path (starting with /) of an existing Cubism .model3.json file, or of a folder holding exactly one; a relative name like coral-idol is not resolved from here, so find the folder with the terminal first (pwd) and pass the absolute path')
        report=inspect_resources(str(source))
        if report['issues']or any(x['status']!='present'for x in report['resources']):raise ValueError('The model has missing or unsafe resources; nothing was copied')
        folder=source.parent.resolve();files=[x for x in folder.rglob('*')if x.is_file()]
        if any(x.is_symlink()for x in folder.rglob('*'))or sum(x.stat().st_size for x in files)>2*1024**3:raise ValueError('The model folder has links or is larger than 2 GB; nothing was copied')
        resources={k:v for k,v in(('viewer_dir',viewer_dir),('render_python',render_python))if v}
        began=self.begin(name,'Existing model opened for inspection and changes; the original files are never modified.',resources)
        p,data=self.load(began['model_id']);dest=p/'model';shutil.copytree(folder,dest,symlinks=False)
        copy=dest/source.name;moc=dest/json.loads(copy.read_text())['FileReferences']['Moc']
        data.update(phase='opened_existing',origin='existing',model_path=str(copy.relative_to(p)),moc_sha256=digest(moc),original_moc_sha256=digest(folder/moc.relative_to(dest)),changes=[],clips=[]);save(p/'model-project.json',data)
        return {'model_id':began['model_id'],'name':name,'phase':data['phase'],'moc_sha256':data['moc_sha256'],'files_copied':len(files),'renderer':{k:v for k,v in self.renderer(data).items()if k in('ready','missing')},'notice':'A working copy was made inside this project; the original model was not touched.'}
    def renderer(self,data):
        res=data.get('resources')or{};viewer=res.get('viewer_dir')or os.environ.get('LIVE2D_SDK_VIEWER');python=res.get('render_python')or os.environ.get('LIVE2D_RENDER_PYTHON')or shutil.which('python3')
        missing=[]
        if not viewer or not all((Path(viewer)/n).is_file()for n in('index.html','viewer.js','core.min.js')):missing.append('Cubism SDK viewer folder (set LIVE2D_SDK_VIEWER or pass viewer_dir to live2d_open_model)')
        else:
            if not(Path(viewer)/'framework'/'Shaders').is_dir():missing.append('viewer framework/Shaders')
        if not python or subprocess.run([python,'-c','import playwright'],capture_output=True,timeout=30).returncode:missing.append('a Python with Playwright (set LIVE2D_RENDER_PYTHON)')
        if not shutil.which('ffmpeg'):missing.append('ffmpeg')
        return {'ready':not missing,'missing':missing,'viewer_dir':viewer,'python':python}
    def _bridge(self,data,args,timeout=300):
        r=self.renderer(data)
        if not r['ready']:raise ValueError('Motion rendering is not ready: '+'; '.join(r['missing']))
        return[r['python'],str(Path(__file__).with_name('corebridge.py')),*args,'--viewer',r['viewer_dir']]
    def inspect_model(self,model_id):
        p,data=self.load(model_id)
        if not data.get('model_path'):raise ValueError('Open or build a model first')
        model=p/data['model_path'];folder=model.parent;settings=json.loads(model.read_text());refs=settings['FileReferences']
        def load(rel):
            try:return json.loads((folder/rel).read_text())if rel else None
            except(OSError,ValueError):return None
        cdi=load(refs.get('DisplayInfo'));phys=load(refs.get('Physics'))
        groups=[{'name':g.get('Name'),'controls':g.get('Ids')}for g in settings.get('Groups',[])]
        physics=[{'group':s['Id'],'driven_by':[{'parameter':i['Source']['Id'],'weight':i['Weight']}for i in s['Input']],'moves':[{'parameter':o['Destination']['Id'],'strength':o['Scale']}for o in s['Output']],'points':len(s['Vertices'])}for s in(phys or{}).get('PhysicsSettings',[])]
        result={'model_id':model_id,'moc_sha256':data['moc_sha256'],'textures':len(refs.get('Textures',[])),'expressions':[e.get('Name')for e in refs.get('Expressions',[])],'motion_groups':{k:len(v)for k,v in refs.get('Motions',{}).items()},'control_groups':groups,'parameters_named':[x.get('Id')for x in(cdi or{}).get('Parameters',[])],'physics':physics,'changes':data.get('changes',[])}
        try:
            command=self._bridge(data,['inspect',str(model)])
            done=subprocess.run(command,capture_output=True,timeout=180,cwd=p,env={k:v for k,v in os.environ.items()if k in('PATH','HOME','LANG','LC_ALL','TMPDIR')})
            if done.returncode:raise RuntimeError(done.stderr.decode(errors='replace')[-300:])
            core=json.loads(done.stdout);result['core']={'parts':core['parts'],'drawable_count':len(core['drawables']),'drawables':core['drawables'],'parameter_ranges':core['parameters'],'core_version':core['coreVersion']}
        except(ValueError,RuntimeError,subprocess.TimeoutExpired,OSError)as exc:result['core']={'unavailable':str(exc)[:300]}
        return result
    def adjust_physics(self,model_id,output_scale=1.0,input_weight=1.0,follow_through=1.0,groups=None,note='',restore_original=False):
        p,data=self.load(model_id)
        if data.get('origin')!='existing':raise ValueError('Open an existing model with live2d_open_model first')
        model=p/data['model_path'];refs=json.loads(model.read_text())['FileReferences'];target=model.parent/refs['Physics'];backup=p/'backup'/'physics3.original.json'
        if not backup.exists():backup.parent.mkdir(exist_ok=True);shutil.copyfile(target,backup)
        if restore_original:
            shutil.copyfile(backup,target);data['changes'].append({'what':'restored original physics','note':note})
            save(p/'model-project.json',data);return{'model_id':model_id,'restored':True,'changes':data['changes']}
        for v in(output_scale,input_weight,follow_through):
            if type(v)not in(int,float)or not .2<=v<=6:raise ValueError('Each multiplier must be between 0.2 and 6')
        if groups is not None and(not isinstance(groups,list)or not all(isinstance(g,str)for g in groups)):raise ValueError('groups is a list of group name fragments')
        doc=json.loads(backup.read_text());touched=[]
        for s in doc['PhysicsSettings']:
            if groups and not any(g.lower()in s['Id'].lower()for g in groups):continue
            for o in s['Output']:o['Scale']=round(o['Scale']*output_scale,3)
            for i in s['Input']:i['Weight']=round(i['Weight']*input_weight,2)
            for q in s['Vertices'][1:]:q['Acceleration']=round(q['Acceleration']*follow_through,3)
            touched.append(s['Id'])
        if not touched:raise ValueError('No physics group matched; inspect the model for its group names')
        target.write_text(json.dumps(doc,indent=2));data['changes'].append({'what':'physics change (multipliers on the original)','groups':touched,'output_scale':output_scale,'input_weight':input_weight,'follow_through':follow_through,'physics_sha256':digest(target),'note':note});save(p/'model-project.json',data)
        return{'model_id':model_id,'changed_groups':touched,'physics_sha256':digest(target),'changes':data['changes'],'notice':'Only the working copy changed. Render the same motion again to compare with the earlier clip.'}

    def _core_ranges(self,p,data):
        try:
            model=p/data['model_path'];done=subprocess.run(self._bridge(data,['inspect',str(model)]),capture_output=True,timeout=180,cwd=p,env={k:v for k,v in os.environ.items()if k in('PATH','HOME','LANG','LC_ALL','TMPDIR')})
            return{x['id']:(x['min'],x['max'])for x in json.loads(done.stdout)['parameters']}if done.returncode==0 else None
        except(ValueError,RuntimeError,subprocess.TimeoutExpired,OSError,KeyError):return None
    def write_motion(self,model_id,name,tracks,seconds=8,fps=30,as_idle=True,note=''):
        """Author a motion3.json from plain curve descriptions, validated against the model's real parameters and ranges."""
        import math
        p,data=self.load(model_id)
        if data.get('origin')!='existing':raise ValueError('Open an existing model with live2d_open_model first')
        if not isinstance(name,str)or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,40}',name):raise ValueError('Motion name: letters, digits, - and _ only')
        if type(seconds)not in(int,float)or not 2<=seconds<=60 or fps not in(15,24,30,60):raise ValueError('seconds 2-60, fps 15, 24, 30 or 60')
        if not isinstance(tracks,list)or not 1<=len(tracks)<=40:raise ValueError('Give 1 to 40 tracks')
        model=p/data['model_path'];folder=model.parent;settings=json.loads(model.read_text());refs=settings['FileReferences']
        cdi=json.loads((folder/refs['DisplayInfo']).read_text())if refs.get('DisplayInfo')else{};known={x['Id']for x in cdi.get('Parameters',[])}
        ranges=self._core_ranges(p,data)
        if ranges:known=set(ranges)
        if not known:raise ValueError('The model lists no parameters to validate against')
        n=int(seconds*fps)+1;curves={};clamped=[];warnings=[]
        def smooth(u):u=min(1.0,max(0.0,u));return u*u*(3-2*u)
        for tr in tracks:
            if not isinstance(tr,dict)or tr.get('parameter')not in known:raise ValueError('Unknown parameter %r; inspect the model for real parameter ids'%(tr.get('parameter')if isinstance(tr,dict)else tr))
            pid=tr['parameter'];wave=tr.get('wave');vals=[0.0]*n
            if wave=='sine':
                for k in('center','amplitude','cycles'):
                    if type(tr.get(k))not in(int,float):raise ValueError('sine track needs numeric center, amplitude and cycles')
                if tr['cycles']!=int(tr['cycles'])or tr['cycles']<1:raise ValueError('cycles must be a whole number so the motion loops cleanly')
                ph=float(tr.get('phase',0));vals=[tr['center']+tr['amplitude']*math.sin(math.tau*(tr['cycles']*i/(n-1)+ph))for i in range(n)]
            elif wave=='blink':
                times=tr.get('at');dur=float(tr.get('closed_seconds',.16));base=float(tr.get('open_value',1));closed=float(tr.get('closed_value',0))
                if not isinstance(times,list)or not times or not all(type(t)in(int,float)and 0<=t<=seconds for t in times):raise ValueError('blink needs "at": a list of times in seconds inside the motion')
                vals=[base]*n
                for i in range(n):
                    t=i/fps;depth=max((1-min(1,abs(t-b)/(dur/2))for b in times),default=0);vals[i]=base+(closed-base)*max(0,depth)
            elif wave=='keys':
                keys=tr.get('keys')
                if not isinstance(keys,list)or len(keys)<2 or not all(isinstance(k,list)and len(k)==2 and all(type(x)in(int,float)for x in k)for k in keys)or any(b[0]<=a[0]for a,b in zip(keys,keys[1:])):raise ValueError('keys: [[seconds, value], ...] with increasing times')
                for i in range(n):
                    t=i/fps
                    if t<=keys[0][0]:vals[i]=keys[0][1];continue
                    if t>=keys[-1][0]:vals[i]=keys[-1][1];continue
                    for a,b in zip(keys,keys[1:]):
                        if a[0]<=t<=b[0]:vals[i]=a[1]+(b[1]-a[1])*smooth((t-a[0])/(b[0]-a[0]));break
                if abs(keys[0][1]-keys[-1][1])>1e-6 or keys[0][0]>0 or keys[-1][0]<seconds-1e-6:warnings.append('%s: keys do not start at 0 s and end at the full length with the same value, so the loop may jump'%pid)
            else:raise ValueError('wave must be sine, blink or keys')
            if ranges:
                lo,hi=ranges[pid]
                if any(v<lo-1e-9 or v>hi+1e-9 for v in vals):clamped.append({'parameter':pid,'range':[lo,hi]});vals=[min(hi,max(lo,v))for v in vals]
            curves[pid]=[round(v,4)for v in vals]
        segs=[]
        for pid,vals in curves.items():
            row=[0.0,vals[0]]
            for i in range(1,n):row+=[0,round(i/fps,4),vals[i]]
            segs.append({'Target':'Parameter','Id':pid,'Segments':row})
        doc={'Version':3,'Meta':{'Duration':float(seconds),'Fps':float(fps),'Loop':True,'AreBeziersRestricted':True,'CurveCount':len(segs),'TotalSegmentCount':len(segs)*(n-1),'TotalPointCount':len(segs)*n,'UserDataCount':0,'TotalUserDataSize':0},'Curves':segs}
        (folder/'motions').mkdir(exist_ok=True);out=folder/'motions'/(name+'.motion3.json')
        if out.exists()and not data.get('own_motions',{}).get(name):raise ValueError('A motion with this name already exists in the model; choose a new name (the original motions are kept)')
        out.write_text(json.dumps(doc));data.setdefault('own_motions',{})[name]=True
        if as_idle:
            backup=p/'backup'/'model3.original.json'
            if not backup.exists():backup.parent.mkdir(exist_ok=True);shutil.copyfile(model,backup)
            settings=json.loads(backup.read_text());settings['FileReferences'].setdefault('Motions',{})['Idle']=[{'File':'motions/'+out.name}];model.write_text(json.dumps(settings,indent=2))
        from .motion import check_motion
        check=check_motion(str(folder/refs['DisplayInfo']),str(out))if refs.get('DisplayInfo')else None
        data.setdefault('changes',[]).append({'what':'wrote motion','name':name,'parameters':list(curves),'seconds':seconds,'used_as_idle':as_idle,'note':note});save(p/'model-project.json',data)
        return{'model_id':model_id,'motion':name,'file':'motions/'+out.name,'seconds':seconds,'parameters':list(curves),'values_limited_to_range':clamped,'warnings':warnings,'check':check,'used_as_idle':as_idle,'notice':'Written to the working copy only. Render it with live2d_render_clip (motion name) and look at the frames.'}
    def _motion_arg(self,folder,settings,name):
        if name in('standard','rest'):return name
        if name is None:
            idle=settings['FileReferences'].get('Motions',{}).get('Idle')
            return str(folder/idle[0]['File'])if idle and(folder/idle[0]['File']).is_file()else'standard'
        files=[x['File']for g in settings['FileReferences'].get('Motions',{}).values()for x in g]
        for f in files:
            if Path(f).name.removesuffix('.motion3.json').lower()==str(name).lower():return str(folder/f)
        direct=folder/'motions'/(str(name)+'.motion3.json')
        if direct.is_file()and not direct.is_symlink():return str(direct)
        raise ValueError('No motion called %s; use standard, rest or a motion name from live2d_inspect_model'%name)
    def render_clip(self,model_id,label,seconds=8,view='full',width=720,height=1080,motion=None):
        p,data=self.load(model_id)
        if view not in('full','upper','head')or type(seconds)not in(int,float)or not 2<=seconds<=20 or not all(type(v)is int and 240<=v<=2160 for v in(width,height)):raise ValueError('view is full, upper or head; seconds 2-20; sizes 240-2160')
        model=p/data['model_path'];arg=self._motion_arg(model.parent,json.loads(model.read_text()),motion);argv=self._bridge(data,['render','{project}/'+data['model_path'],'{output}','--seconds',str(seconds),'--view',view,'--width',str(width),'--height',str(height),'--motion',arg.replace(str(p),'{project}',1)if arg not in('standard','rest')else arg])
        phys=model.parent/json.loads(model.read_text())['FileReferences']['Physics'];before=set(data.get('motion_videos',[]));result=self.motion(model_id,argv,timeout_seconds=900)
        p,data=self.load(model_id);new=[v for v in data['motion_videos']if v not in before];data.setdefault('clips',[]).append({'label':label,'video':new[0]if new else None,'view':view,'motion':motion or'standard','physics_sha256':digest(phys),'moc_sha256':data['moc_sha256']});save(p/'model-project.json',data)
        sheets=[str(x)for x in(p/Path(data['clips'][-1]['video']).parent).glob('contact-sheet.png')]
        report=p/Path(data['clips'][-1]['video']).parent/'report.json'if new else None
        measured=json.loads(report.read_text()).get('measured')if report and report.is_file()else None
        return{**result,'label':label,'physics_sha256':digest(phys),'measured_movement':measured,'contact_sheet':sheets[0]if sheets else None,'notice':'Same standard motion every time (head turns left and right, blinks, small body sway). measured_movement states what actually moved in the rendered frames (ranges of head, body, eyes, breathing, hair; blink count): describe the clip only from it. The contact sheet shows six frames left to right if you can view images.'}

S={'type':'string'};M={'model_id':S}
TOOLS={
'live2d_begin_model':('Begin creating a complete editable Live2D character from a brief and the user’s actual resources. Artwork, rigging, native compilation and motion review are production stages; inspectors remain diagnostics.',{'name':S,'brief':S,'resources':{'type':'object'}},['name','brief'],'begin'),
'live2d_model_layer':('Import one actual complete RGBA part after MAIN-session native image creation/review. Preserve hidden backing and neutral identity; do not treat interlocked portrait slices as complete parts. Names are unique per model. Parts are either full-canvas PNGs sharing one canvas size, or cropped PNGs with integer x and y placement on that canvas.',{**M,'name':S,'role':S,'source_path':S,'review_note':S,'x':{'type':'integer'},'y':{'type':'integer'}},['model_id','name','role','source_path','review_note'],'layer'),
'live2d_model_rig':('Save an actual authored rig source using the selected producer’s API. The active host authors this; no worker agent/model is launched.',{**M,'source':S,'filename':S},['model_id','source'],'rig'),
'live2d_build_model':('Run the explicitly selected real native authoring toolchain on the project, requiring actual MOC3/model3 output. Trusted toolchain code executes; use only the resource/paths authorized for this production. Missing compiler stays blocked.',{**M,'command_argv':{'type':'array','items':S},'timeout_seconds':{'type':'integer','minimum':1,'maximum':900}},['model_id','command_argv'],'build'),
'live2d_render_model_motion':('Render the built model through a selected actual SDK/Core renderer into a real motion MP4 for MAIN-session review. No physical camera/tracker/VTS integration is part of this operation.',{**M,'command_argv':{'type':'array','items':S},'timeout_seconds':{'type':'integer','minimum':1,'maximum':900}},['model_id','command_argv'],'motion'),
'live2d_model_status':('Read actual model production layers/rig/compiled package/motion state, never a fabricated ready flag.',M,['model_id'],'status')
,'live2d_open_model':('Open an EXISTING Live2D model (the .model3.json the user already has, or the folder that holds it; a relative path is read from the current working folder) as a working copy inside a new project, so it can be inspected, changed and rendered. The original files are never modified. Use this when the user already has a character; use live2d_begin_model to create a new one.',{'name':S,'model_path':S,'viewer_dir':S,'render_python':S},['name','model_path'],'open_existing'),
'live2d_inspect_model':('Describe an opened model in plain terms: controls, expressions, motions, physics groups (what drives what, how strongly) and, when the Cubism renderer is available, the separate parts and drawable pieces and each control range.',M,['model_id'],'inspect_model'),
'live2d_adjust_physics':('Change how loose parts (hair, tentacles, skirt) swing on the WORKING COPY of an opened model: multipliers for output strength, how strongly head/body motion drives them, and follow-through (swing that continues after the head stops). Applied to the saved original each time, not compounded. restore_original undoes it.',{**M,'output_scale':{'type':'number'},'input_weight':{'type':'number'},'follow_through':{'type':'number'},'groups':{'type':'array','items':S},'note':S,'restore_original':{'type':'boolean'}},['model_id'],'adjust_physics'),
'live2d_render_clip':('Render the opened or built model moving through the official Cubism Core (physics running) into a labelled motion clip. motion: a motion name from the model or one you wrote; left out it plays the model\u2019s own Idle motion (how she moves now), or standard if it has none; standard = test sequence (head turns left and right, blinks, small body sway); rest = no motion. Same camera and length every time so before/after clips compare directly. Look at the contact sheet in the main session.',{**M,'label':S,'motion':S,'seconds':{'type':'number'},'view':{'type':'string','enum':['full','upper','head']},'width':{'type':'integer'},'height':{'type':'integer'}},['model_id','label'],'render_clip'),'live2d_write_motion':('Write a new motion (for example an idle that makes her breathe, sway, look around and blink) into the WORKING COPY of an opened model from plain curve descriptions, validated against the model\u2019s real parameter ids and ranges, and register it as the Idle motion. tracks: list of {parameter, wave:sine (center, amplitude, cycles = whole number per loop, optional phase 0-1) | blink (at: [seconds], optional closed_seconds, open_value, closed_value) | keys ([[seconds, value], ...] eased)}. The structural check runs automatically.',{**M,'name':S,'tracks':{'type':'array','items':{'type':'object'}},'seconds':{'type':'number'},'fps':{'type':'integer'},'as_idle':{'type':'boolean'},'note':S},['model_id','name','tracks'],'write_motion')}
