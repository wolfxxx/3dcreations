import bpy, math, os, sys, runpy, bmesh
from mathutils import Vector
from math import sin,cos,pi
root='C:/Users/PC/Documents/GITHUBprojects/3dcreations'
out=root+'/boy1/attempt09'
os.makedirs(out,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
def mat(name,c,rough=.48,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True
 p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 return m
skin=mat('Porcelain pale blue',(0.66,.77,.83));hair=mat('Midnight violet hair',(.055,.052,.105))
black=mat('Black eye lacquer',(.007,.009,.015));yellow=mat('Yellow eyes',(.88,.73,.008),.32)
lip=mat('Indigo lip',(.025,.035,.27));teeth=mat('Ivory teeth',(.69,.65,.29));groove=mat('Tooth incisions',(.31,.29,.10))
feather=mat('Charcoal feather',(.025,.022,.018));suit=mat('Petrol blue leather',(.009,.063,.095))
silver=mat('Pewter ornaments',(.5,.57,.55),.35,.55);red=mat('Crimson apple',(.45,.008,.007),.3);brown=mat('Apple stalk',(.09,.035,.009));cloth=mat('Black brown fringe',(.065,.051,.04))
def finish(o,name,m):
 o.name=name;o.data.materials.append(m)
 if o.type=='MESH':
  for p in o.data.polygons:p.use_smooth=True
 return o
def ell(name,loc,sc,m):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=32,location=loc);o=bpy.context.object;o.scale=sc
 return finish(o,name,m)
def path(name,pts,r,m):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=24;cu.bevel_depth=r;cu.bevel_resolution=4;cu.use_fill_caps=True
 sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
 for p,co in zip(sp.bezier_points,pts):p.co=co;p.handle_left_type='VECTOR' if 'incision' in name else 'AUTO';p.handle_right_type=p.handle_left_type
 o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o);o.data.materials.append(m);return o
def poly(name,coords,m,depth=.02):
 me=bpy.data.meshes.new(name);me.from_pydata(coords,[],[list(range(len(coords)))]);me.update()
 o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);finish(o,name,m)
 if 'eye mask' in name:
  bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=list(bm.faces))
  bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=8,use_grid_fill=True)
  for v in bm.verts:
   x,z=v.co.x,v.co.z
   v.co.y=.90*max(.001,1-(abs(x)/1.48)**(2/.64)-(abs(z-3.25)/1.20)**(2/.65))**(.56/2)+.022
  bm.to_mesh(me);bm.free()
 mod=o.modifiers.new('Molded thickness','SOLIDIFY');mod.thickness=depth
 mod=o.modifiers.new('Soft manufactured edge','BEVEL');mod.width=.008;mod.segments=3
 return o
def lock(name,pts,width,depth,m):
 # tapered oval tube following a smooth Bezier-sampled spine
 cu=bpy.data.curves.new('spine','CURVE');cu.dimensions='3D';sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
 for p,co in zip(sp.bezier_points,pts):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 # Catmull-Rom
 points=[Vector(p) for p in pts];v=[];faces=[];N=36;K=16
 for i in range(N+1):
  t=i/N*(len(points)-1);j=min(int(t),len(points)-2);u=t-j
  a=points[max(j-1,0)];b=points[j];c=points[j+1];d=points[min(j+2,len(points)-1)]
  p=.5*((2*b)+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u)
  tangent=(c-b).normalized();side=Vector((0,1,0)).cross(tangent).normalized()
  if side.length<.1:side=Vector((1,0,0))
  other=tangent.cross(side).normalized()
  taper=max(.012,max(0,sin(pi*i/N))**.75)
  for k in range(K):
   q=p+side*(width*taper*cos(2*pi*k/K))+other*(depth*taper*sin(2*pi*k/K));v.append(q)
 for i in range(N):
  for k in range(K):faces.append((i*K+k,i*K+(k+1)%K,(i+1)*K+(k+1)%K,(i+1)*K+k))
 faces.extend([tuple(reversed(range(K))),tuple(N*K+k for k in range(K))])
 me=bpy.data.meshes.new(name);me.from_pydata(v,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);finish(o,name,m)
 return o
