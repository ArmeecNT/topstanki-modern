import requests,concurrent.futures as F,json,os,re,time,hashlib,xml.etree.ElementTree as E
from bs4 import BeautifulSoup
from urllib.parse import urlparse
ROOT='/workspace/sites/topstanki-modern/dist';os.makedirs(ROOT+'/assets',exist_ok=True)
S=requests.Session()
def get(u):
 for i in range(3):
  try:
   r=S.get(u,timeout=40);r.raise_for_status();return r
  except Exception:
   if i==2: raise
ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
def sitemap(u):
 root=E.fromstring(get(u).content);return [x.text for x in root.findall('s:url/s:loc',ns)]
maps=['post','page','product1','product2','category','product_cat']
urls=[]
with F.ThreadPoolExecutor(max_workers=6) as ex:
 for name,ls in zip(maps,ex.map(sitemap,['https://topstanki.ru/'+m.replace('product1','product').replace('product2','product')+'-sitemap'+('1' if m=='product1' else '2' if m=='product2' else '')+'.xml' for m in maps])):
  urls += ls
urls=list(dict.fromkeys(urls));print('Pages',len(urls),flush=True)
records=[];failed=[]
def parse(u):
 s=BeautifulSoup(get(u).text,'html.parser');title=s.select_one('h1');title=title.get_text(' ',strip=True) if title else s.title.get_text().split('—')[0]
 isprod=bool(s.select_one('.single-product')) or '/product/' in u
 body=s.select_one('.site-content') or s.select_one('main') or s.body
 if body is None: return None
 for t in body.select('script,style,iframe,form,.wd-products-nav,.related,.upsells,.woocommerce-notices-wrapper,.wd-sticky-btn,.woocommerce-tabs .tabs,.wd-social-icons,.wd-sizeguide,.wd-wishlist-btn,.wd-compare-btn,.wd-buttons,.wd-more-desc-btn,.wd-nav-product-cat,.wd-shop-tools,.woocommerce-breadcrumb,.wd-single-breadcrumbs,.wd-product-brands,.wd-single-reviews,.comments-area'):
  t.decompose()
 for t in body.find_all(True):
  for a in list(t.attrs):
   if a.startswith('on'): del t[a]
 for im in body.select('img'):
  im['src']=im.get('data-wpfc-original-src') or im.get('data-src') or im.get('src',''); im['loading']='lazy'
  for a in ['srcset','data-wpfc-original-srcset','sizes','style','onload']:im.attrs.pop(a,None)
 images=list(dict.fromkeys(im.get('src') for im in body.select('img') if '/uploads/' in im.get('src','')))
 cats=[a.get_text(' ',strip=True) for a in s.select('.posted_in a')]
 price=s.select_one('.summary .price');price=price.get_text(' ',strip=True) if price else ''
 # Product pages retain all description, attributes, gallery and supporting content.
 if isprod:
  parts=[]
  for selector in ['.woocommerce-product-details__short-description','#tab-description','#tab-additional_information']:
   t=body.select_one(selector)
   if t:parts.append(str(t))
  content=''.join(parts) or str(body)
 else:content=str(body)
 return {'url':u,'path':urlparse(u).path,'title':title,'kind':'product' if isprod else 'category' if '/product-category/' in u else 'page' if u in pageurls else 'article','price':price,'categories':cats,'images':images,'content':content}
pageurls=set()
try:pageurls=set(sitemap('https://topstanki.ru/page-sitemap.xml'))
except:pass
with F.ThreadPoolExecutor(max_workers=12) as ex:
 futures={ex.submit(parse,u):u for u in urls if u!='https://topstanki.ru/shop/'}
 for idx,f in enumerate(F.as_completed(futures)):
  try:
   r=f.result()
   if r:records.append(r)
  except Exception as e:failed.append({'url':futures[f],'error':str(e)})
  if idx%30==0:print('Imported',idx+1,flush=True)
json.dump(records,open(ROOT+'/data.json','w'),ensure_ascii=False)
json.dump(failed,open(ROOT+'/import-failures.json','w'),ensure_ascii=False)
print('Content complete',len(records),'failed',len(failed),flush=True)
assets=list(dict.fromkeys(im for r in records for im in r['images']))
# Also preserve homepage editorial images and company logo.
s=BeautifulSoup(open('/workspace/scratch/43eddf79e8c6/original.html').read(),'html.parser')
for im in s.select('img'):
 u=im.get('data-wpfc-original-src') or im.get('src','')
 if '/uploads/' in u:assets.append(u)
assets=list(dict.fromkeys(assets));mapping={};af=[]
def dl(u):
 name=hashlib.sha256(u.encode()).hexdigest()[:16]+os.path.splitext(urlparse(u).path)[1];r=get(u);open(ROOT+'/assets/'+name,'wb').write(r.content);return u,'/assets/'+name
with F.ThreadPoolExecutor(max_workers=12) as ex:
 fs={ex.submit(dl,u):u for u in assets}
 for idx,f in enumerate(F.as_completed(fs)):
  try:u,p=f.result();mapping[u]=p
  except Exception as e:af.append(fs[f])
  if idx%100==0:print('Images',idx+1,'/',len(assets),flush=True)
for r in records:
 r['images']=[mapping.get(u,u) for u in r['images']]
 for u,p in mapping.items():r['content']=r['content'].replace(u,p)
json.dump(records,open(ROOT+'/data.json','w'),ensure_ascii=False)
json.dump(mapping,open(ROOT+'/assets-map.json','w'),ensure_ascii=False)
json.dump({'pages':len(records),'pageFailures':failed,'images':len(mapping),'imageFailures':af},open(ROOT+'/import-report.json','w'),ensure_ascii=False)
print('DONE',len(records),len(mapping),'image failures',len(af),flush=True)
