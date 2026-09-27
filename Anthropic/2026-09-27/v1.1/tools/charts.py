"""Publication figures using existing ReportLab charts; PDFium rasterizes PNG.
No downloads, installation, network, or simulated values.
"""
import json,csv,math
from pathlib import Path
from reportlab.graphics.shapes import Drawing,String,Rect,Line
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics import renderSVG,renderPDF
from reportlab.lib.colors import HexColor,Color
import pypdfium2 as pdfium
from reportlab import rl_config
rl_config.invariant=1
ROOT=Path(__file__).resolve().parents[1];FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
T=json.loads((ROOT/'trend_data.json').read_text());S=json.loads((ROOT/'summary-data.json').read_text())
COLORS=['#134E4A','#D08A39','#9B5363','#698B99'];W,H=900,480
LABEL={'Overall':'Any core product','Claude.ai':'Claude.ai','API':'First-party API','Console':'Console','Claude Code':'Claude Code','Cowork':'Cowork','Government':'Government'}
def base(title,subtitle):
 d=Drawing(W,H);d.add(Rect(0,0,W,H,fillColor=HexColor('#FAFBF9'),strokeColor=None));d.add(String(38,H-42,title,fontName='Helvetica-Bold',fontSize=21,fillColor=HexColor('#173C38')));d.add(String(38,H-67,subtitle,fontName='Helvetica',fontSize=10.5,fillColor=HexColor('#52635D')))
 d.add(String(38,22,'Source: status.claude.com | Frozen 2026-09-27 16:10:43 UTC | Reviewed v1.1',fontName='Helvetica',fontSize=9,fillColor=HexColor('#63726C')));return d

def save(d,name,head,data):
 renderSVG.drawToFile(d,str(FIG/f'{name}.svg'));renderPDF.drawToFile(d,str(FIG/f'{name}.pdf'))
 doc=pdfium.PdfDocument(str(FIG/f'{name}.pdf'));page=doc[0];img=page.render(scale=2).to_pil();img.save(FIG/f'{name}.png');page.close();doc.close()
 with (FIG/f'{name}.csv').open('w',newline='',encoding='utf-8-sig') as f:w=csv.writer(f);w.writerow(head);w.writerows(data)

def legend(d,labels):
 x=80
 for j,lab in enumerate(labels):
  d.add(Rect(x,58,12,8,fillColor=HexColor(COLORS[j]),strokeColor=None));d.add(String(x+18,56,lab,fontName='Helvetica',fontSize=10,fillColor=HexColor('#334840')));x+=250 if len(labels)<4 else 205

def bars(name,title,subtitle,cats,values,labels,axis_min=0,axis_max=None,step=None):
 d=base(title,subtitle)
 count_axis=axis_max is None
 if count_axis:
  target=max(max(v) for v in values)/5;unit=10**math.floor(math.log10(max(target,1)));tick=next(z*unit for z in [1,2,5,10] if z*unit>=target);axis_max=math.ceil(max(max(v) for v in values)*1.1/tick)*tick;step=tick
 c=VerticalBarChart();c.x=78;c.y=108;c.width=780;c.height=265;c.data=values;c.categoryAxis.categoryNames=cats;c.categoryAxis.labels.fontName='Helvetica';c.categoryAxis.labels.fontSize=10;c.valueAxis.labels.fontSize=9;c.valueAxis.valueMin=axis_min;c.valueAxis.valueMax=axis_max if axis_max is not None else math.ceil(max(max(v) for v in values)*1.2);c.valueAxis.valueStep=step if step else max(1,round((c.valueAxis.valueMax-axis_min)/5,1));c.valueAxis.visibleGrid=True;c.valueAxis.gridStrokeColor=HexColor('#DCE4DD');c.categoryAxis.strokeColor=HexColor('#AEBDB5');c.valueAxis.strokeColor=HexColor('#AEBDB5');c.bars.strokeColor=None;c.groupSpacing=20;c.barSpacing=3
 for j in range(len(values)):c.bars[j].fillColor=HexColor(COLORS[j])
 c.barLabels.fontSize=8;c.barLabelFormat='%.0f' if count_axis else '%.2f';d.add(c);legend(d,labels)
 save(d,name,['category']+labels,[[cat]+[round(v[k],6) for v in values] for k,cat in enumerate(cats)])

