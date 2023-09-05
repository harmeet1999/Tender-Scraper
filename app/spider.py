# Import required libraries
import json
import time
import os
import requests
import rich
from bs4 import BeautifulSoup
import urllib
from rich.console import Console

# selenium 4
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

import constants
from helper import (
    format_string,
    check_dom_element,
    func_logging,
    get_domain_name,
    create_logger,
    get_encoded_url,
    search_string,
    upload_document,
    scraper_logs,
    get_location_by_pincode,
)
from captcha_solver import captcha_solver_easyOCR as captcha_solver
from utils.aws import s3_file_upload
from utils.driver import WebDriver

console = Console()
website_driver = WebDriver()
logger = create_logger()


class BaseScraper(object):
    def __init__(self, url):
        self.url = url
        self.driver = website_driver.get_driver()
        self.driver.get(self.url)

    def __del__(self):
        self.driver.quit()


class AutomateAdvancedSearch(object):
    def __init__(self, url):
        self.url = url
        self.driver = website_driver.get_driver()
        self.driver.get(self.url)
        # search_link = BeautifulSoup(self.driver.page_source, 'html.parser')
        search_button = self.driver.find_element(By.XPATH, "//a[@title='Search']")
        search_button.click()
        self.soup = BeautifulSoup(self.driver.page_source, "html.parser")

    def get_tender_type_options(self):
        tendor_type_options_div_list = self.soup.find(
            "select", {"id": "TenderType"}
        ).find_all("option")[1:]
        tender_types = dict()
        for tendor_type_options_div in tendor_type_options_div_list:
            tender_types[tendor_type_options_div.text] = tendor_type_options_div[
                "value"
            ]
        return tender_types

    def set_tender_type_options(self, tender_type):
        tender_type_select = self.driver.find_element(By.ID, "TenderType")
        select = Select(tender_type_select)
        select.select_by_value(tender_type)


