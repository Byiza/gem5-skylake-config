# -*- coding: utf-8 -*-
# Copyright (c) 2020 The Regents of the University of California
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Authors: Jason Lowe-Power, Trivikram Reddy

import m5
from m5.objects import *
import argparse
from se  import MySystem
from m5.objects import AtomicSimpleCPU, O3CPU  #add
from core import *

valid_configs = [VerbatimCPU, TunedCPU, UnconstrainedCPU]
valid_configs = {cls.__name__[:-3]:cls for cls in valid_configs}

parser = argparse.ArgumentParser()
parser.add_argument('config', choices = valid_configs.keys())
parser.add_argument('binary', type = str, help = "Path to binary to run")
parser.add_argument('action', choices=[
	'create_by_fixed_ticks',
	'create_by_fixed_insts',
	'restore',
	'restore_and_switch',
	'switch_repeatedly',
	'simpoint_profile',
	'take_simpoint_checkpoints',
	'restore_simpoint']) #added by zjj
parser.add_argument('command',choices=[
  '400',
  '401',
  '403',
  '429',
  '445',
  '456',
  '458',
  '462',
  '464',
  '471',
  '473',
  '483']) #added by sgh

parser.add_argument('--bmk_input', type = str, required=False, help = 'the input of benchmark') #added by sgh
  


args = parser.parse_args()
action = args.action #added by zjj


class TestSystem(MySystem):
    _CPUModel = valid_configs[args.config]

system = TestSystem()
system.workload = SEWorkload.init_compatible(args.binary)
system.setTestBinary(args.binary, args.command, args.bmk_input) #modified by sgh
#root = Root(full_system = False, system = system)


#m5.instantiate()

########################added by zjj##############################
#######################################
#         System Instantiation        #
#######################################

# Before system instantiation, add an O3CPU as switch_cpu to system if we
# will switch. It should copy key settings from the original cpu
if 'switch' in action:
    switch_cpu = O3CPU(switched_out=True, cpu_id=0)
    switch_cpu.workload = system.cpu.workload
    switch_cpu.clk_domain = system.cpu.clk_domain
    switch_cpu.progress_interval = system.cpu.progress_interval
    switch_cpu.isa = system.cpu.isa

    switch_cpu.createThreads()
    system.switch_cpu = switch_cpu

# Set ckpt_dir if we are restoring from some checkpoint
ckpt_dir = None
m5out = m5.options.outdir
if 'restore' in action:
    ckpt_dir = os.path.join(m5out, 'ckpt.001')
    if not os.path.exists(ckpt_dir):
        print("You haven't create any checkpoint yet! Abort")
        exit(-1)

simpoint_interval = 300000

# Add SimPoint probe to cpu if we will profile for SimPoint
if action == 'simpoint_profile':
    system.cpu.addSimPointProbe(simpoint_interval)

# Add breakpoints if we will create SimPoint checkpoints
if action == 'take_simpoint_checkpoints':
    try:
        with open('/home/shen-gh/Desktop/simpoints.txt') as f: # modified by sgh
            ss = f.readlines()
        with open('/home/shen-gh/Desktop/weights.txt') as f:
            ws = f.readlines()
    except FileNotFoundError:
        print("Either 'm5out/simpoints.txt' or 'm5out/weights.txt' not found")
        exit(-1)

    # Read simpoints and weights
    print('Read simpoints and weights')
    simpoints = []
    for sl, wl in zip(ss, ws):
        s = int(sl.split()[0])
        w = float(wl.split()[0])
        simpoints.append((s, w))

    # Compute start insts
    simpoints.sort()
    simpoint_start_insts = []
    for s, _ in simpoints:
        insts = s * simpoint_interval
        simpoint_start_insts.append(insts)
    system.cpu.simpoint_start_insts = simpoint_start_insts

# Add breakpoints if we will restore SimPoint checkpoints
if action == 'restore_simpoint':
    system.cpu.simpoint_start_insts = [simpoint_interval]

