"""Recompute compact RQ tables and the selected-method heatmap from raw runs.

No solver run and no PDF generation. Run with standard-library Python.
"""
from pathlib import Path
import json
import math
import statistics as st
import csv
from collections import Counter

ROOT = Path(__file__).resolve().parent
SAT = ['sat-binary', 'sat-commander', 'sat-product', 'sat-sequential']
OTHER = ['cp-optimizer', 'cplex-mip', 'gurobi-mip', 'cp-sat']
NAMES = {'sat-binary': 'Binary', 'sat-commander': 'Commander',
         'sat-product': 'Product', 'sat-sequential': 'Sequential',
         'cp-optimizer': 'CP Optimizer', 'cplex-mip': 'CPLEX MIP',
         'gurobi-mip': 'Gurobi MIP', 'cp-sat': 'CP-SAT'}


def summarize(rs):
    good = [r for r in rs if r['status'] == 'SOLVED']
    assert rs and all(r['status'] in ('SOLVED', 'TIMEOUT') for r in rs)
    return dict(n=len(rs), solved=len(good), rate=100*len(good)/len(rs),
                build=st.mean(r['build_time_s'] for r in rs),
                median=st.median(r['total_time_s'] for r in good),
                ram=st.median(r['peak_rss_bytes']/2**20 for r in rs),
                **{f'par{k}': st.mean(r['build_time_s'] +
                    (r['solve_time_s'] if r['status'] == 'SOLVED' else k*60)
                    for r in rs) for k in (1, 2, 10)})


def ranked(value, values, fmt, reverse=False):
    levels = sorted(set(values), reverse=reverse)
    rendered = format(value, fmt)
    if value == levels[0]:
        return r'\best{' + rendered + '}'
    if len(levels) > 1 and value == levels[1]:
        return r'\second{' + rendered + '}'
    return rendered


def amo(m, kind):
    if kind == 'sat-binary':
        k = math.ceil(math.log2(m)); return k, m*k
    if kind == 'sat-sequential': return m-1, 3*m-4
    if kind == 'sat-product':
        p = math.ceil(math.sqrt(m)); q = math.ceil(m/p)
        return p+q, 2*m+math.comb(p, 2)+math.comb(q, 2)
    if m <= 3: return 0, math.comb(m, 2)
    q = math.ceil(m/3); a, c = amo(q, kind)
    return q+a, m+sum(math.comb(min(3, m-i), 2) for i in range(0, m, 3))+c


def write_rows(name, lines):
    (ROOT/'tables'/name).write_text('\n'.join(lines)+'\n', encoding='utf-8')


