"""
Both method redirects stdout to IDA Pro's console.
"""
from __future__ import print_function

import sys
import threading
import time
from subprocess import Popen as _Popen, PIPE, STDOUT

from PyQt5.QtCore import QCoreApplication

if sys.version_info.major == 3:
    import queue as Queue
else:
    import Queue


class Popen(_Popen):
    """
    Subclass of :py:meth:`subprocess.Popen` that
    if stdout is not given, it'll redirect stdout to messages window.
    """

    def __init__(self, *args, **kwargs):
        if 'stdout' not in kwargs:
            kwargs['stdout'] = PIPE
            if 'stderr' not in kwargs:
                kwargs['stderr'] = STDOUT

            queue = Queue.Queue()
            done = []

            # Now launch the process
            super(Popen, self).__init__(*args, **kwargs)

            t_reader = threading.Thread(
                target=self._reader, args=(done, queue,))
            t_receiver = threading.Thread(
                target=self._receiver, args=(done, queue,))

            t_reader.start()
            t_receiver.start()

            self.threads = t_reader, t_receiver
        else:
            # No need to do anything
            super(Popen, self).__init__(*args, **kwargs)

    @staticmethod
    def _receiver(done, queue):
        buff = []
        last_output_time = time.time()
        stdout = getattr(sys.stdout, 'buffer', sys.stdout)
        while not (done and queue.empty()):
            cur_time = time.time()
            if last_output_time < cur_time - 0.01:
                stdout.write(b''.join(buff).replace(b'\r', b''))
                last_output_time = cur_time
                buff[:] = []
            try:
                item = queue.get(timeout=0.01)
            except Queue.Empty:
                continue
            buff.append(item)
            queue.task_done()
        stdout.write(b''.join(buff).replace(b'\r', b''))

    def _reader(self, done, queue):
        while True:
            byte = self.stdout.read(1)
            if not byte:
                done.append(True)
                break
            queue.put(byte)


def system(cmd):
    """
    Wrapper around :py:meth:`os.system`, except that output will be redirected to messages window.

    :param cmd: Command to execute.
    :return: exit status.
    :rtype: int
    """
    process = Popen(cmd, shell=True)

    # call processEvents() to prevent hang
    timeout = 0.01
    while all(thread.is_alive() for thread in process.threads):
        for thread in process.threads:
            thread.join(timeout)
        QCoreApplication.processEvents()

    return process.wait()


if __name__ == '__main__':
    print(system('pip install requests'))
