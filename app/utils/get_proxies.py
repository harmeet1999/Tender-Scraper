import requests
import time
from bs4 import BeautifulSoup

def get_proxy_ip():
    # scrape the list of proxy servers from a website
    url = 'https://www.sslproxies.org/'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find("table",{"class":"table-striped"})
    rows = table.tbody.find_all('tr')
    # //*[@id="list"]/div/div[2]/div/table

    # loop through the rows and extract the IP addresses and ports
    proxies = []
    for row in rows:
        cells = row.find_all('td')
        if len(cells) > 0:
            ip = cells[0].text
            port = cells[1].text
            proxy = f'{ip}:{port}'
            proxies.append(proxy)

    # test the proxies and measure their response time
    tested_proxies = []
    for proxy in proxies[:10]:
        try:
            start_time = time.time()
            response = requests.get('https://eprocure.gov.in/eprocure/app', proxies={'http': proxy, 'https': proxy}, timeout=5)
            response_time = time.time() - start_time
            if response.status_code == 200:
                tested_proxies.append((proxy, response_time))
        except Exception as e:
            # print(e)
            pass

    # sort the tested proxies by response time and get the fastest one
    best_proxy = sorted(tested_proxies, key=lambda x: x[1])[0][0]

    # use the best proxy for further requests
    print(f'The best proxy is: {best_proxy}')
    return best_proxy