class TenderScraper(object):
    def __init__(self, tendor_folder_name, tender_json_file, tender_base_url):
        self.tender_json_file = tender_json_file
        self.tender_base_url = tender_base_url
        self.tendor_folder_name = tendor_folder_name
        self.driver = website_driver.get_driver()

    @func_logging
    def add_cookie(self):
        self.driver.get(
            constants.TENDER_SEARCH_PAGE_URL.format(
                **{"tender_base_url": self.tender_base_url}
            )
        )
        cookies = self.driver.get_cookies()
        cookie = {
            "name": constants.COOKIE_NAME,
            "value": cookies[0]["value"],
            "path": cookies[0]["path"],
        }
        self.driver.add_cookie(cookie)
        self.driver.refresh()
        return

    @func_logging
    def get_tendor_info_div_from_xpath(self, type, TITLE, page_url):
        for xpath in constants.XPATHS[type]:
            title_div_xpath = xpath["title_div_xpath"]
            table_div_xpath = xpath["table_div_xpath"]
            try:
                title_div = self.driver.find_element(
                    By.XPATH, title_div_xpath
                ).get_attribute("innerHTML")
                title_soup = BeautifulSoup(title_div, "html.parser")
                title_text = title_soup.text.strip()
                # print(title_text)

                if TITLE in title_text:
                    div = self.driver.find_element(
                        By.XPATH, table_div_xpath
                    ).get_attribute("innerHTML")
                    # rich.print(page_url)
                    return div
            except Exception:
                continue
        # rich.print(page_url)
        return

    @func_logging
    def search_filter(self, reload=True, filters=[]):
        if reload:
            self.driver.get(
                constants.TENDER_SEARCH_PAGE_URL.format(
                    **{
                        "tender_base_url": self.tender_base_url,
                    }
                )
            )
        # Additonal Filters
        for name, value in filters.items():
            if name == "tendor_type":
                # Select tender type using dropdown menu
                select_div = self.driver.find_element(By.ID, "TenderType")
                select = Select(select_div)
                select.select_by_value(value)
            elif name == "tender_id":
                select_div = self.driver.find_element(By.ID, "tenderId")
                select_div.clear()
                select_div.send_keys(value)
            elif name == "from_date":
                # Date Criteria -> Published Date
                select_div = self.driver.find_element(By.ID, "dateCriteria")
                Select(select_div).select_by_value("1")
                # From Date
                self.driver.execute_script(
                    "document.getElementById('fromDate').removeAttribute('readonly',0);"
                )
                select_div = self.driver.find_element(By.ID, "fromDate")
                select_div.clear()
                select_div.send_keys(value.strftime("%d/%m/%Y"))
            elif name == "to_date":
                # Date Criteria -> Published Date
                select_div = self.driver.find_element(By.ID, "dateCriteria")
                Select(select_div).select_by_value("1")
                # From Date
                self.driver.execute_script(
                    "document.getElementById('toDate').removeAttribute('readonly',0);"
                )
                select_div = self.driver.find_element(By.ID, "toDate")
                select_div.clear()
                select_div.send_keys(value.strftime("%d/%m/%Y"))
            else:
                raise Exception("No Matching Filters found !!")

        # Wait for captcha image to load and fetch its source URL
        captcha_img = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "captchaImage"))
        )
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        captcha_img = soup.find("img", {"id": "captchaImage"}).get("src")

        response = urllib.request.urlopen(captcha_img)
        with open("sample/image.jpg", "wb") as f:
            f.write(response.file.read())

        captcha_text = captcha_solver("sample/image.jpg")
        rich.print(f"CAPTCHA Text :- {captcha_text}")
        logger.info(f"CAPTCHA Text :- {captcha_text}")
        time.sleep(2)

        # Enter solved captcha text into input field and submit form
        captcha_input = self.driver.find_element(By.ID, "captchaText")
        captcha_input.send_keys(captcha_text.upper())
        search_button = self.driver.find_element(By.ID, "submit")
        search_button.click()

    # Define function to scrape basic tender list
    @func_logging
    def tender_list_scraper(self, filters=[]):
        is_captcha_invalid = True
        count_tries = 0
        while is_captcha_invalid:
            # Search filters and extract page content
            self.search_filter(reload=bool(count_tries < 1), filters=filters)
            is_captcha_invalid = check_dom_element(
                self.driver, "//span[contains(@class, 'error')]"
            )
            # rich.print(is_captcha_invalid)
            count_tries += 1
            time.sleep(2)

        # Page Html
        content = self.driver.page_source
        soup = BeautifulSoup(content, "html.parser")
        # Extract tender information from HTML table
        tender_list = list()

        next_page_button_element = soup.find("a", {"id": "linkFwd"})
        first_page_without_next_page = True
        page_counter = 1
        with console.status("[bold green]Fetching data...") as status:
            while (next_page_button_element is not None) | first_page_without_next_page:
                content = self.driver.page_source
                soup = BeautifulSoup(content, "html.parser")
                st_divs1 = soup.find_all("tr", {"class": ["odd", "even"]})
                for tender_info in st_divs1:
                    tender_div = tender_info.find_all("td")
                    tender_data = {
                        "S.No": int(tender_div[0].text.replace(".", "")),
                        "e-Published Date": tender_div[1].text,
                        "Closing Date": tender_div[2].text,
                        "Opening Date": tender_div[3].text,
                        "Title and Ref.No./Tender ID": [
                            "https://"
                            + get_domain_name(self.tender_base_url)
                            + tender_div[4].find("a")["href"],
                            tender_div[4].text.replace("\t", "").replace("\n", ""),
                        ],
                        "Organisation Chain": tender_div[5]
                        .text.replace("\t", "")
                        .replace("\n", ""),
                        "details": {
                            "Basic Details": {},
                            "Payment Instructions": [],
                            "Covers Information and No. Of Covers": {},
                            "Tender Fee Details": {},
                            "EMD Fee Details": {},
                            "Work Item Details": {},
                            "Critical Dates": {},
                            "Tender Documents": {},
                            "Latest Corrigendum List": {},
                            "Tender Inviting Authorities": {},
                        },
                    }
                    tender_list.append(tender_data)

                # Write data to file
                with open("sample/temp.json", "w", encoding="utf8") as f:
                    json.dump(tender_list, f, ensure_ascii=False, indent=1)
                s3_file_upload("sample/temp.json", self.tender_json_file)

                next_page_button_element = soup.find("a", {"id": "linkFwd"})
                if next_page_button_element:
                    next_page_button = self.driver.find_element(By.ID, "linkFwd")
                    next_page_button.click()
                first_page_without_next_page = False
                console.log(
                    f"[green]Finish fetching data from Page [/green] {page_counter}"
                )
                page_counter += 1
        time.sleep(2)
        return tender_list

    @func_logging
    def basic_details(self, basic_details_table):
        basic_table = BeautifulSoup(basic_details_table, "html.parser")
        basic_table_rows = basic_table.find_all("tr")
        basic_details = {}
        for basic_table_item in basic_table_rows:
            title_list = basic_table_item.find_all("td", {"class": "td_caption"})
            info_list = basic_table_item.find_all("td", {"class": "td_field"})
            count = 0
            length_diff = len(title_list)
            while length_diff > 0:
                # print(title_list[count].text, info_list[count].text, length_diff)
                basic_details[f"{title_list[count].text}"] = info_list[count].text
                length_diff -= 1
                count += 1
        return basic_details

    @func_logging
    def payment_information(self, payment_information_table):
        payment_information_table = BeautifulSoup(
            payment_information_table, "html.parser"
        )
        payment_information_table_rows = payment_information_table.find_all("tr")
        payment_information_list = []
        for payment_information_table_item in payment_information_table_rows[1:]:
            payment_information_text = payment_information_table_item.find_all("td")[
                1
            ].text
            # print(payment_information_text)
            payment_information_list.append(payment_information_text)
        return payment_information_list

    @func_logging
    def tender_fees_details(self, tender_fees_table):
        tender_fees = BeautifulSoup(tender_fees_table, "html.parser")
        tender_fees_rows = tender_fees.find_all("tr")
        tender_fees_details = {}
        for tender_fees_item in tender_fees_rows:
            title_list = tender_fees_item.find_all("td", {"class": "td_caption"})
            info_list = tender_fees_item.find_all("td", {"class": "td_field"})
            count = 0
            length_diff = len(title_list)
            while length_diff > 0:
                # print(title_list[count].text, info_list[count].text, length_diff)
                key = title_list[count].text.replace("\n", "").replace("\t", "")
                tender_fees_details[key] = info_list[count].text
                length_diff -= 1
                count += 1
        return tender_fees_details

    @func_logging
    def critical_dates_details(self, critical_dates_details_table):
        critical_dates_table = BeautifulSoup(
            critical_dates_details_table, "html.parser"
        )
        critical_dates_table_rows = critical_dates_table.find_all("tr")
        critical_dates_details = {}
        for critical_dates_table_item in critical_dates_table_rows:
            title_list = critical_dates_table_item.find_all(
                "td", {"class": "td_caption"}
            )
            info_list = critical_dates_table_item.find_all("td", {"class": "td_field"})
            count = 0
            length_diff = len(title_list)
            while length_diff > 0:
                # print(title_list[count].text, info_list[count].text, length_diff)
                critical_dates_details[f"{title_list[count].text}"] = info_list[
                    count
                ].text
                length_diff -= 1
                count += 1
        return critical_dates_details

    @func_logging
    def work_details(self, work_details_table):
        work_table = BeautifulSoup(work_details_table, "html.parser")
        work_table_rows = work_table.find_all("tr")
        work_details = {}
        for work_table_item in work_table_rows:
            title_list = work_table_item.find_all("td", {"class": "td_caption"})
            info_list = work_table_item.find_all("td", {"class": "td_field"})
            count = 0
            length_diff = len(title_list)
            while length_diff > 0:
                # print(title_list[count].text, info_list[count].text, length_diff)
                work_details[f"{title_list[count].text}"] = info_list[count].text
                if title_list[count].text == "Pincode":
                    work_details["State"] = get_location_by_pincode(
                        info_list[count].text.strip()
                    )["State"]
                length_diff -= 1
                count += 1
        return work_details

    @func_logging
    def EMD_fees_details(self, EMD_fees_details_table):
        EMD_table = BeautifulSoup(EMD_fees_details_table, "html.parser")
        EMD_table_rows = EMD_table.find_all("tr")
        EMD_fees_details = {}
        for EMD_table_item in EMD_table_rows:
            title_list = EMD_table_item.find_all("td", {"class": "td_caption"})
            info_list = EMD_table_item.find_all("td", {"class": "td_field"})
            count = 0
            length_diff = len(title_list)
            while length_diff > 0:
                # print(title_list[count].text, info_list[count].text, length_diff)
                key = title_list[count].text.replace("\n", "").replace("\t", "")
                EMD_fees_details[key] = info_list[count].text
                length_diff -= 1
                count += 1
        return EMD_fees_details

    @func_logging
    def tendors_documents(self, tendors_documents_table, tender_id):
        def get_tender_url(anchor_div):
            if anchor_div.find("a"):
                return (
                    "https://"
                    + get_domain_name(self.tender_base_url)
                    + anchor_div.find("a").get("href")
                )

        def upload_document(filename, tender_id):
            return s3_file_upload(
                os.path.join("sample", filename),
                os.path.join(self.tendor_folder_name, tender_id, filename),
            )

        def download_document(url, tender_id):
            if url:
                document_link = ""
                # Get the cookies
                cookies = self.driver.get_cookies()
                headers = {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Language": "en-GB,en;q=0.8",
                    "Connection": "keep-alive",
                    "Cookie": f'JSESSIONID={cookies[0]["value"]}',
                }

                # http = urllib3.PoolManager()
                response = requests.request("GET", url, headers=headers, verify=False)

                filename = None
                if "content-disposition" in response.headers:
                    disposition = response.headers["content-disposition"]
                    if "filename" in disposition:
                        filename = disposition.split("filename=")[1].strip('"')

                if filename is None:
                    filename = url.split("/")[-1]

                updated_filename = f"sample/{filename}"
                rich.print(updated_filename)
                with open(updated_filename, "wb") as f:
                    f.write(response.content)

                document_link = upload_document(filename, tender_id)
                return document_link

        @func_logging
        def get_nit_documents(div, tender_id, *args, **kwargs):
            nit_documents_data = list()
            nit_documents_title = div.find("td", {"class": "td_caption"}).text.strip()
            if nit_documents_title == "NIT Document":
                nit_documents_divs = div.select("tr[id^='informal_']")
                nit_document_dict = {}
                for nit_documents_div in nit_documents_divs:
                    data = nit_documents_div.find_all("td")
                    nit_document_dict = {
                        "S.No": format_string(data[0].text),
                        "Document Name": {
                            "name": format_string(data[1].text),
                            "url": get_tender_url(data[1]),
                            "link": download_document(
                                get_tender_url(data[1]), tender_id
                            ),
                        },
                        "Description": format_string(data[2].text),
                        "Document Size (in KB)": format_string(data[3].text),
                    }
                    nit_documents_data.append(nit_document_dict)
            return nit_documents_data

        @func_logging
        def get_works_document(div, *args, **kwargs):
            works_document_data = list()
            works_document_title = div.find("td", {"class": "td_caption"}).text.strip()
            if works_document_title == "Work Item Documents":
                works_document_divs = div.select("tr[id^='informal_']")
                works_document_dict = {}
                for works_document_div in works_document_divs:
                    data = works_document_div.find_all("td")
                    works_document_dict = {
                        "S.No": format_string(data[0].text),
                        "Document Type": format_string(data[1].text),
                        "Document Name": {
                            "name": format_string(data[2].text),
                            "url": get_tender_url(data[2]),
                            "link": get_tender_url(data[2]),
                        },
                        "Description": format_string(data[3].text),
                        "Document Size (in KB)": format_string(data[4].text),
                    }
                    works_document_data.append(works_document_dict)
            return works_document_data

        @func_logging
        def get_zip_link(div, tender_id):
            try:
                zip_link = div.find("a").get("href", "")
                return download_document(
                    f"https://{get_domain_name(self.tender_base_url)}{zip_link}",
                    tender_id,
                )
            except Exception as e:
                rich.print("get_zip_link", e)
                return

        tendors_documents_table = BeautifulSoup(tendors_documents_table, "html.parser")
        tendors_documents_table_rows = list(tendors_documents_table.children)
        tendors_documents_dict = {
            "NIT Document": get_nit_documents(
                tendors_documents_table_rows[0], tender_id
            ),
            "Work Item Documents": get_works_document(tendors_documents_table_rows[-2]),
            "ZIP Link": get_zip_link(tendors_documents_table_rows[-4], tender_id),
        }
        return tendors_documents_dict

    @func_logging
    def tender_inviting_details(self, tender_inviting_details_table):
        tender_inviting_table = BeautifulSoup(
            tender_inviting_details_table, "html.parser"
        )
        tender_inviting_table_rows = tender_inviting_table.find_all("tr")
        tender_inviting_details = {}
        for tender_inviting_table_item in tender_inviting_table_rows:
            title_list = tender_inviting_table_item.find_all(
                "td", {"class": "td_caption"}
            )
            info_list = tender_inviting_table_item.find_all("td", {"class": "td_field"})
            count = 0
            length_diff = len(title_list)
            while length_diff > 0:
                # print(title_list[count].text, info_list[count].text, length_diff)
                key = title_list[count].text.replace("\n", "").replace("\t", "")
                tender_inviting_details[key] = info_list[count].text
                length_diff -= 1
                count += 1
        return tender_inviting_details

    @func_logging
    def tender_corrigendum_list(self, tender_corrigendum_list_table, tender_id):
        def upload_document(filename, tender_id):
            return s3_file_upload(
                os.path.join("sample", filename),
                os.path.join(self.tendor_folder_name, tender_id, filename),
            )

        def download_document(url, tender_id):
            if url:
                document_link = ""
                # Get the cookies
                cookies = self.driver.get_cookies()
                headers = {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Language": "en-GB,en;q=0.8",
                    "Connection": "keep-alive",
                    "Cookie": f'JSESSIONID={cookies[0]["value"]}',
                }

                # http = urllib3.PoolManager()
                response = requests.request("GET", url, headers=headers, verify=False)

                filename = None
                if "content-disposition" in response.headers:
                    disposition = response.headers["content-disposition"]
                    if "filename" in disposition:
                        filename = disposition.split("filename=")[1].strip('"')

                if filename is None:
                    filename = url.split("/")[-1]

                updated_filename = f"sample/{filename}"
                rich.print(updated_filename)
                with open(updated_filename, "wb") as f:
                    f.write(response.content)

                document_link = upload_document(filename, tender_id)
                return document_link

        # Main Code
        tender_corrigendum_table = BeautifulSoup(
            tender_corrigendum_list_table.get_attribute("innerHTML"), "html.parser"
        )
        tender_corrigendum_link = tender_corrigendum_table.find_all(
            "a", {"id": "DirectLink_10"}
        )[0].get("href", "")

        """Open Tender Details in new Tab"""
        # Get the current window handle
        current_handle = self.driver.current_window_handle

        # Open a new tab using JavaScript
        tender_corrigendum_list_table.find_elements(By.ID, "DirectLink_10")[0].click()

        # Switch to the new tab
        for handle in self.driver.window_handles:
            if handle != current_handle:
                self.driver.switch_to.window(handle)
                break

        # Scraping Logic
        corrigendum_details = (
            BeautifulSoup(
                self.driver.find_element(By.ID, "corrDoctable").get_attribute(
                    "innerHTML"
                ),
                "html.parser",
            )
            .find("tr", {"class": "even"})
            .find_all("td")
        )
        corrigendum_no = corrigendum_details[0].text
        corrigendum_title = corrigendum_details[1].text
        corrigendum_description = corrigendum_details[2].text
        corrigendum_published_date = corrigendum_details[3].text
        corrigendum_document_link = download_document(
            urllib.parse.urljoin(
                self.tender_base_url, corrigendum_details[4].find("a").get("href")
            ),
            tender_id,
        )
        corrigendum_doc_size = corrigendum_details[5].text

        tender_corrigendum_details = {
            "Corr.No.": corrigendum_no,
            "Corrigendum Title": corrigendum_title,
            "Corrigendum Description": corrigendum_description,
            "Published Date": corrigendum_published_date,
            "Document Link": corrigendum_document_link,
            "Doc Size(in KB)": corrigendum_doc_size,
        }

        # Close the new window
        self.driver.close()

        # Switch back to the original window
        self.driver.switch_to.window(current_handle)

        return tender_corrigendum_details

    @func_logging
    def tender_page(self, TENDER_TEMP_JSON_FILE):
        @func_logging
        def search_doc_captcha():
            # Wait for captcha image to load and fetch its source URL
            captcha_img = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "captchaImage"))
            )
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            captcha_img = soup.find("img", {"id": "captchaImage"}).get("src")

            response = urllib.request.urlopen(captcha_img)
            with open("sample/image.jpg", "wb") as f:
                f.write(response.file.read())

            captcha_text = captcha_solver("sample/image.jpg")
            rich.print(f"CAPTCHA Text :- {captcha_text}")
            logger.info(f"CAPTCHA Text :- {captcha_text}")
            time.sleep(2)

            # Enter solved captcha text into input field and submit form
            captcha_input = self.driver.find_element(By.ID, "captchaText")
            captcha_input.send_keys(captcha_text.upper())
            search_button = self.driver.find_element(By.ID, "Submit")
            search_button.click()

        @func_logging
        def migrate_to_doc_download_page(url):
            self.driver.get(url)
            tendors_documents_table = self.get_tendor_info_div_from_xpath(
                "tendors_documents", "Tenders Documents", url
            )
            tendors_documents_table = BeautifulSoup(
                tendors_documents_table, "html.parser"
            )
            tendors_documents_table_rows = list(tendors_documents_table.children)
            zip_link = tendors_documents_table_rows[-4].find("a").get("href", "")
            self.driver.get(
                f"https://{get_domain_name(self.tender_base_url)}{zip_link}"
            )

            is_captcha_invalid = True
            # rich.print(is_captcha_invalid)
            while is_captcha_invalid:
                search_doc_captcha()
                is_captcha_invalid = check_dom_element(
                    self.driver, "//span[contains(@class, 'error')]"
                )
                # rich.print(is_captcha_invalid)
                time.sleep(2)

        content = self.driver.page_source
        soup = BeautifulSoup(content, "html.parser")

        with open(TENDER_TEMP_JSON_FILE, "r", encoding="utf-8") as file:
            tender_list = json.load(file)

        # self.add_cookie()
        # tender_basic_details_list = list()
        tender_details_list = list()

        rich.print("[bold cyan]Tender Details[/bold cyan]")

        # for idx,tender_info in tqdm(enumerate(tender_list), bar_color='green', bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'):
        for idx, tender_info in enumerate(tender_list):
            tender_list_page_url = tender_info["Title and Ref.No./Tender ID"][0]
            # rich.print(f"TENDER_DETAIL_PAGE_URL :- {tender_list_page_url}")
            logger.info(f"TENDER_DETAIL_PAGE_URL :- {tender_list_page_url}")

            if idx == 0:
                migrate_to_doc_download_page(tender_list_page_url)
            else:
                self.driver.get(tender_list_page_url)

            tender_id_div = self.driver.find_element(
                By.XPATH,
                "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr[3]/td[2]",
            ).get_attribute("innerHTML")
            tender_id = BeautifulSoup(tender_id_div, "html.parser").text

            basic_details_table = self.driver.find_element(
                By.XPATH,
                "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody",
            ).get_attribute("innerHTML")
            tender_basic_details = self.basic_details(basic_details_table)
            tender_info["details"]["Basic Details"] = tender_basic_details

            tender_fees_details_table = self.get_tendor_info_div_from_xpath(
                "tender_fees_details", "Tender Fee Details", tender_list_page_url
            )
            if tender_fees_details_table:
                tender_fees_details = self.tender_fees_details(
                    tender_fees_details_table
                )
                tender_info["details"]["Tender Fee Details"] = tender_fees_details
            else:
                logger.debug("Div(Tender Fee Details) not Found !!")

            payment_information_table = self.get_tendor_info_div_from_xpath(
                "payment_information", "Payment Instruments", tender_list_page_url
            )
            if payment_information_table:
                payment_information = self.payment_information(
                    payment_information_table
                )
                tender_info["details"]["Payment Instructions"] = payment_information
            else:
                logger.debug("Div(Payment Instruments) not Found !!")

            tendors_documents_table = self.get_tendor_info_div_from_xpath(
                "tendors_documents", "Tenders Documents", tender_list_page_url
            )
            if tendors_documents_table:
                tendors_documents = self.tendors_documents(
                    tendors_documents_table, tender_id
                )
                tender_info["details"]["Tender Documents"] = tendors_documents
            else:
                logger.debug("Div(Tender Documents) not Found !!")

            emd_fees_details_table = self.get_tendor_info_div_from_xpath(
                "EMD_fees_details", "EMD Fee Details", tender_list_page_url
            )
            if emd_fees_details_table:
                emd_fees_details = self.EMD_fees_details(emd_fees_details_table)
                tender_info["details"]["EMD Fee Details"] = emd_fees_details
            else:
                logger.debug("Div(EMD Fee Details) not Found !!")

            work_details_table = self.get_tendor_info_div_from_xpath(
                "work_details", "Work Item Details", tender_list_page_url
            )
            if work_details_table:
                work_details = self.work_details(work_details_table)
                tender_info["details"]["Work Item Details"] = work_details
            else:
                logger.debug("Div(Work Item Details) not Found !!")

            critical_dates_details_table = self.get_tendor_info_div_from_xpath(
                "critical_dates_details", "Critical Dates", tender_list_page_url
            )
            if critical_dates_details_table:
                critical_dates_details = self.critical_dates_details(
                    critical_dates_details_table
                )
                tender_info["details"]["Critical Dates"] = critical_dates_details
            else:
                logger.debug("Div(Critical Dates) not Found !!")

            # Latest Corrigendum List
            try:
                tender_corrigendum_list_table = self.driver.find_element(
                    By.ID, "corrigendumDocumenttable"
                )
                tender_corrigendum_list = self.tender_corrigendum_list(
                    tender_corrigendum_list_table, tender_id
                )
                tender_info["details"][
                    "Latest Corrigendum List"
                ] = tender_corrigendum_list
            except Exception as e:
                logger.debug("Div(Latest Corrigendum List) not Found !!")

            tender_inviting_details_table = self.get_tendor_info_div_from_xpath(
                "tender_inviting_details",
                "Tender Inviting Authority",
                tender_list_page_url,
            )
            if tender_inviting_details_table:
                tender_inviting_details = self.tender_inviting_details(
                    tender_inviting_details_table
                )
                tender_info["details"][
                    "Tender Inviting Authorities"
                ] = tender_inviting_details
            else:
                logger.debug("Div(Tender Inviting Authorities) not Found !!")

            tender_details_list.append(tender_info)

            with open(self.tender_json_file, "w", encoding="utf8") as f:
                json.dump(tender_details_list, f, ensure_ascii=False, indent=2)
            scraper_logs(
                tenderUrl=self.tender_base_url, status="PENDING", tenderFetch=idx
            )
            s3_file_upload(self.tender_json_file, self.tender_json_file)

        scraper_logs(tenderUrl=self.tender_base_url, status="DONE", tenderFetch=idx)

    def __del__(self):
        self.driver.quit()


