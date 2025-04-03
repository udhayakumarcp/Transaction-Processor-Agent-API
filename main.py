"""Main File"""

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
    ai_model: AiModel = Form(),
    api_key: str = Form(),
    statements: UploadFile = File(),
    vendor_file: UploadFile = File(),
):
    """Process the input files and return the AI model result."""
    try:

        if not statements:
            raise HTTPException(status_code=400, detail="No transaction files provided")

        if not vendor_file:
            raise HTTPException(status_code=400, detail="No vendor file provided")

        vendor_list = load_vendor_list(vendor_file)

        text_pages = await extract_text_from_pdf(statements)

        all_transactions = []

        for i, (page_num, page_text) in enumerate(text_pages):
            transactions = process_and_categorize(
                page_text, vendor_list, api_key, ai_model
            )
            all_transactions.extend(transactions)

        return {ai_model}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
