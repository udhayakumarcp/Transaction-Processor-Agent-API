"""Service"""

from io import BytesIO
import json

# import requests
import pandas as pd
import pdfplumber
from fastapi import UploadFile

from langchain_google_genai import ChatGoogleGenerativeAI

from types_app import AiModel


def load_vendor_list(vendor_file: UploadFile) -> list:
    """Extract the data from the sheet with column Payee"""
    filename = vendor_file.filename
    file = vendor_file.file

    if filename.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    return df["Payee"].tolist() if "Payee" in df.columns else []


async def extract_text_from_pdf(file: UploadFile) -> list:
    """Extract text from a valid, non-corrupt PDF file."""
    pdf_data = await file.read()
    pdf_stream = BytesIO(pdf_data)

    text_pages = []
    with pdfplumber.open(pdf_stream) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text:
                text_pages.append((page_num, text.strip()))
    return text_pages


def process_and_categorize(
    text: str, vendor_list: list, api_key: str, ai_model: AiModel
):
    """Processes transactions and categorizes them in one API call."""

    prompt = f"""
    Extract structured transactions from the bank statement and match them to vendors.
 
    **STRICT RULES:**
    - Use vendor names **ONLY** from this list:
      {json.dumps(vendor_list, indent=2)}
    - Do **NOT** assume vendors. If no match is found, return **"Unknown"**.
    - Do **NOT** modify transaction descriptions.
    - Return **pure JSON output** ONLY. No explanations, no additional text.
 
    **Statement Text:**
    {text}
 
    **Output Format (ONLY JSON)**
    ```json
    [
        {{"Date": "MM/DD/YYYY", "Description": "transaction details", "Deposits_Credits": number, "Withdrawals_Debits": number, "Vendor Name": "matched vendor"}},
        {{"Date": "MM/DD/YYYY", "Description": "another transaction", "Deposits_Credits": number, "Withdrawals_Debits": number, "Vendor Name": "matched vendor"}}
    ]
    ```
 
    **Example:**
    ```json
    [
        {{
            "Date": "11/01/2023",
            "Description": "Overdraft Fee for a Transaction Posted on 10/31 $143.00 Dell",
            "Deposits_Credits": 0,
            "Withdrawals_Debits": 35.00,
            "Vendor Name": "Overdraft Fee"
        }},
        {{
            "Date": "11/01/2023",
            "Description": "ATM Cash Deposit on 11/01 1530 Heitman St Fort Myers FL",
            "Deposits_Credits": 600.00,
            "Withdrawals_Debits": 0,
            "Vendor Name": "ATM"
        }}
    ]
    ```
    """

    if ai_model == AiModel.GEMINI:
        gemini = ChatGoogleGenerativeAI(
            # gemini-2.0-flash
            # gemini-2.0-pro-exp-02-05
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0,
        )

        response = gemini.invoke(prompt)
        if not response or not response.content.strip():
            return []

        transactions = json.loads(response.content.strip("```json").strip("```"))

        for tx in transactions:
            tx["Deposits_Credits"] = tx.get("Deposits_Credits", 0) or 0
            tx["Withdrawals_Debits"] = tx.get("Withdrawals_Debits", 0) or 0

        return transactions

    # elif ai_model == AiModel.DEEP_SEEK:
    #     payload = {
    #         "model": "deepseek-chat",
    #         "messages": [{"role": "user", "content": prompt}],
    #         "temperature": 0,
    #         "stream": False,
    #     }
    #     headers = {
    #         "Authorization": f"Bearer {api_key}",
    #         "Content-Type": "application/json",
    #     }
    #     response = requests.post(
    #         "https://api.deepseek.com/v1/chat/completions",
    #         headers=headers,
    #         json=payload,
    #     )

    #     if response.status_code == 200:
    #         try:
    #             json_data = response.json()["choices"][0]["message"]["content"]
    #             return json.loads(json_data.strip("```json").strip("```"))
    #         except Exception as e:
    #             return []
    #     else:
    #         return []
