COOKIE_NAME = "JSESSIONID"
COOKIE_VALUE = "6719DD8F3BEB7D1A5857E39CA187ADD7.modspeg1"
TENDER_SEARCH_PAGE_URL = "{tender_base_url}?page=FrontEndAdvancedSearch&service=page"

XPATHS = {
    "payment_information": [
        {
            "title_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[4]/td/table/tbody/tr/td[1]/table/tbody/tr[1]/td/table/tbody/tr",
            "table_div_xpath": "//*[@id='offlineInstrumentsTableView' or @id='onlineInstrumentsTableView']/tbody",
        },
    ],
    "tender_fees_details": [
        {
            "title_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[9]/td/table/tbody/tr/td[1]/table/tbody/tr[1]/td/table/tbody/tr",
            "table_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[9]/td/table/tbody/tr/td[1]/table/tbody/tr[2]/td/table/tbody",
        },
        {
            "title_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[12]/td/table/tbody/tr/td[1]/table/tbody/tr[1]/td/table/tbody/tr",
            "table_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[12]/td/table/tbody/tr/td[1]/table/tbody/tr[2]/td/table/tbody",
        },
    ],
    "EMD_fees_details": [
        {
            "title_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[9]/td/table/tbody/tr/td[2]/table/tbody/tr[1]/td/table/tbody/tr",
            "table_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[9]/td/table/tbody/tr/td[2]/table/tbody/tr[2]/td/table/tbody",
        },
        {
            "title_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[12]/td/table/tbody/tr/td[2]/table/tbody/tr[1]/td/table/tbody/tr",
            "table_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[12]/td/table/tbody/tr/td[2]/table/tbody/tr[2]/td/table/tbody",
        },
    ],
    "work_details": [
        {
            "title_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[13]/td/table/tbody/tr",
            "table_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[14]/td/table/tbody",
        },
        {
            "title_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[16]/td/table/tbody/tr",
            "table_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody",
        },
    ],
    "critical_dates_details": [
        {
            "title_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[16]/td/table/tbody/tr",
            "table_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody",
        },
        {
            "title_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[19]/td/table/tbody/tr",
            "table_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[20]/td/table/tbody",
        },
    ],
    "tendors_documents": [
        {
            "title_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[19]/td/table/tbody/tr",
            "table_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[20]/td/table/tbody/tr/td/table/tbody",
        },
        {
            "title_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[22]/td/table/tbody/tr",
            "table_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[23]/td/table/tbody/tr/td/table/tbody",
        },
    ],
    "tender_inviting_details": [
        {
            "title_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[19]/td/table/tbody/tr",
            "table_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[20]/td/table/tbody",
        },
        {
            "title_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[22]/td/table/tbody/tr",
            "table_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[23]/td/table/tbody",
        },
        {
            "title_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[25]/td/table/tbody/tr",
            "table_div_xpath": "//*[@id='content']/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[26]/td/table/tbody",
        },
    ],
}
