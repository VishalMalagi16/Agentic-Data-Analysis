# bivariate_env/bivariate_tools.py
import matplotlib
matplotlib.use('Agg')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
from statsmodels.graphics.mosaicplot import mosaic
from bivariate_env.method_functions import methods as test_functions
def get_value_counts(df: pd.DataFrame, column: str) -> str:
    """Gets the count of unique values in a categorical column."""
    if column not in df.columns:
        return json.dumps({"error": f"Column '{column}' not found."})
    if not isinstance(df[column].dtype, (pd.CategoricalDtype, object)):
         return json.dumps({"error": f"Column '{column}' is not categorical."})
    
    counts = df[column].nunique()
    return json.dumps({"column": column, "unique_value_count": int(counts)})
# --- Utility to identify identifier and datetime columns ---
def is_identifier_column(col_name):
    lowered = col_name.lower()
    return (
        'id' in lowered or 'identifier' in lowered or 'emp_no' in lowered
    )

def is_datetime_column(df, col_name):
    if pd.api.types.is_datetime64_any_dtype(df[col_name]):
        return True
    lowered = col_name.lower()
    return (
        'date' in lowered or 'time' in lowered or 'timestamp' in lowered
    )

def get_all_column_names(df: pd.DataFrame) -> str:
    """Gets a list of all column names from the DataFrame, excluding identifier and datetime columns."""
    exclude_cols = [
        col for col in df.columns
        if is_identifier_column(col) or is_datetime_column(df, col)
    ]
    filtered_cols = [col for col in df.columns if col not in exclude_cols]
    return json.dumps({"columns": filtered_cols})

def _save_plot(fig, filename_prefix: str) -> str:
    """Helper to save a plot and return its web-friendly URL path."""
    save_dir = os.path.join('artifacts', 'plots')
    os.makedirs(save_dir, exist_ok=True)
    filename = f"{filename_prefix}.png"
    save_path = os.path.join(save_dir, filename)
    url_path = os.path.join('plots', filename).replace('\\', '/')
    fig.savefig(save_path)
    plt.close(fig)
    return url_path

def infer_dtype(series):
    """Infers simplified dtype for analysis."""
    if pd.api.types.is_numeric_dtype(series): return "numerical"
    return "categorical"

def get_pair_dtypes(df: pd.DataFrame, column1: str, column2: str) -> str:
    """Gets the data types for a pair of columns."""
    if column1 not in df.columns or column2 not in df.columns:
        return json.dumps({"error": "One or both columns not found."})
    dtype1 = infer_dtype(df[column1])
    dtype2 = infer_dtype(df[column2])
    return json.dumps({"column1": column1, "dtype1": dtype1, "column2": column2, "dtype2": dtype2})

# --- Statistical Test Tools ---
def pearson_correlation(df: pd.DataFrame, x_col: str, y_col: str) -> str:
    result = test_functions['pearson_correlation'](df[x_col], df[y_col])
    if isinstance(result, dict):
        result['pair'] = [x_col, y_col]
    return json.dumps(result)

def spearman_correlation(df: pd.DataFrame, x_col: str, y_col: str) -> str:
    result = test_functions['spearman_correlation'](df[x_col], df[y_col])
    if isinstance(result, dict):
        result['pair'] = [x_col, y_col]
    return json.dumps(result)
    
def linear_regression(df: pd.DataFrame, x_col: str, y_col: str) -> str:
    result = test_functions['linear_regression'](df[x_col], df[y_col])
    if isinstance(result, dict):
        result['pair'] = [x_col, y_col]
    return json.dumps(result)

def t_test(df: pd.DataFrame, x_col: str, y_col: str) -> str:
    result = test_functions['t_test'](df[x_col], df[y_col])
    if isinstance(result, dict):
        result['pair'] = [x_col, y_col]
    return json.dumps(result)

def anova(df: pd.DataFrame, x_col: str, y_col: str) -> str:
    result = test_functions['anova'](df[x_col], df[y_col])
    if isinstance(result, dict):
        result['pair'] = [x_col, y_col]
    return json.dumps(result)

def mann_whitney_u(df: pd.DataFrame, x_col: str, y_col: str) -> str:
    result = test_functions['mann_whitney_u'](df[x_col], df[y_col])
    if isinstance(result, dict):
        result['pair'] = [x_col, y_col]
    return json.dumps(result)

