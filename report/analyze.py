"""Recreate report tables/figures from the bundled observations; no solver rerun.
Python >=3.10, matplotlib. Run: python analyze.py
"""
from pathlib import Path
import csv, json, math, statistics as st
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np

ROOT = Path(__file__).resolve().parent
rows = [json.loads(s) for s in (ROOT/'data/all-results.jsonl').read_text().splitlines()]
meta, rows = rows[0], rows[1:]
manifest = list(csv.DictReader((ROOT/'data/manifest.csv').open(encoding='utf-8-sig')))
methods = ['sat-binary','sat-commander','sat-product','sat-sequential','cp-optimizer','cplex-mip','gurobi-mip','cp-sat']
names = ['SAT binary','SAT commander','SAT product','SAT sequential','CP Optimizer','CPLEX MIP','Gurobi MIP','CP-SAT']
labels = dict(zip(methods,names))
sizes = [9,16,25]
diffs = ['easy','medium','hard']
vn = dict(easy='Dễ',medium='Vừa',hard='Khó')
assert len(rows)==2160 and len(manifest)==90
assert len({(r['puzzle_id'],r['method'],r['repeat']) for r in rows})==2160
assert len({r['source_root'] for r in manifest})==90
assert Counter(r['status'] for r in rows)=={'SOLVED':2120,'TIMEOUT':40}
def amo_counts(m,e):
    if m<2:return 0,0
    if e=='binary':
        k=(m-1).bit_length();return k,m*k
    if e=='sequential':return m-1,3*m-4
    if e=='product':
        p=math.isqrt(m)+(math.isqrt(m)**2<m);q=(m+p-1)//p
        return p+q,2*m+math.comb(p,2)+math.comb(q,2)
    if m<=3:return 0,math.comb(m,2)
    q=(m+2)//3;a,c=amo_counts(q,e)
    return q+a,m+sum(math.comb(min(3,m-i),2) for i in range(0,m,3))+c
for r in rows:
    n,g=r['size'],r['clues']
    if r['method'].startswith('sat-'):
        a,c=amo_counts(n,r['method'][4:]);v,k=n**3+4*n*n*a,4*n*n*(1+c)+g
    elif r['method'] in ('cplex-mip','gurobi-mip'):v,k=n**3,4*n*n+g
    else:v,k=n*n,3*n+g
    assert (r['model_variables'],r['model_constraints'])==(v,k)
for p in manifest:
    sub=[r for r in rows if r['puzzle_id']==p['id']]
    assert {(r['method'],r['repeat']) for r in sub}=={(m,k) for m in methods for k in (1,2,3)}
    grid=json.loads((ROOT/'data/puzzles'/p['output_path']).read_text())['grid']
    n=len(grid); b=math.isqrt(n); target=set(range(1,n+1))
    for r in sub:
        assert r['size']==n and r['hardness_level']==p['hardness_level']
        assert abs(r['total_time_s']-r['build_time_s']-r['solve_time_s'])<1e-8
        assert r['peak_rss_bytes']>0
        if r['status']=='SOLVED':
            s=r['solution']; assert r['solution_valid'] is True
            assert len(s)==n and all(len(row)==n and set(row)==target for row in s)
            assert all({s[i][j] for i in range(n)}==target for j in range(n))
            assert all({s[i][j] for i in range(a,a+b) for j in range(c,c+b)}==target for a in range(0,n,b) for c in range(0,n,b))
            assert all(grid[i][j]==0 or grid[i][j]==s[i][j] for i in range(n) for j in range(n))

def par(r,k=2):
    return r['build_time_s']+(r['solve_time_s'] if r['status']=='SOLVED' else k*60)
def stats(rs):
    ss=[r for r in rs if r['status']=='SOLVED']
    return dict(attempts=len(rs),solved=len(ss),par2=st.mean(map(par,rs)),
      par_solve=st.mean(r['solve_time_s'] if r['status']=='SOLVED' else 120 for r in rs),
      median_total=st.median(r['total_time_s'] for r in ss),
      mean_build=st.mean(r['build_time_s'] for r in rs),
      median_ram=st.median(r['peak_rss_bytes']/2**20 for r in rs),
      max_ram=max(r['peak_rss_bytes']/2**20 for r in rs),
      median_wall=st.median(r['attempt_wall_s'] for r in ss),
      median_overhead=st.median(r['attempt_wall_s']-r['total_time_s'] for r in rs),
      par1=st.mean(par(r,1) for r in rs),par10=st.mean(par(r,10) for r in rs))
