import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from scipy import stats
import missingno as msno
from scipy.stats.mstats import winsorize


class PreprocessingTools:
    """All preprocessing tool functions."""

    def check_missing_values(self, df: pd.DataFrame):
        return {
            "missing_sum": df.isnull().sum().to_dict(),
            "missing_mean": df.isnull().mean().round(3).to_dict(),
        }

    def impute_column(self, df: pd.DataFrame, column: str, strategy: str, is_categorical: bool = False):
        # <--- ROBUSTNESS IMPROVEMENT
        if is_categorical or strategy == 'most_frequent':
            fill_value = df[column].mode(dropna=True)
            if not fill_value.empty:
                df[column] = df[column].fillna(fill_value.iloc[0])
        elif strategy == "median":
            fill_value = df[column].median()
            df[column] = df[column].fillna(fill_value)
        elif strategy == "mean":
            fill_value = df[column].mean()
            df[column] = df[column].fillna(fill_value)
        else:
            raise ValueError(f"Unsupported strategy '{strategy}' for numerical column '{column}'")
        return df

    def drop_column(self, df: pd.DataFrame, column: str):
        return df.drop(columns=[column])

    def check_skewness(self, df: pd.DataFrame):
        numeric = df.select_dtypes(include="number")
        skewness = numeric.skew(skipna=True).round(3)
        return skewness.to_dict()

    def detect_outliers_iqr(self, df: pd.DataFrame, column: str):
        q1 = df[column].quantile(0.25)
        q3 = df[column].quantile(0.75)
        iqr = q3 - q1
        mask = (df[column] < (q1 - 1.5 * iqr)) | (df[column] > (q3 + 1.5 * iqr))
        return mask

    def detect_outliers_zscore(self, df: pd.DataFrame, column: str):
        mean = df[column].mean()
        std = df[column].std()
        mask = abs((df[column] - mean) / std) > 3
        return mask

    def cap_outliers(self, df: pd.DataFrame, column: str):
        q1 = df[column].quantile(0.25)
        q3 = df[column].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        df[column] = df[column].clip(lower, upper)
        return df

    def remove_outliers(self, df: pd.DataFrame, column: str):
        mask = self.detect_outliers_zscore(df, column)
        df = df[~mask]
        return df

    def check_data_types(self, df: pd.DataFrame):
        return df.dtypes.astype(str).to_dict()
    
    def time_series_impute(self, df, column, method='ffill'):
        """
        Imputes missing values in a time series column using specified method.
        """
        if method == 'ffill':
            df[column] = df[column].fillna(method='ffill')
        elif method == 'bfill':
            df[column] = df[column].fillna(method='bfill')
        elif method == 'interpolate':
            df[column] = df[column].interpolate()
        else:
            raise ValueError("Invalid method. Choose from 'ffill', 'bfill', or 'interpolate'")
        return df
    
    def winsorize_outliers(self, df, column, limits=(0.01, 0.01)):
        """
        Caps extreme values (outliers) in a numeric column using winsorization.
        """
        df[column] = winsorize(df[column], limits=limits)
        return df

    def transform_column(self, df, column, method='log'):
        """
        Applies transformation to a column to reduce skewness or handle outliers.
        """
        if method == 'log':
            df[column] = np.log1p(df[column])  # log(1 + x) to avoid log(0)
        elif method == 'sqrt':
            df[column] = np.sqrt(df[column])
        else:
            raise ValueError("Unsupported transformation. Use 'log' or 'sqrt'.")
        return df