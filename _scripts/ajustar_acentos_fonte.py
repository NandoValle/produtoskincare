import sys
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
src,dst,flavor=sys.argv[1],sys.argv[2],(sys.argv[3] if len(sys.argv)>3 else None)
SCALE=float(sys.argv[4]) if len(sys.argv)>4 else 0.66; DROP=int(sys.argv[5]) if len(sys.argv)>5 else 22
t=TTFont(src); g=t['glyf']; cm=t.getBestCmap(); n=0
for ch in 'àáâèéêìíîòóôùúûý':
    name=cm.get(ord(ch))
    if not name: continue
    gl=g[name]
    if gl.isComposite() or gl.numberOfContours<2: continue
    co=gl.coordinates; ends=gl.endPtsOfContours; start=0; changed=False
    pts=list(co)
    for e in ends:
        ys=[pts[i][1] for i in range(start,e+1)]
        if min(ys)>=440:  # contorno do acento
            y0=min(ys)
            for i in range(start,e+1):
                x,y=pts[i]; pts[i]=(x, round(y0-DROP+(y-y0)*SCALE))
            changed=True
        start=e+1
    if changed:
        gl.coordinates=GlyphCoordinates(pts); gl.recalcBounds(g); n+=1
for rec in t['name'].names:
    if rec.nameID in (1,4,16) :
        s=rec.toUnicode()
        if 'PS' not in s: rec.string=s.replace('Cormorant Garamond','Cormorant Garamond PS')
    if rec.nameID==5: rec.string=rec.toUnicode()+'; acentos de minúsculas rebaixados para produtoskincare.com.br'
if flavor: t.flavor=flavor
t.save(dst); print(dst,n,'glifos')