def chi_square_test(df: pd.DataFrame, x_col: str, y_col: str) -> str:
    result = test_functions['chi_square_test'](df[x_col], df[y_col])
    if isinstance(result, dict):
        result['pair'] = [x_col, y_col]
    return json.dumps(result)
    
def fishers_exact_test(df: pd.DataFrame, x_col: str, y_col: str) -> str:
    result = test_functions['fishers_exact_test'](df[x_col], df[y_col])
    if isinstance(result, dict):
        result['pair'] = [x_col, y_col]
    return json.dumps(result)

def cramers_v(df: pd.DataFrame, x_col: str, y_col: str) -> str:
    result = test_functions['cramers_v'](df[x_col], df[y_col])
    if isinstance(result, dict):
        result['pair'] = [x_col, y_col]
    return json.dumps(result)

# --- Visualization Tools ---
def plot_scatter(df: pd.DataFrame, x_col: str, y_col: str) -> str:
    fig, ax = plt.subplots(); sns.scatterplot(data=df, x=x_col, y=y_col, ax=ax)
    ax.set_title(f"Scatter Plot of {y_col} vs. {x_col}")
    path = _save_plot(fig, f"scatter_{x_col}_{y_col}")
    return json.dumps({"plot_path": path, "pair": [x_col, y_col]})

def plot_grouped_boxplot(df: pd.DataFrame, x_col: str, y_col: str) -> str:
    fig, ax = plt.subplots()
    num_col, cat_col = (y_col, x_col) if infer_dtype(df[y_col]) == 'numerical' else (x_col, y_col)
    sns.boxplot(data=df, x=cat_col, y=num_col, ax=ax)
    ax.set_title(f"Box Plot of {num_col} by {cat_col}")
    path = _save_plot(fig, f"boxplot_{cat_col}_{num_col}")
    return json.dumps({"plot_path": path, "pair": [x_col, y_col]})

def plot_heatmap(df: pd.DataFrame, x_col: str, y_col: str) -> str:
    fig, ax = plt.subplots()
    numeric_df = df[[x_col, y_col]].select_dtypes(include=np.number)
    if numeric_df.shape[1] < 2:
        return json.dumps({"error": "Heatmap requires two numerical columns.", "pair": [x_col, y_col]})
    corr = numeric_df.corr()
    sns.heatmap(corr, annot=True, cmap='coolwarm', ax=ax)
    ax.set_title(f"Heatmap of {x_col} and {y_col}")
    path = _save_plot(fig, f"heatmap_{x_col}_{y_col}")
    return json.dumps({"plot_path": path, "pair": [x_col, y_col]})

def plot_stacked_bar(df: pd.DataFrame, x_col: str, y_col: str) -> str:
    fig, ax = plt.subplots()
    ct = pd.crosstab(df[x_col], df[y_col])
    ct.div(ct.sum(1), axis=0).plot(kind="bar", stacked=True, ax=ax)
    ax.set_title(f"Stacked Bar Chart of {y_col} by {x_col}")
    path = _save_plot(fig, f"stacked_bar_{x_col}_{y_col}")
    return json.dumps({"plot_path": path, "pair": [x_col, y_col]})

def plot_mosaic(df: pd.DataFrame, x_col: str, y_col: str) -> str:
    fig, _ = mosaic(df, [x_col, y_col], title=f"Mosaic Plot of {x_col} and {y_col}")
    path = _save_plot(fig, f"mosaic_{x_col}_{y_col}")
    return json.dumps({"plot_path": path, "pair": [x_col, y_col]})


# SOLUTION: Register all the tools mentioned in the prompt
AVAILABLE_BIVARIATE_TOOLS = {
    "get_value_counts": get_value_counts,
    "get_all_column_names": get_all_column_names,
    "get_pair_dtypes": get_pair_dtypes,
    "pearson_correlation": pearson_correlation,
    "spearman_correlation": spearman_correlation,
    "linear_regression": linear_regression,
    "t_test": t_test,
    "anova": anova,
    "mann_whitney_u": mann_whitney_u,
    "chi_square_test": chi_square_test,
    "fishers_exact_test": fishers_exact_test,
    "cramers_v": cramers_v,
    "plot_scatter": plot_scatter,
    "plot_heatmap": plot_heatmap,
    "plot_grouped_boxplot": plot_grouped_boxplot,
    "plot_stacked_bar": plot_stacked_bar,
    "plot_mosaic": plot_mosaic,
}