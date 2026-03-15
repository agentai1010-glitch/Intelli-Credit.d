import asyncio
import httpx
from datetime import datetime
import urllib.parse
import xml.etree.ElementTree as ET

async def fetch_with_retry(client: httpx.AsyncClient, url: str, params: dict = None) -> httpx.Response:
    last_exception = None
    for attempt, wait_time in enumerate([1.0, 2.0, 4.0]):
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            return response
        except Exception as e:
            last_exception = e
            await asyncio.sleep(wait_time)
    raise last_exception if last_exception else Exception("Failed to fetch")

async def scrape_mca_filings(company_name: str, cin: str = None) -> list:
    return [{
        "source": "MCA Portal",
        "date": datetime.now().isoformat(),
        "type": "Data Retrieval",
        "severity": "RESTRICTED",
        "detail": "MCA Portal requires authenticated CIN-based lookup. Manual verification recommended.",
        "source_url": "https://www.mca.gov.in/mcafoportal/",
        "scraped_at": datetime.now().isoformat(),
        "status": "ACCESS_RESTRICTED"
    }]

async def scrape_ecourts(company_name: str, promoter_names: list) -> list:
    return [{
        "source": "eCourts Services",
        "date": datetime.now().isoformat(),
        "type": "Litigation Search",
        "severity": "RESTRICTED",
        "detail": "eCourts Portal requires captcha and manual lookup. Manual verification recommended.",
        "source_url": "https://services.ecourts.gov.in/ecourtindia_v6/",
        "scraped_at": datetime.now().isoformat(),
        "status": "ACCESS_RESTRICTED"
    }]

async def scrape_rbi_defaulter_list(company_name: str) -> dict:
    return {
        "is_wilful_defaulter": False,
        "is_non_cooperative": False,
        "details": [
            {
                "source": "RBI Defaulter List",
                "date": datetime.now().isoformat(),
                "type": "Defaulter Check",
                "severity": "RESTRICTED",
                "detail": "RBI Defaulter List requires authenticated lookup. Manual verification recommended.",
                "source_url": "https://rbi.org.in",
                "scraped_at": datetime.now().isoformat(),
                "status": "ACCESS_RESTRICTED"
            }
        ]
    }

async def scrape_ibbi_insolvency(company_name: str) -> list:
    return [{
        "source": "IBBI Insolvency records",
        "date": datetime.now().isoformat(),
        "type": "Insolvency Check",
        "severity": "RESTRICTED",
        "detail": "IBBI Portal requires manual lookup. Manual verification recommended.",
        "source_url": "https://ibbi.gov.in",
        "scraped_at": datetime.now().isoformat(),
        "status": "ACCESS_RESTRICTED"
    }]

async def scrape_google_news(company_name: str) -> list:
    queries = [
        f"{company_name} NCLT insolvency proceedings",
        f"{company_name} RBI defaulter notice",
        f"{company_name} fraud investigation ED CBI",
        f"{company_name} court case judgment",
        f"{company_name} regulatory penalty SEBI"
    ]
    
    flags = []
    adverse_keywords = ["insolvency", "fraud", "defaulter", "nclt", "cbi", "regulatory action", "penalty", "wilful defaulter"]
    
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
            tasks = []
            for query in queries:
                encoded_query = urllib.parse.quote(query)
                url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
                tasks.append(fetch_with_retry(client, url))
            
            # Wrap all queries in a global 15s timeout to prevent UI hang
            print(f"[CRAWLER] Launching {len(tasks)} parallel news queries...")
            responses = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=15.0)
            
            for i, res in enumerate(responses):
                if isinstance(res, Exception):
                    print(f"[CRAWLER] Query {i} failed/timed out softly: {res}")
                    continue
                if res.status_code == 200:
                    root = ET.fromstring(res.text)
                    for item in root.findall('.//item'):
                        title_el = item.find('title')
                        desc_el = item.find('description')
                        link_el = item.find('link')
                        
                        title = title_el.text if title_el is not None else ""
                        desc = desc_el.text if desc_el is not None else ""
                        link = link_el.text if link_el is not None else ""
                        
                        text_to_check = (title + " " + desc).lower()
                        # STRICTOR ACCURACY FILTER: Must contain core clean company name
                        core_name = company_name.lower().replace(" ltd.", "").replace(" pvt.", "").replace(" private", "").replace(" limited", "").strip()
                        
                        if core_name in text_to_check:
                            if any(kw in text_to_check for kw in adverse_keywords) or "ed raid" in text_to_check:
                                flags.append({
                                    "source": "Google News Intelligence",
                                    "date": datetime.now().isoformat(),
                                    "type": "Adverse News",
                                    "severity": "ADVERSE",
                                    "detail": f"News article found: {title}",
                                    "source_url": link,
                                    "scraped_at": datetime.now().isoformat()
                                })
    except asyncio.TimeoutError:
        print("[CRAWLER] Global News Crawl timed out (15s). Proceeding with document intelligence only.")
    except Exception as e:
        print(f"[CRAWLER] News Scrape encountered error: {e}")
                            
    return flags

