import json
import sys
from graph_algorithms import dsu, kruskal, prim, scc, topo, dag


def solve(req):
    t, n = req["task"], req["n"]
    if t == "ping":
        return {"task": "ping", "ok": True}
    if t == "dsu":
        return {"states": dsu(n, req.get("operations", []))}
    if t == "kruskal":
        return kruskal(n, req.get("edges", []))
    if t == "prim":
        return prim(n, req.get("edges", []))
    if t == "scc":
        return scc(n, req.get("edges", []))
    if t == "topo":
        return topo(n, req.get("edges", []))
    if t == "dag":
        return dag(n, req.get("edges", []), req["source"])
    raise ValueError("unknown task: " + str(t))


def main():
    for line in sys.stdin:
        if line.strip():
            sys.stdout.write(json.dumps(solve(json.loads(line))) + "\n")


if __name__ == "__main__":
    main()