def build():
    raw = [json.loads(line) for line in (ROOT/'data/all-results.jsonl').read_text(encoding='utf-8').splitlines()]
    rows = raw[1:]
    assert len(rows) == 2160
    overall = {m: summarize([r for r in rows if r['method'] == m]) for m in SAT+OTHER}
    by_size = {(n, m): summarize([r for r in rows if r['method'] == m and r['size'] == n])
               for n in (9, 16, 25) for m in SAT+OTHER}
    hard = {m: summarize([r for r in rows if r['method'] == m and r['size'] == 25 and r['difficulty'] == 'hard'])
            for m in SAT+OTHER}
    # Each row has an explicit STT and every number is derived from the same raw runs.
    lines = []
    for i, m in enumerate(SAT, 1):
        cells = [str(i), NAMES[m]]
        for key, fmt, rev in [('solved', 'd', True), ('build', '.3f', False),
                              ('median', '.4f', False), ('par2', '.3f', False), ('ram', '.2f', False)]:
            v = ranked(overall[m][key], [overall[k][key] for k in SAT], fmt, rev)
            cells.append(v+('/270' if key == 'solved' else ''))
        lines.append(' & '.join(cells)+r' \\')
    write_rows('rq1_sat.tex', lines)

    average = {f'par{k}': st.mean(overall[m][f'par{k}'] for m in SAT) for k in (1, 2, 10)}
    average['rate'] = st.mean(overall[m]['rate'] for m in SAT)
    comparison = [('SATmean', average)] + [(NAMES[m], overall[m]) for m in OTHER]
    lines = []
    for i, (name, values) in enumerate(comparison, 1):
        rate = ranked(values['rate'], [v['rate'] for _, v in comparison], '.2f', True)+r'\%'
        score = ranked(values['par2'], [v['par2'] for _, v in comparison], '.3f')
        lines.append(f'{i} & {name} & {rate} & {score}'+r' \\')
    write_rows('rq2_sat_mean.tex', lines)

    best = min(SAT, key=lambda m: overall[m]['par2'])
    selected = [best, 'cp-sat', 'cplex-mip', 'gurobi-mip', 'cp-optimizer']
    lines = []
    for i, n in enumerate((9, 16, 25), 1):
        cells = [str(i), str(n)]
        cells += [ranked(by_size[n, m]['par2'], [by_size[n, k]['par2'] for k in selected], '.3f') for m in selected]
        lines.append(' & '.join(cells)+r' \\')
    write_rows('rq3_size.tex', lines)

    lines = []
    for i, m in enumerate(selected, 1):
        cells = [str(i), 'SAT '+NAMES[m] if m in SAT else NAMES[m]]
        for key, fmt, rev in [('solved', 'd', True), ('median', '.3f', False), ('par2', '.3f', False), ('ram', '.1f', False)]:
            v = ranked(hard[m][key], [hard[k][key] for k in selected], fmt, rev)
            cells.append(v+('/30' if key == 'solved' else ''))
        lines.append(' & '.join(cells)+r' \\')
    write_rows('rq3_hard25.tex', lines)

    lines = []
    counts = {n: {m: (n**3+4*n*n*amo(n, m)[0], 4*n*n*(1+amo(n, m)[1])) for m in SAT}
              for n in (9, 16, 25)}
    for i, m in enumerate(SAT, 1):
        cells = [str(i), NAMES[m]]
        for n in (9, 16, 25):
            cells += [ranked(counts[n][m][j], [counts[n][k][j] for k in SAT], ',d') for j in (0, 1)]
        lines.append(' & '.join(cells)+r' \\')
    write_rows('counts_compact.tex', lines)

    manifest = list(csv.DictReader((ROOT/'data/manifest.csv').open(encoding='utf-8', newline='')))
    levels = ['Val','ValBS','ValDS','ValChan','Bnd','BndBS','BndDS','BndChan','Dom','DomBS','DomDS','UNSOLVED']
    lines = []
    for i, (n, d) in enumerate(((n, d) for n in (9, 16, 25) for d in ('easy', 'medium', 'hard')), 1):
        sub = [p for p in manifest if int(p['size']) == n and p['difficulty'] == d]
        assert len(sub) == 10
        counts = Counter(p['hardness_level'] for p in sub)
        clues = [int(p['clues']) for p in sub]
        labels = ', '.join(f'{level}: {counts[level]}' for level in levels if counts[level])
        tier = {'easy':'Dễ','medium':'Vừa','hard':'Khó'}[d]
        lines.append(f'{i} & {n} & {tier} & {min(clues)}--{max(clues)} & {labels}'+r' \\')
    write_rows('dataset_numbered.tex', lines)

    group = {(n, d, m): summarize([r for r in rows if r['size'] == n and r['difficulty'] == d and r['method'] == m])['par2']
             for n in (9, 16, 25) for d in ('easy', 'medium', 'hard') for m in selected}
    lo, hi = min(map(math.log10, group.values())), max(map(math.log10, group.values()))
    lines = [r'\begin{tikzpicture}[x=1.08cm,y=.55cm]']
    for i, m in enumerate(selected):
        y = len(selected)-1-i
        name = 'SAT '+NAMES[m] if m in SAT else NAMES[m]
        lines.append(rf'\node[anchor=east,font=\scriptsize] at (-.12,{y+.5}) {{{name}}};')
        for j, (n, d) in enumerate((n, d) for n in (9, 16, 25) for d in ('easy', 'medium', 'hard')):
            v = group[n, d, m]; shade = round(12+72*(math.log10(v)-lo)/(hi-lo))
            color = 'white' if shade > 52 else 'black'
            lines.append(rf'\fill[reportblue!{shade}!white,draw=white] ({j},{y}) rectangle ({j+1},{y+1});')
            lines.append(rf'\node[text={color},font=\tiny] at ({j+.5},{y+.5}) {{{v:.3f}}};')
    for j, (n, d) in enumerate((n, d) for n in (9, 16, 25) for d in ('easy', 'medium', 'hard')):
        tier = {'easy': 'Dễ', 'medium': 'Vừa', 'hard': 'Khó'}[d]
        lines.append(rf'\node[font=\scriptsize,align=center] at ({j+.5},-.43) {{{n}$\times${n}\\{tier}}};')
    lines += [r'\node[anchor=west,font=\scriptsize] at (0,-1.10) {Giá trị trong ô: PAR2-total (s); màu dùng thang log.};',r'\end{tikzpicture}']
    (ROOT/'figures/rq3_heatmap.tex').write_text('\n'.join(lines)+'\n', encoding='utf-8')

    derived = dict(overall=overall, best=best, satmean=average,
        satmean_ratios={m: average['par2']/overall[m]['par2'] for m in OTHER},
        satmean_size={str(n): st.mean(by_size[n, m]['par2'] for m in SAT) for n in (9, 16, 25)},
        hard25=hard,
        hard25_share={m: hard[m]['par2']/(9*overall[m]['par2'])*100 for m in SAT+OTHER},
        without_hard25={m: summarize([r for r in rows if r['method'] == m and not(r['size'] == 25 and r['difficulty'] == 'hard')])['par2'] for m in SAT+OTHER},
        satmean_timeout_component=120*sum(overall[m]['n']-overall[m]['solved'] for m in SAT)/1080)
    (ROOT/'data/rq-summary.json').write_text(json.dumps(derived, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Recomputed six compact numbered tables, selected-method heatmap and rq-summary.json.')


if __name__ == '__main__':
    build()
