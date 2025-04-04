"""Main File"""

from typing import List
from fastapi import FastAPI, UploadFile, HTTPException, Form, File
from fastapi.middleware.cors import CORSMiddleware

from service import load_vendor_list, extract_text_from_pdf, process_and_categorize
from types_app import AiModel

app = FastAPI(title="Transaction Processor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
)


@app.post("/process")
async def process(
    ai_model: AiModel = Form(...),
    api_key: str = Form(...),
    statements: List[UploadFile] = File(...),
    vendor_file: UploadFile = File(...),
):
    """
    Process the input files and return the AI model result.
    """

    if not statements:
        raise HTTPException(status_code=400, detail="No transaction files provided")

    if not vendor_file:
        raise HTTPException(status_code=400, detail="No vendor file provided")

    try:

        vendor_list = load_vendor_list(vendor_file)

        all_transactions = []
        for pdf_idx, pdf_file in enumerate(statements):

            print(f"Processing the file {pdf_file.filename}")

            text_pages = await extract_text_from_pdf(pdf_file)

            if not text_pages:
                continue

            transactions_per_pdf = []

            for i, (page_num, page_text) in enumerate(text_pages):

                transactions = []

                # transactions = process_and_categorize(
                #     page_text, vendor_list, api_key, ai_model
                # )

                print(f"transactions completed for {page_num}")

                transactions_per_pdf.extend(transactions)

            all_transactions.extend(transactions)

        if all_transactions:
            return all_transactions

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
