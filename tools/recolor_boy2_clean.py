import bpy,sys,os,json,hashlib,shutil,math
from mathutils import Vector
src,out=sys.argv[sys.argv.index('--')+1:][:2]
os.makedirs(out,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
ext=os.path.splitext(src)[1].lower()
if ext in ['.glb','.gltf']:bpy.ops.import_scene.gltf(filepath=src)
elif ext=='.fbx':bpy.ops.import_scene.fbx(filepath=src)
else:raise ValueError('Expected GLB/glTF or FBX')
# Bake world position into UV space for precise spatial color selection
import numpy as np
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1
obj=next(o for o in scene.objects if o.type=='MESH');original_mat=obj.data.materials[0]
bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
position_image=bpy.data.images.new('Temporary UV position',width=4096,height=4096,alpha=True,float_buffer=True)
position_image.colorspace_settings.name='Non-Color'
bake_mat=bpy.data.materials.new('Temporary position bake');bake_mat.use_nodes=True;nodes=bake_mat.node_tree.nodes;nodes.clear();links=bake_mat.node_tree.links
geo=nodes.new('ShaderNodeNewGeometry');add=nodes.new('ShaderNodeVectorMath');add.operation='ADD';add.inputs[1].default_value=(.5,.5,.5)
emit=nodes.new('ShaderNodeEmission');output=nodes.new('ShaderNodeOutputMaterial');target=nodes.new('ShaderNodeTexImage');target.image=position_image;nodes.active=target
links.new(geo.outputs['Position'],add.inputs[0]);links.new(add.outputs['Vector'],emit.inputs['Color']);links.new(emit.outputs[0],output.inputs['Surface'])
obj.data.materials[0]=bake_mat
bpy.ops.object.bake(type='EMIT',margin=3,use_clear=True)
posbuf=np.empty(len(position_image.pixels),dtype=np.float32);position_image.pixels.foreach_get(posbuf)
xyz=posbuf.reshape((-1,4))[:,:3]-.5;x,y,z=xyz.T
obj.data.materials[0]=original_mat
bpy.data.materials.remove(bake_mat);bpy.data.images.remove(position_image)
changes=[];seen=set()
headfront=(y<-.11)&(z>-.22)&(z<.27)
candidate_hair=(z>.16)|((abs(x)>.255)&(z>-.055))|((y>.04)&(z>-.15))
strict_hair=(z>.255)|((abs(x)>.30)&(z>.065))|((y>.12)&(z>-.10))
for n in original_mat.node_tree.nodes:
 if n.type!='TEX_IMAGE' or not n.image or n.image.as_pointer() in seen:continue
 im=n.image;seen.add(im.as_pointer())
 if 'basecolor' not in im.name.lower():continue
 buf=np.empty(len(im.pixels),dtype=np.float32);im.pixels.foreach_get(buf);rgba=buf.reshape((-1,4));rgb=rgba[:,:3]
 r,g,bb=[rgb[:,i].copy() for i in range(3)]
 hairmask=strict_hair|(candidate_hair&(r<.72)&(bb>r*.86)&(bb>g*.87))
 face=headfront&(r>.40)&(g>r*.88)&(bb>r*.91)&~hairmask
 eyes=headfront&(r>.50)&(g>.48)&(bb<.20)&(z>-.045)
 mouth=headfront&(z>-.165)&(z<-.045)&(abs(x)<.275)
 teeth=mouth&(r>.32)&(g>.28)&(bb<g*.87)&(bb>r*.16)
 mask=headfront&(z>-.045)&(z<.155)&(abs(x)>.055)&(r<.20)&(g<.20)&(bb<.28)&~eyes&~hairmask
 lips=mouth&(bb>r*1.8)&(bb>g*1.4)&(bb>.09)&~teeth
 body=(z<-.20)&(g>r*1.4)&(bb>g*.95)
 hairvar=np.clip(bb/(np.median(bb[hairmask]) if hairmask.any() else .3),.84,1.04)
 rgb[hairmask]=hairvar[hairmask,None]*np.array([.003,.70,.94])
 fv=np.clip((r+g+bb)/3/.82,.90,1.08);rgb[face]=fv[face,None]*np.array([.43,.45,.47])
 rgb[eyes]=np.array([1.0,.81,.003]);rgb[teeth]=np.array([1.0,.79,.004])
 rgb[mask]=np.array([.006,.007,.012]);rgb[lips]=np.array([.018,.018,.12]);rgb[body]*=.60
 np.clip(rgb,0,1,out=rgb);im.pixels.foreach_set(buf);im.update()
 im.filepath_raw=os.path.join(out,'boy2_clean_basecolor.png');im.file_format='PNG';im.save();im.pack()
 changes.append({'method':'UV world-position bake plus albedo region masks','cyan_hair_pixels':int(hairmask.sum()),'black_eye_mask_pixels':int(mask.sum()),'gray_face_pixels':int(face.sum())})
seen=set()
for n in original_mat.node_tree.nodes:
 if n.type!='TEX_IMAGE' or not n.image or n.image.as_pointer() in seen:continue
 im=n.image;seen.add(im.as_pointer())
 if 'roughness' not in im.name.lower():continue
 buf=np.empty(len(im.pixels),dtype=np.float32);im.pixels.foreach_get(buf);rgba=buf.reshape((-1,4))
 rgba[:,1]=np.clip(.62+.25*rgba[:,1],0,1);rgba[:,2]*=.35;rgba[headfront,2]=0
 im.pixels.foreach_set(buf);im.update();im.filepath_raw=os.path.join(out,'boy2_satin_rm.png');im.file_format='PNG';im.save();im.pack()
 changes.append('satin roughness; nonmetal head; subdued metal accessories')
bpy.ops.object.select_all(action='SELECT')
export_path=os.path.join(out,'model.glb')
bpy.ops.export_scene.gltf(filepath=export_path,export_format='GLB',use_selection=True)
# Render the actual portable export, so evaluation covers the delivered material
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=export_path)

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
report={'source':src,'source_sha256':hashlib.sha256(open(src,'rb').read()).hexdigest(),'original_dimensions':list(hi-lo),'mesh_objects':len(meshes),'vertices':sum(len(o.data.vertices) for o in meshes),'polygons':sum(len(o.data.polygons) for o in meshes),'materials':[m.name for m in bpy.data.materials],'textures':[{'name':im.name,'width':im.size[0],'height':im.size[1]} for im in bpy.data.images if im.type=='IMAGE' and im.size[0]>0],'materials_modified':True,'material_changes':changes,'method':'Local boy2 alternate finish using accepted geometry, checked after GLB reimport','views':[v[0] for v in views]}
with open(os.path.join(out,'inspection.json'),'w') as f:json.dump(report,f,indent=2)
print(json.dumps(report))

