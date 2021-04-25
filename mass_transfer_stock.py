import csv
import pynetbox
import metod
from settings import token, my_id
# меняет имя инвентарнику и перемещает его в нужную стойку (серверы кроме фатов)


option = ['1. смонтировать в стойки (и фаты тоже)',
    '2. переместить между складами',
    '3. вернуть на склад',
    '4. заменить платформу',
    '5. смонтировать коммутаторы в стойки',
    '6. метка -> хост -> серийник',
    '7. хост -> метка -> серийник (+фаты +свичи)',
    '9. править данные хосту (свичи)',
    '101. править имя хосту rename_host(reader)',
    '121. жоско править серийник метке',
    '10. переименовать хост ноды толстяка node_rename(reader)']

for x in option:
    print(f"\t{x}")

answer = input('\nответ: ').strip()

nb = pynetbox.api('https://netbox.mvk.com', token=token)

def node_rename(reader):
    for line in reader:
        hostname_x = hostname(line['name'].strip())
        temp_x = nb.dcim.devices.get(name=hostname_x)
        if temp_x is None:
            print(f"{hostname_x}\tне найден")
        else:
            f_unit = first_unit(temp_x.parent_device.name)
            node = int(temp_x.parent_device.device_bay.name[-1])
            hostname_y = f"{hostname_x[0:3]}{temp_x.parent_device.name[-6:-3]}{str(int(temp_x.parent_device.name[-3:])-f_unit+(node-1))}"
            # print(hostname_y)
            comment = line['comments'].strip() + ' // ' +temp_x.comments
            temp_y = nb.dcim.devices.get(name=hostname_y)
            if temp_y is None:
                temp_x.update({
                    'name': hostname_y,
                    'comments': comment
                })
                print(f"{hostname_x}\t{hostname_y}\t{temp_x.parent_device.name}")
            else:
                print(f"{hostname_x}\t{hostname_y}\tуже существует")

def rename_host(reader):
    for line in reader:
        hostname_x = line['name'].strip()
        temp_x = nb.dcim.devices.get(name=hostname_x)
        if temp_x is None:
            print(f"{hostname_x}\tне найден")
        else:
            hostname_y = hostname(hostname_x)
            comment = line['comments'].strip() + ' // ' +temp_x.comments
            temp_y = nb.dcim.devices.get(name=hostname_y)
            if temp_y is None:
                temp_x.update({
                    'name': hostname_y,
                    'comments': comment
                })
                print(f"{hostname_x}\t{hostname_y}\t{str(temp_x.parent_device)}")
            else:
                print(f"{hostname_x}\t{hostname_y}\tуже существует")

def csv_dict_reader(file_obj):
    fieldnames = ['name','asset_tag','serial', 'face', 'comments','asset_tag2', 'cf_id_mac', 'position']
    reader = csv.DictReader(file_obj, fieldnames=fieldnames, delimiter='\t')
    next(reader, None)
    if answer == '1' or answer == '5':
        sap_on_stock(reader, answer)
    elif answer == '2':
        from_stock_to_stock(reader)
    elif answer == '3':
        from_rack_to_stock(reader)
    elif answer == '4':
        swap_sap_id(reader)
    elif answer == '6':
        show_sap_sn(reader)
    elif answer == '7':
        show_host_sap_sn(reader)
    elif answer == '9':
        metod.set_data_2_host(reader, nb)
    elif answer == '10':
        node_rename(reader)
    elif answer == '101':
        rename_host(reader)
    elif answer == '121':
        metod.hard_set_sn_2_sap(reader, nb)

def sap_on_stock(reader, answer):
    for line in reader:
        temp_x = nb.dcim.devices.get(asset_tag=line['asset_tag'].strip())
        if temp_x is None:
            print(line['asset_tag'].strip() + ' --> метки нет в базе')
        elif 'stock' in str(temp_x.site).lower():
            if answer == '1':
                from_stock_to_rack(line)
            elif answer == '5':
                from_stock_to_rack_4_switch(line)
        elif 'stock' not in str(temp_x.site).lower():
            print(line['asset_tag'].strip() + ' не на складе ' + str(temp_x.name))

