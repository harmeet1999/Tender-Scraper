import json
import boto3
from botocore.exceptions import NoCredentialsError

"""
    Step 1 :- Create a file `aws-credentials.json`
    Step 2 :- Insert the AWS Credentials e.g. {"Access key ID" : "your_access_key","Secret access key": "your_secret_key"}
"""

with open("aws-credentials.json","r") as file:
    aws_credentials = json.load(file)

ACCESS_KEY = aws_credentials["Access key ID"]
SECRET_KEY = aws_credentials["Secret access key"]
BUCKET = 'web-scrape-nexg'
# FILE_NAME = 'file_to_upload.txt'
# OBJECT_NAME = 'uploaded_file.txt'

s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

def s3_file_upload(FILE_NAME, OBJECT_NAME):
    try:
        s3.upload_file(FILE_NAME, BUCKET, OBJECT_NAME)
        print("Upload Successful")
    except FileNotFoundError:
        print("The file was not found")
    except NoCredentialsError:
        print("Credentials not available")

    # url = s3.generate_presigned_url(ClientMethod='get_object',Params={'Bucket': BUCKET,'Key': OBJECT_NAME},ExpiresIn=3600)
    url = f"https://{BUCKET}.s3.amazonaws.com/{OBJECT_NAME}"
    return url
