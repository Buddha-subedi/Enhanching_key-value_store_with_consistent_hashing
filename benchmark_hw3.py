"""End-to-end concurrent benchmark; records observed rather than invented results."""
import argparse
import csv
import json
import math
import statistics
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import requests


def percentile(values, pct):
    vals = sorted(values)
    return vals[min(len(vals)-1, math.ceil(len(vals)*pct/100)-1)]


def run(base, headers, nodes, ops, workers, read_fraction):
    r = requests.post(base+'/_admin/membership',headers=headers,json={'nodes':[f'kv{i}' for i in range(1,nodes+1)]},timeout=300)
    r.raise_for_status()
    prefix = uuid.uuid4().hex
    keys = [f'bench-{prefix}-{i}' for i in range(max(100, ops//4))]
    with requests.Session() as session:
        for key in keys:
            resp = session.put(base+'/'+key,json={'value':'x'*128},timeout=300)
            resp.raise_for_status()
    def operation(i):
        key = keys[i % len(keys)]
        method = 'GET' if (i % 100) < int(read_fraction*100) else 'PUT'
        start = time.perf_counter()
        try:
            response = requests.request(method,base+'/'+key,json={'value':'y'*128} if method=='PUT' else None,timeout=300)
            success = response.status_code == 200
        except requests.RequestException:
            success = False
        return (time.perf_counter()-start)*1000,success
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        outcomes = list(pool.map(operation,range(ops)))
    elapsed = time.perf_counter()-t0
    latencies = [x for x, ok in outcomes if ok]
    errors = sum(not ok for _,ok in outcomes)
    for key in keys:
        requests.delete(base+'/'+key,timeout=300)
    return dict(nodes=nodes,workers=workers,operations=ops,successful=len(latencies),errors=errors,elapsed_s=round(elapsed,4),throughput_ops_s=round(len(latencies)/elapsed,3),mean_ms=round(statistics.mean(latencies),3) if latencies else None,p50_ms=round(percentile(latencies,50),3) if latencies else None,p95_ms=round(percentile(latencies,95),3) if latencies else None,p99_ms=round(percentile(latencies,99),3) if latencies else None)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--url',default='http://localhost:8000')
    parser.add_argument('--operations',type=int,default=1200)
    parser.add_argument('--workers',type=int,default=16)
    parser.add_argument('--repeats',type=int,default=3)
    parser.add_argument('--read-fraction',type=float,default=.8)
    parser.add_argument('--token',default='local-dev-token')
    args=parser.parse_args()
    if not (0<=args.read_fraction<=1):
        parser.error('read-fraction must be between 0 and 1')
    headers={'X-Admin-Token':args.token}
    results=[]
    Path('results').mkdir(exist_ok=True)
    for n in (1,2,3):
        for rep in range(args.repeats):
            result=run(args.url,headers,n,args.operations,args.workers,args.read_fraction)
            result['repeat']=rep+1
            print(json.dumps(result),flush=True)
            results.append(result)
    path=Path('results/benchmark.csv')
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=results[0].keys())
        writer.writeheader();writer.writerows(results)
    print('Saved',path)

if __name__=='__main__':
    main()
