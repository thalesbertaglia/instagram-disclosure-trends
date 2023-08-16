import os
import argparse
import logging

import pandas as pd
from dotenv import load_dotenv

from src.data_collection import fetch_posts_for_accounts
from src.data_processing import (
    process_crowdtangle_data_directory,
    filter_processed_posts,
)


def load_env():
    if not load_dotenv():
        logging.error(
            "Failed to load environment variables from .env file. Ensure the file exists."
        )
        exit(1)

    API_TOKEN = os.getenv("API_TOKEN")
    if not API_TOKEN:
        logging.error(
            "API_TOKEN not found in environment variables. Ensure it's set in the .env file."
        )
        exit(1)

    return API_TOKEN


def get_account_tuples(metadata):
    """Extract account tuples from metadata DataFrame."""
    tuples = []
    tuples_full_date = []

    for _, row in metadata.iterrows():
        first_date = row["first_post"].split()[0]
        last_date = row["last_post"].split()[0]
        tuples.append((row["username"], first_date, last_date))
        tuples_full_date.append((row["username"], row["first_post"], row["last_post"]))

    return tuples, tuples_full_date


def main():
    # Configure logging
    logger = logging.getLogger(__name__)
    # Configure argument parser
    parser = argparse.ArgumentParser(description="Process dataset accounts")
    parser.add_argument(
        "--csv_path",
        default="data/dataset_accounts.csv",
        help="Path to the dataset_accounts.csv file",
    )
    parser.add_argument(
        "--skip_collection", action="store_true", help="Skip data collection"
    )
    parser.add_argument(
        "--skip_create_df",
        action="store_true",
        help="Skip processing the raw CrowdTangle data into a DataFrame",
    )
    parser.add_argument(
        "--post_df_path",
        default="data/df_posts.pkl",
        help="Path to the processed posts df pickle file",
    )
    parser.add_argument(
        "--profile_df_path",
        default="data/df_profiles.pkl",
        help="Path to the processed profiles df pickle file",
    )
    args = parser.parse_args()
    # Load API key
    API_TOKEN = load_env()
    # Load dataset metadata
    dataset_metadata = pd.read_csv(args.csv_path)
    account_tuples, account_tuples_full_date = get_account_tuples(dataset_metadata)
    # Data collection
    if not args.skip_collection:
        fetch_posts_for_accounts(account_tuples, API_TOKEN)
    # Data processing
    if not args.skip_create_df:
        df_posts, df_profiles = process_crowdtangle_data_directory()
        df_posts = filter_processed_posts(df_posts, account_tuples_full_date)
        df_posts.to_pickle(args.post_df_path)
        df_profiles.to_pickle(args.profile_df_path)


if __name__ == "__main__":
    main()
