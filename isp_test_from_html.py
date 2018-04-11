#!/usr/bin/python3.6
import re
from connecting_devices import command_send
from connecting_devices import connect_cisco_router
from passwords import get_ip_address
from passwords import get_service_desc_password
from excel import get_isp_provider
from excel import get_list_object
from excel import exist_object
import time
import cgi

form = cgi.FieldStorage()
hostname = form.getfirst("hostname", False)

if not hostname:
    print("Объект не задан")
    exit()
hostname = str(hostname).strip()
if not exist_object(hostname):
    print("Объект не найден в Network_no_pass")
    exit()
obj = {'name': hostname}
PING_REPEAT = 10
EXT_PING_REPEAT = 100  # Расширенный пинг, используется, если обычный прошел удачно
PING_SIZE = 1400  # Размер отправляемых пакетов
PROVIDER_SPEED = 500000  # Максимально допустимая загрузка канала(Bits),
# после данного значения скрипт будет думать, что канал загружен.
# По идее необходимо сформировать в БД, для кажого провайдера свою скорость и считать среднее значение
MAXIMUM_LOSTS_PACKETS = 3  # Допустимое количество потерянных пакетов. После чего канал считается неработоспособным
MAXIMUM_DELAY = 300  # Допустимая задержка для канала
TRACEROUTE_TTL = 5  # TTL при проверке traceroute
INTERFACE_RATE = 800 # Какая допустимая загрузка канала(Kbit), после которого срабатывает сбор статистики sh ip top talkers

IP_COD_BEELINE, IP_COD_PROSTOR, IP_COD_DOMRU, IP_COD_INET = get_ip_address()
SERVICE_LOGIN, SERVICE_PASS = get_service_desc_password()

# Глобальные переменныеTimeout waiting for output from CGI script
t = None  # Переменная для подключения к оборудованию.
full_text = ''
result = ''
###