class GujratTendersScraper(object):
    def __init__(self, url, listing_filename_abs) -> None:
        # self.url = "https://www.gujarattenders.in/"
        self.url = url
        self.listing_filename_abs = listing_filename_abs
        self.driver = website_driver.get_driver()
        self.driver.get(self.url)

    def listing(self):
        def get_details_by_span_id(soup, id):
            div = soup.find("span", {"id": id})
            return div.text if div else None

        counter = 1
        tender_list = list()

        with console.status("[bold green]Fetching data...") as _:
            while True:
                try:
                    tender_table_div = self.driver.find_element(
                        By.XPATH,
                        "//table[@id='ctl00_ContentPlaceHolder1_GRDFreshTender']",
                    ).get_attribute("innerHTML")
                    tender_soup_list = BeautifulSoup(
                        tender_table_div, "html.parser"
                    ).find_all("table", {"id": "Table1"})

                    for index, tender_soup in enumerate(tender_soup_list):
                        tender_detail_soup = tender_soup.find_all("td")
                        tender_detail_url = urllib.parse.urljoin(
                            self.url, tender_detail_soup[6].find("a").get("href")
                        )
                        tender_data = {
                            "Sector": format_string(tender_detail_soup[0].text),
                            "Tender Value": format_string(tender_detail_soup[1].text),
                            "Location": format_string(tender_detail_soup[2].text),
                            "Ref.No": format_string(tender_detail_soup[3].text),
                            "Closing Date": format_string(tender_detail_soup[4].text)
                            .replace("   ", "")
                            .replace("\xa0|\xa0", ""),
                            "Tender Name": format_string(tender_detail_soup[6].text)
                            .replace("  ", "")
                            .replace("Get Liaison Service", ""),
                            "Temder Detail Link": tender_detail_url,
                        }
                        counter += 1
                        tender_list.append(tender_data)

                        """Open Tender Details in new Tab"""
                        # Get the current window handle
                        current_handle = self.driver.current_window_handle

                        # Open a new tab using JavaScript
                        # self.driver.execute_script('window.open("https://google.com");')
                        self.driver.execute_script(
                            f'window.open("{tender_detail_url}", "_blank");'
                        )
                        # self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.COMMAND + 't')

                        # Switch to the new tab
                        for handle in self.driver.window_handles:
                            if handle != current_handle:
                                self.driver.switch_to.window(handle)
                                break

                        # Wait for the new page to load
                        wait = WebDriverWait(self.driver, 50)
                        wait.until(EC.url_to_be(tender_detail_url))

                        # Scraping Logic
                        tender_details_soup = BeautifulSoup(
                            self.driver.page_source, "html.parser"
                        )

                        product_detail = get_details_by_span_id(
                            tender_details_soup,
                            "ctl00_ContentPlaceHolder1_lblproductdetailval",
                        )
                        tender_detail = get_details_by_span_id(
                            tender_details_soup,
                            "ctl00_ContentPlaceHolder1_lblTenderDetails",
                        )
                        tender_location = get_details_by_span_id(
                            tender_details_soup,
                            "ctl00_ContentPlaceHolder1_lbllocationVal",
                        )
                        tender_value = get_details_by_span_id(
                            tender_details_soup,
                            "ctl00_ContentPlaceHolder1_lbltendervalueval",
                        )
                        tender_closiing_date = get_details_by_span_id(
                            tender_details_soup,
                            "ctl00_ContentPlaceHolder1_lblclosingdateval",
                        )
                        tender_opening_data = get_details_by_span_id(
                            tender_details_soup,
                            "ctl00_ContentPlaceHolder1_lblopeningDate",
                        )
                        tender_industry_type = get_details_by_span_id(
                            tender_details_soup,
                            "ctl00_ContentPlaceHolder1_lblSubIndustry",
                        )
                        tender_EMD = get_details_by_span_id(
                            tender_details_soup, "ctl00_ContentPlaceHolder1_lblcurrEMD"
                        )

                        tender_details = {
                            "Product Detail": product_detail,
                            "Tender Detail": tender_detail,
                            "Tender Location": tender_location,
                            "Tender Value": tender_value,
                            "Tender EMD": tender_EMD,
                            "Tender Closing Date": tender_closiing_date,
                            "Tender Opening Date": tender_opening_data,
                            "Sub-Industry/Industry": tender_industry_type,
                        }
                        tender_data["details"] = tender_details

                        # Close the new window
                        self.driver.close()

                        # Switch back to the original window
                        self.driver.switch_to.window(current_handle)

                    # Write data to file
                    with open(
                        f"sample/temp_[{get_domain_name(self.url)}].json",
                        "w",
                        encoding="utf8",
                    ) as f:
                        json.dump(tender_list, f, ensure_ascii=False, indent=1)
                    scraper_logs(
                        tenderUrl=self.url, status="PENDING", tenderFetch=counter
                    )
                    s3_file_upload(
                        f"sample/temp_[{get_domain_name(self.url)}].json",
                        self.listing_filename_abs,
                    )

                    next_button = self.driver.find_element(
                        By.ID, "ctl00_ContentPlaceHolder1_Nextbutton"
                    )
                    next_button.click()
                    wait = WebDriverWait(self.driver, 50)
                    wait.until(EC.staleness_of(next_button))

                except Exception as error:
                    rich.print("Next Button Not Found !!")
                    break

                console.log(f"[green]Finish fetching data from Page [/green] {counter}")

            scraper_logs(tenderUrl=self.url, status="DONE", tenderFetch=counter)
            return tender_list

    def __del__(self):
        self.driver.quit()


