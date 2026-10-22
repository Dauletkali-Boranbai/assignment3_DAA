import itertools, os, random, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from graph_algorithms import dsu, kruskal, prim, scc, topo, dag, reconstruct_route
from solve import solve


def reach_matrix(n, pairs):
    r = [[i == j for j in range(n)] for i in range(n)]
    for u, v in pairs:
        r[u][v] = True
    for k in range(n):
        for i in range(n):
            if r[i][k]:
                for j in range(n):
                    if r[k][j]:
                        r[i][j] = True
    return r

def _forest_components(n, edge_list):
    p = list(range(n))
    def f(x):
        while p[x] != x:
            p[x] = p[p[x]]; x = p[x]
        return x
    for u, v in edge_list:
        a, b = f(u), f(v)
        if a == b:
            return None
        p[a] = b
    return len({f(x) for x in range(n)})

def forest_ok(n, edges, res):
    ids = res["edge_ids"]
    if len(set(ids)) != len(ids) or any(not 0 <= i < len(edges) for i in ids):
        return False
    comps = _forest_components(n, [edges[i][:2] for i in ids])
    return comps == res["components"] and sum(edges[i][2] for i in ids) == res["cost"]

def brute_msf_cost(n, edges):
    target = None
    p = list(range(n))
    def f(x):
        while p[x] != x:
            x = p[x]
        return x
    for u, v, _ in edges:
        a, b = f(u), f(v)
        if a != b:
            p[a] = b
    target = len({f(x) for x in range(n)})
    best = None
    for k in range(len(edges) + 1):
        for sub in itertools.combinations(range(len(edges)), k):
            if _forest_components(n, [edges[i][:2] for i in sub]) == target:
                c = sum(edges[i][2] for i in sub)
                best = c if best is None else min(best, c)
    return best

def valid_topo(n, edges, order):
    if sorted(order) != list(range(n)):
        return False
    pos = {v: i for i, v in enumerate(order)}
    return all(pos[u] < pos[v] for u, v in edges)

def valid_sp(n, edges, source, res, ref_dist):
    if res["distance"] != ref_dist:
        return False
    for v in range(n):
        pe = res["parent_edge"][v]
        if v == source or ref_dist[v] is None:
            if pe != -1:
                return False
        else:
            if not 0 <= pe < len(edges):
                return False
            u, x, w = edges[pe]
            if x != v or ref_dist[u] is None or ref_dist[u] + w != ref_dist[v]:
                return False
    return True

def bellman_ford(n, edges, source):
    d = [None] * n
    d[source] = 0
    for _ in range(n):
        for u, v, w in edges:
            if d[u] is not None and (d[v] is None or d[u] + w < d[v]):
                d[v] = d[u] + w
    return d


