# selenium 4
import rich
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from .get_proxies import get_proxy_ip

class WebDriver(object):
    def __init__(self, browser_type="chrome"):
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        # options.add_argument('--headless')
        # try :
        #     proxy = get_proxy_ip()
        #     options.add_argument('--proxy-server=http://' + proxy)
        # except Exception as e:
        #     rich.print("Proxy Not Found !!")

        '''
        Reference Link :- https://pypi.org/project/webdriver-manager/
        '''
        if browser_type == "chrome":
            service = ChromeService(ChromeDriverManager().install())
        elif browser_type == "brave":
            service = ChromeService(ChromeDriverManager(chrome_type=ChromeType.BRAVE).install())
        elif browser_type == "chromium":
            service = ChromeService(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        else :
            raise Exception("Browser Type Not Found !!")

        self.driver = webdriver.Chrome(service=service, options=options)

    def get_driver(self):
        return self.driver
