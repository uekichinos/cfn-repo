import boto3
import os
import tempfile
from openpyxl import Workbook

s3 = boto3.client('s3')
textract = boto3.client('textract')

def handler(event, context):
    # Get S3 event data
    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    key = record['s3']['object']['key']

    print(f"Processing file: s3://{bucket}/{key}")

    # Extract text from document using Textract
    text_lines = extract_text_from_s3(bucket, key)

    # Create Excel file
    output_key = key.rsplit('.', 1)[0] + '.xlsx'
    with tempfile.NamedTemporaryFile(suffix=".xlsx") as tmp:
        save_to_excel(text_lines, tmp.name)

        # Upload to S3
        s3.upload_file(tmp.name, bucket, output_key)
        print(f"Uploaded Excel to s3://{bucket}/{output_key}")

    return {
        "statusCode": 200,
        "body": f"Processed {key}, extracted {len(text_lines)} lines."
    }

def extract_text_from_s3(bucket, key):
    response = textract.detect_document_text(
        Document={'S3Object': {'Bucket': bucket, 'Name': key}}
    )
    lines = [item["Text"] for item in response["Blocks"] if item["BlockType"] == "LINE"]
    return lines

def save_to_excel(lines, file_path):
    wb = Workbook()
    ws = wb.active
    ws.title = "ExtractedText"

    for idx, line in enumerate(lines, start=1):
        ws.cell(row=idx, column=1, value=line)

    wb.save(file_path)
