import heapq


def dsu(n, operations):

    parent = list(range(n))
    size = [1] * n
    comps = n
    largest = 1 if n else 0

    def find(x):
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:
            parent[x], x = root, parent[x]
        return root

    states = []
    for u, v in operations:
        ru, rv = find(u), find(v)
        if ru != rv:
            if size[ru] < size[rv]:
                ru, rv = rv, ru
            parent[rv] = ru
            size[ru] += size[rv]
            comps -= 1
            if size[ru] > largest:
                largest = size[ru]
        states.append([comps, largest])
    return states


def kruskal(n, edges):
    parent = list(range(n))
    size = [1] * n

    def find(x):
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:
            parent[x], x = root, parent[x]
        return root

    order = sorted(range(len(edges)), key=lambda i: edges[i][2])
    cost, chosen = 0, []
    for i in order:
        u, v, w = edges[i]
        ru, rv = find(u), find(v)
        if ru == rv:
            continue
        if size[ru] < size[rv]:
            ru, rv = rv, ru
        parent[rv] = ru
        size[ru] += size[rv]
        cost += w
        chosen.append(i)
    return {"cost": cost, "edge_ids": sorted(chosen), "components": n - len(chosen)}


def prim(n, edges):
    adj = [[] for _ in range(n)]
    for i, (u, v, w) in enumerate(edges):
        if u != v:
            adj[u].append((w, i, v))
            adj[v].append((w, i, u))
    visited = [False] * n
    cost, chosen, comps = 0, [], 0
    for s in range(n):
        if visited[s]:
            continue
        comps += 1
        visited[s] = True
        heap = list(adj[s])
        heapq.heapify(heap)
        while heap:
            w, i, v = heapq.heappop(heap)
            if visited[v]:
                continue
            visited[v] = True
            cost += w
            chosen.append(i)
            for item in adj[v]:
                if not visited[item[2]]:
                    heapq.heappush(heap, item)
    return {"cost": cost, "edge_ids": sorted(chosen), "components": comps}


def scc(n, edges):
    g = [[] for _ in range(n)]
    gt = [[] for _ in range(n)]
    for u, v in edges:
        g[u].append(v)
        gt[v].append(u)

    seen = [False] * n
    finish = []
    for s in range(n):
        if seen[s]:
            continue
        seen[s] = True
        stack = [(s, 0)]
        while stack:
            u, k = stack.pop()
            if k < len(g[u]):
                stack.append((u, k + 1))
                v = g[u][k]
                if not seen[v]:
                    seen[v] = True
                    stack.append((v, 0))
            else:
                finish.append(u)

    comp = [-1] * n
    count = 0
    for s in reversed(finish):
        if comp[s] != -1:
            continue
        comp[s] = count
        stack = [s]
        while stack:
            u = stack.pop()
            for v in gt[u]:
                if comp[v] == -1:
                    comp[v] = count
                    stack.append(v)
        count += 1

    cond = sorted({(comp[u], comp[v]) for u, v in edges if comp[u] != comp[v]})
    return {"component": comp, "count": count, "condensation": [list(p) for p in cond]}


def _topological_order(n, adj):

    state = [0] * n
    post = []
    for s in range(n):
        if state[s]:
            continue
        state[s] = 1
        stack = [(s, 0)]
        while stack:
            u, k = stack.pop()
            if k < len(adj[u]):
                stack.append((u, k + 1))
                v = adj[u][k][0]
                if state[v] == 1:
                    return None
                if state[v] == 0:
                    state[v] = 1
                    stack.append((v, 0))
            else:
                state[u] = 2
                post.append(u)
    post.reverse()
    return post


def topo(n, edges):
    adj = [[] for _ in range(n)]
    for i, (u, v) in enumerate(edges):
        adj[u].append((v, i))
    order = _topological_order(n, adj)
    if order is None:
        return {"acyclic": False, "order": []}
    return {"acyclic": True, "order": order}


def dag(n, edges, source):

    adj = [[] for _ in range(n)]
    for i, (u, v, w) in enumerate(edges):
        adj[u].append((v, i))
    order = _topological_order(n, adj)
    if order is None:
        return {"acyclic": False, "distance": [], "parent_edge": []}
    dist = [None] * n
    parent = [-1] * n
    dist[source] = 0
    for u in order:
        du = dist[u]
        if du is None:
            continue
        for v, i in adj[u]:
            nd = du + edges[i][2]
            if dist[v] is None or nd < dist[v]:
                dist[v] = nd
                parent[v] = i
    return {"acyclic": True, "distance": dist, "parent_edge": parent}


def reconstruct_route(edges, parent_edge, source, target):
    if target == source:
        return {"vertices": [source], "edges": []}
    if parent_edge[target] == -1:
        return None
    path_edges, v = [], target
    while v != source:
        e = parent_edge[v]
        if e == -1 or len(path_edges) > len(parent_edge):
            raise ValueError("corrupt parent_edge array")
        path_edges.append(e)
        v = edges[e][0]
    path_edges.reverse()
    return {"vertices": [source] + [edges[e][1] for e in path_edges], "edges": path_edges}
