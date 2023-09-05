import os
import re
import rich
import json
from datetime import datetime
from spider import (
    TenderScraper,
    AutomateAdvancedSearch,
    GujratTendersScraper,
    EILTendersScraper,
    TenderWizardScraper,
)
from helper import (
    create_logger,
    create_folder,
    remove_folder,
    check_file,
    get_domain_name,
    save_updated_json,
)
from utils.aws import s3_file_upload

logger = create_logger()


def file_manager(func):
    """
    A decorator function that manages file and folder operations before and after running a function.

    Args:
        func: The function to be decorated.

    Returns:
        The decorated function.
    """

    def wrapper(*args, **kwargs):
        try:
            foldername = kwargs["folder_name"]
            filename = kwargs["listing_filename"]
            create_folder(foldername, "sample")

            if check_file(foldername, filename):
                kwargs["modes"] = ["details"]
            else:
                kwargs["modes"] = ["listing", "details"]

            # kwargs["listing_filename"] = os.path.join(foldername, filename)

            result = func(*args, **kwargs)
            rich.print("Folder :- ", foldername)
            return result
        except Exception:
            logger.exception(f"There is error in Folder Management [{foldername}]")
        finally:
            remove_folder("docs", "sample")

    return wrapper


@file_manager
def main(url, folder_name, listing_filename, modes=None, *args, **kwargs):
    rich.print(
        "[red]Please wait while this runs, logs may appear to be stuck but they are still working. Do not quit the prcoess.[/red]"
    )

    listing_filename_abs = os.path.join(folder_name, listing_filename)

    if re.search(r"gujarattenders", url):
        tender_listing = GujratTendersScraper(url, listing_filename_abs).listing()
        save_updated_json(listing_filename_abs, tender_listing)
        s3_file_upload(
            listing_filename_abs, os.path.join(folder_name, listing_filename)
        )

    elif re.search(r"tenders.eil.co.in", url):
        tender_listing = EILTendersScraper(url).listing()

        # Open the same file for writing (this will overwrite the original file)
        with open(listing_filename_abs, "w+", encoding="utf8") as f:
            json.dump(tender_listing, f, indent=4)

        s3_file_upload(
            listing_filename_abs, os.path.join(folder_name, listing_filename)
        )

    elif re.search(r"eproc.bihar.gov.in", url):
        tender_listing = TenderWizardScraper(url, folder_name).listing()
        save_updated_json(listing_filename_abs, tender_listing)
        s3_file_upload(
            listing_filename_abs, os.path.join(folder_name, listing_filename)
        )

    else:
        TENDER_TEMP_JSON_FILE = os.path.join(folder_name, "temp_tendor_listing.json")
        advancedSearch = AutomateAdvancedSearch(url)
        tender_type_dict = advancedSearch.get_tender_type_options()

        tender_scraper_obj = TenderScraper(folder_name, listing_filename_abs, url)

        for mode in modes:
            if mode == "listing":
                for _, tender_types_value in tender_type_dict.items():
                    try:
                        # if tender_types =="Limited Tender":
                        filters = {
                            "tendor_type": tender_types_value,
                            # "tender_id": "2023_BSNL_769271_1",
                            # "from_date": datetime.now(),
                            # "to_date": datetime.now(),
                        }

                        tender_listing = tender_scraper_obj.tender_list_scraper(filters)
                        save_updated_json(listing_filename_abs, tender_listing)
                        save_updated_json(TENDER_TEMP_JSON_FILE, tender_listing)
                        s3_file_upload(
                            listing_filename_abs,
                            os.path.join(folder_name, listing_filename),
                        )
                        os.remove("sample/temp.json")
                    except Exception as error:
                        logger.error(f"{url} :- ", error)
                s3_file_upload(
                    listing_filename_abs, os.path.join(folder_name, listing_filename)
                )
                s3_file_upload(
                    TENDER_TEMP_JSON_FILE, os.path.join(folder_name, listing_filename)
                )
            if mode == "details":
                tender_scraper_obj.tender_page(TENDER_TEMP_JSON_FILE)
            s3_file_upload(
                listing_filename_abs, os.path.join(folder_name, listing_filename)
            )


if __name__ == "__main__":
    FOLDER_NAME = os.path.join("docs", "{url}", "{date}")
    TODAY = datetime.now().strftime("%Y/%m/%d")
    TENDER_LISTING_JSON_FILE = "tendor_listing.json"
    URLS = [
        "https://eprocure.gov.in/eprocure/app",
        "https://govtprocurement.delhi.gov.in/nicgep/app",
        "https://etender.up.nic.in/nicgep/app",
        "https://defproc.gov.in/nicgep/app",
        "https://etenders.gov.in/eprocure/app",
        "https://pmgsytenders.gov.in/nicgep/app",
        "https://iocletenders.nic.in/nicgep/app",
        "https://eprocurentpc.nic.in/nicgep/app",
        "https://coalindiatenders.nic.in/nicgep/app",
        "https://arunachaltenders.gov.in/nicgep/app",
        "https://www.gujarattenders.in/",
        "https://tenders.eil.co.in/newtenders/nit$open$mr",

        "https://www.eproc.bihar.gov.in/ROOTAPP/Mobility/index.html?dc=encuK824DhVFSmfVet4flvJsA==#/home"
    ]

    for url in URLS:
        rich.print(f"Tender Scraping URL :- {url}")
        logger.info(f"Tender Scraping URL :- {url}")

        folder_name = FOLDER_NAME.format(**{"url": get_domain_name(url), "date": TODAY})
        rich.print(f"Folder Name :- {folder_name}")
        logger.info(f"Folder Name :- {folder_name}")

        parameters = {
            "url": url,
            "folder_name": folder_name,
            "listing_filename": TENDER_LISTING_JSON_FILE,
        }
        main(**parameters)