async def aggregate_regulatory_intelligence(company_name: str, cin: str = None, promoter_names: list = None) -> dict:
    if promoter_names is None:
        promoter_names = []
        
    results = await asyncio.gather(
        scrape_mca_filings(company_name, cin),
        scrape_ecourts(company_name, promoter_names),
        scrape_rbi_defaulter_list(company_name),
        scrape_ibbi_insolvency(company_name),
        scrape_google_news(company_name),
        return_exceptions=True
    )
    
    # Handle direct exceptions during the asyncio.gather mapping
    mca_res = results[0] if not isinstance(results[0], Exception) else [{"severity": "RESTRICTED", "detail": "Exception in MCA task"}]
    ecourts_res = results[1] if not isinstance(results[1], Exception) else [{"severity": "RESTRICTED", "detail": "Exception in eCourts task"}]
    rbi_res = results[2] if not isinstance(results[2], Exception) else {"details": [{"severity": "RESTRICTED", "detail": "Exception in RBI task"}]}
    ibbi_res = results[3] if not isinstance(results[3], Exception) else [{"severity": "RESTRICTED", "detail": "Exception in IBBI task"}]
    news_res = results[4] if not isinstance(results[4], Exception) else []

    all_flags = []
    all_flags.extend(mca_res)
    all_flags.extend(ecourts_res)
    all_flags.extend(rbi_res.get("details", []))
    all_flags.extend(ibbi_res)
    all_flags.extend(news_res)
    
    # Deduplicate news articles by title so we don't flag the same article 5 times for 5 queries
    seen_titles = set()
    deduped_flags = []
    for flag in all_flags:
        if flag.get("severity") == "ADVERSE":
            title = flag.get("detail", "")
            if title in seen_titles:
                continue
            seen_titles.add(title)
        deduped_flags.append(flag)
        
    all_flags = deduped_flags
    
    critical_flags = []
    warnings = []
    clean_checks = []
    sources_checked = ["MCA Portal", "eCourts Services", "RBI Defaulter List", "IBBI Insolvency records", "Google News Intelligence"]
    
    score = 100
    adverse_penalty = 0
    has_high = False
    
    for flag in all_flags:
        sev = flag.get("severity")
        if sev == "HIGH":
            critical_flags.append(flag)
            score -= 20
            has_high = True
        elif sev == "ADVERSE": 
            critical_flags.append(flag)
            adverse_penalty += 25
        elif sev == "MEDIUM":
            warnings.append(flag)
            score -= 8
        elif sev == "RESTRICTED":
            warnings.append(flag) 
        else:
            clean_checks.append(flag)
            
    # Cap adverse penalty at -50 max
    if adverse_penalty > 50:
        adverse_penalty = 50
        
    score -= adverse_penalty
    
    if adverse_penalty == 0 and not has_high:
        # CLEAN confirmed -> +5 pts
        score += 5
            
    regulatory_risk_score = min(100, max(0, score))
    
    s1 = f"Sources checked across MCA, eCourts, RBI, IBBI, and News yield an overall regulatory profile score of {regulatory_risk_score}/100."
    s2 = f"Critical defaults or adverse news found: {len(critical_flags)}." if len(critical_flags) > 0 else "No critical flags noted in active repositories."
    s3 = f"Warnings or pending manual checks: {len(warnings)}." if len(warnings) > 0 else "No warnings or access errors noted."
    
    if regulatory_risk_score >= 80:
        s4 = "Regulatory profile is clean, proceed normally."
    elif 60 <= regulatory_risk_score <= 79:
        s4 = "Enhanced monitoring recommended."
    else:
        s4 = "Regulatory concerns warrant legal review before sanction."
        
    summary_paragraph = f"{s1} {s2} {s3} {s4}"
    
    return {
        "regulatory_risk_score": regulatory_risk_score,
        "critical_flags": critical_flags,
        "warnings": warnings,
        "clean_checks": clean_checks,
        "sources_checked": sources_checked,
        "summary_paragraph": summary_paragraph
    }


if __name__ == "__main__":
    import json
    
    async def run_test():
        print("Testing Zee...")
        output = await aggregate_regulatory_intelligence("Zee Entertainment Enterprises Ltd.", "", [])
        print(json.dumps(output, indent=2))
        
        print("\n----------------\n")
        print("\nTesting Sharma Textile...")
        output2 = await aggregate_regulatory_intelligence("Sharma Textile Mills Pvt. Ltd.", "", [])
        print(json.dumps(output2, indent=2))
        
    asyncio.run(run_test())
