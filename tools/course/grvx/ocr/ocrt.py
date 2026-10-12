import sys,os,json,subprocess
sys.path.insert(0,os.path.expanduser('~/mnt/quest-log/tools/course/grvx'))
from PIL import Image,ImageOps,ImageFilter
import importlib.util
def hb(im):
    W,H=im.size
    band=im.crop((0,0,int(W*.5),int(H*.2))).convert('L')
    sc=2 if W<1500 else 1
    if sc>1:band=band.resize((band.size[0]*sc,band.size[1]*sc))
    f=f'/tmp/hb_{os.getpid()}.png';band.save(f)
    t=subprocess.run(['tesseract',f,'-','--psm','6','tsv'],capture_output=True,text=True).stdout
    for ln in t.split('\n')[1:]:
        c=ln.split('\t')
        if len(c)>=12 and c[11].strip().lower().startswith('section') and int(c[10] if c[10].lstrip('-').isdigit() else 0)>30:
            return int((int(c[7])+int(c[9]))/sc)+6
    return int(H*.095)
def ocr(path,psm=3,scale=None):
    im=Image.open(path).convert('RGB');H=im.size[1]
    y=hb(im)
    if not .03*H<=y<=.2*H:y=int(H*.095)
    im=im.crop((0,y,im.size[0],H))
    sc=scale or max(2,round(2600/im.size[0]))
    im=im.resize((im.size[0]*sc,im.size[1]*sc),Image.LANCZOS).convert('L')
    im=ImageOps.autocontrast(im,cutoff=1)
    f=f'/tmp/o_{os.getpid()}.png';im.save(f)
    return subprocess.run(['tesseract',f,'-','--psm',str(psm),'-l','eng'],capture_output=True,text=True).stdout
if __name__=='__main__':
    print(ocr(sys.argv[1],int(sys.argv[2])))
