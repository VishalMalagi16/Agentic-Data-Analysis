# univariate_tools.py
import matplotlib
matplotlib.use('Agg') # <-- SOLUTION: Must be before pyplot import

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import shapiro, skew, kurtosis
import json
import os

# Create a directory for plots if it doesn't exist
# This is handled by each plotting function now.

def get_column_dtype(df: pd.DataFrame, column: str) -> str:
    """
    Identifies the data type of a column based on heuristics.
    Returns 'numerical continuous', 'numerical discrete', 'categorical nominal', or 'categorical ordinal'.
    """
    if column not in df.columns:
        return json.dumps({"error": f"Column '{column}' not found."})

    col_data = df[column].dropna()
    if pd.api.types.is_numeric_dtype(col_data):
        # Heuristic for discrete vs. continuous
        if col_data.nunique() < 25 and pd.api.types.is_integer_dtype(col_data):
            return json.dumps({"dtype": "numerical discrete"})
        else:
            return json.dumps({"dtype": "numerical continuous"})
    elif pd.api.types.is_categorical_dtype(col_data) or pd.api.types.is_object_dtype(col_data):
        # Simple assumption: all non-numeric are nominal. Ordinality is hard to infer without metadata.
        return json.dumps({"dtype": "categorical nominal"})
    else:
        return json.dumps({"dtype": "other"})


def calculate_descriptive_stats(df: pd.DataFrame, column: str) -> str:
    """
    Calculates a comprehensive set of descriptive statistics for a numerical column.
    """
    if column not in df.columns or not pd.api.types.is_numeric_dtype(df[column]):
        return json.dumps({"error": f"Column '{column}' is not numerical."})

    col_data = df[column].dropna()
    stats = {
        "count": int(col_data.count()),
        "mean": float(col_data.mean()),
        "median": float(col_data.median()),
        "mode": [float(m) for m in col_data.mode()],
        "minimum": float(col_data.min()),
        "maximum": float(col_data.max()),
        "range": float(col_data.max() - col_data.min()),
        "variance": float(col_data.var()),
        "standard_deviation": float(col_data.std()),
        "quartiles": {
            "q1": float(col_data.quantile(0.25)),
            "q2": float(col_data.quantile(0.50)),
            "q3": float(col_data.quantile(0.75))
        },
        "IQR": float(col_data.quantile(0.75) - col_data.quantile(0.25)),
        "skewness": float(skew(col_data)),
        "kurtosis": float(kurtosis(col_data)) # Fisher's definition (normal=0)
    }
    return json.dumps(stats)

def calculate_frequency_analysis(df: pd.DataFrame, column: str) -> str:
    """
    Performs frequency analysis for a categorical column.
    """
    if column not in df.columns:
        return json.dumps({"error": f"Column '{column}' not found."})

    col_data = df[column].dropna()
    counts = col_data.value_counts()
    percentages = col_data.value_counts(normalize=True) * 100
    
    result = {
        "frequency": counts.to_dict(),
        "proportion": percentages.to_dict(),
        "mode": [m for m in col_data.mode()]
    }
    return json.dumps(result)

def check_normality(df: pd.DataFrame, column: str) -> str:
    if column not in df.columns or not pd.api.types.is_numeric_dtype(df[column]):
        return json.dumps({"error": f"Cannot test normality for non-numerical column '{column}'."})
    
    stat, p_value = shapiro(df[column].dropna())
    result = {"test_statistic": stat, "p_value": p_value}
    if p_value > 0.05:
        result["interpretation"] = "The data appears to be normally distributed (fail to reject H0)."
    else:
        result["interpretation"] = "The data does not appear to be normally distributed (reject H0)."
    return json.dumps(result)

# --- Visualization Tools ---
def plot_histogram(df: pd.DataFrame, column: str) -> str:
    if column not in df.columns or not pd.api.types.is_numeric_dtype(df[column]):
        return json.dumps({"error": f"Cannot plot histogram for non-numerical column '{column}'."})
    
    save_dir = os.path.join('artifacts', 'plots')
    os.makedirs(save_dir, exist_ok=True)
    filename = f'histogram_{column}.png'
    save_path = os.path.join(save_dir, filename)
    
    # SOLUTION: Standardize path for JSON and web contexts
    url_path = os.path.join('plots', filename).replace('\\', '/')

    plt.figure(figsize=(10, 6)); sns.histplot(df[column], kde=True); plt.title(f'Histogram of {column}')
    plt.savefig(save_path); plt.close()
    return json.dumps({"plot_path": url_path})

def plot_boxplot(df: pd.DataFrame, column: str) -> str:
    if column not in df.columns or not pd.api.types.is_numeric_dtype(df[column]):
        return json.dumps({"error": f"Cannot plot boxplot for non-numerical column '{column}'."})
    
    save_dir = os.path.join('artifacts', 'plots')
    os.makedirs(save_dir, exist_ok=True)
    filename = f'boxplot_{column}.png'
    save_path = os.path.join(save_dir, filename)

    # SOLUTION: Standardize path for JSON and web contexts
    url_path = os.path.join('plots', filename).replace('\\', '/')

    plt.figure(figsize=(10, 6)); sns.boxplot(x=df[column]); plt.title(f'Boxplot of {column}')
    plt.savefig(save_path); plt.close()
    return json.dumps({"plot_path": url_path})

def plot_bar_chart(df: pd.DataFrame, column: str) -> str:
    if column not in df.columns:
        return json.dumps({"error": f"Column '{column}' not found."})

    save_dir = os.path.join('artifacts', 'plots')
    os.makedirs(save_dir, exist_ok=True)
    filename = f'barchart_{column}.png'
    save_path = os.path.join(save_dir, filename)
    
    # SOLUTION: Standardize path for JSON and web contexts
    url_path = os.path.join('plots', filename).replace('\\', '/')

    plt.figure(figsize=(12, 7)); df[column].value_counts().plot(kind='bar'); plt.title(f'Bar Chart of {column}')
    plt.ylabel('Count'); plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(save_path); plt.close()
    return json.dumps({"plot_path": url_path})
def get_all_column_names(df: pd.DataFrame) -> str:
    """Gets a list of all column names from the DataFrame."""
    return json.dumps({"columns": df.columns.tolist()})
# This dictionary maps tool names to functions for the agent to use.
AVAILABLE_TOOLS = {
    "get_all_column_names": get_all_column_names,
    "get_column_dtype": get_column_dtype,
    "calculate_descriptive_stats": calculate_descriptive_stats,
    "calculate_frequency_analysis": calculate_frequency_analysis,
    "check_normality": check_normality,
    "plot_histogram": plot_histogram,
    "plot_boxplot": plot_boxplot,
    "plot_bar_chart": plot_bar_chart,
}