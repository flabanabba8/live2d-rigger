"""Bounded image registration of a whole RGBA part against a reference.

This is a proposal generator: semantic resemblance is not proof of placement.
"""
import math
from PIL import Image


def _numpy():
    try: import numpy as np
    except ImportError: raise ValueError('Reference registration needs NumPy in the Hermes runtime; install it or configure an existing runtime that has it') from None
    return np


def _convolve(image, kernel, np):
    h,w=image.shape;kh,kw=kernel.shape;shape=(h+kh-1,w+kw-1)
    f=np.fft.rfftn(image,shape,axes=(0,1));g=np.fft.rfftn(kernel[::-1,::-1],shape,axes=(0,1))
    return np.fft.irfftn(f*g,shape,axes=(0,1))[kh-1:h,kw-1:w].real


def _score_map(image, template, alpha, np):
    weight=alpha.astype(np.float64)/255.;n=weight.sum()
    if n<4:return None
    sum_i=np.zeros((image.shape[0]-template.shape[0]+1,image.shape[1]-template.shape[1]+1));sum_i2=sum_i.copy();cross=sum_i.copy();sum_t=0.;sum_t2=0.
    for c in range(3):
        a=image[:,:,c].astype(np.float64);t=template[:,:,c].astype(np.float64)
        sum_i+=_convolve(a,weight,np);sum_i2+=_convolve(a*a,weight,np);cross+=_convolve(a,t*weight,np)
        sum_t+=float((t*weight).sum());sum_t2+=float((t*t*weight).sum())
    denom=n*3
    mse=np.maximum(0.,(sum_i2-2*cross+sum_t2)/denom)
    # Colour error is meaningful even for a flat template; correlation helps
    # favour a local feature over an unrelated region of similar average colour.
    variance_t=max(0.,sum_t2-sum_t*sum_t/denom)
    var_i=np.maximum(0.,sum_i2-sum_i*sum_i/denom)
    if variance_t>1e-6:
        corr=(cross-sum_i*sum_t/denom)/np.sqrt(np.maximum(var_i*variance_t,1e-12))
        corr=np.clip(corr,0.,1.)
    else:corr=np.ones_like(mse)
    return .7*(1-np.sqrt(mse)/255.)+.3*corr


def _region(role, subject, w, h):
    role=role.lower();sx,sy,ex,ey=subject;sw=ex-sx;sh=ey-sy
    x0,y0,x1,y1=sx,sy,ex,ey;minimum,maximum=.03,1.0
    if any(x in role for x in ('hair','fringe','bang')):y1=sy+sh*.58;minimum,maximum=.50,1.05
    elif any(x in role for x in ('eye','iris','brow','lid')):y0=sy+sh*.18;y1=sy+sh*.54;minimum,maximum=.08,.34
    elif 'mouth' in role:y0=sy+sh*.3;y1=sy+sh*.65;minimum,maximum=.02,.25
    elif 'face' in role:y1=sy+sh*.62;minimum,maximum=.38,.9
    elif 'neck' in role:y0=sy+sh*.32;y1=sy+sh*.68;minimum,maximum=.08,.4
    elif any(x in role for x in ('dress','torso','apron','body')):y0=sy+sh*.38;minimum,maximum=.35,1.0
    elif any(x in role for x in ('leg','shoe','foot')):y0=sy+sh*.62;minimum,maximum=.06,.45
    if any(x in role for x in ('left','_l_')):x1=sx+sw*.62
    elif any(x in role for x in ('right','_r_')):x0=sx+sw*.38
    return max(0,int(x0)),max(0,int(y0)),min(w,math.ceil(x1)),min(h,math.ceil(y1)),minimum*sw,maximum*sw


def _subject_bounds(image,np):
    corners=np.array([image[0,0],image[0,-1],image[-1,0],image[-1,-1]],dtype=np.int16)
    background=np.median(corners,axis=0);delta=np.max(np.abs(image.astype(np.int16)-background),axis=2)
    ys,xs=np.where(delta>35)
    if len(xs)<20:return (0,0,image.shape[1],image.shape[0])
    return (int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1)


def register(reference, part, role='', threshold=.90):
    np=_numpy()
    if not 0<=threshold<=1:raise ValueError('Registration confidence threshold must be between 0 and 1')
    ref=reference.convert('RGB');rgba=part.convert('RGBA');box=rgba.getchannel('A').getbbox()
    if not box:raise ValueError('Part has no visible pixels')
    if ref.width*ref.height>16_000_000:raise ValueError('Reference is too large for bounded registration')
    part_crop=rgba.crop(box);factor=min(1.,192/max(ref.size));small=ref.resize((max(1,round(ref.width*factor)),max(1,round(ref.height*factor))),Image.Resampling.LANCZOS)
    arr=np.asarray(small);subject=_subject_bounds(arr,np);rx0,ry0,rx1,ry1,min_w,max_w=_region(role,subject,small.width,small.height);roi=arr[ry0:ry1,rx0:rx1]
    best=None
    for scale in np.geomspace(.05,2.0,32):
        tw=max(2,round(part_crop.width*factor*scale));th=max(2,round(part_crop.height*factor*scale))
        if tw>roi.shape[1] or th>roi.shape[0] or tw<min_w or tw>max_w:continue
        tile=part_crop.resize((tw,th),Image.Resampling.LANCZOS);scores=_score_map(roi,np.asarray(tile.convert('RGB')),np.asarray(tile.getchannel('A')),np)
        if scores is None:continue
        yy,xx=np.unravel_index(int(np.argmax(scores)),scores.shape);score=float(scores[yy,xx])
        if best is None or score>best[0]:best=(score,(xx+rx0)/factor,(yy+ry0)/factor,float(scale))
    if best is None:raise ValueError('No part scale fits the allowed reference region')
    # Refine on the full-size reference in a small neighbourhood around the
    # coarse peak; only a bounded crop and a few adjacent scales are evaluated.
    _,cx,cy,cs=best;radius=max(4,math.ceil(2/factor));best_full=None
    for scale in np.linspace(cs*.9,cs*1.1,7):
        tw=max(2,round(part_crop.width*scale));th=max(2,round(part_crop.height*scale))
        if tw*factor<min_w or tw*factor>max_w:continue
        x0=max(0,round(cx)-radius);y0=max(0,round(cy)-radius);x1=min(ref.width,round(cx)+radius+tw);y1=min(ref.height,round(cy)+radius+th)
        if x1-x0<tw or y1-y0<th:continue
        tile=part_crop.resize((tw,th),Image.Resampling.LANCZOS);crop=np.asarray(ref.crop((x0,y0,x1,y1)))
        scores=_score_map(crop,np.asarray(tile.convert('RGB')),np.asarray(tile.getchannel('A')),np)
        if scores is None:continue
        yy,xx=np.unravel_index(int(np.argmax(scores)),scores.shape);candidate=(float(scores[yy,xx]),x0+int(xx),y0+int(yy),float(scale))
        if best_full is None or candidate[0]>best_full[0]:best_full=candidate
    score,x,y,scale=best_full or best
    return {'score':round(score,4),'threshold':threshold,'accepted':bool(score>=threshold),'x':round(x-box[0]*scale,3),'y':round(y-box[1]*scale,3),'scale':round(scale,5),'visible_box':[round(x),round(y),round(x+part_crop.width*scale),round(y+part_crop.height*scale)],'notice':'Similarity is only a proposal; inspect the reassembled character. Low scores require a plain-words placement nudge.'}
