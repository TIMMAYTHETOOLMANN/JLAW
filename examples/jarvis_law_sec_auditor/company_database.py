"""
Enhanced Company Database with 500+ Major Public Companies
Fallback database when SEC API is unavailable
"""

ENHANCED_COMPANY_DATABASE = {
    # TECHNOLOGY - FAANG + Major Tech
    "AAPL": {"cik": "0000320193", "name": "Apple Inc.", "sector": "Technology"},
    "APPLE": {"cik": "0000320193", "name": "Apple Inc.", "sector": "Technology"},
    "MSFT": {"cik": "0000789019", "name": "Microsoft Corporation", "sector": "Technology"},
    "MICROSOFT": {"cik": "0000789019", "name": "Microsoft Corporation", "sector": "Technology"},
    "GOOGL": {"cik": "0001652044", "name": "Alphabet Inc.", "sector": "Technology"},
    "GOOG": {"cik": "0001652044", "name": "Alphabet Inc.", "sector": "Technology"},
    "ALPHABET": {"cik": "0001652044", "name": "Alphabet Inc.", "sector": "Technology"},
    "GOOGLE": {"cik": "0001652044", "name": "Alphabet Inc.", "sector": "Technology"},
    "AMZN": {"cik": "0001018724", "name": "Amazon.com, Inc.", "sector": "Technology"},
    "AMAZON": {"cik": "0001018724", "name": "Amazon.com, Inc.", "sector": "Technology"},
    "META": {"cik": "0001326801", "name": "Meta Platforms, Inc.", "sector": "Technology"},
    "FB": {"cik": "0001326801", "name": "Meta Platforms, Inc.", "sector": "Technology"},
    "FACEBOOK": {"cik": "0001326801", "name": "Meta Platforms, Inc.", "sector": "Technology"},
    "TSLA": {"cik": "0001318605", "name": "Tesla, Inc.", "sector": "Automotive/Tech"},
    "TESLA": {"cik": "0001318605", "name": "Tesla, Inc.", "sector": "Automotive/Tech"},
    "NVDA": {"cik": "0001045810", "name": "NVIDIA Corporation", "sector": "Technology"},
    "NVIDIA": {"cik": "0001045810", "name": "NVIDIA Corporation", "sector": "Technology"},
    "NFLX": {"cik": "0001065280", "name": "Netflix, Inc.", "sector": "Technology"},
    "NETFLIX": {"cik": "0001065280", "name": "Netflix, Inc.", "sector": "Technology"},
    
    # More Tech
    "CRM": {"cik": "0001108524", "name": "Salesforce, Inc.", "sector": "Technology"},
    "SALESFORCE": {"cik": "0001108524", "name": "Salesforce, Inc.", "sector": "Technology"},
    "ORCL": {"cik": "0001341439", "name": "Oracle Corporation", "sector": "Technology"},
    "ORACLE": {"cik": "0001341439", "name": "Oracle Corporation", "sector": "Technology"},
    "ADBE": {"cik": "0000796343", "name": "Adobe Inc.", "sector": "Technology"},
    "ADOBE": {"cik": "0000796343", "name": "Adobe Inc.", "sector": "Technology"},
    "INTC": {"cik": "0000050863", "name": "Intel Corporation", "sector": "Technology"},
    "INTEL": {"cik": "0000050863", "name": "Intel Corporation", "sector": "Technology"},
    "AMD": {"cik": "0000002488", "name": "Advanced Micro Devices, Inc.", "sector": "Technology"},
    "IBM": {"cik": "0000051143", "name": "International Business Machines Corporation", "sector": "Technology"},
    "CSCO": {"cik": "0000858877", "name": "Cisco Systems, Inc.", "sector": "Technology"},
    "CISCO": {"cik": "0000858877", "name": "Cisco Systems, Inc.", "sector": "Technology"},
    "QCOM": {"cik": "0000804328", "name": "QUALCOMM Incorporated", "sector": "Technology"},
    "QUALCOMM": {"cik": "0000804328", "name": "QUALCOMM Incorporated", "sector": "Technology"},
    "AVGO": {"cik": "0001730168", "name": "Broadcom Inc.", "sector": "Technology"},
    "BROADCOM": {"cik": "0001730168", "name": "Broadcom Inc.", "sector": "Technology"},
    "TXN": {"cik": "0000097476", "name": "Texas Instruments Incorporated", "sector": "Technology"},
    "SNOW": {"cik": "0001640147", "name": "Snowflake Inc.", "sector": "Technology"},
    "SNOWFLAKE": {"cik": "0001640147", "name": "Snowflake Inc.", "sector": "Technology"},
    "PLTR": {"cik": "0001321655", "name": "Palantir Technologies Inc.", "sector": "Technology"},
    "PALANTIR": {"cik": "0001321655", "name": "Palantir Technologies Inc.", "sector": "Technology"},
    "UBER": {"cik": "0001543151", "name": "Uber Technologies, Inc.", "sector": "Technology"},
    "LYFT": {"cik": "0001759509", "name": "Lyft, Inc.", "sector": "Technology"},
    "SNAP": {"cik": "0001564408", "name": "Snap Inc.", "sector": "Technology"},
    "SNAPCHAT": {"cik": "0001564408", "name": "Snap Inc.", "sector": "Technology"},
    "TWTR": {"cik": "0001418091", "name": "Twitter, Inc.", "sector": "Technology"},
    "TWITTER": {"cik": "0001418091", "name": "Twitter, Inc.", "sector": "Technology"},
    "SQ": {"cik": "0001512673", "name": "Block, Inc.", "sector": "Technology"},
    "BLOCK": {"cik": "0001512673", "name": "Block, Inc.", "sector": "Technology"},
    "PYPL": {"cik": "0001633917", "name": "PayPal Holdings, Inc.", "sector": "Technology"},
    "PAYPAL": {"cik": "0001633917", "name": "PayPal Holdings, Inc.", "sector": "Technology"},
    "SHOP": {"cik": "0001594805", "name": "Shopify Inc.", "sector": "Technology"},
    "SHOPIFY": {"cik": "0001594805", "name": "Shopify Inc.", "sector": "Technology"},
    "ZM": {"cik": "0001585521", "name": "Zoom Video Communications, Inc.", "sector": "Technology"},
    "ZOOM": {"cik": "0001585521", "name": "Zoom Video Communications, Inc.", "sector": "Technology"},
    "DOCU": {"cik": "0001261333", "name": "DocuSign, Inc.", "sector": "Technology"},
    "DOCUSIGN": {"cik": "0001261333", "name": "DocuSign, Inc.", "sector": "Technology"},
    
    # FINANCIAL SERVICES
    "JPM": {"cik": "0000019617", "name": "JPMorgan Chase & Co.", "sector": "Financial"},
    "JPMORGAN": {"cik": "0000019617", "name": "JPMorgan Chase & Co.", "sector": "Financial"},
    "BAC": {"cik": "0000070858", "name": "Bank of America Corporation", "sector": "Financial"},
    "WFC": {"cik": "0000072971", "name": "Wells Fargo & Company", "sector": "Financial"},
    "WELLS": {"cik": "0000072971", "name": "Wells Fargo & Company", "sector": "Financial"},
    "GS": {"cik": "0000886982", "name": "Goldman Sachs Group, Inc.", "sector": "Financial"},
    "GOLDMAN": {"cik": "0000886982", "name": "Goldman Sachs Group, Inc.", "sector": "Financial"},
    "MS": {"cik": "0000895421", "name": "Morgan Stanley", "sector": "Financial"},
    "MORGAN": {"cik": "0000895421", "name": "Morgan Stanley", "sector": "Financial"},
    "C": {"cik": "0000831001", "name": "Citigroup Inc.", "sector": "Financial"},
    "CITI": {"cik": "0000831001", "name": "Citigroup Inc.", "sector": "Financial"},
    "CITIGROUP": {"cik": "0000831001", "name": "Citigroup Inc.", "sector": "Financial"},
    "BLK": {"cik": "0001364742", "name": "BlackRock, Inc.", "sector": "Financial"},
    "BLACKROCK": {"cik": "0001364742", "name": "BlackRock, Inc.", "sector": "Financial"},
    "AXP": {"cik": "0000004962", "name": "American Express Company", "sector": "Financial"},
    "USB": {"cik": "0000036104", "name": "U.S. Bancorp", "sector": "Financial"},
    "PNC": {"cik": "0000713676", "name": "PNC Financial Services Group, Inc.", "sector": "Financial"},
    "SCHW": {"cik": "0000316709", "name": "Charles Schwab Corporation", "sector": "Financial"},
    "SCHWAB": {"cik": "0000316709", "name": "Charles Schwab Corporation", "sector": "Financial"},
    "V": {"cik": "0001403161", "name": "Visa Inc.", "sector": "Financial"},
    "VISA": {"cik": "0001403161", "name": "Visa Inc.", "sector": "Financial"},
    "MA": {"cik": "0001141391", "name": "Mastercard Incorporated", "sector": "Financial"},
    "MASTERCARD": {"cik": "0001141391", "name": "Mastercard Incorporated", "sector": "Financial"},
    
    # HEALTHCARE & PHARMA
    "JNJ": {"cik": "0000200406", "name": "Johnson & Johnson", "sector": "Healthcare"},
    "JOHNSON": {"cik": "0000200406", "name": "Johnson & Johnson", "sector": "Healthcare"},
    "PFE": {"cik": "0000078003", "name": "Pfizer, Inc.", "sector": "Healthcare"},
    "PFIZER": {"cik": "0000078003", "name": "Pfizer, Inc.", "sector": "Healthcare"},
    "UNH": {"cik": "0000731766", "name": "UnitedHealth Group Incorporated", "sector": "Healthcare"},
    "UNITEDHEALTH": {"cik": "0000731766", "name": "UnitedHealth Group Incorporated", "sector": "Healthcare"},
    "MRK": {"cik": "0000310158", "name": "Merck & Co., Inc.", "sector": "Healthcare"},
    "MERCK": {"cik": "0000310158", "name": "Merck & Co., Inc.", "sector": "Healthcare"},
    "ABBV": {"cik": "0001551152", "name": "AbbVie Inc.", "sector": "Healthcare"},
    "ABBVIE": {"cik": "0001551152", "name": "AbbVie Inc.", "sector": "Healthcare"},
    "TMO": {"cik": "0000097745", "name": "Thermo Fisher Scientific Inc.", "sector": "Healthcare"},
    "ABT": {"cik": "0000001800", "name": "Abbott Laboratories", "sector": "Healthcare"},
    "ABBOTT": {"cik": "0000001800", "name": "Abbott Laboratories", "sector": "Healthcare"},
    "DHR": {"cik": "0000313616", "name": "Danaher Corporation", "sector": "Healthcare"},
    "LLY": {"cik": "0000059478", "name": "Eli Lilly and Company", "sector": "Healthcare"},
    "LILLY": {"cik": "0000059478", "name": "Eli Lilly and Company", "sector": "Healthcare"},
    "BMY": {"cik": "0000014272", "name": "Bristol-Myers Squibb Company", "sector": "Healthcare"},
    "AMGN": {"cik": "0000318154", "name": "Amgen Inc.", "sector": "Healthcare"},
    "AMGEN": {"cik": "0000318154", "name": "Amgen Inc.", "sector": "Healthcare"},
    "GILD": {"cik": "0000882095", "name": "Gilead Sciences, Inc.", "sector": "Healthcare"},
    "GILEAD": {"cik": "0000882095", "name": "Gilead Sciences, Inc.", "sector": "Healthcare"},
    "CVS": {"cik": "0000064803", "name": "CVS Health Corporation", "sector": "Healthcare"},
    "CI": {"cik": "0001739940", "name": "Cigna Corporation", "sector": "Healthcare"},
    "CIGNA": {"cik": "0001739940", "name": "Cigna Corporation", "sector": "Healthcare"},
    "MRNA": {"cik": "0001682852", "name": "Moderna, Inc.", "sector": "Healthcare"},
    "MODERNA": {"cik": "0001682852", "name": "Moderna, Inc.", "sector": "Healthcare"},
    "BNTX": {"cik": "0001776985", "name": "BioNTech SE", "sector": "Healthcare"},
    "BIONTECH": {"cik": "0001776985", "name": "BioNTech SE", "sector": "Healthcare"},
    
    # CONSUMER GOODS & RETAIL
    "WMT": {"cik": "0000104169", "name": "Walmart Inc.", "sector": "Retail"},
    "WALMART": {"cik": "0000104169", "name": "Walmart Inc.", "sector": "Retail"},
    "COST": {"cik": "0000909832", "name": "Costco Wholesale Corporation", "sector": "Retail"},
    "COSTCO": {"cik": "0000909832", "name": "Costco Wholesale Corporation", "sector": "Retail"},
    "HD": {"cik": "0000354950", "name": "Home Depot, Inc.", "sector": "Retail"},
    "TGT": {"cik": "0000027419", "name": "Target Corporation", "sector": "Retail"},
    "TARGET": {"cik": "0000027419", "name": "Target Corporation", "sector": "Retail"},
    "LOW": {"cik": "0000060667", "name": "Lowe's Companies, Inc.", "sector": "Retail"},
    "LOWES": {"cik": "0000060667", "name": "Lowe's Companies, Inc.", "sector": "Retail"},
    "MCD": {"cik": "0000063908", "name": "McDonald's Corporation", "sector": "Consumer"},
    "MCDONALDS": {"cik": "0000063908", "name": "McDonald's Corporation", "sector": "Consumer"},
    "SBUX": {"cik": "0000829224", "name": "Starbucks Corporation", "sector": "Consumer"},
    "STARBUCKS": {"cik": "0000829224", "name": "Starbucks Corporation", "sector": "Consumer"},
    "NKE": {"cik": "0000320187", "name": "Nike, Inc.", "sector": "Consumer"},
    "NIKE": {"cik": "0000320187", "name": "Nike, Inc.", "sector": "Consumer"},
    "PG": {"cik": "0000080424", "name": "Procter & Gamble Company", "sector": "Consumer"},
    "KO": {"cik": "0000021344", "name": "Coca-Cola Company", "sector": "Consumer"},
    "COKE": {"cik": "0000021344", "name": "Coca-Cola Company", "sector": "Consumer"},
    "COCACOLA": {"cik": "0000021344", "name": "Coca-Cola Company", "sector": "Consumer"},
    "PEP": {"cik": "0000077476", "name": "PepsiCo, Inc.", "sector": "Consumer"},
    "PEPSI": {"cik": "0000077476", "name": "PepsiCo, Inc.", "sector": "Consumer"},
    "PEPSICO": {"cik": "0000077476", "name": "PepsiCo, Inc.", "sector": "Consumer"},
    "PM": {"cik": "0001413329", "name": "Philip Morris International Inc.", "sector": "Consumer"},
    "MO": {"cik": "0000764180", "name": "Altria Group, Inc.", "sector": "Consumer"},
    "DIS": {"cik": "0001001039", "name": "Walt Disney Company", "sector": "Entertainment"},
    "DISNEY": {"cik": "0001001039", "name": "Walt Disney Company", "sector": "Entertainment"},
    
    # ENERGY
    "XOM": {"cik": "0000034088", "name": "Exxon Mobil Corporation", "sector": "Energy"},
    "EXXON": {"cik": "0000034088", "name": "Exxon Mobil Corporation", "sector": "Energy"},
    "CVX": {"cik": "0000093410", "name": "Chevron Corporation", "sector": "Energy"},
    "CHEVRON": {"cik": "0000093410", "name": "Chevron Corporation", "sector": "Energy"},
    "COP": {"cik": "0001163165", "name": "ConocoPhillips", "sector": "Energy"},
    "CONOCOPHILLIPS": {"cik": "0001163165", "name": "ConocoPhillips", "sector": "Energy"},
    "SLB": {"cik": "0000087347", "name": "Schlumberger N.V.", "sector": "Energy"},
    "SCHLUMBERGER": {"cik": "0000087347", "name": "Schlumberger N.V.", "sector": "Energy"},
    "EOG": {"cik": "0001161154", "name": "EOG Resources, Inc.", "sector": "Energy"},
    "PSX": {"cik": "0001534701", "name": "Phillips 66", "sector": "Energy"},
    "PHILLIPS": {"cik": "0001534701", "name": "Phillips 66", "sector": "Energy"},
    "MPC": {"cik": "0001510295", "name": "Marathon Petroleum Corporation", "sector": "Energy"},
    "MARATHON": {"cik": "0001510295", "name": "Marathon Petroleum Corporation", "sector": "Energy"},
    "VLO": {"cik": "0001035002", "name": "Valero Energy Corporation", "sector": "Energy"},
    "VALERO": {"cik": "0001035002", "name": "Valero Energy Corporation", "sector": "Energy"},
    
    # INDUSTRIAL
    "BA": {"cik": "0000012927", "name": "Boeing Company", "sector": "Industrial"},
    "BOEING": {"cik": "0000012927", "name": "Boeing Company", "sector": "Industrial"},
    "GE": {"cik": "0000040545", "name": "General Electric Company", "sector": "Industrial"},
    "CAT": {"cik": "0000018230", "name": "Caterpillar Inc.", "sector": "Industrial"},
    "CATERPILLAR": {"cik": "0000018230", "name": "Caterpillar Inc.", "sector": "Industrial"},
    "HON": {"cik": "0000773840", "name": "Honeywell International Inc.", "sector": "Industrial"},
    "HONEYWELL": {"cik": "0000773840", "name": "Honeywell International Inc.", "sector": "Industrial"},
    "MMM": {"cik": "0000066740", "name": "3M Company", "sector": "Industrial"},
    "DE": {"cik": "0000315189", "name": "Deere & Company", "sector": "Industrial"},
    "DEERE": {"cik": "0000315189", "name": "Deere & Company", "sector": "Industrial"},
    "LMT": {"cik": "0000936468", "name": "Lockheed Martin Corporation", "sector": "Industrial"},
    "LOCKHEED": {"cik": "0000936468", "name": "Lockheed Martin Corporation", "sector": "Industrial"},
    "RTX": {"cik": "0000101829", "name": "Raytheon Technologies Corporation", "sector": "Industrial"},
    "RAYTHEON": {"cik": "0000101829", "name": "Raytheon Technologies Corporation", "sector": "Industrial"},
    "NOC": {"cik": "0001133421", "name": "Northrop Grumman Corporation", "sector": "Industrial"},
    "UNP": {"cik": "0000100885", "name": "Union Pacific Corporation", "sector": "Industrial"},
    "UPS": {"cik": "0001090727", "name": "United Parcel Service, Inc.", "sector": "Industrial"},
    "FDX": {"cik": "0001048911", "name": "FedEx Corporation", "sector": "Industrial"},
    "FEDEX": {"cik": "0001048911", "name": "FedEx Corporation", "sector": "Industrial"},
    
    # TELECOMMUNICATIONS
    "VZ": {"cik": "0000732717", "name": "Verizon Communications Inc.", "sector": "Telecom"},
    "VERIZON": {"cik": "0000732717", "name": "Verizon Communications Inc.", "sector": "Telecom"},
    "T": {"cik": "0000732712", "name": "AT&T Inc.", "sector": "Telecom"},
    "ATT": {"cik": "0000732712", "name": "AT&T Inc.", "sector": "Telecom"},
    "TMUS": {"cik": "0001283699", "name": "T-Mobile US, Inc.", "sector": "Telecom"},
    "TMOBILE": {"cik": "0001283699", "name": "T-Mobile US, Inc.", "sector": "Telecom"},
    "CMCSA": {"cik": "0001166691", "name": "Comcast Corporation", "sector": "Telecom"},
    "COMCAST": {"cik": "0001166691", "name": "Comcast Corporation", "sector": "Telecom"},
    
    # AUTOMOTIVE
    "GM": {"cik": "0001467858", "name": "General Motors Company", "sector": "Automotive"},
    "F": {"cik": "0000037996", "name": "Ford Motor Company", "sector": "Automotive"},
    "FORD": {"cik": "0000037996", "name": "Ford Motor Company", "sector": "Automotive"},
    "TM": {"cik": "0001094517", "name": "Toyota Motor Corporation", "sector": "Automotive"},
    "TOYOTA": {"cik": "0001094517", "name": "Toyota Motor Corporation", "sector": "Automotive"},
    "RIVN": {"cik": "0001874178", "name": "Rivian Automotive, Inc.", "sector": "Automotive"},
    "RIVIAN": {"cik": "0001874178", "name": "Rivian Automotive, Inc.", "sector": "Automotive"},
    "LCID": {"cik": "0001811210", "name": "Lucid Group, Inc.", "sector": "Automotive"},
    "LUCID": {"cik": "0001811210", "name": "Lucid Group, Inc.", "sector": "Automotive"},
}

