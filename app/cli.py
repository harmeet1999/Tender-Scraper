import rich
import argparse
from spider import TenderScraper

parser = argparse.ArgumentParser(
    prog="python app/main.py",
    description="Find List and Details of Tenders from different Websites",
    # epilog="Thanks for using %(prog)s! :)",
)

parser.add_argument('-f','--file', dest='TENDER_LISTING_JSON_FILE', default="sample/tender_listing_and_details.json", help='name of the file to process')
parser.add_argument('-u', '--url', dest="TENDER_PAGE_URL", default="https://eprocure.gov.in", help="Tender Website URL")

listing = parser.add_argument_group("Listing")
listing.add_argument('-l','--listing', help="Scrape list of tender from specified url", action='store_true')

detailed = parser.add_argument_group("Details")
detailed.add_argument('-d','--details', help="Scrape details of tender list", action='store_true')

args = parser.parse_args()

"""
    For Listing :- command = python app/main.py --url {url} --listing -f {x}.json
    For details :- command = python app/main.py --details -f {x}.json
"""

if __name__ == "__main__":

    tender_type = "Open Tender"
    value_criteria = "EMD"
    tender_type_dict = {"Open Tender": "1", "Limited Tender": "2"}
    value_criteria_dict = {"EMD": "1", "ECV": "4"}

    tender_scraper_obj = TenderScraper(args.TENDER_LISTING_JSON_FILE, args.TENDER_PAGE_URL)
    if args.listing :
        tender_scraper_obj.tender_list_scraper(
            tender_type_dict[tender_type], value_criteria_dict[value_criteria]
        )
    if args.details :
        tender_scraper_obj.tender_page(
            tender_type_dict[tender_type], value_criteria_dict[value_criteria]
        )
    if (not args.listing) & (not args.details):
        rich.print("[red]Wrong Argument")
