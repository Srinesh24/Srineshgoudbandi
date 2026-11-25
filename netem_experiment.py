#!/usr/bin/env python3
"""AI-assisted lab draft. Review and add your own comments before submission."""
import json, time, statistics, csv, os
from pathlib import Path
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.topo import SingleSwitchTopo

out = Path.home() / 'exp5_results' if not os.environ.get('SUDO_USER') else Path('/home') / os.environ['SUDO_USER'] / 'exp5_results'
out.mkdir(parents=True, exist_ok=True)
net = Mininet(topo=SingleSwitchTopo(k=2), controller=None, switch=OVSSwitch, autoSetMacs=True)
rows = []
def shape(loss, limit):
    result = s1.cmd(f'tc qdisc replace dev s1-eth2 root netem delay 100ms loss {loss}% rate 20mbit limit {limit}')
    if result.strip(): raise RuntimeError(result)
def launch(cc, port, duration, name):
    f = open(out / (name+'.json'), 'w')
    p = h1.popen(['iperf3','-c','10.0.0.2','-p',str(port),'-C',cc,'-t',str(duration),'-J'], stdout=f)
    return p,f,name,cc
def finish(job):
    p,f,name,cc=job
    rc=p.wait(); f.close()
    d=json.loads((out/(name+'.json')).read_text())
    if rc or 'error' in d: raise RuntimeError(str(d.get('error',rc)))
    e=d['end']; s=e['sum_sent']; r=e['sum_received']; t=e['streams'][0]['sender']
    if e.get('sender_tcp_congestion') != cc: raise RuntimeError('Algorithm mismatch')
    return [s['bits_per_second']/1e6,r['bits_per_second']/1e6,s['retransmits'],t['mean_rtt']/1000]
def evidence(name):
    ss=h1.cmd('ss -ti'); print(ss,flush=True); (out/(name+'_ss.txt')).write_text(ss)
def queue(name):
    (out/(name+'_tc.txt')).write_text(s1.cmd('tc -s qdisc show dev s1-eth2'))
try:
    net.start(); h1,h2,s1=net.get('h1','h2','s1')
    s1.cmd('ovs-vsctl set-fail-mode s1 standalone')
    if net.pingAll()!=0: raise RuntimeError('Baseline ping failed')
    available=h1.cmd('sysctl -n net.ipv4.tcp_available_congestion_control').split()
    if not {'cubic','reno'}.issubset(available): raise RuntimeError('Required algorithms unavailable')
    h2.cmd('iperf3 -s -D'); h2.cmd('iperf3 -s -p 5202 -D'); time.sleep(1)
    for loss in [0,0.1,0.5,1,2]:
        for cc in ['cubic','reno']:
            for run in range(1,4):
                shape(loss,1000)
                print(h1.cmd(f'sysctl -w net.ipv4.tcp_congestion_control={cc}'),flush=True)
                name=f'{cc}_loss{loss}_run{run}'
                job=launch(cc,5201,30,name); time.sleep(5); evidence(name)
                values=finish(job); queue(name); rows.append([cc,loss,run,*values]); print(name,values,flush=True)
                with (out/'runs.csv').open('w') as f:
                    w=csv.writer(f); w.writerow(['algorithm','loss_percent','run','sender_mbps','receiver_mbps','retransmits','mean_rtt_ms']); w.writerows(rows)
    print('SUMMARY: algorithm loss mean_sender_Mbps sample_SD mean_retransmits mean_RTT_ms',flush=True)
    with (out/'summary.csv').open('w') as f:
        w=csv.writer(f); w.writerow(['algorithm','loss_percent','mean_sender_mbps','sample_sd_mbps','mean_retransmits','mean_rtt_ms'])
        for loss in [0,0.1,0.5,1,2]:
            for cc in ['cubic','reno']:
                a=[r for r in rows if r[:2]==[cc,loss]]
                line=[cc,loss,statistics.mean(r[3] for r in a),statistics.stdev(r[3] for r in a),statistics.mean(r[5] for r in a),statistics.mean(r[6] for r in a)]
                w.writerow(line); print(line,flush=True)
    with (out/'competition.csv').open('w') as f:
        w=csv.writer(f); w.writerow(['queue_limit','cubic_receiver_mbps','reno_receiver_mbps','jain_index'])
        for limit in [1000,250]:
            shape(0,limit); name=f'competition_{limit}'
            a=launch('cubic',5201,60,name+'_cubic'); b=launch('reno',5202,60,name+'_reno')
            time.sleep(5); evidence(name); x=finish(a); y=finish(b); queue(name)
            u,v=x[1],y[1]; j=(u+v)**2/(2*(u*u+v*v)); w.writerow([limit,u,v,j]); print('COMPETITION',limit,'CUBIC',x,'Reno',y,'Jain',j,flush=True)
finally:
    net.stop()
    if os.environ.get('SUDO_UID'):
        for p in [out,*out.iterdir()]: os.chown(p,int(os.environ['SUDO_UID']),int(os.environ['SUDO_GID']))
