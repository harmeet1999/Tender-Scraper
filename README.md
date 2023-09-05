# Tender Scraper

The purpose of this project is to develop a web scraping application that can extract tender information from various government websites using a tech stack consisting of NodeJS, MongoDB, Python, OCR Recognition, Machine learning, and Amazon S3. The application will be designed to automatically identify and bypass Captcha verification using advanced machine learning algorithms and OCR Recognition techniques. The project will leverage the power of NodeJS and MongoDB to create a robust, scalable, and highly performant web scraping engine capable of handling large volumes of data.

Python will be used to develop custom algorithms for identifying and extracting relevant information from the website's HTML code. OCR Recognition will be utilized to identify and extract data from images, such as scanned documents and handwritten text. Machine learning techniques will be employed to train the system to recognize patterns and identify key data points accurately.

In addition to the above, the project will also include a feature to save the extracted documents to Amazon S3. This will enable the application to securely store and manage large amounts of data while providing easy access to authorized users. The S3 storage will be used to store the tender information and documents, including scanned copies of original documents, ensuring that the data is preserved and easily accessible in the event of any loss or damage.

The ultimate goal of this project is to create a reliable and efficient web scraping solution that can provide users with access to tender information from various government websites, while also offering the ability to securely store and manage the documents on the cloud. The project will save time and effort in the procurement process and enable users to make informed decisions quickly and accurately.


**Pre-requisite:**

*See Environment Variables section*


## **Installation Steps:**

**Step 1** : Install **python**, Recommended python version = 3.10, Install **pip**, recommended pip version : 23.0

Installation pertaining to the base OS.

**Step 2** :- Create a virtual environment

```
virtualenv venv
```

*OR*

Follow any of these docs, in case the given commands do not register for you

https://docs.python.org/3/library/venv.html

https://pypi.org/project/pipenv/

```
pip install pipenv
```

**Step 3:** Activate your current environment via pipenv:
```
pipenv shell
```

*OR*

Activate your environment via environment name:

```
source venv/bin/activate
```
* *here venv is your environment name*

**Step 4:** Install poetry via *pip*

```
pip install poetry
```

**Step 5:** Run poetry install to install depencies
```
poetry install
```

**Step 6:** Execute the scraper script
```
python app/main.py
```

**Step 7:** Set up a cron job to run this once a day at an approrpriate time. You would need to follow the base OS configuration pattern for that. 
## Environment Variables

To run this project

**Create a file named `aws-credentials.json`**

```
{
  "Access key ID" : "your_S3_access_key_here",
  "Secret access key": "your_S3_secret_key_here"
}
```
## Features

- Scrapes the below websites: <br />
    https://eprocure.gov.in/eprocure/app  <br />
    https://govtprocurement.delhi.gov.in/nicgep/app  <br />
    https://etender.up.nic.in/nicgep/app  <br />
    https://defproc.gov.in/nicgep/app   <br />
    https://etenders.gov.in/eprocure/app   <br />

- Scheduler for getting the data fetched to the db 2 hours after the scraping completes.
- CLI updates for the current job.
- Uploads the files to the S3 bucket with the folder structure in *website/yy/mm/dd/tenderID/file.ext* format


## Authors

Powered by 

<img align="left" width="120" src="https://nexgeniots.com/wp-content/uploads/2021/11/NexGen-Logo_512x380.svg">






++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# Tender-Scraper-Backend


The backend for this project scrapes government sites and saves data in Node.js, MongoDB, and Express, using TypeScript. It's designed to efficiently handle large amounts of data and ensure reliable data storage and retrieval. Express.js provides web application framework while TypeScript adds static typing and syntax features to improve code organization and readability. MongoDB is chosen for its scalability and flexibility. Overall, the backend is optimized for performance and stability.


## Pre Requisites

- NodeJS, version <14 (Refer your OS install documentation)
- MongoDB, version 5+ (Refer your OS install documentation)
- 

## Copy the project
```sh
git clone https://github.com/mrgithubrepos/web-scraping-app.git
cd web-scraping-app/scraper-be/
```

## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`API_KEY`

`ANOTHER_API_KEY`

## Install the dependencies

```sh
npm install
```

## Production mode

```sh
npm run start
```

OR 

#### Refer sample Dockerfile in the scraper-be directory

## Access on

Open [https://<your_server_url>:5000](https://your_server_url:5000) with your API explorer to see the result.
## API Reference

#### For all APIs and their references, we are using Swagger

```

@swagger
/v1/detail/search:
  post:
    tags: [Tender Details]
    summary: Search Tenders
    description: Search Tenders from Database
    parameters:
      - in: query
        name: from
        type: integer
        description: Starting index of data to retrieve
      - in: query
        name: size
        type: integer
        description: Number of data items to retrieve
    requestBody:
     description: search form all available tenders
     required: true
     content:
       application/json:
         schema:
           $ref: '#/components/schemas/SearchReq'
    responses:
      200:
        description: A successful response
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TenderList'


router.route('/search').post(searchTenders)

```


