"""Offline publication plots using bundled ReportLab and PDFium; no installations."""
import json,csv
from pathlib import Path
from reportlab.graphics.shapes import Drawing,Rect,String,Line,Circle
from reportlab.graphics import renderSVG,renderPDF
from reportlab.lib.colors import HexColor
from reportlab import rl_config
import pypdfium2 as pdfium
rl_config.invariant=1
ROOT=Path(__file__).resolve().parents[1];FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
T=json.loads((ROOT/'trend_data.json').read_text());S=json.loads((ROOT/'summary-data.json').read_text());A={(r['group'],r['year']):r for r in T['annual']}
LABEL={'Overall':'Overall: any included application','API':'DeepSeek API (historical aggregate)','Chat':'Chat service (Web / App)','Upload':'File upload service','Search':'Search service'}
COLORS=['#142e42','#2877ba','#d87d24','#2b8a73','#9257a1']
def txt(d,x,y,s,size=11,color='#30495c',**kw):d.add(String(x,y,s,fontName='Helvetica',fontSize=size,fillColor=HexColor(color),**kw))
def base(title,subtitle):
 d=Drawing(1000,600);d.add(Rect(0,0,1000,600,fillColor=HexColor('#fbfcfe'),strokeColor=None));txt(d,42,560,title,22);txt(d,42,536,subtitle,11);txt(d,42,22,'Source: status.deepseek.com | Frozen: 2026-09-27 19:36:20 UTC | Public-incident time estimates, not request success rates',9);return d
def save(d,name,rows):
 renderSVG.drawToFile(d,str(FIG/f'{name}.svg'));renderPDF.drawToFile(d,str(FIG/f'{name}.pdf'))
 doc=pdfium.PdfDocument(str(FIG/f'{name}.pdf'));page=doc[0];page.render(scale=1.6).to_pil().save(FIG/f'{name}.png');page.close();doc.close()
 with (FIG/f'{name}.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
d=base('DeepSeek: annual availability by application','One metric for every series: F + P + D | Application colors | Truncated vertical axis: 90-100%')
x=lambda y:100+(y-2024)*390;y=lambda v:235+(v-90)*26
for v in [90,92,94,96,98,100]:d.add(Line(100,y(v),880,y(v),strokeColor=HexColor('#dce4eb')));txt(d,85,y(v)-4,f'{v}%',10,textAnchor='end')
for yr in [2024,2025,2026]:txt(d,x(yr),212,str(yr)+('*' if yr!=2025 else ''),12,textAnchor='middle')
for j,g in enumerate(LABEL):
 pts=[(yr,100*A[g,yr]['availability_all']) for yr in [2024,2025,2026] if (g,yr) in A];color=HexColor(COLORS[j])
 for (ya,va),(yb,vb) in zip(pts,pts[1:]):
  if yb==ya+1:d.add(Line(x(ya),y(va),x(yb),y(vb),strokeColor=color,strokeWidth=3.2 if g=='Overall' else 1.9,strokeDashArray=[6,3]))
 for yr,v in pts:d.add(Circle(x(yr),y(v),5 if g=='Overall' else 3.6,fillColor=color if yr==2025 else HexColor('#fbfcfe'),strokeColor=color,strokeWidth=1.7))
 lx=45+(j%2)*490;ly=174-(j//2)*27;d.add(Line(lx,ly,lx+22,ly,strokeColor=color,strokeWidth=3));txt(d,lx+31,ly-4,LABEL[g]+f"  ({pts[-1][1]:.4f}%)",10,COLORS[j])
txt(d,42,78,'* 2024 starts Feb 1; 2026 ends at the frozen cutoff. Hollow dots = partial year. No extrapolation.',10)
txt(d,42,58,'File upload and Search start Jul 22, 2026 (10:19:38 UTC); earlier years are missing, not 100%.',10)
save(d,'annual-availability',T['annual'])
d=base('2025: two long status episodes dominate the estimate','F + P + D | Same full-year denominator | Exclusion is a sensitivity scenario, not a corrected truth')
x=lambda v:245+(v-90)*61
for v in range(90,101,2):d.add(Line(x(v),165,x(v),485,strokeColor=HexColor('#dce4eb')));txt(d,x(v),143,f'{v}%',10,textAnchor='middle')
out=[]
for j,g in enumerate(['Overall','API','Chat']):
 yy=442-j*108;txt(d,42,yy+3,LABEL[g].split(' (')[0],11)
 for k,r in enumerate([A[g,2025],next(r for r in S['sensitivity_exclude_two_long_2025'] if r['group']==g)]):
  v=r['availability_all']*100;cy=yy-k*31;color=['#2877ba','#2b8a73'][k];d.add(Rect(x(90),cy-8,x(v)-x(90),20,fillColor=HexColor(color),strokeColor=None));txt(d,x(v)+8,cy-3,f'{v:.4f}%',11);out.append({'group':g,'scenario':['All disclosed episodes','Exclude two long episodes'][k],'availability_pct':v,'impact_hours':r['all_hours']})
txt(d,42,100,'Blue: all disclosed episodes. Green: exclude incident IDs 2328579188430287 and 2258210444252287.',10)
txt(d,42,77,'Horizontal axis is truncated to 90-100%. Long status intervals do not mean every request failed throughout.',10)
txt(d,42,55,'Other overlapping incidents remain included; intervals are re-unioned after exclusion.',10)
save(d,'sensitivity-2025',out)
print('Created 2 figures as SVG / PNG / PDF with source CSV.')
