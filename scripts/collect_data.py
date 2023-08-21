import sys
import os
import argparse
import logging
from typing import Dict, List, Tuple

import pandas as pd
from dotenv import load_dotenv

from src.data_collection import fetch_posts_for_accounts
from src.data_processing import (
    process_crowdtangle_data_directory,
    filter_processed_posts,
    augment_processed_posts,
)


def load_env() -> str:
    if not load_dotenv():
        logging.error(
            "Failed to load environment variables from .env file. Ensure the file exists."
        )
        sys.exit(1)

    API_TOKEN = os.getenv("API_TOKEN")
    if not API_TOKEN:
        logging.error(
            "API_TOKEN not found in environment variables. Ensure it's set in the .env file."
        )
        sys.exit(1)

    return API_TOKEN


def get_account_metadata(metadata: pd.DataFrame) -> Dict[str, dict]:
    return {
        row["username"]: {
            key: row[key] for key in metadata.columns if key != "username"
        }
        for _, row in metadata.iterrows()
    }


def get_account_tuples(
    metadata_dict: Dict[str, dict]
) -> Tuple[List[Tuple[str, str, str]], List[Tuple[str, str, str]]]:
    tuples = []
    tuples_full_date = []

    for username, user_data in metadata_dict.items():
        first_date = user_data["first_post"].split()[0]
        last_date = user_data["last_post"].split()[0]
        tuples.append((username, first_date, last_date))
        tuples_full_date.append(
            (username, user_data["first_post"], user_data["last_post"])
        )

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
        "--skip_augmentation",
        action="store_true",
        help="Skip augmenting the DataFrame with additional columns. Use this option for collecting data from new accounts, not included in the original dataset.",
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
    dataset_metadata = get_account_metadata(pd.read_csv(args.csv_path))
    account_tuples, account_tuples_full_date = get_account_tuples(dataset_metadata)
    # Data collection
    if not args.skip_collection:
        fetch_posts_for_accounts(account_tuples, API_TOKEN)
    # Data processing
    if not args.skip_create_df:
        # First processing step, raw jsons to df
        df_posts, df_profiles = process_crowdtangle_data_directory()
        # Ensuring the date ranges are correct
        df_posts = filter_processed_posts(df_posts, account_tuples_full_date)
        # Adding the processed columns, used for the experiments
        if not args.skip_augmentation:
            df_posts = augment_processed_posts(df_posts, dataset_metadata)
        df_posts.to_pickle(args.post_df_path)
        df_profiles.to_pickle(args.profile_df_path)


if __name__ == "__main__":
    main()
