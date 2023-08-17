# Influencer Self-Disclosure Practices on Instagram: A Multi-Country Longitudinal Study

## Description
This repository contains scripts and utilities for experiments related to the paper "Influencer Self-Disclosure Practices on Instagram: A Multi-Country Longitudinal Study". The main script is designed to collect and process data from Instagram using the CrowdTangle API.

## Prerequisites

1. **Python**: The project requires Python 3.9 or higher.

2. **CrowdTangle API Token**: An API token for CrowdTangle is required to fetch data. This token should be set in a `.env` file in the root directory of the project, under the key `API_TOKEN`.

    Example:
    ```
    API_TOKEN="YOUR_API_TOKEN_HERE"
    ```

## CSV File Format: `dataset_accounts.csv`

This file serves as the metadata input for your Instagram data collection and processing. Each row represents an individual Instagram account's metadata. The CSV consists of the following columns:

1. **username** (required): The Instagram handle or username of the account.
   
2. **country** (optional): A country code that represents the primary audience or location of the account. 

3. **size**(optional): The categorization of the account based on its following size (e.g. `micro` or `mega`)

4. **number_of_posts** (optional): The total number of posts made by the account up to the last date of collection.

5. **followers_collection_time** (optional): The follower count of the account at data collection time.

6. **first_post** (required): The earliest date and time (in the format 'YYYY-MM-DD HH:MM:SS') from which posts should be collected for the respective account

7. **last_post** (required): The latest date and time (in the format 'YYYY-MM-DD HH:MM:SS') until which posts should be collected for the respective account.

### Example:
```
username,country,size,number_of_posts,followers_collection_time,first_post,last_post
ab_bowen,US,mega,3652,1626210,2013-06-24 14:01:12,2022-09-15 06:32:49
achrafhakimi,DE,mega,612,10162234,2014-01-19 19:49:42,2022-09-16 12:39:47
```

## Setup & Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/thalesbertaglia/instagram-disclosure-trends
    cd instagram-disclosure-trends
    ```

2. Install dependencies using [Poetry](https://python-poetry.org/docs/):
    ```bash
    poetry install
    ```

3. Activate the virtual environment:
    ```bash
    poetry shell
    ```

## Usage

To run the main script:

```bash
python scripts/collect_data.py [OPTIONS]
```

### Options:
- `--csv_path`: Path to the `dataset_accounts.csv` file. Default is `data/dataset_accounts.csv`.
- `--skip_collection`: If passed, data collection will be skipped.
- `--skip_create_df`: If passed, processing the raw CrowdTangle data into a DataFrame will be skipped.
- `--skip_augmentation`: If passed, augmenting the DataFrame with additional columns will be skipped. Use this option for collecting data from new accounts not included in the original dataset.
- `--post_df_path`: Path to the processed posts df pickle file. Default is `data/df_posts.pkl`.
- `--profile_df_path`: Path to the processed profiles df pickle file. Default is `data/df_profiles.pkl`.

## Troubleshooting
- Ensure that the `.env` file exists in the root directory with the correct API_TOKEN.
- Verify that the CSV file provided contains all the necessary columns.

## License
MIT

## Contact
For any queries or issues, please contact [Thales Bertaglia](mailto:contact@thalesbertaglia.com).
