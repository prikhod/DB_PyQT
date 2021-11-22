import os
import signal
import subprocess
from time import sleep

PROCESS = []

while True:
    ACTION = input('Выберите действие: q - выход, '
                   's - запустить сервер и клиенты, x - закрыть все окна: ')

    if ACTION == 'q':
        print(PROCESS)
        break
    elif ACTION == 's':
        PROCESS.append(subprocess.Popen(['gnome-terminal', '--', 'python3', 'server.py']))
        sleep(1)
        for i in range(1):
            PROCESS.append(subprocess.Popen(['gnome-terminal', '--', 'python3', 'client.py', '-m', 'send']))
        for i in range(1):
            PROCESS.append(subprocess.Popen(['gnome-terminal', '--', 'python3', 'client.py', '-m', 'listen']))
    elif ACTION == 'x':
        while PROCESS:
            VICTIM = PROCESS.pop()
            os.killpg(os.getpgid(VICTIM.pid), signal.SIGTERM)
