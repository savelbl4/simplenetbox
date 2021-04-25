def set_data_2_host(reader, nb):
    for line in reader:
        sap = line['asset_tag'].strip()
        hostname_x = line['name'].strip()
        sn = line['serial'].strip()
        mac = line['cf_id_mac'].strip()
        temp_x = nb.dcim.devices.get(name=hostname_x)
        temp_y = nb.dcim.devices.get(asset_tag=sap)
        comment = line['comments'].strip() + ' // ' + temp_x.comments
        if temp_x is None:
            print(line['name'].strip() + '\tхоста нет в базе')
        elif str(temp_x.asset_tag) == sap:
            if mac != '':
                temp_x.update({
                    'custom_fields': {'id_mac':mac}
                })
            temp_x.update({
                'serial': sn,
                'comments': comment
            })
            temp_x = nb.dcim.devices.get(name=hostname_x)
            print(str(temp_x.name) + '\t' + str(temp_x.asset_tag) + '\t' + str(temp_x.rack) + '\t' + str(temp_x.serial))
        elif str(temp_x.asset_tag) is None or temp_y is None:
            if mac != '':
                temp_x.update({
                    'custom_fields': {'id_mac':mac}
                })
            temp_x.update({
                'asset_tag': sap,
                'serial': sn,
                'comments': comment
            })
            temp_x = nb.dcim.devices.get(name=hostname_x)
            # print(str(temp_x.name) + '\t' + str(temp_x.asset_tag) + '\t' + str(temp_x.rack) + '\t' + str(temp_x.serial))
            print(f"{str(temp_x.name)}\t{str(temp_x.asset_tag)}\t{str(temp_x.rack)}\t{str(temp_x.serial)}\tготово")
        else:
            print(hostname_x + '\tчто-то пошло не так')

def hard_set_sn_2_sap(reader, nb):
    for line in reader:
        sap = line['asset_tag'].strip()
        hostname_x = line['name'].strip()
        sn = line['serial'].strip()
        mac = line['cf_id_mac'].strip()
        temp_y = nb.dcim.devices.get(asset_tag=sap)
        if temp_y is None:
            print(line['asset_tag'].strip() + '\tметки нет в базе')
        else:
            if mac != '':
                temp_y.update({
                    'custom_fields': {'id_mac':mac}
                })
            temp_y.update({
                'serial': sn,
            })
    print('\tдоне')