allstats={m:stats([r for r in rows if r['method']==m]) for m in methods}
groupstats={(n,d,m):stats([r for r in rows if (r['size'],r['difficulty'],r['method'])==(n,d,m)]) for n in sizes for d in diffs for m in methods}
def write_table(name,lines):
    (ROOT/'tables'/name).write_text('\n'.join(lines)+'\n',encoding='utf-8')
write_table('overall.tex',[f"{labels[m]} & {s['solved']}/270 & {s['mean_build']:.3f} & {s['median_total']:.3f} & {s['par2']:.3f} & {s['median_ram']:.1f} \\\\" for m,s in allstats.items()])
write_table('by_size.tex',[labels[m]+' & '+' & '.join(f"{(s:=stats([r for r in rows if r['method']==m and r['size']==n]))['par2']:.3f} ({s['solved']}/90)" for n in sizes)+r' \\' for m in methods])
write_table('hard25.tex',[f"{labels[m]} & {s['solved']}/30 & {s['median_total']:.3f} & {s['par2']:.3f} & {s['median_ram']:.1f} & {s['max_ram']:.1f} \\\\" for m in methods for s in [groupstats[25,'hard',m]]])
data_lines=[]
for n in sizes:
    for d in diffs:
        sub=[p for p in manifest if int(p['size'])==n and p['difficulty']==d]
        counts=Counter(p['hardness_level'] for p in sub)
        order=['Val','ValBS','ValDS','ValChan','Bnd','BndBS','BndDS','BndChan','Dom','DomBS','DomDS','UNSOLVED']
        description=', '.join(f'{k}: {counts[k]}' for k in order if k in counts)
        g=[int(p['clues']) for p in sub]
        data_lines.append(f'{n} & {vn[d]} & {min(g)}--{max(g)} & {description} \\\\')
write_table('dataset.tex',data_lines)

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(figsize=(9.2,4.05))
matrix=np.array([[groupstats[n,d,m]['par2'] for n in sizes for d in diffs] for m in methods])
im=ax.imshow(matrix,norm=LogNorm(vmin=matrix.min(),vmax=matrix.max()),cmap='YlGnBu',aspect='auto')
ax.set_yticks(range(8),names)
ax.set_xticks(range(9),[f'{n}×{n}\n{vn[d]}' for n in sizes for d in diffs])
for i in range(8):
    for j in range(9):
        v=matrix[i,j]; ax.text(j,i,f'{v:.3f}' if v<1 else f'{v:.2f}',ha='center',va='center',fontsize=8,color='white' if v>3 else 'black')
fig.colorbar(im,ax=ax,label='PAR2-total (s), thang log',pad=.02)
fig.tight_layout();fig.savefig(ROOT/'figures/par2_heatmap.pdf');plt.close(fig)

fig,axs=plt.subplots(1,2,figsize=(9.2,3.0))
colors=['#27647b','#d78332','#3b8a67','#9c5d86']
for m,c in zip(methods[:4],colors):
    ss=[stats([r for r in rows if r['method']==m and r['size']==n]) for n in sizes]
    axs[0].plot(sizes,[s['mean_build'] for s in ss],marker='o',color=c,label=labels[m][4:])
    axs[1].plot(sizes,[s['median_ram'] for s in ss],marker='o',color=c)
for ax in axs:
    ax.set_xticks(sizes);ax.set_xlabel('Kích thước N');ax.grid(alpha=.18)
axs[0].set_ylabel('Thời gian dựng trung bình (s)');axs[0].legend(frameon=False,fontsize=8)
axs[1].set_ylabel('Trung vị đỉnh RSS (MiB)')
fig.tight_layout();fig.savefig(ROOT/'figures/sat_cost.pdf');plt.close(fig)

with (ROOT/'data/recomputed-summary.csv').open('w',encoding='utf-8',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=['size','difficulty','method',*next(iter(allstats.values())).keys()]);writer.writeheader()
    for (n,d,m),s in groupstats.items():writer.writerow(dict(size=n,difficulty=d,method=m,**s))
(ROOT/'data/analysis-checks.json').write_text(json.dumps(dict(validated_solutions=2120,total=2160,unique_puzzles=90,distinct_roots=90,overall=allstats),indent=2),encoding='utf-8')
print(json.dumps(allstats,indent=2))
print('Dataset:\n'+'\n'.join(data_lines))
print('SAT mean PAR2-total:',st.mean(allstats[m]['par2'] for m in methods[:4]))
print('25 hard:\n',json.dumps({m:groupstats[25,'hard',m] for m in methods},indent=2))