class EILTendersScraper(object):
    def __init__(self, url) -> None:
        self.url = url
        self.driver = website_driver.get_driver()
        self.driver.get(self.url)

    def listing(self):
        def get_press_tender_list(soup):
            tender_press_tender_soup = soup.find(
                "table", {"id": "ctl00_ContentPlaceHolder1_openTenderGrid"}
            )
            tender_press_tender_div_list = tender_press_tender_soup.find_all("tr")
            tender_press_tender_list = list()
            for i in range(1, len(tender_press_tender_div_list)):
                tender_press_tender_div = tender_press_tender_div_list[i]
                tender_row_div = tender_press_tender_div.find_all("td")
                tender_press_data = {
                    "S.No.": format_string(tender_row_div[0].text),
                    "Item Description": tender_row_div[1].text,
                    "Tender No": format_string(tender_row_div[2].text),
                    "Tender Order Link": tender_row_div[2].find("a").get("href"),
                    "Client": tender_row_div[3].text,
                    "Project": tender_row_div[4].text,
                    "Issue Date": tender_row_div[5].text,
                    "Due Date & Time (IST)": tender_row_div[6].text,
                    "Contact Person": tender_row_div[7].text,
                }
                tender_press_tender_list.append(tender_press_data)
            return tender_press_tender_list

        def get_press_enquiry_tender_list(soup):
            tender_press_enquiry_list = soup.find(
                "table", {"id": "ctl00_ContentPlaceHolder1_openRFQGrid"}
            )
            tender_press_enquiry_div_list = tender_press_enquiry_list.find_all("tr")
            tender_press_enquiry_list = list()
            for i in range(1, len(tender_press_enquiry_div_list)):
                tender_press_enquiry_div = tender_press_enquiry_div_list[i]
                tender_row_div = tender_press_enquiry_div.find_all("td")
                tender_enquiry_data = {
                    "S.No.": format_string(tender_row_div[0].text),
                    "Item Description": tender_row_div[1].text,
                    "Tender No": format_string(tender_row_div[2].text),
                    "Tender Order Link": tender_row_div[2].find("a").get("href"),
                    "Client": tender_row_div[3].text,
                    "Project": tender_row_div[4].text,
                    "Issue Date": tender_row_div[5].text,
                    "Due Date & Time (IST)": tender_row_div[6].text,
                    "Contact Person": tender_row_div[7].text,
                }
                tender_press_enquiry_list.append(tender_enquiry_data)
            return tender_press_enquiry_list

        try:
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            tender_data = {
                "List Of Press Tender": get_press_tender_list(soup),
                "List Of Press Enquiry": get_press_enquiry_tender_list(soup),
            }

            scraper_logs(
                tenderUrl=self.url,
                status="DONE",
                tenderFetch=len(
                    tender_data["List Of Press Tender"]
                    + tender_data["List Of Press Enquiry"]
                ),
            )

            # Write data to file
            with open(
                f"sample/temp_[{get_domain_name(self.url)}].json", "w", encoding="utf8"
            ) as f:
                json.dump(tender_data, f, ensure_ascii=False, indent=1)

            return tender_data
        except Exception as e:
            rich.print(e)

    def __del__(self):
        self.driver.quit()


