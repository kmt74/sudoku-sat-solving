# Sudoku benchmark: 60-second solve limit

- Dataset: `data/benchmark/manifest.csv`, 90 puzzles (9×9, 16×16, 25×25;
  10 easy, 10 medium, 10 hard per size).
- Methods: 4 SAT encodings, CP Optimizer, CPLEX MIP, Gurobi MIP, CP-SAT.
- Repetitions: 3 per puzzle and method; 2,160 attempts in total.
- Solve-phase limit: 60 seconds per attempt. Model construction and process
  startup are measured separately and are not covered by the solve limit.
- Memory mode: one fresh process per attempt; sampled process-tree RSS with
  a target interval of 10 ms. RSS peaks are estimates and can miss brief spikes.
- Start (UTC): 2026-10-15 07:25:48.740054.
- Finish (UTC): 2026-10-15 08:38:21.525647.
- Elapsed: 72 minutes 33 seconds.
- Results: 2,120 SOLVED, 40 TIMEOUT, 0 UNSAT, 0 ERROR. Every SOLVED grid
  passed independent validation.
- Timeout concentration: 3 in 16×16 hard; 37 in 25×25 hard.
- Repository HEAD at run start: `66db303`. The local working tree included
  uncommitted benchmark orchestration changes. Solver models and adapters were
  unchanged from that commit.

`all-results.jsonl` contains one metadata row and 2,160 result rows.
`puzzles/` contains one independently saved JSONL file per puzzle. The two CSV
files group by size and method, with `summary-by-difficulty.csv` additionally
splitting each size by difficulty. Time medians use only valid SOLVED attempts;
memory medians use all non-ERROR attempts with measurements. Always read the
solved rate alongside time medians, as TIMEOUT attempts are excluded from those
time medians.
