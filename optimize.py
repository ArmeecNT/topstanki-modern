from PIL import Image
import os,json,concurrent.futures as F
root='/workspace/sites/topstanki-modern/dist';mapping={}
def convert(f):
 if not f.endswith(('.png','.jpg')):return
 p=root+'/assets/'+f; im=Image.open(p);target=os.path.splitext(p)[0]+'.webp';im.save(target,'WEBP',quality=90,method=4)
 if os.path.getsize(target)<os.path.getsize(p):os.remove(p);return '/assets/'+f,'/assets/'+os.path.basename(target)
 os.remove(target)
with F.ThreadPoolExecutor(max_workers=6) as ex:
 for r in ex.map(convert,os.listdir(root+'/assets')):
  if r:mapping[r[0]]=r[1]
for f in ['data.json','assets-map.json']:
 s=open(root+'/'+f).read()
 for a,b in mapping.items():s=s.replace(a,b)
 open(root+'/'+f,'w').write(s)
print('Optimized',len(mapping),'images')
