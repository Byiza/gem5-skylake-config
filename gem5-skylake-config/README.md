# gem5-skylake-config
gem5-skylake-config配置的时候存在问题，因此修复bug后的新版本放置在此处

1.目前测试了hello world

gem5/build/X86/gem5.opt ./gem5-skylake-config/gem5-configs/system/run-se.py Tuned gem5/tests/test-progs/hello/bin/x86/linux/hello

2.测试了spec2006

对setTestBinary的cmd操作提供了option，对于只有一种输入的benchmark，运行命令以429.mcf为例：
```
~/Desktop/gem5/build/X86/gem5.opt ~/Desktop/gem5-skylake-config/gem5-configs/system/run-se.py Tuned 429.mcf take_simpoint_checkpoints 429 > ./m5out/checkpoint.log 2>&1
```

对于有多种输入的benchmark，运行命令以445.gobmk为例：(即多了--bmk_input capture.tst输入选项)
```
~/Desktop/gem5/build/X86/gem5.opt ~/Desktop/gem5-skylake-config/gem5-configs/system/run-se.py Tuned 445.gobmk take_simpoint_checkpoints 445 --bmk_input capture.tst > ./m5out/checkpoint.log 2>&1
```

- 修改了simpoint.txt、weights.txt的位置

用atomic cpu生成simpoint.bb.gz后，用simpoint工具生成weights，在并行执行过程中不在重复生成，因此将其放到了公共文件夹下（如Desktop），脚本中暂时用的是绝对路径，因此运行时注意修改！

- 并行运行脚本run_spec2006_ljz.py

将run_spec2006_ljz.py放在_results/speccpu_2006/路径下，并在该路径下运行python3 ./run_spec2006_ljz.py

- 说明

还未check哪些benchmark能完全跑完，暂时能确定跑不通的spec2006 benchmark有：400、403、471、483，报的错误均为segment fault。