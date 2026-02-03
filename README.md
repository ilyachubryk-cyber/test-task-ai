# KPA Tool – Income Capitalization

This project implements a simplified Purchase Price Allocation using the German Standard Income Capitalization Approach.

- Backend: FastAPI (JSON API)
- Frontend: Streamlit (interactive UI in 'client/app.py')
- AI Analyst: OpenAI (optional explanation of the valuation)
- CPI Data: Official GENESIS REST API (Destatis)

---

## CPI Data Fetching

CPI data is retrieved from the official GENESIS REST API of the German Federal Statistical Office (Destatis).

- Endpoint: 'POST https://www-genesis.destatis.de/genesisWS/rest/2020/data/table'
- Auth: 'username' and 'password' in request headers (from env).
- Body: 'application/x-www-form-urlencoded' with table id ('61111-0002'), year range, language, etc.

The app requests the previous year, then scans the returned CSV-like content for the row  
'<YEAR> ; October ; <CPI_VALUE> ; ...' and uses that CPI as the October CPI of the year before the purchase date.  

### Why This Approach:

- REST + JSON is easy to integrate and maintain. No HTML parsing or  layout changes.
- No AI for data: The LLM is only used to explain the result (AI Analyst). The CPI value itself always comes from Destatis.

### FastAPI was chosen because it gives:
- Strong typing and validation via Pydantic models.
- Built‑in async support for calling GENESIS and OpenAI without blocking.
- Automatic OpenAPI/Swagger docs with almost no extra code.

---

## Running the App

From the project root:

'''bash
export PYTHONPATH=\"${PYTHONPATH}:<backend_dir_path>\"

# Backend API (FastAPI)
uv run python backend/main.py

# Streamlit UI
uv run streamlit run client/app.py
'''

Set credentials and settings in '.env' (see 'env.example' for the expected variables).


## Possible improvements

Because the retrieved CPI values are static, the app's performance can be improved by introducing a simple caching system (i.e. storing CPI values by years in a file).
