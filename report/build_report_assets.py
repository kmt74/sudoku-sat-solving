"""Format data tables and LaTeX-native figures after analyze.py. No solver run.

Run: python analyze.py && python build_report_assets.py
"""
from pathlib import Path
from collections import Counter
import csv, json, math, statistics as st

ROOT=Path(__file__).resolve().parent
rows=[json.loads(s) for s in (ROOT/'data/all-results.jsonl').read_text(encoding='utf-8').splitlines()][1:]
methods=['sat-binary','sat-commander','sat-product','sat-sequential','cp-optimizer','cplex-mip','gurobi-mip','cp-sat']
names=['SAT binary','SAT commander','SAT product','SAT sequential','CP Optimizer','CPLEX MIP','Gurobi MIP','CP-SAT']
def stat(rs):
    good=[r for r in rs if r['status']=='SOLVED']
    return {'solved':len(good),'build':st.mean(r['build_time_s'] for r in rs),
     'median':st.median(r['total_time_s'] for r in good),
     'par2':st.mean(r['build_time_s']+(r['solve_time_s'] if r['status']=='SOLVED' else 120) for r in rs),
     'ram':st.median(r['peak_rss_bytes']/2**20 for r in rs),
     'maxram':max(r['peak_rss_bytes']/2**20 for r in rs)}
def rankfmt(value,values,format_string,reverse=False):
    unique=sorted(set(values),reverse=reverse)
    value_str=format(value,format_string)
    if value==unique[0]:return r'\best{'+value_str+'}'
    if len(unique)>1 and value==unique[1]:return r'\second{'+value_str+'}'
    return value_str
def amo(m,e):
    if e=='binary':k=math.ceil(math.log2(m));return k,m*k
    if e=='sequential':return m-1,3*m-4
    if e=='product':p=math.ceil(math.sqrt(m));q=math.ceil(m/p);return p+q,2*m+math.comb(p,2)+math.comb(q,2)
    if m<=3:return 0,math.comb(m,2)
    q=math.ceil(m/3);a,c=amo(q,e)
    return q+a,m+sum(math.comb(min(3,m-i),2) for i in range(0,m,3))+c
stats={m:stat([r for r in rows if r['method']==m]) for m in methods}
out=[]
for m,name in zip(methods,names):
    s=stats[m];vals=[]
    for key,fmt,reverse in [('solved','d',True),('build','.3f',False),('median','.4f',False),('par2','.3f',False),('ram','.2f',False)]:
        rendered=rankfmt(s[key],[stats[j][key] for j in methods],fmt,reverse)
        vals.append(rendered+('/270' if key=='solved' else ''))
    out.append(name+' & '+' & '.join(vals)+r' \\')
(ROOT/'tables/overall.tex').write_text('\n'.join(out)+'\n',encoding='utf-8')
size_stats={(n,m):stat([r for r in rows if r['size']==n and r['method']==m]) for n in [9,16,25] for m in methods}
out=[]
for m,name in zip(methods,names):
    cells=[]
    for n in [9,16,25]:
        s=size_stats[n,m]
        cells.append(rankfmt(s['par2'],[size_stats[n,k]['par2'] for k in methods],'.3f')+f' ({s["solved"]}/90)')
    out.append(name+' & '+' & '.join(cells)+r' \\')
(ROOT/'tables/by_size.tex').write_text('\n'.join(out)+'\n',encoding='utf-8')
hard={m:stat([r for r in rows if r['size']==25 and r['difficulty']=='hard' and r['method']==m]) for m in methods}
out=[]
for m,name in zip(methods,names):
    s=hard[m];cells=[]
    for key,fmt,reverse in [('solved','d',True),('median','.3f',False),('par2','.3f',False),('ram','.1f',False),('maxram','.1f',False)]:
        rendered=rankfmt(s[key],[hard[j][key] for j in methods],fmt,reverse)
        cells.append(rendered+('/30' if key=='solved' else ''))
    out.append(name+' & '+' & '.join(cells)+r' \\')
(ROOT/'tables/hard25.tex').write_text('\n'.join(out)+'\n',encoding='utf-8')
counts={n:{e:(n**3+4*n*n*amo(n,e)[0],4*n*n*(1+amo(n,e)[1])) for e in ['binary','commander','product','sequential']} for n in [9,16,25]}
out=[]
for e in ['binary','commander','product','sequential']:
    cells=[]
    for n in [9,16,25]:
        for idx in [0,1]:
            val=counts[n][e][idx]
            cell=rankfmt(val,[counts[n][t][idx] for t in counts[n]],',d')
            cells.append(cell)
    out.append(e.capitalize()+' & '+' & '.join(cells)+r' \\')
