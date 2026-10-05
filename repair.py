import json,requests,concurrent.futures as F,hashlib,os
from bs4 import BeautifulSoup
from urllib.parse import urlparse
root='/workspace/sites/topstanki-modern/dist';records=json.load(open(root+'/data.json'));mapping=json.load(open(root+'/assets-map.json'));sess=requests.Session()
def repair(r):
 if r['kind']!='product':return r
 s=BeautifulSoup(sess.get(r['url'],timeout=45).text,'html.parser')
 price=s.select_one('.wd-single-price .price, .summary .price');r['price']=price.get_text(' ',strip=True) if price else ''
 r['categories']=[a.get_text(' ',strip=True) for a in s.select('.posted_in a')]
 parts=[]
 for selector in ['.woocommerce-product-details__short-description','.wd-single-attrs','.woocommerce-Tabs-panel']:
  for x in s.select(selector):
   for t in x.select('script,style,form,.wpcf7-contact-form-not-found'):t.decompose()
   parts.append(str(x))
 r['content']=''.join(parts) or r['content']
 gal=s.select_one('.wd-single-gallery') or s.select_one('.woocommerce-product-gallery')
 if gal:
  ims=[]
  for x in gal.select('img'):
   u=x.get('data-wpfc-original-src') or x.get('src','')
   if '/uploads/' in u:ims.append(u)
  if ims:r['images']=list(dict.fromkeys(ims))
 for u,p in mapping.items():r['content']=r['content'].replace(u,p)
 r['images']=[mapping.get(u,u) for u in r['images']]
 return r
out=[];fails=[]
with F.ThreadPoolExecutor(max_workers=12) as ex:
 fs={ex.submit(repair,r):r for r in records}
 for i,f in enumerate(F.as_completed(fs)):
  try:out.append(f.result())
  except Exception as e:out.append(fs[f]);fails.append(fs[f]['url'])
  if i%60==0:print('Rechecked',i,flush=True)
json.dump(out,open(root+'/data.json','w'),ensure_ascii=False)
print('DONE',len(fails),'failures',flush=True)
