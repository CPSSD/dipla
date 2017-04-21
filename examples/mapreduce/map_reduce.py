from os import path
from time import time
import sys
# Append to path so that this script can access the dipla package
sys.path.append(path.abspath('../dipla'))

from dipla.api import Dipla

# This program finds the word with the most vowels from the opening of the Communist Manifesto

true_start_time = time()

splits = []
with open('examples/mapreduce/pg30254.txt', 'r') as f:
    while True:
        curr = f.readline()
        s = None
        for _ in range(10):
            s = f.readline()
            if s == '':
                print('s is None >')
                break
            curr += f.readline()
        splits.append(curr)
        if s == '':
            print('s is None')
            break
        if len(splits) > 10:
            break

with open('examples/mapreduce/stopwords.txt', 'r') as f:
    stop_words = set([w.lower().strip() for w in f.readlines()])

@Dipla.distributable()
def tokenise(doc):
    import re
    words = re.split(r"[^a-z']", doc.lower())
    d = {}
    for word in words:
        if word == '':
            continue
        if word in d:
            d[word] += 1
        else:
            d[word] = 1
    return d

@Dipla.reduce_distributable(n=2)
def combine_dicts(d):
    comb = {}
    for e in d:
        for w in e:
            if w in comb:
                comb[w] += e[w]
            else:
                comb[w] = e[w]
    if len(comb) > 50:
        sorted_keys = sorted(comb, key = lambda x: comb[x], reverse=True)
        small_comb = {}
        for k in sorted_keys[:50]:
            small_comb[k] = comb[k]
        return small_comb
    return comb

start_time = time()

d = Dipla.apply_distributable(tokenise, splits)
e = Dipla.apply_distributable(combine_dicts, d)
f = e.get()
end_time = time()
print('Distributed work took {} seconds'.format(end_time - start_time))

g = {w: v for w, v in f.items() if w not in stop_words}
sorted_keys = sorted(g, key=lambda x: g[x], reverse=True)
for i in range(min(20, len(sorted_keys))):
    print(sorted_keys[i], f[sorted_keys[i]])

print('All work (inc. pre- and post-processing) took {} seconds'.format(time() - true_start_time))
