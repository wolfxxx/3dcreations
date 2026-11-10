import bpy,sys,os,json,hashlib,shutil,math
from mathutils import Vector
src,out=sys.argv[sys.argv.index('--')+1:][:2]
os.makedirs(out,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
ext=os.path.splitext(src)[1].lower()
if ext in ['.glb','.gltf']:bpy.ops.import_scene.gltf(filepath=src)
elif ext=='.fbx':bpy.ops.import_scene.fbx(filepath=src)
else:raise ValueError('Expected GLB/glTF or FBX')
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
report={'source':src,'source_sha256':hashlib.sha256(open(src,'rb').read()).hexdigest(),'original_dimensions':list(hi-lo),'mesh_objects':len(meshes),'vertices':sum(len(o.data.vertices) for o in meshes),'polygons':sum(len(o.data.polygons) for o in meshes),'materials':[m.name for m in bpy.data.materials],'textures':[{'name':im.name,'width':im.size[0],'height':im.size[1]} for im in bpy.data.images if im.type=='IMAGE' and im.size[0]>0],'materials_modified':False,'views':[v[0] for v in views]}
with open(os.path.join(out,'inspection.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))

