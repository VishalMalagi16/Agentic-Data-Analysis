import numpy as np
import scipy.stats as stats
import pandas as pd

def pearson_correlation(x, y):
    x, y = pd.to_numeric(x, errors="coerce"), pd.to_numeric(y, errors="coerce")
    x, y = x.dropna(), y.dropna()
    if len(x) < 2 or len(y) < 2:
        return {"error": "`x` and `y` must have length at least 2."}
    corr, p = stats.pearsonr(x, y)
    return {"correlation": corr, "p_value": p}

def spearman_correlation(x, y):
    x, y = pd.to_numeric(x, errors="coerce"), pd.to_numeric(y, errors="coerce")
    x, y = x.dropna(), y.dropna()
    if len(x) < 2 or len(y) < 2:
        return {"error": "`x` and `y` must have length at least 2."}
    corr, p = stats.spearmanr(x, y)
    return {"correlation": corr, "p_value": p}

def linear_regression(x, y):
    # Ensure both x and y are numeric
    if not (pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y)):
        return {"message": "Linear regression is only applicable for numerical-numerical pairs. Skipping this pair."}
    # Align x and y by dropping rows where either is NaN
    x = pd.to_numeric(x, errors="coerce")
    y = pd.to_numeric(y, errors="coerce")
    mask = ~(x.isna() | y.isna())
    x_clean = x[mask]
    y_clean = y[mask]
    if len(x_clean) < 2 or len(y_clean) < 2:
        return {"error": "Inputs must not be empty."}
    # Always treat x as independent, y as dependent
    slope, intercept, r_value, p_value, std_err = stats.linregress(x_clean, y_clean)
    return {
        "model": f"y = {slope:.3f}*x + {intercept:.3f}",
        "slope": round(slope, 3),
        "intercept": round(intercept, 3),
        "r_squared": round(r_value ** 2, 3),
        "p_value": round(p_value, 3),
        "std_error": round(std_err, 3)
    }


def t_test(x, y):
    try:
        df = pd.DataFrame({'num': x, 'cat': y}).dropna()
        cat_counts = df['cat'].value_counts()
        if len(cat_counts) != 2:
            return {"error": "t-test requires exactly 2 groups in the categorical variable."}
        groups = [pd.to_numeric(df[df['cat'] == val]['num'], errors='coerce').dropna() for val in cat_counts.index]
        if any(len(g) < 2 for g in groups):
            return {"error": "Each group must contain at least 2 valid samples."}
        stat, p = stats.ttest_ind(groups[0], groups[1])
        return {"t_statistic": stat, "p_value": p}
    except Exception as e:
        return {"error": str(e)}


def anova(x, y):
    try:
        df = pd.DataFrame({'num': x, 'cat': y}).dropna()
        df['num'] = pd.to_numeric(df['num'], errors='coerce')
        groups = [df[df['cat'] == g]['num'].dropna() for g in df['cat'].unique()]
        valid_groups = [g for g in groups if len(g) >= 2]
        if len(valid_groups) < 2:
            return {"error": "ANOVA requires at least two groups with 2+ samples each."}
        stat, p = stats.f_oneway(*valid_groups)
        return {"f_statistic": stat, "p_value": p}
    except Exception as e:
        return {"error": str(e)}


def mann_whitney_u(x, y):
    try:
        df = pd.DataFrame({'num': x, 'cat': y}).dropna()
        cat_counts = df['cat'].value_counts()
        if len(cat_counts) != 2:
            return {"error": "Mann-Whitney U test requires exactly 2 groups."}
        groups = [pd.to_numeric(df[df['cat'] == val]['num'], errors='coerce').dropna() for val in cat_counts.index]
        if any(len(g) < 2 for g in groups):
            return {"error": "Each group must contain at least 2 valid samples."}
        stat, p = stats.mannwhitneyu(groups[0], groups[1], alternative='two-sided')
        return {"u_statistic": stat, "p_value": p}
    except Exception as e:
        return {"error": str(e)}


def chi_square_test(x, y):
    try:
        table = pd.crosstab(x, y)
        stat, p, dof, _ = stats.chi2_contingency(table)
        return {"chi_square": stat, "p_value": p, "df": dof}
    except Exception as e:
        return {"error": str(e)}

def fishers_exact_test(x, y):
    try:
        table = pd.crosstab(x, y)
        if table.shape != (2, 2):
            return {"error": "Fisher's exact test requires a 2x2 contingency table."}
        oddsratio, p = stats.fisher_exact(table)
        return {"odds_ratio": oddsratio, "p_value": p}
    except Exception as e:
        return {"error": str(e)}

def cramers_v(x, y):
    try:
        confusion_matrix = pd.crosstab(x, y)
        chi2 = stats.chi2_contingency(confusion_matrix)[0]
        n = confusion_matrix.sum().sum()
        phi2 = chi2 / n
        r, k = confusion_matrix.shape
        v = np.sqrt(phi2 / min(k - 1, r - 1))
        return {"cramers_v": v}
    except Exception as e:
        return {"error": str(e)}

# Map name to function
methods = {
    "pearson_correlation": pearson_correlation,
    "spearman_correlation": spearman_correlation,
    "linear_regression": linear_regression,
    "t_test": t_test,
    "anova": anova,
    "mann_whitney_u": mann_whitney_u,
    "chi_square_test": chi_square_test,
    "fishers_exact_test": fishers_exact_test,
    "cramers_v": cramers_v
}
