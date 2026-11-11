"""Conservative single-colour cutout; ambiguous backgrounds are rejected."""
from collections import deque
from PIL import Image, ImageDraw, ImageFilter


def cutout(image, key=None, tolerance=18, softness=35):
    if not 0 <= tolerance <= 80 or not 1 <= softness <= 100:
        raise ValueError('Choose tolerance 0–80 and edge softness 1–100')
    im = image.convert('RGB'); w,h = im.size
    if w*h > 4_000_000 or min(w,h) < 3: raise ValueError('Part dimensions must be between 3 pixels and 4 megapixels')
    pixels = list(im.get_flattened_data() if hasattr(im,'get_flattened_data') else im.getdata()); corners=[pixels[0], pixels[w-1], pixels[-w], pixels[-1]]
    if key is None:
        key=tuple(sorted(c[i] for c in corners)[1] for i in range(3))
    if not isinstance(key,(list,tuple)) or len(key)!=3 or any(type(x) is not int or not 0<=x<=255 for x in key):
        raise ValueError('Key colour must be three RGB integers from 0 to 255')
    def distance(p): return max(abs(p[i]-key[i]) for i in range(3))
    # Requiring every border pixel to match excludes checkerboards, shadows, gradients,
    # and clipped artwork instead of silently eating it.
    border=list(range(w))+list(range((h-1)*w,h*w))+[y*w for y in range(1,h-1)]+[y*w+w-1 for y in range(1,h-1)]
    if any(distance(pixels[i])>tolerance for i in border):
        raise ValueError('Background is not a flat key colour around every edge, or the artwork touches the border; use a flat background without checkerboard, gradient or shadow')
    threshold=tolerance+softness
    distances=[distance(p) for p in pixels]
    low=min(range(3),key=lambda i:key[i]);high=[i for i in range(3) if key[i]-key[low]>=150]
    def keylike(p):
        return bool(high) and all(p[i]-p[low]>=65 for i in high) and max(p[i] for i in high)-min(p[i] for i in high)<=65
    chroma=bytearray(1 if keylike(p) else 0 for p in pixels)
    tight=bytearray(1 if d<=tolerance else 0 for d in distances)
    hard=bytearray(1 if tight[i] or chroma[i] else 0 for i in range(w*h))
    strong=Image.frombytes('L',(w,h),bytes(255 if distances[i]>threshold and not chroma[i] else 0 for i in range(w*h)))
    near_strong=strong.filter(ImageFilter.MaxFilter(5)).tobytes()
    # Find clearly keyed pixels connected to the border; other keyed pixels are
    # enclosed holes. They are also removed under the single-key art contract.
    connected=bytearray(w*h);q=deque(border)
    for i in border:connected[i]=1
    while q:
        i=q.popleft();x=i%w;y=i//w
        for j in ((i-1 if x else -1),(i+1 if x+1<w else -1),(i-w if y else -1),(i+w if y+1<h else -1)):
            if j>=0 and not connected[j] and hard[j]:connected[j]=1;q.append(j)
    hard_image=Image.frombytes('L',(w,h),bytes(255*v for v in tight))
    near=hard_image.filter(ImageFilter.MaxFilter(5)).tobytes()
    uncertain=sum(1 for i,d in enumerate(distances) if tolerance<d<=threshold and not near[i])
    foreground=sum(1 for d in distances if d>tolerance)
    limit=max(16,round(foreground*.01))
    if uncertain>limit:
        raise ValueError(f'Ambiguous key-colour band: {uncertain} pixels of {foreground} non-key pixels ({100*uncertain/max(1,foreground):.2f}%; limit {limit} pixels). Background may have a gradient or shadow, or the key resembles the part; regenerate on the other key colour.')
    holes=Image.frombytes('L',(w,h),bytes(255 if hard[i] and not connected[i] else 0 for i in range(w*h)))
    out=Image.new('RGBA',(w,h)); data=[]
    for i,p in enumerate(pixels):
        if chroma[i] and not near_strong[i]:data.append((0,0,0,0));continue
        if distances[i]>threshold and not chroma[i]: data.append((*p,255));continue
        alpha=max(0,min(255,round((distance(p)-tolerance)*255/softness)))
        if chroma[i]:alpha=min(alpha,128)
        # Undo the key-colour contribution at partially covered edges.
        if alpha:
            a=alpha/255; rgb=tuple(max(0,min(255,round((p[c]-key[c]*(1-a))/a))) for c in range(3))
            data.append((*rgb,alpha))
        else:data.append((0,0,0,0))
    out.putdata(data)
    # Remove only tiny isolated islands; cap the threshold at 16 pixels.
    alpha=out.getchannel('A'); mask=bytearray(1 if v else 0 for v in (alpha.get_flattened_data() if hasattr(alpha,'get_flattened_data') else alpha.getdata())); seen=bytearray(w*h)
    speck_limit=min(16,max(3,w*h//100000))
    for i in range(w*h):
        if not mask[i] or seen[i]:continue
        seen[i]=1;q=deque([i]);component=[]
        while q:
            j=q.popleft();component.append(j);x=j%w;y=j//w
            for k in ((j-1 if x else -1),(j+1 if x+1<w else -1),(j-w if y else -1),(j+w if y+1<h else -1)):
                if k>=0 and mask[k] and not seen[k]:seen[k]=1;q.append(k)
        if len(component)<=speck_limit:
            for j in component:data[j]=(0,0,0,0)
    out.putdata(data);box=out.getbbox()
    if box is None:raise ValueError('Cutout removed the entire image; choose a different key colour')
    out.info['cutout_holes']=holes
    return out,box,tuple(key)


def preview(before, after):
    size=(320,320); a=before.convert('RGB');a.thumbnail(size)
    b=after.copy();b.thumbnail(size)
    sheet=Image.new('RGB',(640,320),'white');sheet.paste(a,((320-a.width)//2,(320-a.height)//2))
    tile=Image.new('RGB',b.size,'white');d=ImageDraw.Draw(tile)
    for y in range(0,b.height,12):
        for x in range(0,b.width,12):
            if (x//12+y//12)%2:d.rectangle((x,y,x+11,y+11),fill='#cccccc')
    tile.paste(b,(0,0),b)
    holes=after.info.get('cutout_holes')
    if holes:
        holes=holes.copy();holes.thumbnail(size)
        tint=Image.new('RGB',tile.size,(255,100,20));tile.paste(tint,(0,0),holes)
    sheet.paste(tile,(320+(320-b.width)//2,(320-b.height)//2))
    return sheet
