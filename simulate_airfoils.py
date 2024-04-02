import gc
import os
import sys
import numpy
import threading
import subprocess
import numpy as np
import concurrent.futures
from queue import Queue, Empty

# XFOIL parameters
ALFA = 2.7                     # angle of attack
MACH = 0.5                     # speed (617.4km/h)
REYNOLDS = 1000000             # Reynolds Number

xfoil_iterations = 100

# using UNIX, this will assume you are using xfoil in /bin - alternatively use /path/to/venv/bin
# using WSL you can download the xfoil.exe and create a systemlink or specify the filepath
xfoil_path = r"xfoil"


def xfoil(iterations):
    """Executes xfoil with given parameters, implements Thread counting errors on stdout"""

    print("\nstart xfoil [...]")
      
    n_cores = os.cpu_count()
    executor = concurrent.futures.ProcessPoolExecutor(max_workers=n_cores)

    # Submit tasks to the ThreadPoolExecutor for concurrent execution
    futures = [executor.submit(run_xfoil, i) for i in range(iterations)]

    # Wait for all tasks to complete
    concurrent.futures.wait(futures)

    # Retrieve booleans from futures
    results = [future.result() for future in futures]

    success_indices = []
    for i in range(iterations):
        if results[i]:
            if i not in success_indices:
                success_indices.append(i)

    obj_batch = []
    success_indices_copy = success_indices.copy()
    for index in success_indices_copy:


        # Read lift and drag from Xfoil output
        xfoil_output = numpy.loadtxt(f'airfoil_{index}.log', skiprows=12)
        lift, drag = xfoil_output[1], xfoil_output[2]

        # Output format (adjust the script to your needs by using the corresponding indices)

        #           Lift      Drag
        #   alpha    CL        CD       CDp       CM     Top_Xtr  Bot_Xtr  Top_Itr  Bot_Itr
        # ------ -------- --------- --------- -------- -------- -------- -------- --------


        if lift < 0 or drag < 0:
            if drag < 0: print("\n")
            print(f"{index}: (negative lift or drag) - drag: {drag}")
            if drag < 0: print("\n")
            success_indices.remove(index)
        else:
            obj = calculate_obj(drag, lift)
            if np.isfinite(obj) and not np.isnan(obj):
                obj_batch.append(obj)
            if ~np.isfinite(obj) or np.isnan(obj):
                # this edgecase only occured once upon evaluation
                # of a sobol sample of size 1 000 000
                success_indices.remove(index)

    obj_batch = np.array(obj_batch)
    convergence_errors = iterations - len(success_indices)

    print("[...] finished xfoil\n")

    return convergence_errors, success_indices, numpy.array(obj_batch)


def run_xfoil(index):
    """
    returns:
        True    (for converged airfoils)
        False   (if error occured)
    """
    ON_POSIX = 'posix' in sys.builtin_module_names

    try:
        os.remove(f'airfoil_{index}.log')
    except FileNotFoundError:
        pass

    process = subprocess.Popen(xfoil_path, stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True, close_fds=ON_POSIX, bufsize=1)
    queue = Queue()

    with open(f"airfoil_{index}.dat", 'r') as file:
        line = file.readlines()[2]

    if line == "Invalid Airfoil\n":
        terminate_subprocess(process, index)
        return False

    # start thread to populate queue
    output_thread = threading.Thread(target=populate_queue, args=(process.stdout, queue)) # mysteriously, threads are executed twice (debug in future)
    output_thread.deamon = True # thread dies with the process
    output_thread.start()
    
    # command part
    commands = ''
    commands += command('NORM')
    commands += command('LOAD ' + f'airfoil_{index}' + '.dat')
    commands += command('PANE')  # smooth airfoil to improve convergence
    commands += command('OPER')  # load parameters 
    commands += command('VISC ' + str(REYNOLDS))
    commands += command('MACH ' + str(MACH))
    commands += command('ITER ' + str(xfoil_iterations))
    commands += command('PACC')
    commands += command(f'airfoil_{index}' + '.log')  # output file
    commands += command('')  # no dump file
    commands += command('alfa ' + str(ALFA))
    commands += command(' ')  # escape OPER
    commands += command('quit')

    process.stdin.write(commands)
    process.stdin.flush()
    process.stdin.close()

    is_valid_solution = capture_errors(process=process, queue=queue, i=index)
            
    process.stdout.close()
    process.terminate()

    gc.collect()

    return is_valid_solution


def calculate_obj(drag, lift):
    "Examplatory objective function - maximize upward force while minimizing aerodynamic resistance"

    obj = lift/drag
    return obj


def command(cmd):
    return cmd + '\n'


def capture_errors(process, queue, i):
    """
    Captures & reacts to errors from XFOIL stdout
    
    returns:
        True    (for converged airfoils)
        False   (if error occured)
    """

    error_counter = 0

    while True:
        try:
            line = queue.get(timeout=2.5)
            #print(line.strip())

            if not line: # empty line
                return True

            if "Sequence halted since previous" in line:
                print(f"\n{i}: (sequence halted)")
                terminate_subprocess(process, i)
                return False

            if "TRCHEK2: N2 convergence failed" in line or "PANLST: Side 1, inviscid convergence failed" in line:
                error_counter += 1
                if error_counter >= 2000:
                    print(f"{i}: (convergence failed)")
                    terminate_subprocess(process, i)
                    process.stdout.close()
                    return False

            if "VISCAL:  Convergence failed" in line:
                print(f"{i}: (viscal error)")
                terminate_subprocess(process, i)
                return False
            
        except Empty: # when viscal error occurs, stdout will stop producing output, thus queue.get() will throw an Empty exception, however, viscal errors are *sometimes* not printed to stdout, so it cant always be captured
            print(f"{i}: (queue.Empty)")
            terminate_subprocess(process, i)
            return False


        except ValueError: # queue.get() Raises a ValueError if called more times than there were items placed in the queue.
            print(f"Value Error: {i}")
            return False

    

def populate_queue(stdout, queue):
    """
    XFOIL is interactive, thus readline() blocks. The solution is to
    let another thread handle the XFOIL communication, and communicate
    with that thread using a queue.
       https://stackoverflow.com/questions/375427/a-non-blocking-read-on-a-subprocess-pipe-in-python
       http://eyalarubas.com/python-subproc-nonblock.html
       https://github.com/tmolteno/3d/blob/master/prop/xfoil_2.py
    """
    try:
        for line in iter(stdout.readline, b''): # b'' is empty byte string
            queue.put(line)
            
    except ValueError:
            pass

    stdout.close()


def terminate_subprocess(process, i):

    process.terminate()
    process.stdout.close()
