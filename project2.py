"""
collect_jobs.py
---------------
Pobiera oferty pracy z JSearch API (RapidAPI), filtruje holenderskie
opisy i zapisuje do CSV.

Użycie:
    pip install requests langdetect pandas
    export RAPIDAPI_KEY="twój_klucz"
    python collect_jobs.py

Wynik: jobs_nl.csv
"""

import os
import time
import requests
import pandas as pd
from langdetect import detect, LangDetectException

# ── Konfiguracja ────────────────────────────────────────────────────────────
API_KEY   = os.environ.get("RAPIDAPI_KEY", "5444c813fdmshab7f8c4bcbb185ep1e0be7jsne5e0826f4206")
HEADERS   = {
    "X-RapidAPI-Key":  "5444c813fdmshab7f8c4bcbb185ep1e0be7jsne5e0826f4206",
    "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
}
ENDPOINT  = "https://jsearch.p.rapidapi.com/search-v2"

# Zapytania targetujące rynek NL — kilka różnych żeby zebrać więcej materiału
QUERIES = QUERIES = [
    "vacatures Nederland",
    "werk Amsterdam",
    "baan Rotterdam",
    "vacature Utrecht",
    "administratief medewerker Nederland",
    "financieel analist Nederland",
    "data engineer Nederland",
    "software developer Nederland",
    "marketing manager Nederland",
    "projectmanager Nederland",
    "accountant Nederland",
    "verpleegkundige Nederland",
    "leraar Nederland",
    "Power BI",
    "Databricks",
    "Data enginner",
    "Product Owner",
    "IT Engineer",
    "Risk data analayst",
    "chauffeur Nederland",
    "klantenservice Nederland",
    "inkoper Nederland",
    "hr medewerker Nederland",
    "jurist Nederland",
    "architect Nederland",
    "monteur Nederland",
]

PAGES_PER_QUERY = 2   # 1 strona = ~10 ofert; 3 strony × 10 zapytań = ~300 ofert
DELAY_SECONDS   = 1.2 # przerwa między requestami (rate limiting)
OUTPUT_FILE     = "/Users/ernestsitterle/Documents/jobs_nl.csv"
# ─────────────────────────────────────────────────────────────────────────────


def fetch_jobs(query: str, page: int) -> list[dict]:
    """Pobiera jedną stronę wyników dla danego query."""
    params = {
        "query":      query,
        "page":       str(page),
        "num_pages":  "1",
        "date_posted": "all",
        "country":    "nl",
        "language":   "nl",
    }
    try:
        r = requests.get(ENDPOINT, headers=HEADERS, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        return data.get("data", {}).get("jobs", [])
    except requests.RequestException as e:
        print(f"  ⚠️  Błąd requestu ({query}, strona {page}): {e}")
        return []


def is_dutch(text: str) -> bool:
    """Zwraca True jeśli tekst jest po niderlandzku."""
    if not text or len(text.strip()) < 50:
        return False
    try:
        return detect(text) == "nl"
    except LangDetectException:
        return False


def collect() -> pd.DataFrame:
    rows = []
    seen_ids = set()

    for query in QUERIES:
        print(f"\n🔍 Query: '{query}'")
        for page in range(1, PAGES_PER_QUERY + 1):
            jobs = fetch_jobs(query, page)
            if not jobs:
                break

            nl_count = 0
            for job in jobs:
                # Zabezpieczenie — pomiń jeśli element nie jest słownikiem
                if not isinstance(job, dict):
                    print(f"  ⚠️  Nieoczekiwany typ elementu: {type(job)} → {str(job)[:100]}")
                    continue
                job_id = job.get("job_id", "")
                if job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                description = job.get("job_description", "")
                if not is_dutch(description):
                    continue

                rows.append({
                    "job_id":          job_id,
                    "job_title":       job.get("job_title", ""),
                    "employer_name":   job.get("employer_name", ""),
                    "job_city":        job.get("job_city", ""),
                    "job_country":     job.get("job_country", ""),
                    "date_posted":     job.get("job_posted_at_datetime_utc", ""),
                    "job_description": description,
                    "job_apply_link":  job.get("job_apply_link", ""),
                })
                nl_count += 1

            print(f"  Strona {page}: {len(jobs)} ofert pobrano, {nl_count} po niderlandzku")
            time.sleep(DELAY_SECONDS)

    df = pd.DataFrame(rows)
    print(f"\n✅ Łącznie unikalnych ofert NL: {len(df)}")
    return df


if __name__ == "__main__":
    df = collect()
    if df.empty:
        print("❌ Brak danych. Sprawdź klucz API i połączenie.")
    else:
        df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
        print(f"💾 Zapisano do: {OUTPUT_FILE}")
        print(df[["job_title", "employer_name", "job_city"]].head(10).to_string())