matched=[r for r in T['matched_windows'] if r['group']=='Overall'];bars('01_same_period_counts','Reported incidents increased across matching periods','Jan 1 to Sep 27 16:10:43 UTC each year; any core product; publication count', [str(r['year']) for r in matched],[[r['publication_count'] for r in matched]],['Incident announcements'])
annual=[r for r in T['annual'] if r['group']=='Overall'];vals=[[100*r[k] for r in annual] for k in ['availability_full','availability_full_partial','availability_all']];lo=max(0,5*math.floor(min(min(x) for x in vals)/5)-5)
bars('02_annual_availability','Three definitions give different availability estimates','Known assessed intervals + labelled time proxies; 2023 and 2026 are partial years; truncated % axis',[str(r['year'])+('*' if r['year'] in [2023,2026] else '') for r in annual],vals,['F only','F + P','F + P + D'],lo,100,5)
y26=[r for r in T['annual'] if r['year']==2026];vals=[[100*r[k] for r in y26] for k in ['availability_full','availability_full_partial','availability_all']];lo=max(0,5*math.floor(min(min(x) for x in vals)/5)-5)
bars('03_product_availability','2026 availability depends on product and impact definition','Government / Cowork have shorter windows; Overall means any product affected; truncated % axis',[LABEL[r['group']] for r in y26],vals,['F only','F + P','F + P + D'],lo,100,5)
scenarios=['reviewed','exclude_suspension','unknown_as_full'];groups=['Overall','API','Claude.ai','Claude Code'];vals=[[100*next(r['availability_all'] for r in S['sensitivity_2026'] if r['series']==sc and r['group']==g) for g in groups] for sc in scenarios];lo=max(0,5*math.floor(min(min(x) for x in vals)/5)-5)
bars('04_sensitivity','Model suspension and unknown grades affect the estimate','F + P + D; scenario comparison, NOT confidence bounds; truncated % axis',[LABEL[g] for g in groups],vals,['Reviewed incl. suspension','Exclude specified suspension','Located unknowns treated as F'],lo,100,5)
monthly=[r for r in T['monthly'] if r['group']=='Overall' and r['year']>=2024];d=base('Monthly known-impact availability varies sharply','Any core product; all three definitions; retrospective dates retained; partial Sep 2026')
c=HorizontalLineChart();c.x=78;c.y=112;c.width=775;c.height=255;c.data=[[100*r[k] for r in monthly] for k in ['availability_full','availability_full_partial','availability_all']];c.categoryAxis.categoryNames=[r['month'] if i%3==0 else '' for i,r in enumerate(monthly)];c.categoryAxis.labels.angle=35;c.categoryAxis.labels.fontSize=9;c.categoryAxis.labels.boxAnchor='ne';c.valueAxis.valueMin=max(0,10*math.floor(min(min(v) for v in c.data)/10)-10);c.valueAxis.valueMax=100;c.valueAxis.valueStep=10;c.valueAxis.visibleGrid=True;c.valueAxis.gridStrokeColor=HexColor('#DCE4DD');c.valueAxis.labels.fontSize=9
for j in range(3):c.lines[j].strokeColor=HexColor(COLORS[j]);c.lines[j].strokeWidth=2.3
c.categoryAxis.strokeColor=c.valueAxis.strokeColor=HexColor('#AEBDB5');d.add(c);legend(d,['F only','F + P','F + P + D']);save(d,'05_monthly_availability',['month','F_pct','FP_pct','FPD_pct'],[[r['month'],100*r['availability_full'],100*r['availability_full_partial'],100*r['availability_all']] for r in monthly])
gc=S['grade_counts'];bars('06_reviewed_grades','All records reviewed; unsupported grades remain unknown','916 incidents, excluding 4 maintenance records; unknown is missing evidence, not a fourth severity',['Full','Partial','Degraded','Unknown'],[[gc.get(k,0) for k in ['full_outage','partial_outage','degraded_performance','unknown']]],['Reviewed incident count'])
print('Created 6 figures in SVG, PNG, PDF, plus source CSV.')
