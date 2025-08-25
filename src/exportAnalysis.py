# src/exportAnalysis.py

import os
import pandas as pd
from portfolioAnalysis import PortfolioAnalyzer

# Export directory
EXPORT_DIR = os.path.join("data", "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

def export_analysis_results(csv_path, portfolio_name, output_prefix):
    """
    Run analysis on a portfolio and export results into CSVs
    for Tableau / Power BI integration.
    """
    # Load portfolio data
    df = pd.read_csv(csv_path)

    # Initialize analyzer
    analyzer = PortfolioAnalyzer(df, portfolio_name)

    # Portfolio summary
    summary = pd.DataFrame([analyzer.summary()])
    summary.to_csv(os.path.join(EXPORT_DIR, "{}_summary.csv".format(output_prefix)), index=False)

    # Composite credit distribution
    cd = analyzer.credit_distribution().reset_index()
    cd.columns = ["Rating", "Market Value %"]
    cd["Portfolio"] = portfolio_name
    cd.to_csv(os.path.join(EXPORT_DIR, "{}_credit_distribution.csv".format(output_prefix)), index=False)

    # Credit distributions by agency
    ratings = analyzer.rating_distributions()
    for col, dist in ratings.items():
        dist = dist.reset_index()
        dist.columns = ["Rating", "Market Value %"]
        dist["Portfolio"] = portfolio_name
        dist.to_csv(os.path.join(EXPORT_DIR, "{}_{}_distribution.csv".format(output_prefix, col.replace(' ', '_'))), index=False)

    # Sector exposure
    se = analyzer.sector_exposure().reset_index()
    se.columns = ["Sector", "Market Value %"]
    se["Portfolio"] = portfolio_name
    se.to_csv(os.path.join(EXPORT_DIR, "{}_sector_exposure.csv".format(output_prefix)), index=False)

    # KRD profile
    krd = analyzer.krd_profile().reset_index()
    krd.columns = ["Tenor", "Contribution"]
    krd["Portfolio"] = portfolio_name
    krd.to_csv(os.path.join(EXPORT_DIR, "{}_krd_profile.csv".format(output_prefix)), index=False)

    # Top holdings
    th = analyzer.top_holdings().reset_index()
    th.columns = ["Issuer", "Market Value"]
    th["Portfolio"] = portfolio_name
    th.to_csv(os.path.join(EXPORT_DIR, "{}_top_holdings.csv".format(output_prefix)), index=False)

    # Duration
    dur = pd.DataFrame([analyzer.duration()])
    dur.to_csv(os.path.join(EXPORT_DIR, "{}_duration.csv".format(output_prefix)), index=False)

    # Maturity buckets
    mb = analyzer.maturity_buckets().reset_index()
    mb.columns = ["Maturity Bucket", "Market Value %"]
    mb["Portfolio"] = portfolio_name
    mb.to_csv(os.path.join(EXPORT_DIR, "{}_maturity_buckets.csv".format(output_prefix)), index=False)

    # Currency exposure
    ce = analyzer.currency_exposure().reset_index()
    ce.columns = ["Currency", "Market Value %"]
    ce["Portfolio"] = portfolio_name
    ce.to_csv(os.path.join(EXPORT_DIR, "{}_currency_exposure.csv".format(output_prefix)), index=False)

    # Other categorical breakdowns
    cat_breaks = analyzer.categorical_breakdowns()
    for col, dist in cat_breaks.items():
        dist = dist.reset_index()
        dist.columns = [col, "Market Value %"]
        dist["Portfolio"] = portfolio_name
        dist.to_csv(os.path.join(EXPORT_DIR, "{}_{}_breakdown.csv".format(output_prefix, col.replace(' ', '_'))), index=False)


def combine_exports(export_dir, metric_name, files, output_file):
    """Combine multiple CSVs (USD + EUR) into one for Power BI Service"""
    dfs = []
    for f in files:
        path = os.path.join(export_dir, f)
        if os.path.exists(path):
            df = pd.read_csv(path)
            dfs.append(df)
    if dfs:
        combined = pd.concat(dfs, ignore_index=True)
        combined.to_csv(os.path.join(export_dir, output_file), index=False)


if __name__ == "__main__":
    # Run exports for USD and EUR portfolios
    export_analysis_results("data/clean/PORT_USD_clean.csv", "USD Portfolio", "USD_Portfolio")
    export_analysis_results("data/clean/PORT_EUR_clean.csv", "EUR Portfolio", "EUR_Portfolio")

    # === Combine key metrics into single CSVs ===
    combine_exports(EXPORT_DIR, "summary", [
        "USD_Portfolio_summary.csv",
        "EUR_Portfolio_summary.csv"
    ], "ALL_Portfolios_summary.csv")

    combine_exports(EXPORT_DIR, "credit", [
        "USD_Portfolio_credit_distribution.csv",
        "EUR_Portfolio_credit_distribution.csv"
    ], "ALL_Portfolios_credit_distribution.csv")

    combine_exports(EXPORT_DIR, "sector", [
        "USD_Portfolio_sector_exposure.csv",
        "EUR_Portfolio_sector_exposure.csv"
    ], "ALL_Portfolios_sector_exposure.csv")

    combine_exports(EXPORT_DIR, "krd", [
        "USD_Portfolio_krd_profile.csv",
        "EUR_Portfolio_krd_profile.csv"
    ], "ALL_Portfolios_krd_profile.csv")

    combine_exports(EXPORT_DIR, "top_holdings", [
        "USD_Portfolio_top_holdings.csv",
        "EUR_Portfolio_top_holdings.csv"
    ], "ALL_Portfolios_top_holdings.csv")

    combine_exports(EXPORT_DIR, "duration", [
        "USD_Portfolio_duration.csv",
        "EUR_Portfolio_duration.csv"
    ], "ALL_Portfolios_duration.csv")

    combine_exports(EXPORT_DIR, "maturity", [
        "USD_Portfolio_maturity_buckets.csv",
        "EUR_Portfolio_maturity_buckets.csv"
    ], "ALL_Portfolios_maturity_buckets.csv")

    combine_exports(EXPORT_DIR, "currency", [
        "USD_Portfolio_currency_exposure.csv",
        "EUR_Portfolio_currency_exposure.csv"
    ], "ALL_Portfolios_currency_exposure.csv")
