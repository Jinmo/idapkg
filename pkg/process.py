import Queue
import threading
import time
import sys

from subprocess import Popen as _Popen, PIPE, STDOUT


def Popen(*args, **kwargs):
    if 'stdout' not in kwargs:
        kwargs['stdout'] = PIPE
        if 'stderr' not in kwargs:
            kwargs['stderr'] = STDOUT

    else:
        return _Popen(*args, **kwargs)

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

    p = _Popen(*args, **kwargs)

    t1 = threading.Thread(target=reader_thread)
    t2 = threading.Thread(target=receiver_thread)

    t1.start()
    t2.start()

    p.threads = t1, t2

    return p


def system(cmd):
    p = Popen(cmd, shell=True)
    # trigger trace callback to prevent hang
    t1, t2 = p.threads
    TIMEOUT = 0.01
    while t1.is_alive() and t2.is_alive():
        t1.join(TIMEOUT)
        t2.join(TIMEOUT)
    return p.wait()


if __name__ == '__main__':
    print system('pip install requests')
