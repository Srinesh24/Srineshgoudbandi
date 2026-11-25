CSC6410 – Experiment 5

TCP Congestion Control and Fairness

This experiment compares TCP CUBIC and Reno using Mininet, Linux Netem and iperf3.

Experimental configuration

Bandwidth: 20 Mbps

RTT: approximately 100 ms

Packet loss: 0%, 0.1%, 0.5%, 1% and 2%

Three runs per algorithm at each loss rate

Queue limits: 1,000 and 250 packets

Total throughput tests: 30

Files

netem_experiment.py — Experiment automation script.

CSC6410_EXP5_Evidence.zip — Raw experimental measurements, CSV files and terminal logs.

Results

Both congestion control algorithms experienced reduced throughput as packet loss increased.

Jain's fairness index:

Deep queue: 0.982890

Shallow queue: 0.992009

Environment

Windows 11, WSL2 Ubuntu, Mininet and Open vSwitch.

AI disclosure

ChatGPT assisted with script development, troubleshooting and result verification. The experiments were executed on my local machine.