class TenderWizardScraper(BaseScraper):
    def __init__(self, url, folder_name):
        super().__init__(url)
        self.folder_name = folder_name
        self.cookies = self.driver.get_cookies()
        self.navigate_to_listing_page()

    def navigate_to_listing_page(self):
        wait = WebDriverWait(self.driver, 50)
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@class, 'sha-pg010-close')]")
            )
        )

        # Execute JavaScript to simulate a click anywhere on the screen
        self.driver.find_element(
            By.XPATH, "//div[contains(@class, 'sha-pg010-close')]"
        ).click()

        # Search Page in New Window
        new_window_handle = self.driver.window_handles[-1]
        self.driver.switch_to.window(new_window_handle)

        e_tender_button = self.driver.find_elements(
            By.CLASS_NAME, "sha-pg001-02-menu-item"
        )[1]
        e_tender_button.click()

        # Get the window handles and switch to the new window
        handles = self.driver.window_handles
        self.driver.switch_to.window(handles[-1])

        # Do something in the new window
        print(self.driver.title)

        # Click Opened Radio button in Advanced Search
        wait = WebDriverWait(self.driver, 50)
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='frm_sr']")))
        self.driver.execute_script("toggleSearch('SAME_WINDOW'); return false;")

        wait = WebDriverWait(self.driver, 100)
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@id='sr_advanced']/table/tbody/tr[3]/td[2]/input[2]")
            )
        )
        opened_radio_button = self.driver.find_element(
            By.XPATH, "//*[@id='sr_advanced']/table/tbody/tr[3]/td[2]/input[2]"
        )
        time.sleep(5)
        opened_radio_button.click()

        # Click Search Button
        self.driver.execute_script("search_submit()")

    def listing(self):
        def work_details(soup):
            def get_text(soup):
                if soup:
                    return soup.text
                return None

            tender_no = soup[3].text
            serial_no = soup[0].text

            redirect_page_counter = (
                str(int(serial_no) % 10) if int(serial_no) % 10 != 0 else "10"
            )
            self.driver.execute_script(f"summaryLink_36({redirect_page_counter})")

            """Open Tender Details in new Tab"""
            # Get the current window handle
            current_handle = self.driver.current_window_handle

            # Switch to the new tab
            self.driver.switch_to.window(self.driver.window_handles[-1])

            tender_details_soup = BeautifulSoup(self.driver.page_source, "html.parser")

            # Scraping Logic
            tender_details = {
                "Tender": get_text(
                    tender_details_soup.find("span", {"id": "tenderNumberspan"})
                ),
                "Title/Type of Project/Procurement Model": get_text(
                    tender_details_soup.find("span", {"id": "titlespan"})
                ),
                "Tender Creation Date and Time:": get_text(
                    tender_details_soup.find("span", {"id": "announceDatespan"})
                ),
                "Tender Called For": get_text(
                    tender_details_soup.find("span", {"id": "isPreQualificationspan"})
                ),
                "Stage": get_text(
                    tender_details_soup.find("span", {"id": "tenderStagespan"})
                ),
                "Email": get_text(
                    tender_details_soup.find("span", {"id": "emailNamespan"})
                ),
                "Contact No": get_text(
                    tender_details_soup.find("span", {"id": "contactNumberspan"})
                ),
                "Multiple Submission": get_text(
                    tender_details_soup.find("span", {"id": "isMultipleSubmissionspan"})
                ),
                "Run Line Number": get_text(
                    tender_details_soup.find("span", {"id": "lineNumberspan"})
                ),
                "Estimated Cost": get_text(
                    tender_details_soup.find("span", {"id": "estimatedCostspan"})
                ),
                "EMD": get_text(tender_details_soup.find("span", {"id": "emdspan"})),
                "Cost of BOQ": get_text(
                    tender_details_soup.find("span", {"id": "formFeespan"})
                ),
                "TPF(Inc.of GST)BSEDC PAN-AACCB0540P GSTIN-10AACCB0540P1Z2": get_text(
                    tender_details_soup.find("span", {"id": "tenderProcessFeespan"})
                ),
                "Region": get_text(
                    tender_details_soup.find("div", {"id": "div_region"})
                ),
                "COT": get_text(tender_details_soup.find("div", {"id": "div_cot"})),
                "General Document Upload Required": get_text(
                    tender_details_soup.find("span", {"id": "uploadGeneralDocspan"})
                ),
                "Description Of Work": get_text(
                    tender_details_soup.find("span", {"id": "descOfWorkspan"})
                ),
                "Remarks if Any": get_text(
                    tender_details_soup.find("span", {"id": "tendRemarkspan"})
                ),
                "Request of Tender Document From": get_text(
                    tender_details_soup.find("span", {"id": "recvOfAppFromDatespan"})
                ),
                "Issue of Tender Document From": get_text(
                    tender_details_soup.find(
                        "span", {"id": "issueOfTenderDocFromDatespan"}
                    )
                ),
                "Request of Tender Document To": get_text(
                    tender_details_soup.find("span", {"id": "recvOfAppToDatespan"})
                ),
                "Issue of Tender Document To": get_text(
                    tender_details_soup.find(
                        "span", {"id": "issueOfTenderDocToDatespan"}
                    )
                ),
                "Bid Clarification date": get_text(
                    tender_details_soup.find("span", {"id": "bidClrDatespan"})
                ),
                "Tender Closing Date and Time": get_text(
                    tender_details_soup.find("span", {"id": "receiptOfTendToDatespan"})
                ),
                "Cost Open Date and Time": get_text(
                    tender_details_soup.find("span", {"id": "costOpenDatespan"})
                ),
            }

            # Closing Window
            self.driver.close()

            # Switch back to the original window
            self.driver.switch_to.window(current_handle)

            return tender_details

        def actions(soup):
            department = soup[2].text
            tender_no = soup[3].text
            line_no = soup[4].text

            show_form_url = get_encoded_url(
                "https://www.eproc.bihar.gov.in/ROOTAPP/servlet/SelectScheduleServlet",
                {
                    "freeView": "yes",
                    "Buyer": department,
                    "TenderNo": tender_no,
                    "LineNo": line_no,
                    "line": "Line",
                    "combidsheet": "yes",
                },
            )
            print_link = get_encoded_url(
                "https://www.eproc.bihar.gov.in/ROOTAPP/servlet/SelectScheduleServlet",
                {"Name": department, "TenderNo": tender_no, "LineNo": line_no},
            )

            """Open Tender Details in new Tab"""
            # Get the current window handle
            current_handle = self.driver.current_window_handle

            # Open a new tab using JavaScript
            self.driver.execute_script(f'window.open("{show_form_url}", "_blank");')

            # Switch to the new tab
            self.driver.switch_to.window(self.driver.window_handles[-1])

            # Wait for the new page to load
            # wait = WebDriverWait(self.driver, 50)
            # wait.until(EC.url_to_be(show_form_url))

            # Scraping Logic
            tender_documents_list = list()

            tender_document_div_list = self.driver.find_elements(
                By.XPATH,
                "//tr[contains(@id, 'xtr')][contains(@id, '_xtd')][contains(@class, 'tr_odd')]",
            )
            for tender_document_div in tender_document_div_list:
                tender_document_soup = BeautifulSoup(
                    tender_document_div.get_attribute("innerHTML"), "html.parser"
                )
                tender_document_data = tender_document_soup.find_all("td")
                # tender_document_link_params = search_string(r"(?:downloadCorrAddendum)?adDownload\('([^']*)'\)", tender_document_data[3].find('a').get('onclick'))
                tender_document_link_params = search_string(
                    r"'/([^']*)'", tender_document_data[3].find("a").get("onclick")
                )
                tender_document_link = (
                    "http://www.eproc.bihar.gov.in/" + tender_document_link_params
                    if tender_document_link_params
                    else None
                )
                tender_document = {
                    "Serial no.": tender_document_data[0].text,
                    "Document Name": tender_document_data[1].text,
                    "File ID": tender_document_data[2].text,
                    "Download Link": tender_document_link,
                    "S3 Link": upload_document(
                        tender_document_link, self.cookies, self.folder_name
                    ),
                }
                tender_documents_list.append(tender_document)

            self.driver.close()

            # Switch back to the original window
            self.driver.switch_to.window(current_handle)

            return tender_documents_list

        print("Tender Listing Page")
        tender_list = list()
        with console.status("[bold green]Fetching data...") as _:
            while True:
                try:
                    wait = WebDriverWait(self.driver, 100)
                    wait.until(EC.presence_of_element_located((By.ID, "dvSummary")))

                    tender_table_div = self.driver.find_element(
                        By.ID, "dvSummary"
                    ).get_attribute("innerHTML")
                    tender_table_soup = BeautifulSoup(tender_table_div, "html.parser")

                    tender_even_row_list = tender_table_soup.find_all(
                        "tr", {"class": "even"}
                    )
                    tender_odd_row_list = tender_table_soup.find_all(
                        "tr", {"class": "odd"}
                    )
                    tender_row_list = tender_even_row_list + tender_odd_row_list

                    row_count = 1
                    for i in range(0, len(tender_row_list), 2):
                        tender_row = tender_row_list[i].find_all("td")
                        tender_desciption_row = tender_row_list[i + 1]

                        tender_work_details = work_details(tender_row)
                        tender_actions = actions(tender_row)

                        tender_data = {
                            "Sl No.": tender_row[0].text,
                            "Department": tender_row[2].text,
                            "Tender": tender_row[3].text,
                            "Request of Tender Document To": tender_row[5].text,
                            "Region": tender_row[6].text,
                            "Tender Closing Date & Time": tender_row[7].text,
                            "Estimated Cost	": tender_row[8].text,
                            "Cost of BOQ": tender_row[9].text,
                            "EMD": tender_row[10].text,
                            "COT": tender_row[11].text,
                            "Tender Type": tender_row[12].text,
                            "Description of Work:": tender_desciption_row.find(
                                "input"
                            ).get("value", None),
                            "tender_actions": tender_actions,
                            "tender_details": tender_work_details,
                        }
                        tender_list.append(tender_data)
                        scraper_logs(
                            tenderUrl=self.url,
                            status="PENDING",
                            tenderFetch=len(tender_list),
                        )
                        row_count += 1

                    # Write data to file
                    with open(
                        f"sample/temp_[{get_domain_name(self.url)}].json",
                        "w",
                        encoding="utf8",
                    ) as f:
                        json.dump(tender_list, f, ensure_ascii=False, indent=1)

                    next_button = self.driver.find_element(By.CLASS_NAME, "pg_next")
                    next_button_link = next_button.get_attribute("href")
                    self.driver.get(next_button_link)

                except Exception as error:
                    rich.print("Next Button Not Found !!")
                    break

                # console.log(f"[green]Finish fetching data from Page [/green] {counter}")
        scraper_logs(tenderUrl=self.url, status="DONE", tenderFetch=len(tender_list))
        return tender_list

    def __del__(self):
        self.driver.quit()
