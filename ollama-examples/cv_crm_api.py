# cv_crm_api.py

import requests
import time

class CVCrmAPI:
    """
    Handles all API communications with the CV CRM, supporting CVDW
    endpoints with robust pagination and rate-limit handling.
    """
    def __init__(self, subdomain: str, email: str, token: str):
        if not all([subdomain, email, token]):
            raise ValueError("Subdomain, Email, and Token are all required.")
        self.base_url = f"https://{subdomain}.cvcrm.com.br/api/v1"
        self.headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'email': email,
            'token': token
        }
        print("[OK] CVCrmAPI initialized and ready.")

    def _make_request(self, method: str, endpoint: str, params: dict = None) -> dict:
        """
        Helper function to make a single, raw request to the API.
        This function will now RAISE exceptions on HTTP errors for the caller to handle.
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, params=params, timeout=30)
            # This line will automatically raise an HTTPError for statuses like 429, 404, 500, etc.
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            # Re-raise the exception so the calling function can catch it and decide what to do.
            raise http_err
        except requests.exceptions.RequestException as err:
            # For other network errors (like a timeout or connection error), we also raise it.
            print(f"❌ A network error occurred: {err}")
            raise err

    def _fetch_all_cvdw_pages(self, endpoint: str, base_params: dict = None) -> list:
        """
        Fetches all records from a CVDW endpoint using robust, continuous pagination
        and an exponential backoff strategy to handle rate limiting (429 errors).
        """
        if base_params is None: base_params = {}
        all_records = []
        page = 1
        base_params['registros_por_pagina'] = 100 

        # --- Configuration for our retry logic ---
        MAX_RETRIES = 5
        BASE_DELAY_SECONDS = 2 # Start with a 2-second delay

        print(f"🔎 Starting full data fetch from CVDW endpoint: {endpoint}...")

        while True:
            current_params = base_params.copy()
            current_params['pagina'] = page
            
            response = None # Initialize response to None for the retry loop
            
            # --- Retry Loop: Try fetching the same page up to MAX_RETRIES times ---
            for attempt in range(MAX_RETRIES):
                try:
                    print(f"    Fetching page {page}, attempt {attempt + 1}/{MAX_RETRIES}...")
                    response = self._make_request("GET", endpoint, params=current_params)
                    # If the request was successful, break out of the retry loop.
                    break 
                except requests.exceptions.HTTPError as e:
                    # Check if the error is specifically '429 Too Many Requests'
                    if e.response.status_code == 429:
                        # Calculate how long to wait, increasing the time with each attempt
                        wait_time = BASE_DELAY_SECONDS * (2 ** attempt)
                        print(f"    ⚠️ Rate limit hit (429). Waiting for {wait_time} seconds before retrying...")
                        time.sleep(wait_time)
                        # The 'continue' is implicit, the loop will go to the next attempt
                    else:
                        # It's a different, unrecoverable HTTP error (e.g., 404 Not Found)
                        print(f"❌ Unrecoverable HTTP error encountered: {e}")
                        # Stop the whole process by re-raising the exception
                        raise e 
            
            # If the response is still None after all retries, something went wrong.
            if response is None:
                print(f"❌ Failed to fetch page {page} after {MAX_RETRIES} attempts. Aborting fetch.")
                break

            # --- Process the successful response ---
            records_on_page = response.get("dados")
            if not records_on_page:
                print("    No more data found on the final page. Concluding fetch.")
                break

            all_records.extend(records_on_page)
            
            if len(records_on_page) < base_params['registros_por_pagina']:
                print("    Partial page returned, indicating this is the final page.")
                break

            page += 1
            # A small, polite sleep between *successful* requests is still a good practice.
            time.sleep(0.5)

        print(f"✅ Finished fetching. Total records retrieved: {len(all_records)}")
        return all_records

    # --- Public API Methods (No changes needed here) ---
    def get_all_clients(self) -> list:
        return self._fetch_all_cvdw_pages("/pessoas")

    def get_cvdw_lead_performance_by_broker(self, start_date: str, end_date: str) -> list:
        endpoint = "/cvdw/leads/corretores"
        params = { "data_inicio": start_date, "data_fim": end_date }
        return self._fetch_all_cvdw_pages(endpoint, params)