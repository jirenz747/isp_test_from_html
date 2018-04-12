import xlrd

# Статические строковые индексы. Жесткая привязка. Если добавляется столбец, то также необходимо заново провести индексацию

OBJECT_NAME = 4
OBJECT_ADDRESS = 3
OBJECT_FULL_NAME = 0
OBJECT_NETWORK = 7
OBJECT_STATUS = 1
OBJECT_ISP1 = 8
OBJECT_ISP1_NETWORK = 9
OBJECT_ISP1_CE = 10
OBJECT_ISP1_PE = 11
OBJECT_ISP2 = 13
OBJECT_ISP2_NETWORK = 14
OBJECT_ISP2_CE = 15
OBJECT_ISP2_PE = 16
OBJECT_ISP_BILLING = 24
#DIR = '\\'

obj = {}
workbook = xlrd.open_workbook(f'Network_no_pass.xlsx')
sheet = workbook.sheet_by_index(0)

#Функция проверяет существование объекта
def exist_object(object):
    object = str(object).replace('-gw', '')
    if obj.get(object) is None:
        return False
    return True


def get_isp_provider(object):
    l = []
    if not obj[object].get('isp1') is None:
        l = [list(obj[object]['isp1'].values())]
    if not obj[object].get('isp2') is None:
        l = l + [list(obj[object]['isp2'].values())]
    return l


# Функция которая возвращает ISP1 или ISP2 для словаря
def find_provider(object, provider):
    if not exist_object(object):
        return False
    if not obj[object].get('isp1') is None:
        if provider.lower() in str(obj[object]['isp1'].get('name')).lower():
            return 'isp1'
    if not obj[object].get('isp2') is None:
        if provider.lower() in str(obj[object]['isp2'].get('name')).lower():
            return 'isp2'
    return False

# Функция которя проверяет существование провайдера
def exist_provider(object, provider):
    if find_provider(object, provider) == 'isp1':
        return True
    if find_provider(object, provider) == 'isp2':
        return True
    print("Объект не найден в Файле Network no pass")
    return False

# Функция возврачает список CE,PE,NAME,Network для данного провайдера иначе возвращает False.
def get_list_provider(object, provider):
    prov = find_provider(object, provider)
    if prov:
        return list(obj[object][prov].values())
    else:
        return False

# Получить список
def get_list_provider_ip(object, ip):
    object = str(object).replace('-gw', '')
    if not exist_object(object):
        return False
    if not obj[object].get('isp1') is None:
        if obj[object]['isp1'].get('ce') in ip:
            return list(obj[object]['isp1'].values())
    if not obj[object].get('isp2') is None:
        if obj[object]['isp2'].get('ce') in ip:
            return list(obj[object]['isp2'].values())
    return False

# Функция возвращает список параметров для объекта
def get_list_object(object):
    object = str(object).replace('-gw', '')
    if not exist_object(object):
        return False
    if str(obj[object]['billing']).replace('.','').isdigit():
        obj[object]['billing'] = str(int(obj[object]['billing']))
    return [obj[object]['name'], str(obj[object]['network']).replace('0/24','254'), str(obj[object]['address']).replace('"', ''), obj[object]['billing']]


#print(sheet.cell(2, OBJECT_FULL_NAME).value)
for i in range(250):
    if sheet.cell(i, OBJECT_FULL_NAME).value != '':
        if 'открыт' in str(sheet.cell(i, OBJECT_STATUS).value).lower():
            obj[sheet.cell(i, OBJECT_NAME).value] = {
                'name': sheet.cell(i, OBJECT_FULL_NAME).value,
                'address': sheet.cell(i, OBJECT_ADDRESS).value,
                'network': sheet.cell(i, OBJECT_NETWORK).value,
                'billing': sheet.cell(i, OBJECT_ISP_BILLING).value
            }
            if sheet.cell(i, OBJECT_ISP1).value != '':
                obj[sheet.cell(i, OBJECT_NAME).value]['isp1'] ={
                    'name': sheet.cell(i, OBJECT_ISP1).value,
                    'network': sheet.cell(i, OBJECT_ISP1_NETWORK).value,
                    'ce': str(sheet.cell(i, OBJECT_ISP1_CE).value).strip(),
                    'pe':  str(sheet.cell(i, OBJECT_ISP1_PE).value).strip()
                }
            if sheet.cell(i, OBJECT_ISP2).value != '':
                obj[sheet.cell(i, OBJECT_NAME).value]['isp2'] = {
                    'name': sheet.cell(i, OBJECT_ISP2).value,
                    'network': sheet.cell(i, OBJECT_ISP2_NETWORK).value,
                    'ce': str(sheet.cell(i, OBJECT_ISP2_CE).value).strip(),
                    'pe':  str(sheet.cell(i, OBJECT_ISP2_PE).value).strip()
                }
        else:
            pass
            #print(sheet.cell(i, OBJECT_FULL_NAME).value, " - Магазин закрыт, или на реконструкции")


# for key, values in obj.items():
#     print(key, list(values))

#print(obj['mos2']['isp2'].get('name'))
#print(get_list_provider("orl1", "prostor"))
#print(get_list_provider_ip("ufa5-gw", '172.16.23.137'))
#print(get_list_object('vol4'))
#print(get_isp_provider('ufa5'))

