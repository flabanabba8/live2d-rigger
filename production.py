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
    def clone(self,model_id,name=None):
        source,data=self.load(model_id)
        if any(x.is_symlink() for x in source.rglob('*')):raise ValueError('The source project contains symbolic links; no clone was made')
        if name is not None and (not isinstance(name,str) or not name.strip() or len(name)>120):raise ValueError('Give a bounded name for the working copy')
        ident=uuid.uuid4().hex;dest=self.root/ident;shutil.copytree(source,dest);dest.chmod(0o700)
        data['model_id']=ident;data['name']=name or data['name']+' copy';data['cloned_from']=model_id;save(dest/'model-project.json',data)
        return {'model_id':ident,'name':data['name'],'project_path':str(dest),'notice':'A separate working copy was created; the source project is unchanged.'}
    def layer(self,model_id,name,role,source_path,review_note,x=None,y=None,key_color=None,tolerance=18,softness=35,trim=False,complete_part=None,aligned_to_reference=False,same_canvas_edit=False,reference_path=None):
        p,data=self.load(model_id)
        if complete_part is not True:raise ValueError('Confirm this is an independently painted complete part with the hidden backing it needs, not a flat portrait slice; review it before importing')
        if any(l['name']==name for l in data['layers']):raise ValueError('Layer names must be unique within a model; use a stable role name such as Eye_L_Iris')
        if(x is None)!=(y is None)or any(v is not None and(type(v)is not int or abs(v)>100000)for v in(x,y)):raise ValueError('Give both integer x and y placement offsets, or neither for a full shared-canvas layer')
        if len(data['layers'])>=160:raise ValueError('Split this production part; layer limit160')
        if not all(isinstance(v,str)and v.strip()and len(v)<=2000 for v in(name,role,review_note)):raise ValueError('Name, complete-part role and actual main-session review note are required')
        source=Path(source_path).expanduser()
        if source.is_symlink()or source.suffix.lower()!='.png'or any(x in source.parts for x in('.ssh','.aws','.gnupg','.env')):raise ValueError('Choose a reviewed regular PNG, not private configuration')
        if not source.is_file()or source.stat().st_size>32*1024**2:raise ValueError('Select a bounded PNG layer')
        from PIL import Image
        with Image.open(source)as image:
            image.load(); size=image.size
            opaque=image.mode!='RGBA' or image.getchannel('A').getextrema()==(255,255)
            if opaque:
                if key_color is None:raise ValueError('Opaque part: supply key_color for a single flat background, or provide actual RGBA transparency')
                from .cutout import cutout,preview
                rgba,box,key=cutout(image,None if key_color==[] else key_color,tolerance,softness)
                previews=p/'previews';previews.mkdir(exist_ok=True)
                preview_path=previews/(uuid.uuid4().hex+'.png');preview(image,rgba).save(preview_path)
            else:rgba=image.convert('RGBA');box=rgba.getbbox();key=None;preview_path=None
        if box is None:raise ValueError('The part has no visible pixels; provide a complete reviewed layer')
        if trim and x is None:raise ValueError('Trimming needs explicit x and y placement to retain the common canvas contract')
        full=[data['canvas']] if data.get('canvas') else [l['dimensions']for l in data['layers']if l.get('offset')is None]
        automatic=x is None and not aligned_to_reference and not same_canvas_edit and any('face' in l['name'].lower() for l in data['layers']) and 'face' not in name.lower()
        if x is None and full and list(size)!=list(full[0]):
            if automatic:x=y=0
            else:raise ValueError('Full-canvas layers must share one canvas size (%s); give x and y offsets for cropped parts'%full[0])
        if x is not None and full and not automatic and (x<0 or y<0 or x+size[0]>full[0][0] or y+size[1]>full[0][1]):raise ValueError('Cropped part and its placement must fit inside the established common canvas; adjust the whole part or canvas before importing')
        dest=p/'layers'/(uuid.uuid4().hex+'.png');before=source.stat()
        if opaque or trim:
            if trim:
                rgba=rgba.crop(box);x+=box[0];y+=box[1];size=rgba.size
            rgba.save(dest)
        else:shutil.copyfile(source,dest)
        dest.chmod(0o600);after=source.stat()
        if(before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns):dest.unlink();raise ValueError('Layer changed during import')
        row={'name':name,'role':role,'path':str(dest.relative_to(p)),'dimensions':size,'offset':None if x is None else[x,y],'sha256':digest(dest),'review_note':review_note,'complete_part_attested':True,'cutout_key':key,'cutout_preview':str(preview_path) if preview_path else None,'aligned_to_reference':bool(aligned_to_reference),'same_canvas_edit':bool(same_canvas_edit)}
        if (aligned_to_reference or same_canvas_edit) and (trim or x is not None or not full or list(size)!=list(full[0])):
            dest.unlink();raise ValueError('Reference-aligned parts need the full shared canvas with no trimming or offset')
        data['layers'].append(row);data['phase']='artwork';data['build_stale']=bool(data.get('model_path'));save(p/'model-project.json',data)
        if automatic:
            proposal=next((q for q in self.default_layout(model_id)['proposals'] if q['name']==name),None)
            if proposal:
                p,data=self.load(model_id);row=data['layers'][-1];row['placement']={'x':proposal['x'],'y':proposal['y'],'scale_x':proposal['scale'],'scale_y':proposal['scale']};row['placement_source']='role_default';save(p/'model-project.json',data)
            else:
                p,data=self.load(model_id);row=data['layers'][-1];row['placement_pending']=True;save(p/'model-project.json',data)
        if reference_path:
            try:result=self.register_layer(model_id,name,reference_path)
            except (ValueError,OSError) as exc:result={'accepted':False,'applied':False,'error':str(exc),'notice':'Layer imported; reference registration failed, so review placement manually.'}
            p,data=self.load(model_id);row=next(l for l in data['layers'] if l['name']==name);row={**row,'registration_result':result}
        return row
    def remove_layer(self,model_id,name):
        p,data=self.load(model_id);layer=next((l for l in data['layers'] if l['name']==name),None)
        if layer is None:raise ValueError('No imported layer has that name')
        data['layers'].remove(layer);data.setdefault('removed_layers',[]).append(layer);data['build_stale']=bool(data.get('model_path'));save(p/'model-project.json',data)
        return {'model_id':model_id,'removed':name,'notice':'The layer was removed from the active assembly; its PNG and previous builds remain in the project. Rebuild to apply.'}
    def default_layout(self,model_id,head_count=2.5,apply=False):
        p,data=self.load(model_id)
        if type(head_count) not in (int,float) or not 2<=head_count<=8:raise ValueError('Head count must be between 2 and 8')
        face=next((l for l in data['layers'] if 'face' in l['name'].lower()),None)
        if face is None:raise ValueError('A named face part is needed to derive default layout')
        from PIL import Image
        def bounds(layer):
            with Image.open(p/layer['path']) as im:return im.convert('RGBA').getchannel('A').getbbox()
        box=bounds(face)
        if not box:raise ValueError('Face part has no visible pixels')
        pl=face.get('placement') or {};offset=face.get('offset') or [0,0]
        sx=pl.get('scale_x',pl.get('scale',1));sy=pl.get('scale_y',pl.get('scale',1));fx=pl.get('x',offset[0])+box[0]*sx;fy=pl.get('y',offset[1])+box[1]*sy;fw=(box[2]-box[0])*sx;fh=(box[3]-box[1])*sy
        canvas=data.get('canvas') or next((l['dimensions'] for l in data['layers'] if l.get('offset') is None),None)
        if not canvas:raise ValueError('Set a shared canvas first')
        slots=[];skipped=[]
        for layer in data['layers']:
            if layer is face:continue
            n=layer['name'].lower();role=(n+' '+layer['role']).lower();left='left' in n or '_l' in n;right='right' in n or '_r' in n
            if any(k in role for k in ('hair','fringe','bang')):slot=(fx-.16*fw,fy-.2*fh,1.32*fw,1.35*fh)
            elif 'neck' in role:slot=(fx+.36*fw,fy+.88*fh,.28*fw,.35*fh)
            elif any(k in role for k in ('dress','torso','apron','body')):slot=(fx+.1*fw,fy+1.05*fh,.8*fw,max(.5,head_count-1.4)*fh)
            elif any(k in role for k in ('arm','hand')) and (left or right):slot=(fx+(-.15 if left else .85)*fw,fy+1.05*fh,.3*fw,.8*fh)
            elif any(k in role for k in ('leg','shoe','foot')) and (left or right):slot=(fx+(.2 if left else .55)*fw,fy+(head_count-.6)*fh,.25*fw,.5*fh)
            elif any(k in role for k in ('eye','iris','lid','brow')) and (left or right):slot=(fx+(.16 if left else .58)*fw,fy+.34*fh,.27*fw,.24*fh)
            elif 'mouth' in role:slot=(fx+.36*fw,fy+.72*fh,.28*fw,.12*fh)
            else:skipped.append(layer['name']);continue
            b=bounds(layer)
            if not b:skipped.append(layer['name']);continue
            x,y,w,h=slot;scale=min(w/(b[2]-b[0]),h/(b[3]-b[1]));x+=max(0,(w-(b[2]-b[0])*scale)/2);y+=max(0,(h-(b[3]-b[1])*scale)/2)
            if x<0 or y<0 or x+(b[2]-b[0])*scale>canvas[0] or y+(b[3]-b[1])*scale>canvas[1]:skipped.append(layer['name']);continue
            proposal={'name':layer['name'],'x':round(x-b[0]*scale,3),'y':round(y-b[1]*scale,3),'scale':round(scale,5)};slots.append(proposal)
            if apply:layer['placement']={'x':proposal['x'],'y':proposal['y'],'scale_x':proposal['scale'],'scale_y':proposal['scale']};layer.pop('placement_pending',None)
        if apply:data['build_stale']=bool(data.get('model_path'));save(p/'model-project.json',data)
        return {'proposals':slots,'skipped':skipped,'applied':bool(apply),'notice':'Coarse defaults from the actual face bounds and requested head count; they are not character-specific registration. Review overlapping hair crowns, feature alignment and the assembled result.'}
    def register_layer(self,model_id,name,reference_path,threshold=.9):
        p,data=self.load(model_id);layer=next((l for l in data['layers'] if l['name']==name),None)
        if layer is None:raise ValueError('No imported layer has that name')
        reference=Path(reference_path).expanduser()
        if reference.is_symlink() or not reference.is_file() or reference.stat().st_size>32*1024**2:raise ValueError('Provide a bounded regular reference image')
        from PIL import Image
        from .registration import register
        with Image.open(reference) as ref,Image.open(p/layer['path']) as part:
            size=list(ref.size);canvas=data.get('canvas') or next((l['dimensions'] for l in data['layers'] if l.get('offset') is None),None)
            if canvas and list(canvas)!=size:raise ValueError('Reference dimensions differ from the shared canvas; set the canvas to the reference size first')
            result=register(ref,part,layer['name']+' '+layer['role'],threshold)
        result['reference_sha256']=digest(reference);result['applied']=False
        if result['accepted']:
            layer['placement']={'x':result['x'],'y':result['y'],'scale_x':result['scale'],'scale_y':result['scale']}
            layer['registration']={k:result[k] for k in ('score','threshold','reference_sha256')};layer.pop('placement_pending',None)
            data['build_stale']=bool(data.get('model_path'));save(p/'model-project.json',data);result['applied']=True
            result['notice']='A high-scoring placement proposal was applied; inspect the composite because similarity is not proof of alignment.'
        else:result['notice']='Low-confidence match; no placement changed. Inspect the part and reference and give a placement nudge in words.'
        return result
    def set_canvas(self,model_id,width,height):
        p,data=self.load(model_id)
        if type(width) is not int or type(height) is not int or not 1<=width<=8192 or not 1<=height<=8192:raise ValueError('Canvas width and height must be integers from 1 to 8192')
        for layer in data['layers']:
            placement=layer.get('placement') or {};offset=layer.get('offset') or [0,0]
            x=placement.get('x',offset[0]);y=placement.get('y',offset[1]);sx=placement.get('scale_x',placement.get('scale',1));sy=placement.get('scale_y',placement.get('scale',1))
            if x<0 or y<0 or x+layer['dimensions'][0]*sx>width or y+layer['dimensions'][1]*sy>height:raise ValueError('Existing layer placements must fit in the new canvas')
        data['canvas']=[width,height];data['build_stale']=bool(data.get('model_path'));save(p/'model-project.json',data)
        return {'canvas':[width,height],'notice':'Canvas updated without changing art; rebuild and review the composite.'}
    def place_layer(self,model_id,name,x,y,scale=None,scale_x=None,scale_y=None):
        p,data=self.load(model_id)
        layer=next((l for l in data['layers'] if l['name']==name),None)
        if layer is None:raise ValueError('No imported layer has that name')
        sx=scale_x if scale_x is not None else scale;sy=scale_y if scale_y is not None else scale
        if any(type(v) not in (int,float) for v in (x,y,sx,sy)) or not all(__import__('math').isfinite(v) for v in (x,y,sx,sy)) or not all(.05<=v<=4 for v in (sx,sy)):raise ValueError('Use finite x/y coordinates and horizontal/vertical scales between 0.05 and 4')
        canvas=data.get('canvas') or next((l['dimensions'] for l in data['layers'] if l.get('offset') is None),None)
        if canvas and (x<0 or y<0 or x+layer['dimensions'][0]*sx>canvas[0] or y+layer['dimensions'][1]*sy>canvas[1]):raise ValueError('Placed layer must fit in the common canvas')
        layer['placement']={'x':x,'y':y,'scale_x':sx,'scale_y':sy};layer.pop('placement_pending',None);data['build_stale']=bool(data.get('model_path'));save(p/'model-project.json',data)
        return {'name':name,'placement':layer['placement'],'notice':'Original artwork is unchanged. Rebuild and review the composite before accepting it.'}
    def configure_umamo(self,model_id,java,classpath_file):
        p,data=self.load(model_id)
        path=Path(classpath_file).expanduser();jdk=Path(java).expanduser()
        if not path.is_file() or not jdk.is_file():raise ValueError('Provide an existing classpath JSON and Java executable for the installed toolchain')
        doc=json.loads(path.read_text())
        for name in ('compiler','runtime'):
            values=doc.get(name)
            if not isinstance(values,list) or not values or any(not isinstance(x,str) or not Path(x).exists() for x in values):raise ValueError('Classpath JSON needs compiler and runtime arrays of existing paths')
        resources=data.setdefault('resources',{});resources.update(java=str(jdk),umamo_compiler_classpath=os.pathsep.join(doc['compiler']),umamo_runtime_classpath=os.pathsep.join(doc['runtime']))
        save(p/'model-project.json',data)
        return {'model_id':model_id,'configured':True,'notice':'Installed Umamo classpaths configured for this private project; no software was installed.'}
    def arrange(self,model_id,names):
        p,data=self.load(model_id)
        if not isinstance(names,list) or any(not isinstance(n,str) for n in names) or len(names)!=len(data['layers']) or len(set(names))!=len(names) or set(names)!={layer['name'] for layer in data['layers']}:
            raise ValueError('List every imported layer name exactly once, in back-to-front order')
        by_name={layer['name']:layer for layer in data['layers']};data['layers']=[by_name[n] for n in names]
        data['build_stale']=bool(data.get('model_path'));save(p/'model-project.json',data)
        return {'model_id':model_id,'back_to_front':names,'notice':'Layer order saved; rebuild to apply it and inspect the assembled result.'}
    def rig(self,model_id,source='static-layers',filename='ModelRig.kt'):
        p,data=self.load(model_id)
        if not data['layers']:raise ValueError('Create/review actual complete parts before authoring the rig')
        if source in ('static-layers','prototype-roll'):
            if source=='prototype-roll' and not any('face' in (l['name']+' '+l['role']).lower() for l in data['layers']):raise ValueError('A named face layer is needed to derive the head pivot')
            if not data.get('canvas') and not any(l.get('offset') is None for l in data['layers']):raise ValueError('Set a canvas size or add a full-canvas layer')
            data.update(build_stale=bool(data.get('model_path')),rig_file='builtin:'+source,phase='static_export_prepared' if source=='static-layers' else 'prototype_roll_prepared');save(p/'model-project.json',data)
            return {'phase':data['phase'],'notice':('Prepared a static separate-layer export only; no deformers, controls or physics have been authored.' if source=='static-layers' else 'Experimental head roll, basic sway and breathing for a torso, and provisional blink/gaze and mouth opening for named parts; experimental back-hair physics when hair is present; no XY turns, mouth form or acceptance.')}
        if not isinstance(filename,str)or Path(filename).name!=filename or Path(filename).suffix not in('.kt','.json','.py'):raise ValueError('Use a simple rig source filename for the selected authoring toolchain')
        if not isinstance(source,str)or not source.strip()or len(source)>400000:raise ValueError('Supply executable rig source from the actual selected authoring contract')
        out=p/'src'/filename
        if out.exists():out=out.with_name(out.stem+'-'+uuid.uuid4().hex[:6]+out.suffix)
        out.write_text(source);out.chmod(0o600);data.update(build_stale=bool(data.get('model_path')),rig_file=str(out.relative_to(p)),phase='rig_authored');save(p/'model-project.json',data);return {'rig_source':str(out),'phase':data['phase'],'notice':'Source saved, not proof of a compiled or usable rig. Build and inspect actual output next.'}
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
    def build(self,model_id,command_argv=None,timeout_seconds=300):
        p,data=self.load(model_id)
        if not data['rig_file']:raise ValueError('Author the actual rig first')
        for layer in data['layers']:
            if layer.get('placement_pending'):raise ValueError('A layer has no placement; give a plain-words nudge or set its position before building')
            if digest(p/layer['path'])!=layer['sha256']:raise ValueError('Reviewed layer changed; re-establish the artwork contract')
        output=p/('build-'+uuid.uuid4().hex[:8]);output.mkdir()
        if data['rig_file'] in ('builtin:static-layers','builtin:prototype-roll') and command_argv is None:
            from .umamo_adapter import build
            build(p,output,timeout_seconds,data.get('resources'),data['rig_file']=='builtin:prototype-roll')
        else:self.command(p,command_argv,output,timeout_seconds)
        models=list(output.rglob('*.model3.json'))
        if len(models)!=1:raise ValueError('The native producer must emit one actual Cubism model3.json package; no model placeholder accepted')
        if models[0].is_symlink()or not models[0].resolve().is_relative_to(output.resolve()):raise ValueError('Native model package must remain inside its build directory')
        report=inspect_resources(str(models[0]))
        if report['issues']or any(x['status']!='present'for x in report['resources']):raise ValueError('Native model package has unsafe or missing resources; no compiled success claimed')
        settings=json.loads(models[0].read_text());moc=models[0].parent/settings['FileReferences']['Moc']
        with moc.open('rb')as f:magic=f.read(4)
        if magic!=b'MOC3':raise ValueError('The selected producer did not emit native MOC3 bytes')
        static=data['rig_file']=='builtin:static-layers'
        data.update(build_stale=False,phase='static_compiled_needs_core_review' if static else 'compiled_needs_core_and_motion_review',build_root=str(output.relative_to(p)),model_path=str(models[0].relative_to(p)),moc_sha256=digest(moc),native_editable_documents=[str(x.relative_to(p))for x in output.rglob('*.cmo3')],resource_report=report);save(p/'model-project.json',data)
        return {'model_id':model_id,'model_path':str(models[0]),'moc_sha256':data['moc_sha256'],'native_editable_documents':data['native_editable_documents'],'phase':data['phase'],'notice':('Static layer transport only: no rig, motion controls or physics. Core and visual review remain required.' if static else 'Experimental prototype: head roll, basic sway/breathing and provisional blink/gaze and mouth opening when matching parts exist; experimental back-hair physics when hair is present; no XY turns or mouth form. Core and visual review remain required.' if data['rig_file']=='builtin:prototype-roll' else 'Native output package is present; its header/reference checks do not prove MOC3 validity or Core/appearance/human-motion acceptance. Inspect domains and render through the real SDK; original layers and executable rig source are retained separately.')}
    def rebuild_prototype(self,model_id,timeout_seconds=300):
        _,data=self.load(model_id)
        if data.get('rig_file')!='builtin:prototype-roll':raise ValueError('This action requires a built-in experimental prototype')
        self.rig(model_id,'prototype-roll')
        return self.build(model_id,timeout_seconds=timeout_seconds)
    def motion(self,model_id,command_argv,timeout_seconds=300):
        p,data=self.load(model_id)
        if not data.get('model_path'):raise ValueError('Compile a native model before motion review')
        if data.get('build_stale'):raise ValueError('Layers or placement changed since the last build; rebuild before rendering')
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
        data.update(phase='static_review_pending' if data.get('rig_file')=='builtin:static-layers' else 'motion_review_pending',motion_videos=[str(x.relative_to(p))for x in videos]);save(p/'model-project.json',data)
        return {'model_id':model_id,'videos':[str(x)for x in videos],'phase':data['phase'],'notice':('Static-only output: inspect the still; no motion or physics exists.' if data.get('rig_file')=='builtin:static-layers' else 'Inspect actual frames/motion in the MAIN session and report remaining issues. No physical camera, tracking or VTS installation was performed by this workflow.')}
    def status(self,model_id):
        data=self.load(model_id)[1]
        resources=data.get('resources') or {}
        data['resources']={k:('[configured]' if k in ('java','umamo_compiler_classpath','umamo_runtime_classpath') else v) for k,v in resources.items()}
        return data

    # ---- existing models: work on a copy, never on the user's original ----
    def open_existing(self,name,model_path,viewer_dir=None,render_python=None):
        if not isinstance(name,str)or not name.strip()or len(name)>120:raise ValueError('Give the character a name')
        source=Path(str(model_path)).expanduser()
        if source.is_dir()and not source.is_symlink():
            found=sorted(source.glob('*.model3.json'))
            if len(found)!=1:raise ValueError('Give the .model3.json file, or a folder holding exactly one')
            source=found[0]
        if not source.name.endswith('.model3.json')or not source.is_file()or source.is_symlink():raise ValueError('Give the FULL path (starting with /) of an existing Cubism .model3.json file, or of a folder holding exactly one; a relative name like my-character is not resolved from here, so find the folder with the terminal first (pwd) and pass the absolute path')
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
    def check_domains(self,model_id):
        p,data=self.load(model_id)
        if not data.get('model_path'):raise ValueError('Open or build a model before checking domains')
        if data.get('build_stale'):raise ValueError('Layers or placement changed; rebuild before checking domains')
        argv=self._bridge(data,['domains',str(p/data['model_path'])])
        result=subprocess.run(argv,capture_output=True,timeout=180,cwd=p,env={k:v for k,v in os.environ.items() if k in ('PATH','HOME','LANG','LC_ALL','TMPDIR')})
        if result.returncode:raise RuntimeError('Core domain evaluation failed; no validation is claimed')
        return json.loads(result.stdout)
    def adjust_physics(self,model_id,output_scale=1.0,input_weight=1.0,follow_through=1.0,groups=None,note='',restore_original=False):
        p,data=self.load(model_id)
        if not data.get('model_path'):raise ValueError('Open an existing model or build a model first')
        model=p/data['model_path'];refs=json.loads(model.read_text())['FileReferences'];physics=refs.get('Physics')
        if not physics:raise ValueError('This model has no physics sidecar to adjust')
        data.setdefault('changes',[])
        target=model.parent/physics;backup=p/'backup'/('physics3.original.json' if data.get('origin')=='existing' else model.parent.name+'-physics3.original.json')
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
        if not data.get('model_path'):raise ValueError('Open an existing model or build a model first')
        if data.get('build_stale'):raise ValueError('Layers or placement changed; rebuild before writing motion')
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
            backup=p/'backup'/('model3.original.json' if data.get('origin')=='existing' else model.parent.name+'-model3.original.json')
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
        model=p/data['model_path']
        if data.get('rig_file')=='builtin:static-layers':
            if motion not in (None,'rest'):raise ValueError('The static layer export has no animation controls; render it with motion=rest')
            motion='rest'
        arg=self._motion_arg(model.parent,json.loads(model.read_text()),motion);argv=self._bridge(data,['render','{project}/'+data['model_path'],'{output}','--seconds',str(seconds),'--view',view,'--width',str(width),'--height',str(height),'--motion',arg.replace(str(p),'{project}',1)if arg not in('standard','rest')else arg])
        physics_ref=json.loads(model.read_text())['FileReferences'].get('Physics');phys=model.parent/physics_ref if physics_ref else None;physics_hash=digest(phys) if phys else None;before=set(data.get('motion_videos',[]));result=self.motion(model_id,argv,timeout_seconds=900)
        p,data=self.load(model_id);new=[v for v in data['motion_videos']if v not in before];data.setdefault('clips',[]).append({'label':label,'video':new[0]if new else None,'view':view,'motion':motion or'standard','physics_sha256':physics_hash,'moc_sha256':data['moc_sha256']});save(p/'model-project.json',data)
        sheets=[str(x)for x in(p/Path(data['clips'][-1]['video']).parent).glob('contact-sheet.png')]
        report=p/Path(data['clips'][-1]['video']).parent/'report.json'if new else None
        measured=json.loads(report.read_text()).get('measured')if report and report.is_file()else None
        return{**result,'label':label,'physics_sha256':physics_hash,'measured_movement':measured,'measurement_notice':'These are evaluated parameter values, not proof of visible motion. Eye-close crossings can occur without a visible blink; inspect the frames.','contact_sheet':sheets[0]if sheets else None,'notice':('Static layer export: this is a still rendered in Core, with no rig or animation.' if data.get('rig_file')=='builtin:static-layers' else 'Experimental prototype: roll, basic sway/breathing and provisional blink/gaze and mouth opening when matching parts exist. Review the actual frames; XY turns and mouth form are absent; inspect the experimental hair physics.' if data.get('rig_file')=='builtin:prototype-roll' else 'Same standard motion every time (head turns left and right, blinks, small body sway). measured_movement summarizes evaluated parameter values, which do not prove visible motion; inspect the frames before describing what moved. The contact sheet shows six frames left to right if you can view images.')}