# Instantiate system
root = Root(full_system=False, system=system)
if ckpt_dir is None:
    print('Instantiate')
    m5.instantiate()
else:
    print('Restore checkpoint', repr(ckpt_dir))
    m5.instantiate(ckpt_dir)


#######################################
#           Real Simulation           #
#######################################

if action == 'create_by_fixed_ticks':
    interval_ticks = 20000000
    i = 1

    while True:
        print('Simulate for %d ticks' % interval_ticks)
        exit_event = m5.simulate(interval_ticks)
        if exit_event.getCause() != 'simulate() limit reached':
            break

        print('Pause @ tick', m5.curTick())
        print('Create checkpoint', i)
        m5.checkpoint(os.path.join(m5out, 'ckpt.%03d' % i))
        i += 1

elif action == 'create_by_fixed_insts':
    interval_insts = 20000
    tid = 0  # thread id, should be 0 since we have only one thread
    event_str = 'inst stop'  # any unique string is fine
    i = 1

    while True:
        print('Simulate for %d insts' % interval_insts)
        system.cpu.scheduleInstStop(tid, interval_insts, event_str)
        exit_event = m5.simulate()
        if exit_event.getCause() != event_str:
            break

        print('Pause @ tick', m5.curTick())
        print('Create checkpoint', i)
        m5.checkpoint(os.path.join(m5out, 'ckpt.%03d' % i))
        i += 1

elif action == 'restore':
    print('Resume simulation')
    exit_event = m5.simulate()

elif action == 'restore_and_switch':
    print('Warmup for 10000 ticks')
    m5.simulate(10000)

    print('Switch @ tick', m5.curTick())
    switch_cpu_list = [(system.cpu, system.switch_cpu)]
    m5.switchCpus(system, switch_cpu_list)

    print('Simulate on switch_cpu')
    exit_event = m5.simulate()

elif action == 'switch_repeatedly':
    interval_insts = 10000
    switch_cpu_list = [(system.cpu, system.switch_cpu)]
    tid = 0
    event_str = 'inst stop'

    while True:
        print('Simulate for %d insts' % interval_insts)
        curr_cpu = switch_cpu_list[0][0]
        curr_cpu.scheduleInstStop(tid, interval_insts, event_str)
        exit_event = m5.simulate()
        if exit_event.getCause() != event_str:
            break

        print('Pause @ tick', m5.curTick())
        print('Switch %s -> %s' % (switch_cpu_list[0]))
        m5.switchCpus(system, switch_cpu_list)

        # Reverse each CPU pair in switch_cpu_list
        switch_cpu_list = [(p[1], p[0]) for p in switch_cpu_list]

elif action == 'simpoint_profile':
    print('Simulate and profile for SimPoint')
    exit_event = m5.simulate()

elif action == 'take_simpoint_checkpoints':
    for i, (s, w) in enumerate(simpoints, 1):
        print('Simulate until next simpoint entry')
        exit_event = m5.simulate()

        if exit_event.getCause() == 'simpoint starting point found':
            print('Take simpoint %d @ tick %d' % (s, m5.curTick()))
            ckpt_dir = os.path.join(m5out, 'ckpt.%03d' % i)
            m5.checkpoint(ckpt_dir)
            with open(os.path.join(ckpt_dir, 'weight.txt'), 'w') as f:
                f.write(str(w))

    print('Simulate to end')
    exit_event = m5.simulate()

elif action == 'restore_simpoint':
    print('Simulate simpoint for %d insts' % simpoint_interval)
    exit_event = m5.simulate()

print('Exiting @ tick %d because %s' % (m5.curTick(), exit_event.getCause()))
#################################################################


#exit_event = m5.simulate()

if exit_event.getCause() != 'exiting with last active thread context':
    print("Benchmark failed with bad exit cause.")
    print(exit_event.getCause())
    exit(1)
if exit_event.getCode() != 0:
    print("Benchmark failed with bad exit code.")
    print("Exit code {}".format(exit_event.getCode()))
    exit(1)