(ROOT/'tables/counts.tex').write_text('\n'.join(out)+'\n',encoding='utf-8')

# TikZ is used for the quantitative graphics to keep the same TeX font as body/table text.
# Heatmap colors derive from log-scaled PAR2-total values, analogous to the prior PDF figure.
group={(n,d,m):stat([r for r in rows if r['size']==n and r['difficulty']==d and r['method']==m])['par2']
       for n in [9,16,25] for d in ['easy','medium','hard'] for m in methods}
values=list(group.values());lo=min(map(math.log10,values));hi=max(map(math.log10,values))
lines=[r'\begin{tikzpicture}[x=1.22cm,y=.56cm]',
       r'\node[anchor=east,font=\scriptsize] at (0,8.25) {PAR2-total (s)};']
for i,(m,name) in enumerate(zip(methods,names)):
    y=7-i;lines.append(rf'\node[anchor=east,font=\scriptsize] at (-.12,{y+.5}) {{{name}}};')
    for j,(n,d) in enumerate((n,d) for n in [9,16,25] for d in ['easy','medium','hard']):
        val=group[n,d,m];shade=round(12+72*(math.log10(val)-lo)/(hi-lo))
        color='white' if shade>52 else 'black'
        lines.append(rf'\fill[reportblue!{shade}!white,draw=white] ({j},{y}) rectangle ({j+1},{y+1});')
        lines.append(rf'\node[text={color},font=\tiny] at ({j+.5},{y+.5}) {{{val:.3f} S}};' if False else
                     rf'\node[text={color},font=\tiny] at ({j+.5},{y+.5}) {{{val:.3f}}};')
for j,(n,d) in enumerate((n,d) for n in [9,16,25] for d in ['easy','medium','hard']):
    tier={'easy':'Dễ','medium':'Vừa','hard':'Khó'}[d]
    lines.append(rf'\node[font=\scriptsize,align=center] at ({j+.5},-.43) {{{n}$\times${n}\\{tier}}};')
lines.append(r'\node[anchor=west,font=\scriptsize] at (0,-1.15) {Màu đậm biểu thị PAR2-total lớn hơn; giá trị in trong từng ô là số giây.};')
lines.append(r'\end{tikzpicture}')
(ROOT/'figures/par2_heatmap.tex').write_text('\n'.join(lines)+'\n',encoding='utf-8')
colors=['reportblue','reportorange','reportgreen','reportpurple']
lines=[r'\begin{tikzpicture}',
       r'\begin{groupplot}[group style={group size=2 by 1,horizontal sep=1.1cm},',
       r'width=.44\linewidth,height=5.0cm,xtick={9,16,25},xmin=8,xmax=26,',
       r'xlabel={$N$},grid=major,scaled y ticks=false,',
       r'yticklabel style={/pgf/number format/fixed,/pgf/number format/precision=2},',
       r'title style={font=\small,align=center},',
       r'legend columns=4,',
       r'legend style={draw=none,fill=none,font=\footnotesize,column sep=10pt},',
       r'every axis plot/.append style={mark=*,line width=.85pt}]',
       r'\nextgroupplot[legend to name=satcostlegend,title={(a) Thời gian dựng trung bình (s)},ymin=0,ymax=.18,ytick={0,.05,.10,.15}]']
for m,col in zip(methods[:4],colors):
    coords=' '.join(f'({n},{size_stats[n,m]["build"]:.6f})' for n in [9,16,25])
    lines.append(rf'\addplot[color={col}] coordinates {{{coords}}};\addlegendentry{{{m[4:].capitalize()}}}')
lines.append(r'\nextgroupplot[title={(b) Trung vị đỉnh RSS (MiB)},ymin=0,ymax=95,ytick={0,20,40,60,80}]')
for m,col in zip(methods[:4],colors):
    coords=' '.join(f'({n},{size_stats[n,m]["ram"]:.5f})' for n in [9,16,25])
    lines.append(rf'\addplot[color={col}] coordinates {{{coords}}};')
lines.extend([r'\end{groupplot}',
              r'\node[anchor=north,inner sep=0pt] at ($(group c1r1.south)!0.5!(group c2r1.south)+(0,-1.05cm)$) {\pgfplotslegendfromname{satcostlegend}};',
              r'\end{tikzpicture}'])
(ROOT/'figures/sat_cost.tex').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Ranked tables and TeX-native plots updated.')

# Compact tables for the RQ-based discussion use the same raw observations.
from build_rq_assets import build as build_rq_assets
build_rq_assets()
