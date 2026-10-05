import json,os,re,requests,hashlib,concurrent.futures as F
from bs4 import BeautifulSoup
from urllib.parse import urlparse
root='/workspace/sites/topstanki-modern/dist';rs=json.load(open(root+'/data.json'));mp=json.load(open(root+'/assets-map.json'));extra=set()
for r in rs:
 s=BeautifulSoup(r['content'],'html.parser')
 for im in s.select('img'):
  u=im.get('data-wpfc-original-src') or im.get('src','')
  if '/uploads/' in u:
   if u not in mp:extra.add(u)
   im['src']=mp.get(u,u)
  for a in ['srcset','data-wpfc-original-srcset','onload','sizes']:im.attrs.pop(a,None)
  im['loading']='lazy'
 for bad in s.select('.wpcf7-contact-form-not-found'):bad.decompose()
 r['content']=str(s)
 for u in r['images']:
  if u.startswith('https://') and u not in mp:extra.add(u)
def dl(u):
 r=requests.get(u,timeout=40);r.raise_for_status();name=hashlib.sha256(u.encode()).hexdigest()[:16]+os.path.splitext(urlparse(u).path)[1];open(root+'/assets/'+name,'wb').write(r.content);return u,'/assets/'+name
with F.ThreadPoolExecutor(max_workers=10) as ex:
 for u,p in ex.map(dl,list(extra)):mp[u]=p
# Retain category memberships from original category pages.
for r in rs:
 if r['kind']=='category':
  for pr in rs:
   if pr['kind']=='product' and pr['url'] in r['content'] and r['title'] not in pr['categories']:pr['categories'].append(r['title'].split(' » ')[0])
for r in rs:
 for u,p in mp.items():r['content']=r['content'].replace(u,p)
 r['images']=[mp.get(u,u) for u in r['images']]
rs.sort(key=lambda r:r['path'])
json.dump(rs,open(root+'/data.json','w'),ensure_ascii=False)
json.dump(mp,open(root+'/assets-map.json','w'),ensure_ascii=False)
errors=[]
for r in rs:
 for im in r['images']:
  if im.startswith('/assets/') and not os.path.exists(root+im):errors.append(im)
print('Pages:',len(rs),'Products:',sum(r['kind']=='product' for r in rs),'Images:',len(mp),'Missing:',len(errors),'Products with prices:',sum(bool(r['price']) for r in rs if r['kind']=='product'))
print('Largest asset:',max(os.path.getsize(root+'/assets/'+x) for x in os.listdir(root+'/assets')))
