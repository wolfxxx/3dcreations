import json,hashlib,shutil,struct
from pathlib import Path
root=Path('C:/Users/PC/Documents/GITHUBprojects/3dcreations')
final=root/'final';final.mkdir(exist_ok=True)
ledger="{\"ceiling\":250,\"spent\":110,\"remaining\":140,\"jobs\":[{\"id\":\"a48ad11b-85a0-4495-bc05-8ffe7bb928e9\",\"image\":\"boy1.jpg\",\"cost\":55,\"model\":\"H3.1\",\"geometry\":\"Ultra\",\"texture\":\"4K\",\"pbr\":true,\"status\":\"accepted\",\"source\":\"Tripo Studio\",\"score\":9,\"final\":\"boy1/portable01\",\"review\":{\"raw\":8.9,\"refined\":9,\"resemblance\":9.1,\"geometry\":8.9,\"materials\":9,\"coherence\":9,\"remaining_issues\":[\"Fine facial seams and brow scuffs\",\"Minor eye rim irregularities\",\"Soft double tooth incisions\",\"Rear is inferred from single reference\"]},\"portable_glb_review\":9},{\"id\":\"4acfd2df-c40d-4626-b303-785e9c50ffff\",\"image\":\"boy2.jpg\",\"cost\":55,\"model\":\"H3.1\",\"geometry\":\"Ultra\",\"texture\":\"4K\",\"pbr\":true,\"status\":\"accepted\",\"source\":\"Tripo Studio\",\"raw_score\":8.9,\"final\":\"boy2/portable01\",\"score\":9,\"portable_glb_review\":9,\"review\":{\"raw\":8.9,\"refined\":9,\"resemblance\":9.1,\"geometry\":8.9,\"materials\":9.1,\"coherence\":9,\"remaining_issues\":[\"Minor eye-mask and lip-corner lumpiness\",\"Deep/doubled tooth incision\",\"Simplified ears\",\"Rear design is inferred from single reference\"]}}],\"completed\":true}"
ledger=json.loads(ledger)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def glb_check(p):
 with p.open('rb') as f:
  magic,version,total=struct.unpack('<4sII',f.read(12));n,kind=struct.unpack('<II',f.read(8));data=json.loads(f.read(n))
 assert magic==b'glTF' and version==2 and total==p.stat().st_size
 return {'version':version,'bytes':total,'embedded_images':len(data.get('images',[])),'materials':data.get('materials',[])}
for idx in [1,2]:
 src=root/f'boy{idx}/portable01';dest=final/f'boy{idx}';dest.mkdir(exist_ok=True)
 for name in ['model.glb','model.blend']:
  if idx==1 and (dest/name).exists():
   previous=root/'boy1/tripo01_satin'/name
   assert sha(dest/name)==sha(previous),f'Unexpected edit to {dest/name}; inspect before replacing'
  elif (dest/name).exists():
   assert sha(dest/name)==sha(src/name),f'Unexpected existing {dest/name}'
  shutil.copy2(src/name,dest/name)
 for old,new in [('neg_y','front'),('pos_y','back'),('pos_x','side_pos_x'),('neg_x','side_neg_x'),('quarter_neg_y','quarter'),('quarter_pos_y','rear_quarter')]:
  shutil.copy2(src/(old+'.png'),dest/(new+'.png'))
 shutil.copy2(src/'inspection.json',dest/'inspection.json')
 j=ledger['jobs'][idx-1]
 review=f"# boy{idx}: accepted final model\n\nIndependent score: 9.0/10. All six views reviewed after exported GLB was reimported in Blender.\n\nReference: boy{idx}.jpg. Generation: Tripo Studio H3.1 Ultra geometry, 4K textures, PBR; 55 credits. Job: {j['id']}.\n\n"
 if idx==1:review+="Local refinement: satin roughness map, subdued metallic ornaments, normal-map input disconnected. Corrected texture files encoded into the portable GLB.\n\n"
 else:review+="Local refinement: warmer, brighter yellow eyes and teeth, matte yellow roughness, small emission contribution limited to those regions. Other geometry and colors preserved.\n\n"
 review+="Residual details: "+'; '.join(j['review']['remaining_issues'])+".\n\nOriginal generation downloads and intermediate attempts are preserved outside final/.\n"
 (dest/'REVIEW.md').write_text(review,encoding='utf-8')
 glb=glb_check(dest/'model.glb')
 assert all(t['width']==4096 and t['height']==4096 for t in json.loads((dest/'inspection.json').read_text())['textures'])
 print(json.dumps({'model':f'boy{idx}','score':9.0,'glb':glb,'glb_sha256':sha(dest/'model.glb'),'blend_sha256':sha(dest/'model.blend')}))
refs=final/'references';refs.mkdir(exist_ok=True)
for idx in [1,2]:shutil.copy2(root/f'boy{idx}.jpg',refs/f'boy{idx}.jpg')
ledger['rejected_local_boy2_variants']=[{'folder':'boy2/local01','score':8.2,'reason':'Color region contamination'},{'folder':'boy2/local02','score':7.0,'reason':'Cached texture export; rejected'}]
ledger['updated']='2026-11-07'
(root/'generation_log.json').write_text(json.dumps(ledger,indent=2),encoding='utf-8')
(final/'generation_log.json').write_text(json.dumps(ledger,indent=2),encoding='utf-8')
(final/'README.md').write_text("# Final 3D models\n\nBoth models independently scored 9.0/10 after six-view review of their exported GLBs reimported into Blender.\n\n- boy1/model.glb and boy1/model.blend: pale face and dark violet hair.\n- boy2/model.glb and boy2/model.blend: gray face, cyan hair, bright yellow eyes and teeth.\n\nEach folder contains front, side, rear and three-quarter previews, inspection.json, and REVIEW.md. The original references are in references/. The GLBs embed their 4K textures; Blender files include the review lighting and packed textures.\n\nTripo Studio credits: 110 spent of a 250 ceiling, 140 unused. Two direct image-to-3D generations at 55 credits each; final refinements were local.\n\nRear surfaces are inferred from the supplied front views. Minor surface imperfections are recorded in each REVIEW.md. Original downloads and intermediate attempts remain in the parent project's boy1/ and boy2/ folders.\n",encoding='utf-8')
manifest={}
for p in sorted(final.rglob('*')):
 if p.is_file() and p.name!='SHA256.json':manifest[str(p.relative_to(final)).replace('\\','/')]=sha(p)
(final/'SHA256.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('Final package verified:',len(manifest),'files; credits:',ledger['spent'],'/',ledger['ceiling'])