def main():
    global t
    global obj
    global full_text
    answer = get_isp_provider(obj['name'])
    obj_name, ip_addr, address, billing = get_list_object(obj['name'])
    t = connect_cisco_router(ip_addr)
    if t == False:
        print(f'{obj_name} - {ip_addr} - Недоступен')
        return False
    full_text += f'<b>Начинаем проверку каналов на объекте: {obj_name} по адресу - {address}</b>\n\n'
    print(full_text)
    full_text = ''
    for li in answer:
        global EXT_PING_REPEAT
        global result
        full_text = ''
        provider, _, ce, pe = li

        if 'beeline' in provider.lower():
            ip_cod = IP_COD_BEELINE
            full_text += 'ID канала: ' + billing + '\n'
        elif 'prostor' in provider.lower():
            ip_cod = IP_COD_PROSTOR
        elif 'domru' in provider.lower():
            ip_cod = IP_COD_DOMRU
        else:
            ip_cod = IP_COD_INET

        full_text += '#' * 100 + '\n\n'
        full_text += f'<b>Проверка из магазина до шлюза провайдера - {provider}:</b>\n\n'
        i, text, *_ = test_ping(f'ping {pe} repeat {PING_REPEAT} source {ce} size {PING_SIZE} timeout 1')
        if i == None:
            continue
        if i == False:
            full_text += f'<details><summary>ping {pe} repeat {PING_REPEAT} source {ce} size {PING_SIZE} timeout 1</summary>\n'
            full_text += f"{obj['name']}#" + text + '\n</details>\n<font color="red">Шлюз провайдера недоступен!</font>\n'
            result = 'Result: Шлюз провайдера недоступен!'
            traceroute(f'traceroute ip {ip_cod} source {ce} timeout 1 ttl 1 {TRACEROUTE_TTL} numeric')
            full_text += '#' * 100 + '\n\n'
            print(full_text)
            continue
        i, rate_input, rate_output = get_int_load(provider, PROVIDER_SPEED)
        i, text, avr, lose_percent, *_ = test_ping(f'ping {pe} repeat {EXT_PING_REPEAT} source {ce} size {PING_SIZE} timeout 1')
        full_text += f'<details><summary>ping {pe} repeat {EXT_PING_REPEAT} source {ce} size {PING_SIZE} timeout 1</summary>\n'
        full_text += f"{obj['name']}#" + text + '\n</details>\n<font color="green">Канал иправно работает!</font>\n'
        full_text += f'\n\n<b>Проверка доступности канала до нашего ЦОДа через {provider}:</b>\n\n'
        i, text, avr, success_packet, all_packet =  test_to_cod(ip_cod, ce)

        if not i:
            full_text += f'<details><summary>ping {ip_cod} repeat {PING_REPEAT} source {ce} size {PING_SIZE} timeout 1</summary>\n'
            full_text += f"{obj['name']}#" + text + '\n</details>\n<font color="red">Нет доступности до нашего ЦОДа!</font>\n'
            traceroute(f'traceroute ip {ip_cod} source {ce} timeout 1 ttl 1 {TRACEROUTE_TTL} numeric')
            full_text += '#' * 100 + '\n\n'
            print(full_text)
            continue

        if (int(avr) < 300) and (int(success_packet) > EXT_PING_REPEAT - 30):
            EXT_PING_REPEAT = 200
            i, text, avr, success_packet, all_packet = test_to_cod(ip_cod, ce)
            full_text += f'<details><summary>ping {ip_cod} repeat {EXT_PING_REPEAT} source {ce} size {PING_SIZE} timeout 1</summary>\n'
            full_text += f"{obj['name']}#" + text + '\n</details>\n'
            EXT_PING_REPEAT = 100
        else:
            full_text += f'<details><summary>ping {ip_cod} repeat {EXT_PING_REPEAT} source {ce} size {PING_SIZE} timeout 1</summary>\n'
            full_text += f"{obj['name']}#" + text + '\n</details>\n'

        number_lost_packet = int(all_packet) - int(success_packet)
        if number_lost_packet >= MAXIMUM_LOSTS_PACKETS:
            result = f'Result: Замечены потери трафика. Количество потеряных пакетов {number_lost_packet}'
            full_text += f'<font color="red">Замечены потери трафика. Количество потеряных пакетов {number_lost_packet}</font>\n'
            full_text += 'При этом загрузка канала составляет:\nInput: {:.2f} Kbit'.format(rate_input / 1024)
            full_text += '\nOutput: {:.2f} Kbit\n'.format(rate_output / 1024)
        elif int(avr) > MAXIMUM_DELAY:
            result = f'Result: Слишком большие задержки. Задержки составляют {avr}'
            full_text +=  f'<font color="red">Слишком большие задержки. Задержка составляет {avr}</font>\n'
            full_text += 'При этом загрузка канала составляет:\nInput: {:.2f} Kbit'.format(rate_input / 1024)
            full_text += '\nOutput: {:.2f} Kbit\n'.format(rate_output / 1024)
        else:
            full_text += '<font color="green">Канал иправно работает!</font>\n'
        traceroute(f'traceroute ip {ip_cod} source {ce} timeout 1 ttl 1 {TRACEROUTE_TTL} numeric')
        full_text += '#' * 100 + '\n\n'
        print(full_text)

    full_text = ''
    out = command_send(f'sh ip int brief | i {ip_addr}')
    match = re.search('(.+Ethernet.+)\s+\d+\.\d+\.\d+\.\d+', out)
    obj['int'] = match.group(1).strip()
    out = command_send(f'sh int {obj["int"]}')
    obj['show_interface'] = out
    match = re.search('input rate (\d+) ', obj['show_interface'])
    obj['int_input'] = int(match.group(1))
    match = re.search('output rate (\d+) ', obj['show_interface'])
    obj['int_output'] = int(match.group(1))
    out = command_send('sh ip int brief')
    print(f'<details><summary>Показать статус интерфейсов sh ip int brief</summary>{out}</details>', end='')
    out = command_send('sh ip route')
    print(f'<details><summary>Посмотреть таблицу маршрутизации sh ip route </summary>{out}</details>', end='')
    out = command_send('sh ip arp')
    print(f'<details><summary>Посмотреть ARP таблицу sh ip arp </summary>{out}</details>', end='')
    out = command_send('sh ip dhcp bindin')
    print(f'<details><summary>Посмотреть таблицу выданных ip адресов sh ip dhcp bindings </summary>{out}\n</details>', end='')

    print('<details><summary>Посмотреть сатитстику интерфейса sh int', obj['int'], '</summary>', obj['show_interface'], '</details>\n\n\n')
    obj['int_input'] = obj['int_input'] / 1024
    obj['int_output'] = obj['int_output'] / 1024
    full_text += '<b>Загрузка канала составляет:</b>\nInput: {:.2f} Kbit'.format(obj['int_input'])
    full_text += '\nOutput: {:.2f} Kbit\n'.format(obj['int_output'])
    print(full_text)
    if obj['int_input'] > INTERFACE_RATE or obj['int_output'] > INTERFACE_RATE:
        print('</b>Внимание! канал загружен</b>')
        top_talkers()


