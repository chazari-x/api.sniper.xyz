import random
import threading

import requests
import urllib3
from progress.bar import IncrementalBar
from pyuseragents import random as random_useragent

urllib3.disable_warnings()


def load_proxies(fp: str = "proxies.txt"):
    """
    Простая загрузка прокси в список

    :param fp:
    :return: Список с прокси
    """
    proxies = []
    with open(file=fp, mode="r", encoding="utf-8") as File:
        lines = File.read().split("\n")
    for line in lines:
        try:
            proxies.append(f"http://{line}")
        except ValueError:
            pass

    if proxies.__len__() < 1:
        raise Exception("can't load empty proxies file!")

    print("{} proxies loaded successfully!".format(proxies.__len__()))

    return proxies


def save_res(filename: str, text: str):
    with open(filename, "a") as file:
        file.write(text + '\n')


def func(adr, path_to_save, prox, bar, semaphore):
    with semaphore:
        while True:
            try:
                bal = 0
                profile = {}
                tokenNames = ""
                session = requests.session()
                p = get_proxy(prox)
                session.proxies = {'all': p}
                session.headers = {
                    'user-agent': random_useragent(),
                    'accept': 'application/json, text/plain, */*',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                }
                session.verify = False
                ownedListedNfts = session.get(f'https://api.sniper.xyz/v1/getOwnedListedNfts?wallets={adr}')
                status = ownedListedNfts.status_code
                if ownedListedNfts.json():
                    status = 0
                    for tokenName, values in ownedListedNfts.json().items():
                        profile[tokenName] = {'n': len(values), 'price': 0}
                        tokenNames += f',{tokenName}'
                    ownedCompressedNfts = session.get(f'https://api.sniper.xyz/v1/getOwnedCompressedNfts?wallet={adr}')
                    status = ownedCompressedNfts.status_code
                    if ownedCompressedNfts.json():
                        for tokenName, values in ownedCompressedNfts.json()['collections'].items():
                            if tokenName in profile:
                                profile[tokenName]['n'] += len(values)
                            else:
                                profile[tokenName] = {'n': len(values), 'price': 0}
                                tokenNames += f',{tokenName}'
                    if status != 200: continue
                    status = 0
                    percentChange = session.get(f'https://api.sniper.xyz/v3/percentChange?fields=floorprice,supply&sortKey=floorprice&order=DESC&hideOutliers=false&showCompressed=true&showCompressed=true&collections={tokenNames}')
                    if percentChange.json():
                        if percentChange.json() != {}:
                            status = percentChange.status_code
                        for item in percentChange.json()['items']:
                            profile[item['collection']]['price'] = item['floorprice']
                        for tokenName, value in profile.items():
                            bal += value['n']*value['price']
                if status == 200:
                    if bal > 0:
                        save_res(path_to_save, f'https://www.sniper.xyz/portfolio?wallet={adr} | VALUE: {round(bal, 2)}')
                    break
            except Exception as e:
                pass
        bar.next()


def get_proxy(prox):
    sc = 0
    while sc != 200:
        dd = random.choice(prox)
        try:
            sc = requests.get('https://www.sniper.xyz/',
                              proxies={'all': dd},
                              headers={'user-agent': random_useragent()},
                              verify=False).status_code
        except:
            pass
    return dd


# prox = load_proxies(input('Path to proxies: '))
prox = load_proxies('prx.txt')

# file = input('Path to file with adr: ')
file = 'adr.txt'

mnemonic = open(file).read().splitlines()
print(f'Loaded {len(mnemonic)} address')
threads = []

# sem = threading.Semaphore(value=int(input('Max threads: ')))
sem = threading.Semaphore(value=100)

# path_to_save = input('Path to save: ')
path_to_save = 'sdedeac.txt'

print('started')
bar = IncrementalBar('Countdown', max=len(mnemonic))

for line in mnemonic:
    threads.append(
        threading.Thread(target=func,
                         args=[line, path_to_save, prox, bar, sem]))
for th in threads:
    try:
        th.start()
    except RuntimeError:
        pass

for th in threads:
    th.join()
