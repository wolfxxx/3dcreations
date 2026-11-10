import bpy,sys,os,json,hashlib,shutil,math
from mathutils import Vector
src,out=sys.argv[sys.argv.index('--')+1:][:2]
os.makedirs(out,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
ext=os.path.splitext(src)[1].lower()
if ext in ['.glb','.gltf']:bpy.ops.import_scene.gltf(filepath=src)
elif ext=='.fbx':bpy.ops.import_scene.fbx(filepath=src)
else:raise ValueError('Expected GLB/glTF or FBX')
# Alternate finish derived from the accepted geometry, matched to boy2.jpg
import numpy as np
changes=[]
for mat in bpy.data.materials:
 if not mat.use_nodes:continue
 for n in mat.node_tree.nodes:
  if n.type!='TEX_IMAGE' or not n.image or 'basecolor' not in n.image.name.lower():continue
  im=n.image;buf=np.empty(len(im.pixels),dtype=np.float32);im.pixels.foreach_get(buf);rgba=buf.reshape((-1,4))
  rgb=rgba[:,:3];r=rgb[:,0].copy();g=rgb[:,1].copy();bb=rgb[:,2].copy()
  hairmask=(r>.018)&(r<.62)&(g>r*.78)&(g<r*1.22)&(bb>r*1.10)&(bb>g*1.10)&(bb<r*2.6)&(bb<g*2.6)
  face=(r>.50)&(g>r*.94)&(bb>r*.98)
  teeth=(r>.38)&(g>.32)&(bb<g*.85)&(bb>r*.20)&(r<g*1.35)
  lips=(bb>r*2.6)&(bb>g*1.8)&(bb>.10)&(r<.22)&(g<.22)
  body=(g>r*1.45)&(bb>g*1.02)&(g>.025)&~lips&~hairmask&~face
  # Exclude metallic ornaments from face recoloring using exported RM image
  rm=next((q.image for q in mat.node_tree.nodes if q.type=='TEX_IMAGE' and q.image and 'roughness' in q.image.name.lower()),None)
  if rm and tuple(rm.size)==tuple(im.size):
   mb=np.empty(len(rm.pixels),dtype=np.float32);rm.pixels.foreach_get(mb);face &= mb.reshape((-1,4))[:,2]<.10
  variation=np.clip(bb/(np.median(bb[hairmask]) if hairmask.any() else .3),.72,1.08)
  rgb[hairmask]=variation[hairmask,None]*np.array([.006,.73,.96])
  facevar=np.clip((r+g+bb)/3/(np.median((r[face]+g[face]+bb[face])/3) if face.any() else .8),.8,1.12)
  rgb[face]=facevar[face,None]*np.array([.40,.42,.44])
  rgb[teeth]=np.clip(g[teeth,None]/.65,.75,1.1)*np.array([.98,.76,.008])
  rgb[lips]*=.58;rgb[body]*=.63
  np.clip(rgb,0,1,out=rgb)
  im.pixels.foreach_set(buf);im.update();im.filepath_raw=os.path.join(out,'boy2_basecolor.png');im.file_format='PNG';im.save();im.pack()
  changes.append({'hair_cyan_pixels':int(hairmask.sum()),'gray_face_pixels':int(face.sum()),'yellow_teeth_pixels':int(teeth.sum()),'dark_lip_pixels':int(lips.sum()),'dark_suit_pixels':int(body.sum())})
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=os.path.join(out,'model.glb'),export_format='GLB',use_selection=True)
scene=bpy.context.scene
meshes=[o for o in scene.objects if o.type=='MESH']
pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
lo=Vector([min(p[i] for p in pts) for i in range(3)]);hi=Vector([max(p[i] for p in pts) for i in range(3)])
center=(lo+hi)/2;size=max(hi-lo)
for o in list(scene.objects):
 if o.parent is None:o.location=(o.location-center)/size;o.scale/=size
scene.render.engine='CYCLES';scene.cycles.samples=48
scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Review studio');scene.world.use_nodes=True
bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND')
bg.inputs[0].default_value=(.38,.38,.38,1);bg.inputs[1].default_value=.65
scene.view_settings.view_transform='Standard'
def aim(o):o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power in [('Softbox left',(-2,-3,3),140),('Softbox right',(2,3,3),140),('Fill',(0,0,4),50)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=3;aim(o)
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.2
views=[('neg_y',(0,-3,.08)),('pos_y',(0,3,.08)),('pos_x',(3,0,.08)),('neg_x',(-3,0,.08)),('quarter_neg_y',(2,-3,.3)),('quarter_pos_y',(-2,3,.3))]
for name,loc in views:
 cam.location=loc;aim(cam);scene.render.filepath=os.path.join(out,name+'.png');bpy.ops.render.render(write_still=True)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,'model.blend'))
report={'source':src,'source_sha256':hashlib.sha256(open(src,'rb').read()).hexdigest(),'original_dimensions':list(hi-lo),'mesh_objects':len(meshes),'vertices':sum(len(o.data.vertices) for o in meshes),'polygons':sum(len(o.data.polygons) for o in meshes),'materials':[m.name for m in bpy.data.materials],'textures':[{'name':im.name,'width':im.size[0],'height':im.size[1]} for im in bpy.data.images if im.type=='IMAGE' and im.size[0]>0],'materials_modified':True,'material_changes':changes,'method':'Local color variant of accepted boy1 geometry; independent comparison to boy2.jpg','views':[v[0] for v in views]}
with open(os.path.join(out,'inspection.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))