# Squared rounded head, flat sculptural front
bpy.ops.mesh.primitive_uv_sphere_add(segments=96,ring_count=64,location=(0,0,3.25));o=bpy.context.object
for v in o.data.vertices:
 x,y,z=v.co
 def pw(t,p):return math.copysign(abs(t)**p,t)
 v.co=(1.48*pw(x,.64),.90*pw(y,.56),1.20*pw(z,.65))
for v in o.data.vertices:
 if v.co.y>0:
  x,z=v.co.x,v.co.z+3.25
  v.co.y+=.16*math.exp(-((abs(x)-.72)/.43)**2-((z-3.68)/.15)**2)
finish(o,'Broad square sculpted head',skin)
# Face masks follow slightly convex front, smooth round eye domes
for s in [-1,1]:
 cx=s*.87
 # mirrored angular wing-shaped black patches
 coords=[(.36,.925,3.49),(.76,.955,3.60),(1.17,.84,3.69),(1.24,.78,3.90),(1.25,.8,3.59),(1.10,.9,3.48),(1.06,.94,3.18),(1.21,.82,3.13),(.96,.95,3.04),(.57,.97,3.08),(.38,.95,3.20)]
 poly('Angular black eye mask',[(s*x,.90*max(.02,1-(abs(x)/1.48)**(2/.64)-(abs(z-3.25)/1.20)**(2/.65))**(.56/2)+.012,z) for x,y,z in coords],black,.004)
 ell('Round yellow eye',(cx,.94,3.30),(.26,.095,.26),yellow)
 # seamless brows, shallow
 lock('Sculpted forehead ridge',[(s*.26,.91,3.59),(s*.59,.97,3.68),(s*.98,.89,3.80),(s*1.24,.71,3.90)],.12,.055,skin)
 ell('Ear',(s*1.47,0,2.93),(.14,.24,.30),skin)
 ell('Silver ear stud',(s*1.53,.18,2.83),(.06,.04,.07),silver)
 path('Earring drop',[(s*1.53,.17,2.82),(s*1.54,.18,2.66)],.035,silver)
# Nose
ell('Nose bridge',(0,.91,2.99),(.11,.035,.13),skin)
for s in [-1,1]:path('Nostril',[(s*.025,0.952,3.005),(s*.065,0.959,3.02),(s*.086,0.952,2.967)],.021,black)
# grin shape front band ivory enclosed with indigo rim
upper=[];lower=[]
for i in range(49):
 x=-1.17+2.34*i/48;t=x/1.17
 upper.append((x,.92+.10*(1-t*t),2.69+.21*abs(t)**5+.018*cos(t*pi*2)))
 lower.append((x,.92+.10*(1-t*t),2.43+.40*abs(t)**6))
poly('Closed ivory smile',upper+list(reversed(lower)),teeth,.035)
path('Upper blue lip',upper,.047,lip);path('Lower blue lip',lower,.047,lip)
for s in [-1,1]:path('Sweeping grin corner',[(s*1.16,.92,2.80),(s*1.25,.87,2.91),(s*1.28,.83,3.04)],.045,lip)
zig=[]
for i in range(25):
 x=-1.08+2.16*i/24;t=x/1.17;z=2.56+.23*abs(t)**6+(.039 if i%2 else -.039)
 zig.append((x,1.06-.08*t*t,z))
