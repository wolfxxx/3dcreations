import bpy, sys, os, math, json
from mathutils import Vector
import glob, re
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if args:
 src,out=args[:2]
else:
 src=max(glob.glob('C:/Users/PC/Documents/GITHUBprojects/TRELLIS/outputs/*boy*_attempt*/model.glb'),key=os.path.getmtime)
 label=re.search(r'(boy[12])_attempt(\d+)',src)
 out='C:/Users/PC/Documents/GITHUBprojects/3dcreations/'+label[1]+'/attempt'+label[2]
os.makedirs(out,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
points=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
lo=Vector(tuple(min(p[i] for p in points) for i in range(3)))
hi=Vector(tuple(max(p[i] for p in points) for i in range(3)))
center=(lo+hi)/2
size=max(hi-lo)
for o in bpy.context.scene.objects:
 if o.parent is None:
  o.location=(o.location-center)/size
  o.scale/=size
for o in meshes:
 for poly in o.data.polygons: poly.use_smooth=True
 for mat in o.data.materials:
  if mat and mat.use_nodes:
   for n in mat.node_tree.nodes:
    if n.type=='BSDF_PRINCIPLED':
     n.inputs['Roughness'].default_value=0.68
     n.inputs['Metallic'].default_value=0
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(out,'model.glb'),export_format='GLB',use_selection=True)
s=bpy.context.scene
s.render.engine='CYCLES'
s.cycles.samples=32
s.render.resolution_x=900;s.render.resolution_y=900;s.render.resolution_percentage=100
s.world=bpy.data.worlds.new('Studio');s.world.use_nodes=True
s.world.node_tree.nodes.get('Background').inputs[0].default_value=(0.48,0.48,0.48,1)
s.world.node_tree.nodes.get('Background').inputs[1].default_value=0.8
s.view_settings.view_transform='Standard'
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,scale in [('Key',(2,-3,4),220,4),('Fill',(-3,-2,1),100,3),('Rim',(1,3,3),160,3)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=scale;aim(o,(0,0,0))
bpy.ops.object.camera_add();cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=1.19
for name,loc in [('front',(0,3,0.05)),('quarter',(-2,3,0.3)),('side',(3,0,0.1)),('back',(0,-3,0.1))]:
 cam.location=loc;aim(cam,(0,0,0));s.render.filepath=os.path.join(out,name+'.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,'model.blend'))
report={'source':src,'vertices':sum(len(o.data.vertices) for o in meshes),'polygons':sum(len(o.data.polygons) for o in meshes),'meshes':len(meshes),'materials':len(bpy.data.materials),'original_dimensions':list(hi-lo)}
with open(os.path.join(out,'inspection.json'),'w') as f:json.dump(report,f,indent=2)
print(report)

