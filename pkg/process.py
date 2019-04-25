import subprocess
import Queue
import threading
import time
import sys


def Popen(*args, **kwargs):
    q = Queue.Queue()
    done = []

    def receiver_thread():
        buff = []
        last_output_time = time.time()
        while not (done and q.empty()):
            cur_time = time.time()
            if last_output_time < cur_time - 0.01:
                sys.stdout.write(''.join(buff).replace('\r', ''))
                last_output_time = cur_time
                buff[:] = []
            try:
                item = q.get(timeout=0.01)
            except Queue.Empty:
                continue
            buff.append(item)
            q.task_done()
        sys.stdout.write(''.join(buff).replace('\r', ''))

    def reader_thread():
        while True:
            c = p.stdout.read(1)
            if not c:
                done.append(True)
                break
            q.put(c)

    if 'stdout' not in kwargs:
        kwargs['stdout'] = subprocess.PIPE
        if 'stderr' not in kwargs:
            kwargs['stderr'] = subprocess.STDOUT

    p = subprocess.Popen(*args, **kwargs)

    t1 = threading.Thread(target=reader_thread)
    t2 = threading.Thread(target=receiver_thread)

    t1.start()
    t2.start()

    return p


def system(cmd):
    return Popen(cmd, shell=True).wait()
