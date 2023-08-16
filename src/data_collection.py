import time
import json
import logging
import requests
from typing import Optional
from pathlib import Path
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_fixed, after_log, RetryError


BASE_URL = f"https://api.crowdtangle.com/posts?token="
SLEEP_DURATION_IN_SEC = 12
RETRY_LIMIT = 10
LOG_FORMAT = "%(asctime)s — %(levelname)s — %(message)s"
DATA_PATH = Path("./data/crowdtangle_data/")
LOG_PATH = DATA_PATH / "logs"
DATA_PATH.mkdir(parents=True, exist_ok=True)
LOG_PATH.mkdir(exist_ok=True)
HTTP_SUCCESS = 200
DEFAULT_FILE_NAME = "log.txt"
PROGRESS_FILE = DATA_PATH / "progress.txt"

# Setup logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Create a file handler
file_handler = logging.FileHandler(LOG_PATH / DEFAULT_FILE_NAME)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# Add both handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def construct_url(base_url: str, api_token: str, params: dict) -> str:
    return f"{base_url}{api_token}&{'&'.join(f'{key}={value}' for key, value in params.items())}"


def store_response(response: dict, account: str, target_year: int, page: int) -> None:
    account_path = DATA_PATH / account
    account_path.mkdir(parents=True, exist_ok=True)
    json_file_path = account_path / f"{account}_{target_year}_{page}.json"
    with json_file_path.open("w") as file:
        json.dump(response, file)


def record_error(
    account: str, target_year: int, error_msg: str, file_name: str = DEFAULT_FILE_NAME
) -> None:
    with (LOG_PATH / file_name).open("w") as file:
        file.write(f"{account}\t{target_year}\t{error_msg}\n")


def iterate_year_ranges(start_date, end_date):
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    current_year = start_date.year
    while current_year <= end_date.year:
        year_start = (
            start_date
            if current_year == start_date.year
            else datetime(current_year, 1, 1)
        )
        year_end = min(datetime(current_year, 12, 31), end_date)
        yield year_start.strftime("%Y-%m-%d"), year_end.strftime("%Y-%m-%d")
        current_year += 1


@retry(
    stop=stop_after_attempt(RETRY_LIMIT),
    wait=wait_fixed(SLEEP_DURATION_IN_SEC),
    after=after_log(logger, logging.DEBUG),
)
def retrieve_posts(
    url: str, account: str, target_year: int, page_number: int
) -> Optional[dict]:
    logger.info(
        f"Retrieving posts for {account} in the year {target_year}... Page {page_number}"
    )
    try:
        response = requests.get(url).json()
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from URL: {url} on Page {page_number}")
        return None

    response_status = response.get("status")
    if response_status == HTTP_SUCCESS:
        logger.info(f"Successfully fetched data for Page {page_number}")
        store_response(response, account, target_year, page_number)
        return response
    elif response_status == 429:  # Handle rate limit error
        logger.warning(
            f"Rate limit exceeded for {url} on Page {page_number}: {response}. Sleeping for 65 seconds..."
        )
        time.sleep(
            65
        )  # Sleeping for a little over a minute to ensure the rate limit resets
        raise requests.exceptions.RequestException(
            "Rate limit exceeded and sleeping done. Retrying..."
        )
    else:
        record_error(
            account,
            target_year,
            f"{response_status}\t{response.get('message', 'No message')}",
        )
        logger.warning(f"HTTP Error for {url} on Page {page_number}: {response}")
        return None


def fetch_posts_for_accounts(
    accounts: list[tuple[str, str, str]], api_token: str
) -> None:
    for account_name, start_date, end_date in accounts:
        for start_date_i, end_date_i in iterate_year_ranges(start_date, end_date):
            target_year = datetime.strptime(start_date_i, "%Y-%m-%d").year
            params = {
                "accounts": account_name,
                "startDate": start_date_i,
                "endDate": end_date_i,
                "includeHistory": "false",
                "sortBy": "date",
                "count": "100",
            }
            url = construct_url(BASE_URL, api_token, params)
            page_counter = 1
            try:
                response = retrieve_posts(url, account_name, target_year, page_counter)
                while response and (
                    next_page_url := response.get("result", {})
                    .get("pagination", {})
                    .get("nextPage")
                ):
                    time.sleep(SLEEP_DURATION_IN_SEC)
                    page_counter += 1
                    response = retrieve_posts(
                        next_page_url, account_name, target_year, page_counter
                    )
            except RetryError:
                logger.error(
                    f"Failed to fetch data for {account_name}: {target_year} after {RETRY_LIMIT} attempts."
                )
