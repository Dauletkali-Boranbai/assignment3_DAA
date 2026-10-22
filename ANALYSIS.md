# Assignment 3 — Analysis

## Build / run / test commands
```
python tools/run.py --setup          # template setup
python tools/run.py --check          # 36 public cases
python -m unittest discover -s tests -v   # own tests (31)
python tools/benchmark.py            # Kruskal vs Prim
echo '{"task":"ping","n":0}' | python src/solve.py   # JSON Lines driver
```
Python 3.12, standard library only (`heapq`). No compilation step.

## Common notes
* **State reset.** Every method allocates all arrays locally; there are no globals or caches, so each request starts clean (test `test_mixed_repeated_requests_reset_state`).
* **Deep DFS.** All DFS runs use an explicit stack of `(vertex, next_neighbor_index)`; no recursion, so a 100 000-vertex chain cannot overflow the call stack (tests `test_deep_chain`).
* **Large numbers.** Python integers are unbounded; costs and distances up to 10⁹·10⁵ are exact.

## dsu
*Steps:* parent/size arrays; for each `[u,v]` find both roots (with path compression), attach the smaller tree under the larger, update `components` and `largest`; append `[components, largest]` after every operation (also for no-op unions).
*Invariants:* each tree = one set; `size[root]` = set size; `components` = number of roots; `largest` = max root size (sizes only grow).
*Correctness:* union by size joins exactly the two sets, and compression does not change set membership.
*Boundaries:* n=0, no operations, `u==v`, repeated pairs.
*Complexity:* O((n+q)·α(n)) time, O(n+q) memory (output has q pairs).

## kruskal
*Steps:* sort edge ids by weight (stable), scan with DSU, take an edge iff endpoints are in different sets; `components = n − |chosen|`.
*Invariant:* the chosen edges form a forest that is contained in some minimum spanning forest (cut property).
*Correctness:* an edge skipped closes a cycle, and it is not lighter than the cycle's other edges already taken (sorted order). Loops are skipped by `ru == rv`; negative weights need no special handling; isolates count as components.
*Complexity:* O(m log m) time, O(n+m) memory.

## prim
*Steps:* adjacency lists (loops dropped); for each unvisited vertex start a new tree (components += 1), push its edges `(w, id, v)` into a heap, repeatedly pop the lightest edge to an unvisited vertex, add it, push the new vertex's edges to unvisited vertices.
*Invariant:* the tree grown in the current component is contained in a minimum spanning tree of that component; the heap holds all edges leaving the tree (plus stale ones, skipped lazily).
*Correctness:* cut property on the cut (tree, rest). Restarting from every unvisited vertex gives a forest.
*Complexity:* O(m log m) time, O(n+m) memory.

## scc (Kosaraju)
*Steps:* (1) iterative DFS on G, record finish order; (2) build transpose; (3) iterative DFS/traversal on the transpose in reverse finish order, each tree gets a new label; (4) condensation = sorted set of distinct `(comp[u], comp[v])` with different labels.
*Invariant:* the vertex that finishes last in G lies in a source component of the condensation; so a traversal of the transpose from it cannot leave its component.
*Boundaries:* loops, parallel edges (collapsed in condensation), isolates, n=0.
*Complexity:* O(n+m) DFS plus O(m log m) for sorting the condensation pairs (or O(m) with a set only); O(n+m) memory.

## topo
*Steps:* three-state DFS (white/gray/black). An edge to a gray vertex is a back edge ⇒ cycle ⇒ `{acyclic:false, order:[]}`. Otherwise reverse the post-order.
*Invariant:* gray vertices are exactly the current DFS stack path.
*Correctness:* a directed cycle exists iff a DFS finds a back edge; in a DAG every edge `u→v` has `v` finished before `u`, so reversed post-order is topological. Loops are back edges. All components are searched, so cycles anywhere are found.
*Complexity:* O(n+m) time and memory.

