import pexpect
from passwords import get_network_device_password

LOGIN, PASSWORD, ENABLE_PASSWORD = get_network_device_password()

t = None
def connect_cisco_router(ip_device):
    global t
    t = pexpect.spawn(f'ssh {LOGIN}@{ip_device}', timeout=120)
    i = t.expect([pexpect.TIMEOUT, pexpect.EOF, '[Pp]assword','\(yes\/no\)'])
    if i == 0:
        print(f"* {ip_device} - Недоступен")
        return False
    elif i == 1:
        print(f"* {ip_device} - Необходимо почистить ключ ssh")
        return False
    if i == 3:
        t.sendline("yes")
        i = t.expect(['[Pp]assword'])
    t.sendline(PASSWORD)
    i = t.expect(['[Pp]assword', '>', '#'])
    if i == 0:
        print("Неверный пароль!")
        #t.sendline('')
        #i = t.expect(['[Pp]assword', '>', '#'])
        if i == 0:
            print("Я не знаю пароль")
            return False
    if i == 1:
        t.sendline("enable")
        if t.expect(['[Pp]assword', '#' ]) == 0:
            t.sendline(ENABLE_PASSWORD)
            if t.expect(['[Pp]assword', '#']) == 0:
                print("Я не знаю ENABLE пароль")
                return False
    t.sendline('terminal length 0')
    t.expect('#')
    return t


def command_send(command):
    global t
    t.sendline(command)
    t.expect('#')
    lines = str(t.before)
    lines = lines.replace('\\r\\n\\r\\n', '\\r\\n').replace('\\r\\n', '\n')
    arr = lines.split('\n')
    arr[0] = command
    arr.pop(-1)
    lines = '\n'.join(arr)
    return lines




