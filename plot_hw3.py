"""Plot real benchmark.csv data; does not synthesize results."""
import csv
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt

rows=list(csv.DictReader(open('results/benchmark.csv',newline='')))
groups=defaultdict(list)
for row in rows:
    groups[int(row['nodes'])].append(row)
xs=sorted(groups)
for metric,label,name in [('throughput_ops_s','Successful requests / second','throughput.png'),('mean_ms','Mean latency (ms)','latency_mean.png'),('p95_ms','P95 latency (ms)','latency_p95.png')]:
    ys=[sum(float(r[metric]) for r in groups[n])/len(groups[n]) for n in xs]
    fig,ax=plt.subplots(figsize=(6.5,4))
    ax.plot(xs,ys,'o-',linewidth=2,markersize=8)
    ax.set_xticks(xs);ax.set_xlabel('Active KV store instances');ax.set_ylabel(label)
    ax.set_title(label+' vs number of KV stores');ax.grid(alpha=.25)
    fig.tight_layout();fig.savefig(Path('results')/name,dpi=180);plt.close(fig)
    print(name,dict(zip(xs,ys)))
