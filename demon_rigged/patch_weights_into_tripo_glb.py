"""Copy the fixed skin weights into Tripo's original GLB, changing only JOINTS_0/WEIGHTS_0 bytes.
usage: python patch_weights_into_tripo_glb.py <tripo_raw.glb> <blender_fixed.glb> <out.glb>"""
import json, struct, sys, numpy as np
CT={5120:np.int8,5121:np.uint8,5122:np.int16,5123:np.uint16,5125:np.uint32,5126:np.float32}
NC={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def load(p):
    f=bytearray(open(p,'rb').read()); jl=struct.unpack('<I',f[12:16])[0]
    j=json.loads(f[20:20+jl]); bo=20+jl+8
    return f,j,bo
def view(f,j,bo,ai):
    a=j['accessors'][ai]; bv=j['bufferViews'][a['bufferView']]
    dt=np.dtype(CT[a['componentType']]); n=NC[a['type']]
    stride=bv.get('byteStride',dt.itemsize*n)
    start=bo+bv.get('byteOffset',0)+a.get('byteOffset',0)
    return a,dt,n,stride,start
def read(f,j,bo,ai):
    a,dt,n,stride,start=view(f,j,bo,ai)
    out=np.empty((a['count'],n),dt)
    for i in range(a['count']):
        out[i]=np.frombuffer(f,dt,n,start+i*stride)
    if a.get('normalized') and dt!=np.float32: out=out.astype(np.float32)/np.iinfo(dt).max
    return out
def write(f,j,bo,ai,data):
    a,dt,n,stride,start=view(f,j,bo,ai)
    if a.get('normalized') and dt!=np.float32: data=np.round(data*np.iinfo(dt).max)
    data=data.astype(dt)
    for i in range(a['count']):
        f[start+i*stride:start+i*stride+dt.itemsize*n]=data[i].tobytes()
raw,rj,rbo=load(sys.argv[1]); fix,fj,fbo=load(sys.argv[2])
rn=[rj['nodes'][k]['name'] for k in rj['skins'][0]['joints']]
fn=[fj['nodes'][k]['name'] for k in fj['skins'][0]['joints']]
remap={i:rn.index(n) for i,n in enumerate(fn)}
total=0
for rp,fp in zip(rj['meshes'][0]['primitives'],fj['meshes'][0]['primitives']):
    ra,fa=rp['attributes'],fp['attributes']
    rpos,ruv=read(raw,rj,rbo,ra['POSITION']),read(raw,rj,rbo,ra['TEXCOORD_0'])
    fpos,fuv=read(fix,fj,fbo,fa['POSITION']),read(fix,fj,fbo,fa['TEXCOORD_0'])
    fJ,fW=read(fix,fj,fbo,fa['JOINTS_0']),read(fix,fj,fbo,fa['WEIGHTS_0'])
    rJ,rW=read(raw,rj,rbo,ra['JOINTS_0']),read(raw,rj,rbo,ra['WEIGHTS_0'])
    k=lambda p,u:(tuple(np.round(p,4)),tuple(np.round(u,4)))
    kp=lambda p:tuple(np.round(p,4))
    lut={k(p,u):i for i,(p,u) in enumerate(zip(fpos,fuv))}
    lutp={kp(p):i for i,p in enumerate(fpos)}
    nJ,nW=rJ.copy(),rW.copy(); miss=changed=0
    for i,(p,u) in enumerate(zip(rpos,ruv)):
        m=lut.get(k(p,u), lutp.get(kp(p)))
        if m is None:
            d=np.linalg.norm(fpos-p,axis=1); m=int(d.argmin())
            if d[m]>2e-3: miss+=1; continue
        js=[remap[int(x)] for x in fJ[m]]; ws=fW[m].astype(np.float32)
        ws=ws/ws.sum() if ws.sum()>0 else ws
        nJ[i]=js; nW[i]=ws
        if np.abs(np.sort(ws)-np.sort(rW[i].astype(np.float32)/max(rW[i].sum(),1e-9))).max()>1e-3 or set(js)!=set(int(x) for x in rJ[i]): changed+=1
    write(raw,rj,rbo,ra['JOINTS_0'],nJ); write(raw,rj,rbo,ra['WEIGHTS_0'],nW)
    print('verts',len(rpos),'unmatched',miss,'changed',changed); total+=changed
open(sys.argv[3],'wb').write(raw)
print('wrote',sys.argv[3])
