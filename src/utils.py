from typing import Dict, Any

import pyperclip


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
    df_table: "pd.DataFrame",
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
