# 1. Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
# Аргументом функции является список, в котором каждый сетевой узел должен быть представлен именем хоста или
# ip-адресом. В функции необходимо перебирать ip-адреса и проверять их доступность с выводом соответствующего
# сообщения («Узел доступен», «Узел недоступен»). При этом ip-адрес сетевого узла должен создаваться с помощью
# функции ip_address().
# 2. Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона.
# Меняться должен только последний октет каждого адреса. По результатам проверки должно выводиться соответствующее
# сообщение.
# 3. Написать функцию host_range_ping_tab(), возможности которой основаны на функции из примера 2. Но в
# данном случае результат должен быть итоговым по всем ip-адресам, представленным в табличном формате (использовать
# модуль tabulate). Таблица должна состоять из двух колонок и выглядеть примерно так:
# Reachable
# 10.0.0.1
# 10.0.0.2
# Unreachable
#
# 10.0.0.3
# 10.0.0.4

import subprocess
from ipaddress import ip_address
from itertools import zip_longest

from tabulate import tabulate


def host_ping(addresses):
    for address in addresses:
        try:
            host = ip_address(address)
        except ValueError:
            print(f'{address}: Неверный формат адреса')
            continue
        with subprocess.Popen(f"ping {host} -c 1", shell=True, stdout=subprocess.PIPE) as p:
            out = p.stdout.read().decode('utf-8')
            if 'Unreachable' in out:
                print(f'{host}: Узел недоступен')
            else:
                print(f'{host}: Узел доступен')


def host_range_ping(first_address, last_address):
    try:
        first_address = ip_address(first_address)
        last_address = ip_address(last_address)
    except ValueError:
        print(f'{first_address}, {last_address}: Неверный формат адреса')
        return
    addresses = []
    while last_address > first_address:
        first_address = first_address + 1
        addresses.append(first_address)

    host_ping(addresses)


def host_range_ping_tab(addresses):
    unreachable = []
    reachable = []
    for address in addresses:
        try:
            host = ip_address(address)
        except ValueError:
            print(f'{address}: Неверный формат адреса')
            continue
        with subprocess.Popen(f"ping {host} -c 1", shell=True, stdout=subprocess.PIPE) as p:
            out = p.stdout.read().decode('utf-8')
            if 'Unreachable' in out:
                unreachable.append(str(host))
            else:
                reachable.append(str(host))
    result = zip_longest(reachable, unreachable)
    print(tabulate([['Reachable', 'Unreachable'], *result], headers="firstrow"))


if __name__ == '__main__':
    hosts = ['192.168.1.1', '192.168.1.2', '192.168.1.3', '192.168.1.4', '192.168.1.222', ]
    host_ping(hosts)
    host_range_ping('192.168.1.1', '192.168.1.3')
    host_range_ping_tab(hosts)