S={'type':'string'};M={'model_id':S}
TOOLS={
'live2d_begin_model':('Begin creating a complete editable Live2D character from a brief and the user’s actual resources. Artwork, rigging, native compilation and motion review are production stages; inspectors remain diagnostics.',{'name':S,'brief':S,'resources':{'type':'object'}},['name','brief'],'begin'),
'live2d_remove_layer':('Remove a layer from the active assembly without deleting its source PNG or previous builds; rebuild to apply.',{**M,'name':S},['model_id','name'],'remove_layer'),
'live2d_clone_model':('Copy a plugin-owned EDITABLE LAYER PROJECT including its source layers and evidence for a reversible repair; do not use live2d_open_model, which copies a compiled runtime only. The source project stays unchanged.',{**M,'name':S},['model_id'],'clone'),
'live2d_model_layer':('Import one independently painted complete part after MAIN-session native image creation/review; complete_part=true attests to complete hidden backing and refuses flat portrait slices. This is an attestation, not automated proof. Preserve hidden backing and neutral identity; do not treat interlocked portrait slices as complete parts. Names are unique per model. Parts are either full-canvas PNGs sharing one canvas size, or cropped PNGs with integer x and y placement on that canvas. For an opaque single-flat-colour image, supply key_color as [R,G,B] or [] to detect from corners; the tool performs a conservative cutout and returns a before/after preview. trim requires x and y. For a same-canvas reference edit set same_canvas_edit=true and reference_path to verify and correct high-confidence drift; low confidence preserves its coordinates and requests a nudge.',{**M,'name':S,'role':S,'source_path':S,'review_note':S,'x':{'type':'integer'},'y':{'type':'integer'},'key_color':{'type':'array','items':{'type':'integer'}},'tolerance':{'type':'integer'},'softness':{'type':'integer'},'trim':{'type':'boolean'},'complete_part':{'type':'boolean'},'aligned_to_reference':{'type':'boolean'},'same_canvas_edit':{'type':'boolean'},'reference_path':{'type':'string'}},['model_id','name','role','source_path','review_note','complete_part'],'layer'),
'live2d_default_layout':('Propose or apply rough role-based placement from the actual face bounds and requested head count when no reference is available. Inspect the composite; defaults are not visual acceptance.',{**M,'head_count':{'type':'number'},'apply':{'type':'boolean'}},['model_id'],'default_layout'),
'live2d_register_layer':('Propose position and scale by bounded image matching against a full-figure reference. Applies a candidate only above the strict confidence threshold; inspect the composite and give a placement nudge if confidence is low.',{**M,'name':S,'reference_path':S,'threshold':{'type':'number'}},['model_id','name','reference_path'],'register_layer'),
'live2d_set_canvas':('Set a shared neutral canvas without changing artwork; every placed part must fit.',{**M,'width':{'type':'integer'},'height':{'type':'integer'}},['model_id','width','height'],'set_canvas'),
'live2d_place_layer':('Adjust layer placement, position, offset, move or scale an imported part on the shared canvas without resampling artwork; rebuild and render to apply.',{**M,'name':S,'x':{'type':'number'},'y':{'type':'number'},'scale':{'type':'number'},'scale_x':{'type':'number'},'scale_y':{'type':'number'}},['model_id','name','x','y'],'place_layer'),
'live2d_rebuild_prototype':('Rebuild an experimental prototype using the current built-in authoring recipe after an observed geometry issue, preserving earlier builds. Render the same motion and compare; rebuilding does not guarantee a visual fix.',{**M,'timeout_seconds':{'type':'integer','minimum':1,'maximum':900}},['model_id'],'rebuild_prototype'),
'live2d_check_rig_domains':('Evaluate each actual Core parameter at minimum, default and maximum, check finite geometry and report movement. This does not review intermediate poses or visual quality.',M,['model_id'],'check_domains'),
'live2d_configure_umamo':('Configure an existing installed Java and Umamo toolchain using a user-supplied JSON file with compiler and runtime path arrays. No installation occurs.',{**M,'java':S,'classpath_file':S},['model_id','java','classpath_file'],'configure_umamo'),
'live2d_arrange_layers':('Arrange all imported complete layers back to front before building; list every layer name exactly once.',{**M,'names':{'type':'array','items':S}},['model_id','names'],'arrange'),
'live2d_model_rig':('Save authored rig source, omit source for static export, or pass source=prototype-roll for experimental head roll, basic torso sway/breathing and provisional blink/gaze and mouth opening when matching parts exist. Experimental back-hair physics is included when hair is present; neither route supplies XY turns or mouth form.',{**M,'source':S,'filename':S},['model_id'],'rig'),
'live2d_build_model':('Build with the configured Umamo toolchain when using the static layer export, or run an explicitly selected real native authoring command; requires actual MOC3/model3 output. Trusted toolchain code executes; use only the resource/paths authorized for this production. Missing compiler stays blocked.',{**M,'command_argv':{'type':'array','items':S},'timeout_seconds':{'type':'integer','minimum':1,'maximum':900}},['model_id'],'build'),
'live2d_render_model_motion':('Render the built model through a selected actual SDK/Core renderer into a real motion MP4 for MAIN-session review. No physical camera/tracker/VTS integration is part of this operation.',{**M,'command_argv':{'type':'array','items':S},'timeout_seconds':{'type':'integer','minimum':1,'maximum':900}},['model_id','command_argv'],'motion'),
'live2d_model_status':('Read actual model production layers/rig/compiled package/motion state, never a fabricated ready flag.',M,['model_id'],'status')
,'live2d_open_model':('Open an EXISTING compiled runtime model only (not an editable layer project; use live2d_clone_model to copy a plugin-owned layer project). Open an EXISTING Live2D model (the .model3.json the user already has, or the folder that holds it; give a full absolute path) as a working copy inside a new project, so it can be inspected, changed and rendered. The original files are never modified. Use this when the user already has a character; use live2d_begin_model to create a new one.',{'name':S,'model_path':S,'viewer_dir':S,'render_python':S},['name','model_path'],'open_existing'),
'live2d_inspect_model':('Describe an opened model in plain terms: controls, expressions, motions, physics groups (what drives what, how strongly) and, when the Cubism renderer is available, the separate parts and drawable pieces and each control range.',M,['model_id'],'inspect_model'),
'live2d_adjust_physics':('Change how loose parts (hair, tentacles, skirt) swing in an opened copy or built project: multipliers for output strength, how strongly head/body motion drives them, and follow-through (swing that continues after the head stops). Applied to the saved original each time, not compounded. restore_original undoes it.',{**M,'output_scale':{'type':'number'},'input_weight':{'type':'number'},'follow_through':{'type':'number'},'groups':{'type':'array','items':S},'note':S,'restore_original':{'type':'boolean'}},['model_id'],'adjust_physics'),
'live2d_render_clip':('Render the opened or built model moving through the official Cubism Core (physics running) into a labelled motion clip. motion: a motion name from the model or one you wrote; left out it plays the model\u2019s own Idle motion (how she moves now), or standard if it has none; standard = test sequence (head turns left and right, blinks, small body sway); rest = no motion. Same camera and length every time so before/after clips compare directly. Look at the contact sheet in the main session.',{**M,'label':S,'motion':S,'seconds':{'type':'number'},'view':{'type':'string','enum':['full','upper','head']},'width':{'type':'integer'},'height':{'type':'integer'}},['model_id','label'],'render_clip'),'live2d_write_motion':('Write a new motion (for example an idle that makes her breathe, sway, look around and blink) into an opened copy or built project from plain curve descriptions, validated against the model\u2019s real parameter ids and ranges, and register it as the Idle motion. tracks: list of {parameter, wave:sine (center, amplitude, cycles = whole number per loop, optional phase 0-1) | blink (at: [seconds], optional closed_seconds, open_value, closed_value) | keys ([[seconds, value], ...] eased)}. The structural check runs automatically.',{**M,'name':S,'tracks':{'type':'array','items':{'type':'object'}},'seconds':{'type':'number'},'fps':{'type':'integer'},'as_idle':{'type':'boolean'},'note':S},['model_id','name','tracks'],'write_motion')}
