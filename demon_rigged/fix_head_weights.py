import bpy, sys, collections, mathutils
a=sys.argv[sys.argv.index('--')+1:]; src=a[0]; out=a[1]; heat=a[2] if len(a)>2 else None
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
for o in list(bpy.data.objects):
    if o.type=='MESH' and not o.vertex_groups: bpy.data.objects.remove(o)
mesh=[o for o in bpy.data.objects if o.type=='MESH'][0]
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
me=mesh.data; mw=mesh.matrix_world
vg={g.name:g for g in mesh.vertex_groups}; names={g.index:g.name for g in mesh.vertex_groups}
P='mixamorig:'
def B(n): return arm.matrix_world@arm.data.bones[P+n].head_local
neck=B('Neck'); head=B('Head')
W=[mw@v.co for v in me.vertices]
# islands with position welding
key=lambda co:(round(co.x,5),round(co.y,5),round(co.z,5))
par=list(range(len(me.vertices)))
def f(x):
    while par[x]!=x: par[x]=par[par[x]]; x=par[x]
    return x
pos={}
for v in me.vertices: pos.setdefault(key(v.co),[]).append(v.index)
for l in pos.values():
    for i in l[1:]: par[f(i)]=f(l[0])
for e in me.edges: par[f(e.vertices[0])]=f(e.vertices[1])
isl=collections.defaultdict(list)
for v in me.vertices: isl[f(v.index)].append(v.index)
main=max(isl.values(), key=len); mainset=set(main)
def w(v,n): 
    for g in v.groups:
        if names[g.group]==P+n: return g.weight
    return 0.0
def headw(v): return w(v,'Head')+w(v,'HeadTop_End')
def dom(v):
    gs=[(g.weight,names[g.group]) for g in v.groups]
    return max(gs)[1] if gs else None
rigid=set()
# 1) small islands sitting in the head (mouth/teeth, eyes)
for l in isl.values():
    if l is main: continue
    c=sum((W[i] for i in l), mathutils.Vector())/len(l)
    hs=sum(headw(me.vertices[i]) for i in l)/len(l)
    if c.z>neck.z+0.02 and abs(c.x)<0.2 and hs>=0.4:
        rigid.update(l); print('rigid island',len(l),tuple(round(x,3) for x in c),'head share',round(hs,2))
# 2) main island: flood fill from top of head through head/neck-dominant verts above the jaw cut
CUT=head.z-0.035
adj=collections.defaultdict(set)
for e in me.edges:
    x,y=e.vertices; adj[x].add(y); adj[y].add(x)
for l in pos.values():
    for i in l:
        adj[i].update(j for j in l if j!=i)
seed=max(main, key=lambda i:W[i].z)
ok=lambda i: W[i].z>CUT and (dom(me.vertices[i]) or '').replace(P,'') in ('Head','HeadTop_End','Neck')
seen={seed}; st=[seed]
while st:
    x=st.pop()
    for y in adj[x]:
        if y not in seen and y in mainset and ok(y): seen.add(y); st.append(y)
print('head flood verts',len(seen),'max|x|',round(max(abs(W[i].x) for i in seen),3),'min z',round(min(W[i].z for i in seen),3))
rigid|=seen
# chin underside: in front of the neck, above the neck joint
chin=[i for i in main if i not in rigid and W[i].z>neck.z+0.005 and W[i].y<neck.y-0.055 and abs(W[i].x)<0.2]
print('chin verts',len(chin)); rigid.update(chin)
def setonly(i, wd):
    v=me.vertices[i]
    for g in list(v.groups): mesh.vertex_groups[g.group].remove([i])
    for n,val in wd.items():
        if val>0: vg[P+n].add([i],val,'REPLACE')
for i in rigid: setonly(i,{'Head':1.0})
# 3) jaw-underside / neck band of main island: drop arm influence, blend Neck->Head by height
ARMS=('Arm','ForeArm','Hand','Shoulder')
band=0
for i in main:
    if i in rigid: continue
    co=W[i]
    if neck.z-0.01 < co.z <= CUT+0.01 and abs(co.x)<0.075 and co.y < neck.y+0.06:
        v=me.vertices[i]
        armw=sum(g.weight for g in v.groups if any(names[g.group].endswith(k) or ('Left'+k) in names[g.group] or ('Right'+k) in names[g.group] for k in ARMS))
        if armw<=0: continue
        t=max(0.0,min(1.0,(co.z-neck.z)/(CUT-neck.z)))
        setonly(i,{'Head':t,'Neck':1-t}); band+=1
print('neck band reweighted',band)
# report remaining arm influence above the jaw cut inside head width
left=0
for i in main:
    co=W[i]
    if co.z>CUT and abs(co.x)<0.12 and co.y<-0.15:
        v=me.vertices[i]
        if any(('Arm' in names[g.group] or 'Shoulder' in names[g.group]) and g.weight>0.01 for g in v.groups): left+=1
print('face-front verts still with arm weight',left)
if heat:
    col=me.color_attributes.new('w','FLOAT_COLOR','POINT')
    for v in me.vertices:
        h=headw(v); am=sum(g.weight for g in v.groups if 'Arm' in names[g.group] or 'Shoulder' in names[g.group] or 'Hand' in names[g.group])
        col.data[v.index].color=(am,h,0.15,1)
    sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'; sc.display.shading.color_type='VERTEX'
    sc.render.resolution_x=sc.render.resolution_y=700
    cam=bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera=cam
    cam.data.type='ORTHO'; cam.data.ortho_scale=0.75
    arm.data.pose_position='REST'
    for nm,d in [('front',(0,-1,0)),('side',(1,0,0))]:
        dv=mathutils.Vector(d); cam.location=mathutils.Vector((0,-0.1,0.62))+dv*3
        cam.rotation_euler=(-dv).to_track_quat('-Z','Y').to_euler()
        sc.render.filepath=f"{heat}_{nm}.png"; bpy.ops.render.render(write_still=True)
    arm.data.pose_position='POSE'
    me.color_attributes.remove(me.color_attributes['w'])
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_animation_mode='ACTIONS', export_yup=True)
print('exported',out)
