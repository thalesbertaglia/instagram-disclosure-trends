from typing import Any, Dict

import pandas as pd
import plotly.express as px
import pyperclip
from plotly import graph_objects as go


def safe_get(dictionary: Dict[str, Any], *keys, default=None) -> Any:
    """
    Safely get nested key values from a dictionary.
    """
    for key in keys:
        try:
            dictionary = dictionary[key]
        except KeyError:
            return default
    return dictionary or default


def generate_latex_table(
    df_table: pd.DataFrame,
    table_caption: str,
    table_label: str,
    columns_rename_map: Dict[str, str] = {},
    index_rename_map: Dict[str, str] = {},
):
    n_columns = len(df_table.columns)
    pyperclip.copy(
        df_table.rename(columns=columns_rename_map, index=index_rename_map)
        .style.format(precision=2)
        .applymap_index(lambda v: "font-weight: bold;", axis="columns")
        .applymap_index(lambda v: "font-weight: bold;", axis="index")
        .to_latex(
            hrules=True,
            convert_css=True,
            column_format=f"l{'c'*n_columns}",
            caption=table_caption,
            label=table_label,
            position_float="centering",
        )
    )


def display_formatted(df: pd.DataFrame, precision: int = 0):
    format = "{:,.%df}" % precision
    with pd.option_context("display.float_format", format.format):
        display(df)


def plot_agg_timeseries(
    df_posts: pd.DataFrame, by: str, time_column: str = "dt_year_mon"
) -> go.Figure:
    dt_agg = (
        df_posts.groupby(["country", time_column])[by]
        .mean()
        .unstack()
        .fillna(0)
        .stack()
        .reset_index()
        .rename({time_column: "date", 0: by}, axis=1)
    )
    fig = px.line(dt_agg, x="date", y=by, color="country")
    return fig
