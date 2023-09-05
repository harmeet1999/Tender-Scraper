import os
import re
import json
import shutil
import functools
import urllib3
import logging
import rich
from datetime import datetime
import requests

# Utility
from urllib.parse import urlparse, urlencode, quote
from utils.aws import s3_file_upload

# Selenium
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

http = urllib3.PoolManager()

# Logging
def create_logger():
    logger = logging.getLogger("logger")
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler("debug.log", mode="w")
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


logger = create_logger()


def format_string(string):
    return string.strip().replace("\t", "").replace("\n", "")

    
def check_dom_element(driver, xpath):
    try:
        # Try to find the element with the specified XPath
        element = driver.find_element(By.XPATH, xpath)
        
        # If the element is found, you can do something with it
        rich.print("Found the element:", element.text)
        
        return element.text != "No Tenders found."
    except NoSuchElementException:
        # If the element is not found, handle the exception here (e.g., print a message)
        print("Element not found. Continuing with the rest of the code...")

def create_folder(*args):
    folder_list = args
    for foldername in folder_list:
        if not os.path.exists(foldername):
            os.makedirs(foldername)


def remove_folder(*args):
    folder_list = args
    for foldername in folder_list:
        if os.path.exists(foldername):
            shutil.rmtree(foldername)


def get_domain_name(url):
    parsed_url = urlparse(url)
    domain_name = parsed_url.netloc

    # rich.print("Domain name:", domain_name)
    return domain_name


def check_file(foldername, filename):
    absolute_filename = os.path.join(foldername, filename)
    if os.path.exists(absolute_filename):
        return True
    return False


def save_updated_json(filename, new_data):
    # Open the file for reading
    if os.path.exists(filename):
        with open(filename, "r+", encoding="utf8") as f:
            data = json.load(f)

    else:
        data = []

    # Modify the data as needed
    data += new_data

    # Open the same file for writing (this will overwrite the original file)
    with open(filename, "w+", encoding="utf8") as f:
        json.dump(data, f, indent=4)


def func_logging(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(
                f"Function {func.__name__} called from line {func.__code__.co_firstlineno}"
            )
            logger.exception(e)

    return wrapper


def get_encoded_url(url, query):
    query_string = urlencode(query, quote_via=quote)
    url_with_query = url + "?" + query_string
    return url_with_query


def search_string(pattern, string):
    match = re.search(pattern, string)
    if match:
        url = match.group(1)
        return url


def download_document_by_url(url, cookies, filepath):
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.8",
        "Connection": "keep-alive",
        "Cookie": f'JSESSIONID={cookies[0]["value"]}',
    }
    response = http.request("GET", url)

    filename = None
    if "content-disposition" in response.headers:
        disposition = response.headers["content-disposition"]
        if "filename" in disposition:
            filename = disposition.split("filename=")[1].strip('"')

    if filename is None:
        filename = url.split("/")[-1]

    # Get the current datetime
    current_datetime = datetime.now()

    # Convert the datetime to a formatted string
    datetime_string = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")

    updated_filename = os.path.join(filepath, filename, datetime_string)
    rich.print(updated_filename)
    with open(updated_filename, "wb") as f:
        f.write(response.data)

    # document_link = upload_document(updated_filename, filename)
    return updated_filename, filename


def upload_document(url, cookies, folder_name, unique_identifier=""):
    try :
        original_filename, upload_filename = download_document_by_url(
            url, cookies, folder_name
        )
        return s3_file_upload(
            os.path.join("sample", original_filename),
            os.path.join(folder_name, unique_identifier, original_filename),
        )
    except Exception as error:
        logger.error("Error Occured in File upload \n", error)

def scraper_logs(tenderUrl, status, tenderFetch):
    url = "https://scraper-be.qantily.com/v1/basic/webhook"

    payload = json.dumps({
        "status": status,
        "currentDate": str(datetime.now()),
        "tenderUrl": tenderUrl,
        "tenderFetch": tenderFetch
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 200:
        return response
    else :
        logger.error("scraper_logs :", response)

def get_location_by_pincode(pincode):
    url = f"https://api.postalpincode.in/pincode/{pincode}"
    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload, verify=False)
    if response.status_code == 200:
        return response.json()[0]["PostOffice"][0]
    else :
        logger.error("scraper_logs :", response)