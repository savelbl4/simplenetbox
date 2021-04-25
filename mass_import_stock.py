import csv
import pynetbox
from settings import token, my_id

#добавляет новые устройства на склад или обновляет данные о (таске закупки)/(серийном номере)

nb = pynetbox.api('https://netbox.mvk.com', token=token)
fieldnames = ['comments','asset_tag','serial','device_type','device_role','manufacturer','status','site','cf_id_mac','cf_purchase_task']

def add_field(line):
    if line['cf_purchase_task'] != '' and line['cf_purchase_task'] != temp_x.custom_fields['purchase_task'] and line['serial'] != '' and line['serial'] != temp_x.serial:
        xx = line['comments']+' сканировал серийник: ' + line['serial'].upper() + ' // '+temp_x.comments
        temp_x.update({
            'serial': line['serial'],
            'comments': xx,
            'custom_fields': {'purchase_task':line['cf_purchase_task']}
        })
        print(f"\tдописали таск закупки: {temp_x.custom_fields['purchase_task']}\n\tдописали серийник: {temp_x.serial}")
    if line['cf_purchase_task'] != '' and line['cf_purchase_task'] != temp_x.custom_fields['purchase_task']:
        temp_x.update({
            'custom_fields': {'purchase_task':line['cf_purchase_task']}
        })
        print(f"\tдописали таск закупки: {temp_x.custom_fields['purchase_task']}")
    if line['serial'] != '' and line['serial'] != temp_x.serial:
        xx = line['comments']+' сканировал серийник: ' + line['serial'].upper() + ' // '+temp_x.comments
        temp_x.update({
            'serial': line['serial'],
            'comments': xx
        })
        print(f"\tдописали серийник: {temp_x.serial}")


with open('mass_import.csv', 'r') as f:
    reader = csv.DictReader(f, fieldnames=fieldnames, delimiter='\t')
    next(reader, None)
    for line in reader:
    # slug нужно удалять '/' и приводить к нижнему регистру
    # manufacturer нужно заменять ' ' на '-'
        temp_x = nb.dcim.devices.get(asset_tag=line['asset_tag'].strip())
        if temp_x is None:
            xx = line['comments']+' сканировал серийник: ' + line['serial'].upper() + ' // '
            nb.dcim.devices.create(
                serial = line['serial'].upper(),
                asset_tag = line['asset_tag'].upper(),
                device_type = nb.dcim.device_types.get(manufacturer=line['manufacturer'].strip().replace(' ','-').lower(), slug=line['device_type'].strip().replace('/','').replace(' ','-').lower()).id,
                device_role = nb.dcim.device_roles.get(slug=line['device_role'].lower()).id,
                status = line['status'].lower(),
                site = nb.dcim.sites.get(slug=line['site'].lower()).id,
                comments = xx,
                tenant = nb.tenancy.tenants.get(name='vk'.upper()).id,
                custom_fields = {'id_mac':line['cf_id_mac'], 'purchase_task':line['cf_purchase_task']}
            )
            status = str(nb.dcim.devices.get(asset_tag=line['asset_tag'].upper()).status)
            print(line['asset_tag'].upper() + ' добавили в базу ' + status)
        else:
            device_type = nb.dcim.device_types.get(manufacturer=line['manufacturer'].strip().replace(' ','-').lower(), slug=line['device_type'].strip().replace('/','').replace(' ','-').lower())
            if temp_x.device_type.id == device_type.id:
                print(f"{line['asset_tag'].upper()} уже в базе")
                add_field(line)
            elif temp_x.device_type.id != device_type.id:
                xx = 'поправил тип устройства // '+temp_x.comments
                temp_x.update({
                    'device_type': device_type.id,
                    'comments': xx
                })
                temp_x = nb.dcim.devices.get(asset_tag=line['asset_tag'].strip())
                print(f"{line['asset_tag'].upper()} уже в базе\n\tпоправили тип устройства: {temp_x.device_type.manufacturer}")
                add_field(line)
print('done')