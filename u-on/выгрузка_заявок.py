import requests
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta


load_dotenv()

print("Введите дату от (год-месяц-день)")
date1 = input()
print("Введите дату до (год-месяц-день)")
date2 = input()

key = os.getenv("key")
my_date = datetime.strptime(date1, '%Y-%m-%d').date()
date_from = my_date - relativedelta(months=3)
date_to = date2
page = 1
_format = "json"

url_param = f"https://api.u-on.ru/{key}/requests/{date_from}/{date_to}/{page}.{_format}"


def find_price(id_f):
    incoming = []
    outgoing = []
    id = id_f
    url_param2 = f"https://api.u-on.ru/{key}/request/{id}.{_format}"
    response2 = requests.get(url_param2)
    res2 = response2.json()
    res2 = res2.pop('request')
    for x in res2:
        for y in x['payments']:
            date_y = y['date_create'].split(" ")
            if date_y[0] >= date1 and date_y[0] <= date2:
                if y['cio_name'] == "Приход":
                    incoming.append(y['price'])
                elif y['cio_name'] == "Расход":
                    outgoing.append(y['price'])
    return incoming, outgoing


def find_id(res):
    all_id = []
    id_true = []
    for r in res['requests']:
        all_id.append(r['id'])
    for x in all_id:
        id = x
        url_param2 = f"https://api.u-on.ru/{key}/request/{id}.{_format}"
        response2 = requests.get(url_param2)
        res2 = response2.json()
        res2 = res2.pop('request')
        for x in res2:
            for y in x['payments']:
                date_y = y['date_create'].split(" ")
                if date_y[0] >= date1 and date_y[0] <= date2:
                    id_true.append(x['id'])
    parse_json(res, id_true)


def parse_json(res, id_true):
    inf = []
    res = res['requests']
    for r in res:
        if r['id'] in id_true:
            incoming, outgoing = find_price(r['id'])
            commission = 0
            num = 0
            num_out = 0
            if incoming:
                for _, x in enumerate(incoming):
                    num += int(x)
                if num != 0 and outgoing:
                    for _, y in enumerate(outgoing):
                        num_out += int(y)
                        commission = num - num_out
                else:
                    commission = ""
            else:
                commission = ""
            incoming = ", ".join(map(str, incoming))
            outgoing = ", ".join(map(str, outgoing))
            inf_per_one = {
                'Номер заявки': r['id_internal'],
                'Дата': r['dat'],
                'Заказчик': r['client_surname'],
                'Фамилия менеджера': r['manager_surname'],
                'Туроператор': r['supplier_name'],
                'Оплачено клиентом': r['calc_client'],
                'Приход': incoming,
                'Расход': outgoing,
                'Комиссия': commission
            }
            inf.append(inf_per_one)
        else:
            continue

    df = pd.DataFrame(inf)
    print(df)
    file_name = 'Заявки.xlsx'
    df.to_excel(file_name)


response = requests.get(url_param)
if (response.status_code == 200):
    print("Данные получены")
    res = response.json()
    find_id(res)

else:
    print("Результат не найден")