def hostname(host): # добавляет префикс хосту
    if host[-6]=='5' or host[-6]=='6':
        return 'eva' + host[-6:]
    elif host[-6]=='2':
        return 'cvt' + host[-6:]
    elif host[-6]=='8':
        return 'sdn' + host[-6:]
    else:
        return host

def site(host): # определяем id сайта по хосту
    if '-' in host:
        site = str(nb.dcim.racks.get(name=host[-4:]).site).lower()
    else:
        site = str(nb.dcim.racks.get(name=host[-6:-2]).site).lower()
    return nb.dcim.sites.get(slug=site).id

def first_unit(host): # определяет позицию в стойке
    rack_group = str(nb.dcim.racks.get(name=host[-6:-2]).group).lower()
    if rack_group[0:5] == 'icva2':
        if host[-6:-2] == '6129':# стойка с квм переключателем
            if int(host[-2:]) > 10:
                return 9
            else:
                return 8
        else:
            return 8
    elif rack_group[0:5] == 'icva3':
        return 9
    elif rack_group[0:5] == 'icva1':
        if host[-6:-2] == '5360' or host[-6:-2] == '5280' or host[-6:-2] == '5040' or host[-6:-2] == '5160':#стойки хостинга
            return 13
        elif rack_group[-3:] == '_00' or rack_group[-3:] == '_11':
            return 9
        else:
            return 7
    elif rack_group[0:5] == 'icva_':
        if host[-6:-2] == '5980' or host[-6:-2] == '5981' or host[-6:-2] == '5982':#стойки лабы
            return 1

def position(host): # определяет позицию в стойке
    return int(host[-2:]) + first_unit(host)

def from_stock_to_rack_4_switch(line): # переносим со склада в стойку
    host = line['name'].strip()
    sap = line['asset_tag'].strip()
    sn = line['serial'].strip()
    face = line['face'].strip().lower()
    mac = line['cf_id_mac'].strip()
    pstn = int(line['position'].strip())
    x = nb.dcim.devices.get(asset_tag=sap)
    comment = line['comments'].strip() + ' // '+ x.comments
    old = {'site': str(x.site), 'status': str(x.status)}
    if sn != '':
        x.update({
            'serial': sn
        })
    if mac != '':
        x.update({
            'custom_fields': {'id_mac':mac}
        })
    if 'ipmi' in host.lower():
        x.update({
            'device_role': nb.dcim.device_roles.get(slug='ipmi-switch').id
        })
    x.update({
        'name': host.upper(),
        'site': site(host),
        'status': 'active',
        'face': face,
        'rack': {'name': host[-4:]},
        'position': pstn,
        'tenant': nb.tenancy.tenants.get(name='vk'.upper()).id,
        'comments': comment
    })
    x = nb.dcim.devices.get(asset_tag=sap)
    print(f"{x.asset_tag} : {old['site']}({old['status']}) --> {str(x.name)} - {str(x.site)}({str(x.status)})")
    return

