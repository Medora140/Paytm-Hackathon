"""
Hardcoded seed list of public mutual fund factsheets and scheme documents.
Matches the test fixture (mutual fund factsheets/handbooks) and focuses on
publicly disclosed, regulatory AMFI-compliant documents.
"""

from typing import List, Dict, Any

SEED_BENCHMARK_SOURCES: List[Dict[str, Any]] = [
    {
        "issuer_name": "HDFC Mutual Fund",
        "product_name": "HDFC Top 100 Fund / MF Handbook",
        "product_category": "mutual_fund",
        "source_url": "https://www.hdfcfund.com/content/dam/hdfc-amc/factsheet/HDFC_MF_Handbook_Aug_2024.pdf",
        "doc_format": "pdf",
        "notes": "Official HDFC AMC Monthly Scheme Handbook and Factsheet"
    },
    {
        "issuer_name": "SBI Mutual Fund",
        "product_name": "SBI Bluechip Fund",
        "product_category": "mutual_fund",
        "source_url": "https://www.sbimf.com/en-us/downloads/factsheets/sbi-bluechip-fund-factsheet.pdf",
        "doc_format": "pdf",
        "notes": "SBI Mutual Fund Flagship Large Cap Factsheet"
    },
    {
        "issuer_name": "ICICI Prudential Mutual Fund",
        "product_name": "ICICI Prudential Bluechip Fund",
        "product_category": "mutual_fund",
        "source_url": "https://www.icicipruamc.com/downloads/factsheets/icici-pru-bluechip-factsheet.pdf",
        "doc_format": "pdf",
        "notes": "ICICI Prudential AMC Monthly Scheme Factsheet"
    },
    {
        "issuer_name": "Nippon India Mutual Fund",
        "product_name": "Nippon India Large Cap Fund",
        "product_category": "mutual_fund",
        "source_url": "https://mf.nipponindiaim.com/InvestorServices/FactSheets/NipponIndia-Large-Cap-Factsheet.pdf",
        "doc_format": "pdf",
        "notes": "Nippon India Mutual Fund Factsheet"
    },
    {
        "issuer_name": "Mirae Asset Mutual Fund",
        "product_name": "Mirae Asset Large & Midcap Fund",
        "product_category": "mutual_fund",
        "source_url": "https://www.miraeassetmf.co.in/downloads/factsheets/mirae-asset-large-midcap-factsheet.pdf",
        "doc_format": "pdf",
        "notes": "Mirae Asset Mutual Fund Factsheet"
    },
    {
        "issuer_name": "PPFAS Mutual Fund",
        "product_name": "Parag Parikh Flexi Cap Fund",
        "product_category": "mutual_fund",
        "source_url": "https://amc.ppfas.com/schemes/parag-parikh-flexi-cap-fund/factsheet.pdf",
        "doc_format": "pdf",
        "notes": "PPFAS Flexi Cap Fund Monthly Factsheet"
    },
    {
        "issuer_name": "Kotak Mahindra Mutual Fund",
        "product_name": "Kotak Emerging Equity Fund",
        "product_category": "mutual_fund",
        "source_url": "https://www.kotakmf.com/downloads/factsheets/kotak-emerging-equity-factsheet.pdf",
        "doc_format": "pdf",
        "notes": "Kotak Mutual Fund Factsheet"
    },
    {
        "issuer_name": "UTI Mutual Fund",
        "product_name": "UTI Nifty 50 Index Fund",
        "product_category": "mutual_fund",
        "source_url": "https://www.utimf.com/downloads/factsheets/uti-nifty-50-index-factsheet.pdf",
        "doc_format": "pdf",
        "notes": "UTI Index Fund Factsheet"
    }
]
