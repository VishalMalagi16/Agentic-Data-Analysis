

import pandas as pd
import json
import io

def get_shape(df: pd.DataFrame) -> str:
    """Returns the shape of the DataFrame as a JSON string."""
    return json.dumps({"rows": df.shape[0], "columns": df.shape[1]})

def get_column_info(df: pd.DataFrame) -> str:
    """
    Returns column names, dtypes, and non-null counts as a JSON string.
    This version is more robust as it accesses DataFrame properties directly.
    """
    results = []
    for col in df.columns:
        results.append({
            "column": col,
            "non_null_count": int(df[col].count()), # .count() gives non-null values
            "total_count": len(df),
            "missing_count": int(df[col].isnull().sum()),
            "dtype": str(df[col].dtype)
        })
    return json.dumps({"column_details": results})

def get_head(df: pd.DataFrame, n: int = 5) -> str:
    """Returns the first n rows of the DataFrame as a JSON-serializable string."""
    return json.dumps({"head": df.head(n).to_string()})

def identify_column_types(df: pd.DataFrame) -> str:
    """Identifies and classifies columns into numerical, categorical, datetime, and other types."""
    numerical_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    # First, get native datetime columns
    datetime_cols = df.select_dtypes(include=['datetime64', 'datetime64[ns]']).columns.tolist()
    # Next, try to parse object columns as datetime if possible
    object_cols = df.select_dtypes(include=['object']).columns.tolist()
    for col in object_cols:
        try:
            parsed = pd.to_datetime(df[col], errors='raise')
            # If parsing succeeds and not already in datetime_cols, add it
            if col not in datetime_cols:
                datetime_cols.append(col)
        except Exception:
            pass
    # Remove any object columns that are actually datetime
    categorical_cols = [col for col in object_cols if col not in datetime_cols]
    # Add category and bool columns to categorical
    categorical_cols += df.select_dtypes(include=['category', 'bool']).columns.tolist()
    # Ensure all columns are accounted for
    all_cols = set(df.columns.tolist())
    identified_cols = set(numerical_cols) | set(categorical_cols) | set(datetime_cols)
    other_cols = list(all_cols - identified_cols)
    return json.dumps({
        "numerical": numerical_cols,
        "categorical": categorical_cols,
        "datetime": datetime_cols,
        "other": other_cols
    })

# Create a dictionary to map tool names to their functions
AVAILABLE_SUMMARY_TOOLS = {
    "get_shape": get_shape,
    "get_column_info": get_column_info,
    "get_head": get_head,
    "identify_column_types": identify_column_types,
}