def from_stock_to_rack(line): # переносим со склада в стойку
    sap = line['asset_tag'].strip()
    host = hostname(line['name'].strip())
    print(host)
    sn = line['serial'].strip()
    face = 'front'.strip().lower()
    x = nb.dcim.devices.get(asset_tag=sap)
    old = {'site': str(x.site), 'status': str(x.status)}
    y = nb.dcim.devices.get(name=host)
    comment = line['comments'].strip() + ' // ' + x.comments
    print(position(host))
    if x.device_type.id == 20:
        host_name = f"FT{host[-6:-2]}{position(host)}"
    else:
        host_name = host
    if y is None:
        if sn != '':
            x.update({
                'serial': sn
            })
        x.update({
            'name': host_name,
            'site': site(host),
            'status': 'active',
            'face': face,
            'rack': {'name': host[-6:-2]},
            'position': position(host),
            'tenant': nb.tenancy.tenants.get(name='vk'.upper()).id,
            'comments': comment
        })
        x = nb.dcim.devices.get(asset_tag=sap)
        print(f'{x.asset_tag} : {old["site"]}({old["status"]}) --> {str(x.name)} - {str(x.site)}({str(x.status)})')
        return
    else:
        # print(f"{y.name} уже в стойке\n\t{dir(x)}")
        print(f"{y.name} уже в стойке")
        data_of_x = {
            'asset_tag': x.asset_tag,
            'serial': x.serial,
            'comments': comment,
            'custom_fields': x.custom_fields
        }
        if y.asset_tag is None:
            x.delete()
            y.update({
                'asset_tag': data_of_x['asset_tag'],
                'serial': data_of_x['serial'],
                'comments': data_of_x['comments'],
                'custom_fields': data_of_x['custom_fields']
            })
            y = nb.dcim.devices.get(asset_tag=sap)
            print(f"обновили поля:\n\t{y.asset_tag}\n\t{y.serial}\n\t{y.custom_fields['purchase_task']}")
        return

def show_host_sap_sn(reader):
    for line in reader:
        hostname_x = hostname(line['name'].strip())
        temp_x = nb.dcim.devices.get(name=hostname_x)
        if temp_x is None:
            print(line['name'].strip() + '\tхоста нет в базе')
        else:
            if temp_x.parent_device is None:
                print(f"{str(temp_x.name)}\t{str(temp_x.asset_tag)}\t{str(temp_x.serial)}")
            else:
                temp_y = nb.dcim.devices.get(name=str(temp_x.parent_device))
                print(f"{str(temp_x.name)}\t{str(temp_y.asset_tag)}\t{str(temp_x.parent_device.name)}\t{str(temp_x.parent_device.device_bay.name)}")

def show_sap_sn(reader):
    for line in reader:
        temp_x = nb.dcim.devices.get(asset_tag=line['asset_tag'].strip())
        if temp_x is None:
            print(line['asset_tag'].strip() + '\tметки нет в базе')
        else:
            print(str(temp_x.asset_tag) + '\t' + str(temp_x.status) + '\t' + str(temp_x.name) + '\t' + str(temp_x.serial))

def from_rack_to_stock(reader): # возвращаем на склад
    places = {'1': 'stock-icva', '2': 'stock-sdn', '3': 'stock-cvt'}
    for line in reader:
        temp_x = nb.dcim.devices.get(asset_tag=line['asset_tag'].strip())
        temp_comments = temp_x.comments
        # nb.dcim.device_roles.get(slug=line['device_role'].lower()).id
        # dev_role = temp_x.device_role.name.partition(': ')[0].lower()
        if temp_x is None:
            print(line['asset_tag'].strip() + ' --> метки нет в базе')
        elif str(temp_x.status).lower() != 'active':
            print(line['asset_tag'].strip()+' не активен '+str(temp_x.site).upper()+' // '+str(temp_x.status).upper())
        elif str(temp_x.status).lower() == 'active':
            slug_x = 'stock-'+str(temp_x.site).lower()
            if line['serial'].strip() != '':
                temp_x.update({
                    'serial': line['serial'].strip()
                })
            if temp_x.device_role.name.partition(': ')[0].lower() == 'server':
                temp_x.update({
                    'device_role': nb.dcim.device_roles.get(slug='server').id
                })
            temp_x.update({
                'name': None,
                'face': None,
                'rack': None,
                'position': None,
                'site': nb.dcim.sites.get(slug=slug_x).id,
                'status': 'offline',
                'comments': line['comments'].strip() + ' // ' + temp_comments
            })
            temp_x = nb.dcim.devices.get(asset_tag=line['asset_tag'].strip())
            print(line['asset_tag'].strip()+' теперь '+str(temp_x.site).upper()+' // '+str(temp_x.status).upper())