## dag
*Steps:* topological order via the same three-state DFS on the whole graph (cycle anywhere ⇒ `false` and two empty arrays); `distance[source]=0`; process vertices in topological order, skipping unreachable ones; relax each outgoing edge with strict `<`, storing the original edge id in `parent_edge`.
*Invariant:* when a vertex is popped, all its predecessors are done, so its distance is final.
*Correctness:* standard DAG shortest paths; negative weights are fine because no vertex is relaxed twice after being finalised. Unreachable ⇒ `null`/`-1`; source ⇒ `0`/`-1`.
*Tie rule:* strict `<` keeps the first edge found (parallel edges: lowest id among those processed first).
*Complexity:* O(n+m) time and memory.

### Route helper `reconstruct_route(edges, parent_edge, source, target)`
Walk `parent_edge` backwards from `target` to `source`, reverse; returns `{"vertices", "edges"}` or `None`. Example graph `E = [[0,1,5],[0,1,5],[0,2,2],[2,1,3],[1,3,-4],[4,3,1]]`, source 0 → `distance=[0,5,2,1,null,null]`, `parent_edge=[-1,0,2,4,-1,-1]`.

| Call | Case | Result |
|---|---|---|
| `reconstruct_route(E, pe, 0, 3)` | reachable | `{"vertices":[0,1,3], "edges":[0,4]}` |
| `reconstruct_route(E, pe, 0, 0)` | source | `{"vertices":[0], "edges":[]}` |
| `reconstruct_route(E, pe, 0, 4)` | unreachable | `None` |
| `reconstruct_route(E, pe, 0, 1)` | tied / parallel (edges 0, 1 and 2+3 all cost 5) | `{"vertices":[0,1], "edges":[0]}` |

Complexity: O(path length).

## Tests (tests/test_algorithms.py)
Expected answers are justified in the test code by independent references: naive relabelling (DSU), brute-force over all edge subsets (MSF), Floyd–Warshall reachability (SCC, topo cycle check), Bellman–Ford (DAG). Non-unique answers (forest, order, parent edges) are checked by validators; the tests include an alternative valid answer and an invalid witness for each. Covered: empty graphs, loops, parallel edges, negative weights, isolates, 100 000-vertex chains/cycles, full limits (n=10⁵, m=2.5·10⁵), a cycle unreachable from the DAG source, repeated mixed requests.
Last run: `Ran 31 tests ... OK`.

## Benchmark: Kruskal vs Prim
* **Inputs:** random multigraphs (loops/parallel edges possible), weights uniform in [−10⁹, 10⁹]; `random.Random(20261022 + n)`; sizes (n, m) = (1 000, 5 000), (10 000, 50 000), (100 000, 250 000).
* **Command:** `python tools/benchmark.py`
* **Environment:** Python 3.12.3, Linux x86_64, Intel Xeon @ 2.10 GHz, 1 core.
* **Timer:** `time.perf_counter()`; 1 warm-up call, then 5 timed calls per method per size; median reported. Timed region = the algorithm call only (graph generation excluded; no compilation in Python).

| n | m | Kruskal runs (s) | Kruskal median | Prim runs (s) | Prim median |
|---|---|---|---|---|---|
| 1 000 | 5 000 | 0.0029 0.0028 0.0026 0.0025 0.0027 | **0.0027** | 0.0049 0.0047 0.0046 0.0045 0.0045 | **0.0046** |
| 10 000 | 50 000 | 0.0365 0.0397 0.0370 0.0431 0.0419 | **0.0397** | 0.0867 0.0951 0.0909 0.1199 0.0999 | **0.0951** |
| 100 000 | 250 000 | 0.4654 0.4239 0.4144 0.4706 0.4427 | **0.4427** | 1.0841 1.0271 0.9899 1.0347 1.0418 | **1.0347** |

Both are O(m log m); Kruskal is ≈2.3× faster here because Prim builds adjacency lists (2m tuples) and does many heap pushes, while Kruskal does one sort plus near-constant DSU operations. The gap would shrink for dense graphs with a different heap strategy.