path('Continuous zigzag teeth incision',zig,.006,groove)
# Recover the strongest image-derived hair geometry, rebuild as clean solid volume
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.import_scene.gltf(filepath='C:/Users/PC/Documents/GITHUBprojects/TRELLIS/outputs/20261105_114723_boy1_attempt04/model.glb')
imported=list(bpy.context.selected_objects)
source=next(o for o in imported if o.type=='MESH')
me=source.data;uv=me.uv_layers.active.data
m=me.materials[0];tex=next(n.image for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
pix=list(tex.pixels);w,h=tex.size
verts=[source.matrix_world@v.co for v in me.vertices];faces=[]
for p in me.polygons:
 colors=[]
 for li in p.loop_indices:
  u,v=uv[li].uv;i=(min(h-1,max(0,int(v*h)))*w+min(w-1,max(0,int(u*w))))*4
  colors.append(pix[i:i+3])
 r,g,bb=[sum(c[k] for c in colors)/len(colors) for k in range(3)]
 z=sum(verts[i].z for i in p.vertices)/len(p.vertices)
 if bb>r*1.06 and bb>g*1.02 and max(r,g,bb)<.58 and z>-.02:
  faces.append(tuple(p.vertices))
hm=bpy.data.meshes.new('Recovered hair surface')
hm.from_pydata([(-p.x*4.5,p.y*4.5-.18,p.z*4.5+3.33) for p in verts],[],faces);hm.update()
ho=bpy.data.objects.new('Reconstructed swept hair volume',hm);bpy.context.collection.objects.link(ho)
for o in imported:bpy.data.objects.remove(o,do_unlink=True)
bm=bmesh.new();bm.from_mesh(hm);bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(hm);bm.free()
finish(ho,'Reconstructed swept hair volume',hair)
bpy.ops.object.select_all(action='DESELECT');ho.select_set(True);bpy.context.view_layer.objects.active=ho
sol=ho.modifiers.new('Fill shell thickness','SOLIDIFY');sol.thickness=.065;bpy.ops.object.modifier_apply(modifier=sol.name)
rem=ho.modifiers.new('Seal holes and isolated chips','REMESH');rem.mode='VOXEL';rem.voxel_size=.035;rem.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=rem.name)
sm=ho.modifiers.new('Polished swept locks','SMOOTH');sm.factor=.62;sm.iterations=5;bpy.ops.object.modifier_apply(modifier=sm.name)
sub=ho.modifiers.new('Fine hair surface','SUBSURF');sub.levels=1
print('Recovered hair faces',len(ho.data.polygons),'bounds',tuple(ho.dimensions))
# torso
ell('Crouching torso',(0,0,1.33),(.48,.32,.59),suit)
ell('Neck',(0,0,1.95),(.25,.23,.28),suit)
for s in [-1,1]:
 ell('Raised thigh',(s*.55,.05,.78),(.31,.34,.41),suit)
 ell('Bent shin',(s*.56,.30,.39),(.23,.24,.38),suit)
 ell('Grounded boot',(s*.59,.47,.16),(.27,.40,.17),suit)
 for z in [.34,.46,.58]:path('Boot leather fold',[(s*.76,.47,z),(s*.59,.55,z-.02),(s*.40,.46,z)],.018,suit)
# grounded left arm and fingers
lock('Left long sleeve',[(-.40,0,1.72),(-.48,.24,1.22),(-.56,.46,.69),(-.63,.65,.24)],.18,.15,suit)
ell('Grounded left palm',(-.63,.69,.17),(.22,.19,.12),suit)
for j in range(4):
 x=-.83+j*.12;path('Grounded left finger',[(x,.73,.17),(x-.01,.90,.11),(x,.99,.08)],.049,suit)
path('Left thumb',[(-.43,.69,.17),(-.36,.82,.13),(-.35,.91,.08)],.055,suit)
ell('Left wrist bracelet',(-.61,.62,.38),(.19,.17,.08),silver);ell('Wrist medallion',(-.61,.81,.39),(.12,.035,.10),silver)
# right bent arm supporting apple
lock('Right sleeve',[(.40,0,1.73),(.59,.16,1.32),(.91,.34,1.12)],.17,.15,suit)
ell('Right palm',(.96,.43,1.11),(.24,.18,.10),suit)
ell('Apple',(.95,.44,1.37),(.23,.22,.22),red)
# smooth apple body
path('Apple stalk',[(.95,.45,1.55),(.93,.44,1.67)],.025,brown)
for j in range(4):
 x=.76+j*.125;path('Apple holding finger',[(x,.57,1.10),(x,.63,1.19),(x,.61,1.31)],.045,suit)
