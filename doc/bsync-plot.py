#!/usr/bin/env python
# coding: utf-8

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np


systems=('Laptop', 'Desktop')

y = np.array([1.75,3.33])
compute_fingerprints = np.array((30.0, 24.0))
wait1 = np.array((0.0, 6.0))
transfer_fingerprint = np.array((0.12, 0.12))
wait2 = np.array((4.0, 0.0))
make_patch = np.array((0.0, 4.0))
transfer_patch = np.array((3.5,3.5))
apply_patch = np.array((2.5, 0.0))

plt.barh(y, compute_fingerprints, color='plum')

start = np.copy(compute_fingerprints)

plt.barh(y, wait1, left=start, color='gray', alpha=0.3)

start += wait1

plt.barh(y, transfer_fingerprint, left=start, color='lime')

start += transfer_fingerprint

plt.barh(y, wait2, left=start, color='gray', alpha=0.3)

start += wait2

plt.barh(y, make_patch, left=start, color='plum')

start += make_patch

plt.barh(y, transfer_patch, left=start, color='lime')

start += transfer_patch

plt.barh(y, apply_patch, left=start, color='plum')

plt.text(30.05, 2.5, "hashes", ha="center", va="center", rotation=90,
            size=8,
            color='white',
            bbox={'boxstyle':"rarrow,pad=0.3", 'fc':"darkgreen", 'lw':0})

plt.text(35.8, 2.57, " patch", ha="center", va="center", rotation=-90,
            size=9,
            color='white',
            bbox={'boxstyle':"rarrow,pad=0.3", 'fc':"darkgreen", 'lw':0})

plt.text(15, 1.75, "computing hashes", ha="center", va="center", size=10, color='white')

plt.text(12, 3.33, "computing hashes", ha="center", va="center", size=10, color='white')

plt.annotate('applying\n patch', xy=(38.5, 1.75),  xycoords='data',
            xytext=(49, 1.5), textcoords='data',
            arrowprops=dict(arrowstyle='fancy', lw=0, fc='k'),
            horizontalalignment='center', verticalalignment='center')


plt.annotate('creating\n patch', xy=(32.2, 3.6),  xycoords='data',
            xytext=(26.5, 4.33), textcoords='data',
            arrowprops=dict(arrowstyle='fancy', lw=0, fc='k'),
            horizontalalignment='center', verticalalignment='center')


plt.ylim((1, 5))
plt.xlim((0, 60))
plt.xlabel("Time (seconds)")
plt.yticks(y, systems)

h = [Patch(facecolor='plum', label='Processing'), 
     Patch(fc='gray', alpha=0.3, label='Waiting'), 
     Patch(fc='lime', label='Network transfer')]

plt.legend(handles=h)
