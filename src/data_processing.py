import logging
import json
import re
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple
from .utils import safe_get

# Set up logging
logger = logging.getLogger(__name__)

# Constants
DESCRIPTION = "description"
ACCOUNT = "account"
HANDLE = "handle"
NAME = "name"
URL = "url"
SUBSCRIBER_COUNT = "subscriberCount"
VERIFIED = "verified"
SUBSCRIBER_COUNT = "subscriberCount"
SCORE = "score"
LIKE_AND_VIEW_COUNTS_DISABLED = "likeAndViewCountsDisabled"
STATISTICS = "statistics"
ACTUAL = "actual"
EXPECTED = "expected"
FAVORITE_COUNT = "favoriteCount"
COMMENT_COUNT = "commentCount"
BRANDED_CONTENT_SPONSOR = "brandedContentSponsor"
DATE = "date"
TYPE = "type"
LANGUAGE_CODE = "languageCode"
POST_URL = "postUrl"
ID = "id"
RESULT = "result"
POSTS = "posts"


def extract_caption_data(caption: str) -> Dict[str, Any]:
    """
    Extract caption data from a post's description.
    """
    return {
        "caption": caption,
        "caption_hashtags": re.findall(r"#(\w+)", caption),
        "tagged_users": re.findall(r"@(\w+)", caption),
    }


def get_post_data(post: Dict[str, Any]) -> Dict[str, Any]:
    caption_data = extract_caption_data(post.get(DESCRIPTION, ""))
    is_ad = BRANDED_CONTENT_SPONSOR in post

    return {
        "username": safe_get(post, ACCOUNT, HANDLE),
        **caption_data,
        "subscriber_count": post.get(SUBSCRIBER_COUNT, -1),
        "ct_score": post.get(SCORE, -1),
        "counts_disabled": post.get(LIKE_AND_VIEW_COUNTS_DISABLED, False),
        "likes": safe_get(post, STATISTICS, ACTUAL, FAVORITE_COUNT, default=-1),
        "likes_expected": safe_get(
            post, STATISTICS, EXPECTED, FAVORITE_COUNT, default=-1
        ),
        "comments": safe_get(post, STATISTICS, ACTUAL, COMMENT_COUNT, default=-1),
        "comments_expected": safe_get(
            post, STATISTICS, EXPECTED, COMMENT_COUNT, default=-1
        ),
        "is_ad": is_ad,
        "content_sponsor": safe_get(post, BRANDED_CONTENT_SPONSOR, HANDLE, default=""),
        "date": post.get(DATE, ""),
        "type": post.get(TYPE, ""),
        "language": post.get(LANGUAGE_CODE, ""),
        "post_url": post.get(POST_URL, ""),
        "ct_id": post.get(ID, -1),
    }


def get_profile_data(post: Dict[str, Any]) -> Dict[str, Any]:
    account_data = post.get(ACCOUNT, {})

    return {
        "username": safe_get(account_data, HANDLE, default=""),
        "full_name": safe_get(account_data, NAME, default=""),
        "external_url": safe_get(account_data, URL, default=""),
        "is_verified": safe_get(account_data, VERIFIED, default=False),
        "followers": safe_get(account_data, SUBSCRIBER_COUNT, default=-1),
        "ct_id": safe_get(account_data, ID, default=-1),
    }


def load_data_from_file(file_path: Path) -> dict:
    try:
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {file_path}: {e}")
        return {}


def process_post(post: dict, accs: dict, post_data: List[Dict], acc_data: List[Dict]):
    post_data.append(get_post_data(post))
    account_handle = safe_get(post, ACCOUNT, HANDLE)

    if account_handle not in accs:
        accs[account_handle] = 0
        acc_data.append(get_profile_data(post))

    accs[account_handle] += 1


def process_files_in_directory(directory_path: Path) -> Tuple[List[Dict], List[Dict]]:
    post_data = []
    acc_data = []
    accs = {}

    for file_path in directory_path.glob("*.json"):
        raw_data = load_data_from_file(file_path)

        for post in safe_get(raw_data, RESULT, POSTS, default=[]):
            process_post(post, accs, post_data, acc_data)


def process_files_in_directory(directory_path: Path) -> Tuple[List[Dict], List[Dict]]:
    post_data = []
    acc_data = []
    accs = {}

    for file_path in directory_path.glob("*.json"):
        raw_data = load_data_from_file(file_path)
        n_posts = len(raw_data.get("result", {}).get("posts", []))
        for post in raw_data.get("result", {}).get("posts", []):
            post_data.append(get_post_data(post))
            if post["account"]["handle"] not in accs:
                accs[post["account"]["handle"]] = 0
                acc_data.append(get_profile_data(post))
            accs[post["account"]["handle"]] += n_posts

    return post_data, acc_data


def process_crowdtangle_data_directory() -> Tuple[pd.DataFrame, pd.DataFrame]:
    base_path = Path("./data/crowdtangle_data/")
    post_data, acc_data = [], []

    for sub_dir in base_path.iterdir():
        if sub_dir.is_dir():
            p_data, a_data = process_files_in_directory(sub_dir)
            post_data.extend(p_data)
            acc_data.extend(a_data)

    return pd.DataFrame(post_data), pd.DataFrame(acc_data)


def filter_processed_posts(
    df_posts: pd.DataFrame, accounts: list[tuple[str, str, str]]
) -> pd.DataFrame:
    filtered_posts = [
        df_posts.query(f"username == @username and @first_post <= date <= @last_post")
        for username, first_post, last_post in accounts
    ]

    return pd.concat(filtered_posts)


def augment_processed_posts(
    df_posts: pd.DataFrame, metadata_dict: Dict[str, dict]
) -> pd.DataFrame:
    # Mapping the columns from the metadata_dict
    keys_to_map = ["country", "size", "followers_collection_time"]
    for key_name in keys_to_map:
        values_to_map = {
            username: data[key_name]
            for username, data in metadata_dict.items()
            if key_name in data
        }
        df_posts[key_name] = df_posts["username"].map(values_to_map)

    # Additional columns
    df_posts["dt_year_mon"] = df_posts["date"].str[:7].str.replace("-", "/")

    return df_posts
