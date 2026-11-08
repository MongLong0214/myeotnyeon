import json,csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=Path(__file__).resolve().parent;cuts=list(csv.DictReader((r/'cuts.csv').open()));voice=list(csv.DictReader((r/'narration_30s.csv').open()));aud=list(csv.DictReader((r/'reference_audio_1s.csv').open()));chap=json.load(open(r/'chapters.json'))
fig,axs=plt.subplots(3,1,figsize=(13,8),sharex=True,facecolor='#f7f5f1')
t=np.arange(0,522,30);counts=[sum(a<=float(c['time_s'])<min(a+30,521.8) for c in cuts)*60/(min(a+30,521.8)-a) for a in t];axs[0].bar(t,counts,width=np.minimum(30,521.8-t),align='edge',color='#a22a36');axs[0].set_ylabel('Cuts / min\n(30s window)');axs[0].set_ylim(0,32)
axs[1].plot([float(v['start_s'])+(float(v['end_s'])-float(v['start_s']))/2 for v in voice],[float(v['syllables_per_timeline_s']) for v in voice],marker='o',color='#233b62');axs[1].set_ylabel('Syllables / s\n(30s window)');axs[1].set_ylim(0,8)
axs[2].plot([float(a['start_s']) for a in aud],[float(a['mix_dbfs']) for a in aud],lw=.8,label='Full mix RMS',color='#233b62');axs[2].plot([float(a['start_s']) for a in aud],[float(a['side_dbfs']) for a in aud],lw=.8,label='Stereo side RMS (not music stem)',color='#a22a36');axs[2].set_ylim(-65,-5);axs[2].set_ylabel('dBFS (1s)');axs[2].legend(loc='lower left');axs[2].set_xlabel('Seconds')
for ax in axs:
 ax.set_facecolor('#f7f5f1');ax.grid(axis='y',alpha=.2);ax.set_xlim(0,521.8)
 for c in chap[1:]:ax.axvline(c['start_s'],color='gray',ls='--',alpha=.6)
axs[0].set_title('Extol reference 2: measured timing, speech and audio mixture\nDashed lines: four chapter entries; source video 521.8 s',loc='left',pad=18)
fig.tight_layout();fig.savefig(r/'timeline_metrics.png',dpi=150);plt.close(fig)