def top_talkers():
    command_send("conf t")
    command_send("int " + obj['int'])
    command_send("ip flow ingress")
    command_send("ip flow egress")
    command_send("exit")
    command_send("ip flow-top-talkers")
    command_send("top 10")
    command_send("sort-by bytes")
    command_send("exit")
    time.sleep(10)
    out = command_send("do sh ip flow top-talkers")
    print("<details><summary>Показать Top 10, кто генерирует траффик:</summary>", out, "</details>")
    command_send("no ip flow-top-talkers")
    command_send("int " + obj['int'])
    command_send("no ip flow ingress")
    command_send("no ip flow egress")
    command_send("exit")
    command_send("exit")


def test_to_cod(cod_ip, ce):
    global full_text
    global result
    i, out, avr, success_packet, all_packet = test_ping(f'ping {cod_ip} repeat {PING_REPEAT} source {ce} size {PING_SIZE} timeout 1')
    if i == False:
        result = 'Result: Нет доступности до нашего ЦОДа!'
        return [i, out, avr, success_packet, all_packet]
    i, out, avr, success_packet, all_packet = test_ping(f'ping {cod_ip} repeat {EXT_PING_REPEAT} source {ce} size {PING_SIZE} timeout 1')
    return [i, out, avr, success_packet, all_packet]


def test_ping(test):
    global t
    out = command_send(test)
    match = re.search('\d+\/(\d+)\/\d+', out)
    match_2 = re.search('percent \((\d+)\/(\d+)\)', out)
    match_3 = re.search('Invalid', out)
    avr = None
    if match_3 != None:
        return [None, 0, 0, 0, 0]
    if not match:
        return [False, out, avr, match_2.group(1), match_2.group(2)]
    avr = match.group(1)
    return [True, out, avr, match_2.group(1), match_2.group(2)]


def traceroute(test):
    global t
    global full_text
    full_text += f'\n<details><summary>{test}</summary>'
    out = command_send(test)
    full_text += out
    full_text += '</details>\n'
    return out


# Возвращает FALSE, если загрузки канала нет.
def get_int_load(provider,speed):
    provider = provider.lower()
    print(provider)
    if 'beeline' in provider:
        int_tun_1 = command_send('show int tun17')
        int_tun_2 = command_send('show int tun27')
    elif 'domru' in provider:
        int_tun_1 = command_send('show int tun41')
        int_tun_2 = command_send('show int tun51')
    elif 'prostor' in provider:
        int_tun_1 = command_send('show int tun61')
        int_tun_2 = command_send('show int tun71')
    else:
        int_tun_1 = command_send('show int tun1')
        int_tun_2 = command_send('show int tun2')
    match = re.search('input rate (\d+) ', int_tun_1)
    int_tun_1_input = int(match.group(1))
    match = re.search('output rate (\d+) ', int_tun_1)
    int_tun_1_output = int(match.group(1))
    match = re.search('input rate (\d+) ', int_tun_2)
    int_tun_2_input = int(match.group(1))
    match = re.search('output rate (\d+) ', int_tun_2)
    int_tun_2_output = int(match.group(1))
    if (int_tun_1_input > speed or int_tun_1_output > speed or int_tun_2_input > speed or int_tun_2_output > speed):
        return [True, int_tun_1_input + int_tun_2_input, int_tun_1_output + int_tun_2_output]
    return [False, int_tun_1_input + int_tun_2_input, int_tun_1_output + int_tun_2_output]

print("Content-type: text/html")
print()

print("<html>")
print("<head>")
print('<meta charset="utf-8">')
print("</head>")
print("<body>")
print("<pre>")

main()
print("</pre>")
print("</body>")
print("</html>")