class TestDSU(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(dsu(5, [[0, 1], [1, 0], [2, 3], [1, 3], [4, 4]]),
                         [[4, 2], [4, 2], [3, 2], [2, 4], [2, 4]])
    def test_empty(self):
        self.assertEqual(dsu(0, []), [])
        self.assertEqual(dsu(3, []), [])
    def test_random_vs_naive(self):
        rnd = random.Random(1)
        for _ in range(200):
            n = rnd.randint(1, 12)
            ops = [[rnd.randrange(n), rnd.randrange(n)] for _ in range(rnd.randint(0, 20))]
            lab = list(range(n)); exp = []
            for u, v in ops:
                a, b = lab[u], lab[v]
                lab = [a if x == b else x for x in lab]
                cnt = {}
                for x in lab:
                    cnt[x] = cnt.get(x, 0) + 1
                exp.append([len(cnt), max(cnt.values())])
            self.assertEqual(dsu(n, ops), exp)
    def test_deep_chain(self):
        n = 100000
        r = dsu(n, [[i, i + 1] for i in range(n - 1)])
        self.assertEqual(r[-1], [1, n])


class TestMSF(unittest.TestCase):
    def test_known(self):
        e = [[0, 1, 4], [1, 2, 1], [0, 2, 3], [3, 3, -5], [0, 1, 2], [4, 4, 0]]
        for fn in (kruskal, prim):
            r = fn(5, e)
            self.assertEqual((r["cost"], r["components"]), (3, 3))
            self.assertTrue(forest_ok(5, e, r))
    def test_negative_and_parallel(self):
        e = [[0, 1, -7], [0, 1, -9], [1, 2, 0]]
        for fn in (kruskal, prim):
            r = fn(3, e)
            self.assertEqual(r["cost"], -9)
            self.assertEqual(r["edge_ids"], [1, 2])
    def test_empty_and_isolates(self):
        for fn in (kruskal, prim):
            self.assertEqual(fn(0, []), {"cost": 0, "edge_ids": [], "components": 0})
            self.assertEqual(fn(4, [])["components"], 4)
    def test_prim_restarts_in_each_component(self):
        e = [[0, 1, 1], [2, 3, 2], [4, 5, 3]]
        r = prim(7, e)
        self.assertEqual((r["cost"], r["components"], r["edge_ids"]), (6, 4, [0, 1, 2]))
    def test_random_vs_bruteforce(self):
        rnd = random.Random(2)
        for _ in range(150):
            n = rnd.randint(1, 6)
            e = [[rnd.randrange(n), rnd.randrange(n), rnd.randint(-5, 5)] for _ in range(rnd.randint(0, 8))]
            ref = brute_msf_cost(n, e)
            for fn in (kruskal, prim):
                r = fn(n, e)
                self.assertTrue(forest_ok(n, e, r))
                self.assertEqual(r["cost"], ref)
    def test_alternative_valid_answer_and_invalid_witness(self):
        e = [[0, 1, 1], [1, 2, 1], [0, 2, 1]]
        self.assertTrue(forest_ok(3, e, {"cost": 2, "edge_ids": [0, 2], "components": 1}))
        self.assertFalse(forest_ok(3, e, {"cost": 3, "edge_ids": [0, 1, 2], "components": 1}))
    def test_kruskal_prim_agree_large(self):
        rnd = random.Random(3)
        n, m = 20000, 80000
        e = [[rnd.randrange(n), rnd.randrange(n), rnd.randint(-10**9, 10**9)] for _ in range(m)]
        a, b = kruskal(n, e), prim(n, e)
        self.assertEqual(a["cost"], b["cost"])
        self.assertEqual(a["components"], b["components"])
        self.assertTrue(forest_ok(n, e, a) and forest_ok(n, e, b))


class TestSCC(unittest.TestCase):
    def test_known(self):
        e = [[0, 1], [1, 2], [2, 0], [2, 3], [3, 4], [4, 3], [1, 1], [2, 3]]
        r = scc(6, e)
        c = r["component"]
        self.assertTrue(c[0] == c[1] == c[2])
        self.assertTrue(c[3] == c[4])
        self.assertEqual(len({c[0], c[3], c[5]}), 3)
        self.assertEqual(r["condensation"], [[c[0], c[3]]])
    def test_random_vs_reachability(self):
        rnd = random.Random(4)
        for _ in range(200):
            n = rnd.randint(0, 8)
            e = [[rnd.randrange(n), rnd.randrange(n)] for _ in range(rnd.randint(0, 14))] if n else []
            r = scc(n, e); R = reach_matrix(n, e); c = r["component"]
            for i in range(n):
                for j in range(n):
                    self.assertEqual(c[i] == c[j], R[i][j] and R[j][i])
            self.assertEqual(r["count"], len(set(c)))
            self.assertEqual({tuple(p) for p in r["condensation"]},
                             {(c[u], c[v]) for u, v in e if c[u] != c[v]})
    def test_deep_cycle(self):
        n = 100000
        self.assertEqual(scc(n, [[i, (i + 1) % n] for i in range(n)])["count"], 1)
    def test_deep_chain(self):
        n = 100000
        r = scc(n, [[i, i + 1] for i in range(n - 1)])
        self.assertEqual(r["count"], n)
        self.assertEqual(len(r["condensation"]), n - 1)


class TestTopo(unittest.TestCase):
    def test_known(self):
        e = [[0, 1], [0, 2], [1, 3], [2, 3], [0, 3]]
        r = topo(4, e)
        self.assertTrue(r["acyclic"] and valid_topo(4, e, r["order"]))
    def test_cycles(self):
        for e in ([[0, 0]], [[0, 1], [1, 2], [2, 0]]):
            self.assertEqual(topo(3, e), {"acyclic": False, "order": []})
    def test_cycle_in_second_component(self):
        self.assertFalse(topo(6, [[0, 1], [3, 4], [4, 5], [5, 3]])["acyclic"])
    def test_empty(self):
        self.assertEqual(topo(0, []), {"acyclic": True, "order": []})
    def test_random_vs_reachability(self):
        rnd = random.Random(5)
        for _ in range(300):
            n = rnd.randint(1, 8)
            e = [[rnd.randrange(n), rnd.randrange(n)] for _ in range(rnd.randint(0, 10))]
            R = reach_matrix(n, e)
            cyc = any(u == v for u, v in e) or any(R[i][j] and R[j][i] for i in range(n) for j in range(n) if i != j)
            r = topo(n, e)
            self.assertEqual(r["acyclic"], not cyc)
            if cyc:
                self.assertEqual(r["order"], [])
            else:
                self.assertTrue(valid_topo(n, e, r["order"]))
    def test_alternative_and_invalid_order(self):
        self.assertTrue(valid_topo(3, [[0, 1]], [2, 0, 1]))
        self.assertTrue(valid_topo(3, [[0, 1]], [0, 1, 2]))
        self.assertFalse(valid_topo(3, [[0, 1], [1, 2]], [2, 1, 0]))
        self.assertFalse(valid_topo(3, [[0, 1]], [0, 1]))
    def test_deep_chain(self):
        n = 100000
        e = [[i, i + 1] for i in range(n - 1)]
        self.assertEqual(topo(n, e)["order"], list(range(n)))
        e.append([n - 1, 0])
        self.assertFalse(topo(n, e)["acyclic"])


class TestDAG(unittest.TestCase):
    E = [[0, 1, 5], [0, 1, 5], [0, 2, 2], [2, 1, 3], [1, 3, -4], [4, 3, 1]]
    def test_known(self):
        r = dag(6, self.E, 0)
        self.assertEqual(r["distance"], [0, 5, 2, 1, None, None])
        self.assertEqual(r["parent_edge"], [-1, 0, 2, 4, -1, -1])
    def test_cycle_unreachable_from_source(self):
        self.assertEqual(dag(5, [[0, 1, 1], [2, 3, 1], [3, 4, 1], [4, 2, 1]], 0),
                         {"acyclic": False, "distance": [], "parent_edge": []})
    def test_self_loop_and_single_vertex(self):
        self.assertFalse(dag(1, [[0, 0, -1]], 0)["acyclic"])
        self.assertEqual(dag(1, [], 0), {"acyclic": True, "distance": [0], "parent_edge": [-1]})
    def test_random_vs_bellman_ford(self):
        rnd = random.Random(6)
        for _ in range(300):
            n = rnd.randint(1, 9)
            perm = list(range(n)); rnd.shuffle(perm)
            e = []
            for _ in range(rnd.randint(0, 15)):
                if n > 1:
                    a, b = sorted(rnd.sample(range(n), 2))
                    e.append([perm[a], perm[b], rnd.randint(-9, 9)])
            s = rnd.randrange(n)
            r = dag(n, e, s)
            self.assertTrue(r["acyclic"])
            self.assertTrue(valid_sp(n, e, s, r, bellman_ford(n, e, s)))
    def test_alternative_and_invalid_witness(self):
        r = dag(6, self.E, 0)
        alt = {"distance": r["distance"], "parent_edge": [-1, 1, 2, 4, -1, -1]}
        self.assertTrue(valid_sp(6, self.E, 0, alt, r["distance"]))
        bad = {"distance": r["distance"], "parent_edge": [-1, 0, 2, 5, -1, -1]}
        self.assertFalse(valid_sp(6, self.E, 0, bad, r["distance"]))
    def test_route_helper(self):
        r = dag(6, self.E, 0)
        self.assertEqual(reconstruct_route(self.E, r["parent_edge"], 0, 3),
                         {"vertices": [0, 1, 3], "edges": [0, 4]})
        self.assertEqual(reconstruct_route(self.E, r["parent_edge"], 0, 0),
                         {"vertices": [0], "edges": []})
        self.assertIsNone(reconstruct_route(self.E, r["parent_edge"], 0, 4))
        self.assertEqual(reconstruct_route(self.E, r["parent_edge"], 0, 1),
                         {"vertices": [0, 1], "edges": [0]})
    def test_deep_chain_and_big_weights(self):
        n = 100000
        e = [[i, i + 1, -10**9] for i in range(n - 1)]
        r = dag(n, e, 0)
        self.assertEqual(r["distance"][-1], -10**9 * (n - 1))
        self.assertEqual(len(reconstruct_route(e, r["parent_edge"], 0, n - 1)["edges"]), n - 1)


class TestInterface(unittest.TestCase):
    def test_full_limits(self):
        rnd = random.Random(7)
        n, m = 100000, 250000
        ops = [[rnd.randrange(n), rnd.randrange(n)] for _ in range(m)]
        self.assertEqual(len(dsu(n, ops)), m)
        e = [[rnd.randrange(n), rnd.randrange(n), rnd.randint(-10**9, 10**9)] for _ in range(m)]
        a, b = kruskal(n, e), prim(n, e)
        self.assertEqual((a["cost"], a["components"]), (b["cost"], b["components"]))
        pairs = [[u, v] for u, v, _ in e]
        self.assertEqual(len(scc(n, pairs)["component"]), n)
        self.assertIn(len(topo(n, pairs)["order"]), (0, n))
    def test_mixed_repeated_requests_reset_state(self):
        reqs = [
            {"task": "ping", "n": 0},
            {"task": "dsu", "n": 3, "operations": [[0, 1]]},
            {"task": "dag", "n": 3, "source": 0, "edges": [[0, 1, 1]]},
            {"task": "dsu", "n": 3, "operations": [[0, 1]]},
            {"task": "kruskal", "n": 2, "edges": [[0, 1, 1]]},
            {"task": "prim", "n": 2, "edges": [[0, 1, 1]]},
            {"task": "scc", "n": 2, "edges": [[0, 1]]},
            {"task": "topo", "n": 2, "edges": [[1, 0]]},
        ]
        first = [solve(r) for r in reqs]
        second = [solve(r) for r in reqs]
        self.assertEqual(first, second)
        self.assertEqual(first[1], first[3])


if __name__ == "__main__":
    unittest.main()
