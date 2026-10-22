
import os, platform, random, statistics, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from graph_algorithms import kruskal, prim

SEED = 20261022
SIZES = [(1_000, 5_000), (10_000, 50_000), (100_000, 250_000)]
RUNS = 5

print(f"python {platform.python_version()} | {platform.platform()} | {platform.machine()} | seed={SEED}")
print("n,m,method,runs_s,median_s")
for n, m in SIZES:
    rnd = random.Random(SEED + n)
    edges = [[rnd.randrange(n), rnd.randrange(n), rnd.randint(-10**9, 10**9)] for _ in range(m)]
    for name, fn in (("kruskal", kruskal), ("prim", prim)):
        fn(n, edges)                                    # warm-up
        ts = []
        for _ in range(RUNS):
            t0 = time.perf_counter(); fn(n, edges); ts.append(time.perf_counter() - t0)
        print(f"{n},{m},{name},{' '.join(f'{t:.4f}' for t in ts)},{statistics.median(ts):.4f}")