# belt and layered fringe
path('Silver belt',[(-.43,.1,.98),(-.35,.30,.97),(0,.35,.94),(.35,.30,.97),(.43,.1,.98)],.037,silver)
path('Belt lower beads',[(-.41,.20,.89),(0,.37,.85),(.41,.20,.89)],.025,silver)
for j in range(11):
 x=-.36+j*.072
 lock('Tapered layered skirt',[(x,.25,.92),(x*1.05,.32,.64),(x*1.11,.28,.38+(.04 if j%2 else 0))],.065,.055,cloth)
ell('Belt skull medallion',(0,.41,.96),(.12,.045,.13),silver)
for j in range(14):
 a=j*2*pi/14
 ell('Buckle filigree',(.13*cos(a),.43,.96+.135*sin(a)),(.028,.026,.032),silver)
for j in range(13):
 x=-.38+j*.063
 ell('Belt bead',(x,.31+.08*(1-(x/.4)**2),.86),(.027,.026,.027),silver)
for s in [-1,1]:
 for j in range(3):
  z=1.24+j*.1
  path('Sleeve folds',[(s*.48,.27,z),(s*.54,.34,z-.025),(s*.64,.28,z-.005)],.014,suit)
for j in range(12):
 a=j*2*pi/12
 ell('Wrist medallion rim',(-.61+.105*cos(a),.838,.39+.084*sin(a)),(.018,.012,.018),silver)
for s in [-1,1]:ell('Skull eye',(s*.04,.454,.99),(.022,.009,.027),cloth)
# Irregular branching sprays of twisted feathers
for s in [-1,1]:
 for j in range(10):
  endx=[2.04,2.14,1.85,2.08,1.77,1.69,1.48,1.25,1.65,1.94][j]
  endz=[2.91,2.61,2.45,2.21,1.96,1.80,1.69,1.63,2.28,2.77][j]
  yy=-.03-(j%3)*.09
  lock('Curling collar feather',[(s*.24,yy,1.91),(s*.82,yy+.04,1.99+(endz-2)*.16),(s*(endx-.30),yy-.08,endz-.28),(s*endx,yy-.01,endz+.1)],.10+(j%3)*.02,.075,feather)
  if j<7:
   lock('Feather tapered offshoot',[(s*.84,yy,2.0),(s*1.22,yy-.04,2.06+(endz-2)*.30),(s*(endx-.10),yy-.04,endz-.33)],.053,.035,feather)
 for j in range(6):
  lock('Throat small feather',[(s*.08,.27,1.96),(s*(.24+j*.10),.30,1.87),(s*(.32+j*.12),.26,1.68-j*.025)],.07,.04,feather)
# material decoration garment rings
for x in [-.46,-.35,-.24]:
 path('Shoulder metal stitch',[(x,.27,1.61),(x,.30,1.53)],.015,silver)
# Lower entire head onto collar while preserving tiny crouching body
for o in list(bpy.context.scene.objects):
 if any(t in o.name.lower() for t in ['hair','lock','head','eye','forehead','nose','nostril','lip','smile','grin','incision','ear','widow']):
  if 'feather' not in o.name.lower() and 'holding' not in o.name.lower():
   o.location.z-=.48
# Widen smile to measured source proportion
for o in bpy.context.scene.objects:
 if any(t in o.name.lower() for t in ['lip','smile','grin','incision']):
  o.scale.x*=1.12
 if 'collar feather' in o.name.lower() or 'offshoot' in o.name.lower() or 'throat small' in o.name.lower():o.location.z-=.15
# Correct mirror so apple appears on viewer right
for o in bpy.context.scene.objects:
 o.location.x=-o.location.x
 o.scale.x=-o.scale.x
# export explicit model, renderer converts all meshes and curves
bpy.ops.object.select_all(action='SELECT')
bpy.context.view_layer.objects.active=next(o for o in bpy.context.selected_objects if o.type=='CURVE')
bpy.ops.object.convert(target='MESH')
src=out+'/constructed.glb'
bpy.ops.export_scene.gltf(filepath=src,export_format='GLB')
sys.argv=['review','--',src,out]
runpy.run_path(root+'/tools/review_model.py',run_name='__main__')