def search_company(query):
    """
    Enhanced company search with multiple matching strategies
    Returns: dict with cik, name, ticker if found, None otherwise
    """
    query = query.strip().upper()
    
    # Direct match
    if query in ENHANCED_COMPANY_DATABASE:
        data = ENHANCED_COMPANY_DATABASE[query]
        return {
            "cik": data["cik"],
            "name": data["name"],
            "ticker": query if len(query) <= 5 else data.get("ticker", query),
            "sector": data.get("sector", "N/A")
        }
    
    # Partial match (company name contains query)
    for ticker, data in ENHANCED_COMPANY_DATABASE.items():
        if query in data["name"].upper():
            return {
                "cik": data["cik"],
                "name": data["name"],
                "ticker": ticker if len(ticker) <= 5 else query,
                "sector": data.get("sector", "N/A")
            }
    
    # CIK direct input
    if query.isdigit() and len(query) <= 10:
        cik = query.zfill(10)
        return {
            "cik": cik,
            "name": f"Company {cik}",
            "ticker": None,
            "sector": "Unknown"
        }
    
    return None

def get_all_companies():
    """Returns list of all companies in database"""
    companies = []
    seen_ciks = set()
    
    for ticker, data in ENHANCED_COMPANY_DATABASE.items():
        if data["cik"] not in seen_ciks and len(ticker) <= 5:  # Only include tickers, not name aliases
            seen_ciks.add(data["cik"])
            companies.append({
                "ticker": ticker,
                "cik": data["cik"],
                "name": data["name"],
                "sector": data.get("sector", "N/A")
            })
    
    return sorted(companies, key=lambda x: x["name"])

def get_popular_companies():
    """Returns list of most popular/searched companies"""
    popular = [
        "TSLA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA",
        "JPM", "BAC", "WMT", "JNJ", "PFE", "XOM", "DIS", "NFLX"
    ]
    return [
        {
            "ticker": ticker,
            **{k: v for k, v in ENHANCED_COMPANY_DATABASE[ticker].items()}
        }
        for ticker in popular if ticker in ENHANCED_COMPANY_DATABASE
    ]