def swap_sap_id(reader): #замена платформ
    for line in reader:
        tag1 = line['asset_tag'].strip().upper()
        tag2 = line['asset_tag2'].strip().upper()
        if tag2 == '':
            print('отсутствует вторая метка')
            return
        tag_1 = nb.dcim.devices.get(asset_tag=tag1)
        tag_2 = nb.dcim.devices.get(asset_tag=tag2)
        slug_1 = 'stock-'+str(tag_1.site).lower()
        output_1 = {
            'sap id': tag1,
            'name': str(tag_1.name),
            'face': str(tag_1.face).lower(),
            'rack': str(tag_1.rack),
            'position': int(tag_1.position),
            'status': str(tag_1.status).lower(),
            'site': nb.dcim.sites.get(slug=str(tag_1.site).lower()).id,
            'comments': line['comments'].strip() + ' // ' +tag_2.comments
        }
        if str(tag_2.site).lower()[0:5] == 'stock':
            xx = line['comments'].strip() + ' // ' +tag_1.comments
            tag_1.update({
                'name': None,
                'face': None,
                'rack': None,
                'position': None,
                'site': nb.dcim.sites.get(slug=slug_1).id,
                'status': 'offline',
                'comments': xx
            })
            tag_2.update({
                'name': output_1['name'],
                'face': output_1['face'],
                'rack': {'name': output_1['rack']},
                'position': output_1['position'],
                'site': output_1['site'],
                'status': output_1['status'],
                'comments': output_1['comments']
            })
            print(f"{tag_1.asset_tag} - {tag_1.status}\t{tag_2.asset_tag} - {tag_2.name}({tag_2.status})")

def from_stock_to_stock(reader): # перемещаем между складами
    places = {
        '1': ['stock-icva','ICVA'],
        '2': ['stock-sdn','SDN'],
        '3': ['stock-cvt','CVT'],
        '4': ['moskva','Москва'],
        '44': ['m100','М100'],
        '5': ['rostov','Ростов'],
        '6': ['novosibirsk','Новосибирск'],
        '7': ['ekaterinburg','Екатеринбург'],
        '8': ['samata','Самара'],
        '9': ['habarovsk','Хабаровск'],
        'x': ['icva','ИЦВА(прод)']
        }
    print('откуда')
    for x in places:
        print(f"\t{x}. {places.get(x)[1]}")
    from_ = input('\n\nответ: ').strip()
    print('куда')
    for x in places:
        print(f"\t{x}. {places.get(x)[1]}")
    to_ = input('\n\nответ: ').strip()
    for line in reader:
        temp_x = nb.dcim.devices.get(asset_tag=line['asset_tag'].strip())
        if temp_x is None:
            print(line['asset_tag'].strip() + ' --> метки нет в базе')
        elif str(temp_x.site).lower() == places.get(from_)[0].replace('-',' '):
            if line['serial'] != '' and line['serial'] != temp_x.serial:
                xx = line['comments']+' сканировал серийник: ' + line['serial'].upper() + ' // '+temp_x.comments
                temp_x.update({
                    'serial': line['serial'],
                    'comments': xx
                })
                print(f"\tдописали серийник: {temp_x.serial}")
            xx = line['comments'] + ' // '+temp_x.comments
            temp_x.update({
                'site': nb.dcim.sites.get(slug=places.get(to_)[0]).id,
                'comments': xx,
                'face': None,
                'rack': None,
                'position': None
            })
            temp_x = nb.dcim.devices.get(asset_tag=line['asset_tag'].strip())
            print(line['asset_tag'].strip()+' перемещён из '+ places.get(from_)[0].replace('-',' ').upper()+' на '+str(temp_x.site).upper())

if __name__ == '__main__':
    with open('input.csv') as f_obj:
        csv_dict_reader(f_obj)