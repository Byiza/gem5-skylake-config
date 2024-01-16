import subprocess
import multiprocessing
import os

TARGET_BENCHMARKS = ["401.bzip2","429.mcf","445.gobmk","456.hmmer","458.sjeng",
        "462.libquantum","464.h264ref","471.omnetpp","473.astar"]
NUM_THREADS =  20#max threads=28
bzip2_input =["input.program"] #,"dryer.jpg"]
gobmk_input =["capture.tst"] #,"connect.tst","connection.tst","connection_rot.tst","connect_rot.tst","cutstone.tst","dniwog.tst"]
def run_cmd_using_shell(cmd):
  '''
  function:
  '''
  print('Running cmd:', cmd)
  subprocess.call(cmd, shell=True)


def run_parallel_commands_local(cmds, num_threads=None):
  '''
  function:
  '''
  with multiprocessing.Pool(num_threads) as pool:
    pool.map(run_cmd_using_shell, cmds)

def main(): 
   
   cmds=[]
   for benchmark in TARGET_BENCHMARKS:
        run_se = '~/Desktop/gem5-skylake-config/gem5-configs/system/run-se.py'
        gem5opt ='~/Desktop/gem5/build/X86/gem5.opt'
        check_point =benchmark.split(".")[0]
        processor_type = 'Tuned'
        output_file ='./m5out/checkpoint.log'
        dir_name ='./{}/m5out'.format(benchmark)
        os.makedirs(dir_name,exist_ok=True)
        if (benchmark=="401.bzip2"):
           for input in bzip2_input:
              cmds.append('cd {} && {} {} {} {} take_simpoint_checkpoints {} --bmk_input {} >{} 2>&1'.format(benchmark,gem5opt,run_se,processor_type,benchmark,check_point,input,output_file))
        elif (benchmark=="445.gobmk"):
           for input in gobmk_input:
              cmds.append('cd {} && {} {} {} {} take_simpoint_checkpoints {} --bmk_input {} >{} 2>&1'.format(benchmark,gem5opt,run_se,processor_type,benchmark,check_point,input,output_file))
        else:
           cmds.append('cd {} && {} {} {} {} take_simpoint_checkpoints {} >{} 2>&1'.format(benchmark,gem5opt,run_se,processor_type,benchmark,check_point,output_file))
   run_parallel_commands_local(cmds, NUM_THREADS)
      
    


if __name__ == '__main__':
    main()
