import pandas as pd
import os
import re

class PortfolioAnalyzer:
    """
    Analyze fixed income portfolios for summary stats,
    credit quality, sector exposure, KRD risk profile,
    maturity, duration, and categorical exposures.
    """

    def __init__(self, df, name="Portfolio"):
        self.df = df.copy()
        self.name = name
        self.df.columns = [c.strip() for c in self.df.columns]

        self.alias_map = {
            "rating": ["Rating", "Composite Rating", "Moody", "S&P", "Fitch", "MSCI"],
            "sector": ["Sector", "Issuer Sector", "Industry", "GICS Sector"],
            "issuer": ["Issuer Name", "Issuer", "Security Name", "Description", "Ticker"],
            "currency": ["Currency", "Ccy", "Base Currency", "Trade Currency"]
        }
        self.rating_cols = self._find_cols("rating")   # list of all rating cols
        self.sector_col = self._get_primary_col(self._find_cols("sector"))
        self.issuer_col = self._get_primary_col(self._find_cols("issuer"))
        self.currency_col = self._get_primary_col(self._find_cols("currency"))

        if "Market Value" in self.df.columns:
            self.df["Market Value"] = pd.to_numeric(self.df["Market Value"], errors="coerce")
    def _find_cols(self, category):
        """Return all matching columns for a category"""
        aliases = self.alias_map.get(category, [])
        return [c for c in self.df.columns if any(alias.lower() in c.lower() for alias in aliases)]

    def _get_primary_col(self, cols):
        """Return the first column if multiple matches are found"""
        return cols[0] if cols else None

    def summary(self):
        total_mv = self.df["Market Value"].sum()

        weighted_yield = None
        if "Yield to Worst" in self.df.columns:
            weighted_yield = (self.df["Yield to Worst"] * self.df["Market Value"]).sum() / total_mv

        avg_maturity = None
        if "Maturity" in self.df.columns:
            avg_maturity = (pd.to_datetime(self.df["Maturity"], errors="coerce") - pd.Timestamp.today()).dt.days.mean()
            avg_maturity = avg_maturity / 365.0

        return {
            "Portfolio": self.name,
            "Total Market Value": total_mv,
            "Weighted Yield to Worst": weighted_yield,
            "Average Maturity (yrs)": avg_maturity
        }

    def combined_rating(self):
        """Build a Composite Rating column from Fitch, Moody's, S&P, MSCI (priority order)"""
        if not self.rating_cols:
            return None

        priority = ["Fitch", "Moody", "S&P", "MSCI"]

        def pick_rating(row):
            for p in priority:
                for col in self.rating_cols:
                    if p.lower() in col.lower() and pd.notnull(row[col]):
                        return row[col]
            return None

        self.df["Composite Rating"] = self.df.apply(pick_rating, axis=1)
        return "Composite Rating"

    def credit_distribution(self):
        """Aggregate credit quality distribution using Composite Rating"""
        comp_col = self.combined_rating()
        if comp_col:
            dist = self.df.groupby(comp_col)["Market Value"].sum()
            return (dist / dist.sum() * 100).sort_index()
        return pd.Series()

    def rating_distributions(self):
        """
        Return a dictionary of distributions for each rating column found.
        Example: {"Moody's": Series, "S&P": Series, ...}
        """
        results = {}
        for col in self.rating_cols:
            dist = self.df.groupby(col)["Market Value"].sum()
            results[col] = (dist / dist.sum() * 100).sort_index()
        return results

    def sector_exposure(self):
        if self.sector_col:
            exp = self.df.groupby(self.sector_col)["Market Value"].sum()
            return (exp / exp.sum() * 100).sort_values(ascending=False)
        return pd.Series()

    def krd_profile(self):
        krd_cols = [c for c in self.df.columns if "KRD Contribution" in c]
        if not krd_cols:
            return pd.Series()

        krd_weighted = self.df[krd_cols].multiply(self.df["Market Value"], axis=0).sum()
        return krd_weighted / self.df["Market Value"].sum()

    def top_holdings(self, n=10):
        if self.issuer_col:
            return self.df.groupby(self.issuer_col)["Market Value"].sum().nlargest(n)
        return pd.Series([], name="No Issuer Column Found")

    def duration(self):
        dur_col = next((c for c in self.df.columns if "duration" in c.lower()), None)
        if dur_col:
            weighted_dur = (self.df[dur_col] * self.df["Market Value"]).sum() / self.df["Market Value"].sum()
            return {"Portfolio": self.name, "Weighted Duration": float(weighted_dur)}
        return {"Portfolio": self.name, "Weighted Duration": None}

    def maturity_buckets(self):
        if "Maturity" not in self.df.columns:
            return pd.Series([], name="No Maturity Column Found")

        today = pd.Timestamp.today()
        self.df["Maturity Date"] = pd.to_datetime(self.df["Maturity"], errors="coerce")
        self.df["Years to Maturity"] = (self.df["Maturity Date"] - today).dt.days / 365.0

        bins = [0, 3, 5, 10, 30, 100]
        labels = ["0-3y", "3-5y", "5-10y", "10-30y", "30y+"]
        self.df["Maturity Bucket"] = pd.cut(self.df["Years to Maturity"], bins=bins, labels=labels, right=False)

        dist = self.df.groupby("Maturity Bucket", observed=False)["Market Value"].sum()
        return (dist / dist.sum() * 100).sort_index()

    def currency_exposure(self):
        if self.currency_col:
            exp = self.df.groupby(self.currency_col)["Market Value"].sum()
            return (exp / exp.sum() * 100).sort_values(ascending=False)
        return pd.Series([], name="No Currency Column Found")

    def categorical_breakdowns(self, top_n=10):
        """
        Return breakdowns of all non-numeric columns (besides IDs),
        weighted by Market Value.
        """
        results = {}
        for col in self.df.select_dtypes(include="object").columns:
            if col not in ["Issuer Name", "Description"]:  # skip verbose text if needed
                dist = self.df.groupby(col)["Market Value"].sum()
                results[col] = (dist / dist.sum() * 100).sort_values(ascending=False).head(top_n)
        return results

if __name__ == "__main__":
    usd_port = pd.read_csv("data/clean/PORT_USD_clean.csv")
    eur_port = pd.read_csv("data/clean/PORT_EUR_clean.csv")

    usd_analyzer = PortfolioAnalyzer(usd_port, "USD Portfolio")
    eur_analyzer = PortfolioAnalyzer(eur_port, "EUR Portfolio")
    print("\n=== Portfolio Summaries ===")
    print(pd.DataFrame([usd_analyzer.summary(), eur_analyzer.summary()]))

    print("\n=== Composite Credit Distribution (USD) ===")
    print(usd_analyzer.credit_distribution())
    print("\n=== Composite Credit Distribution (EUR) ===")
    print(eur_analyzer.credit_distribution())

    print("\n=== Credit Distribution by Agency (USD) ===")
    for col, dist in usd_analyzer.rating_distributions().items():
        print(f"\n{col}:\n{dist}")

    print("\n=== Credit Distribution by Agency (EUR) ===")
    for col, dist in eur_analyzer.rating_distributions().items():
        print(f"\n{col}:\n{dist}")

    print("\n=== Sector Exposure (USD) ===")
    print(usd_analyzer.sector_exposure())
    print("\n=== Sector Exposure (EUR) ===")
    print(eur_analyzer.sector_exposure())

    print("\n=== KRD Profile (USD) ===")
    print(usd_analyzer.krd_profile())
    print("\n=== KRD Profile (EUR) ===")
    print(eur_analyzer.krd_profile())

    print("\n=== Top Holdings (USD) ===")
    print(usd_analyzer.top_holdings())
    print("\n=== Top Holdings (EUR) ===")
    print(eur_analyzer.top_holdings())

    print("\n=== Duration (USD) ===")
    print(usd_analyzer.duration())
    print("\n=== Duration (EUR) ===")
    print(eur_analyzer.duration())

    print("\n=== Maturity Buckets (USD) ===")
    print(usd_analyzer.maturity_buckets())
    print("\n=== Maturity Buckets (EUR) ===")
    print(eur_analyzer.maturity_buckets())

    print("\n=== Currency Exposure (USD) ===")
    print(usd_analyzer.currency_exposure())
    print("\n=== Currency Exposure (EUR) ===")
    print(eur_analyzer.currency_exposure())

    print("\n=== Other Categorical Breakdowns (USD) ===")
    for col, dist in usd_analyzer.categorical_breakdowns().items():
        print(f"\n{col}:\n{dist}")

    print("\n=== Other Categorical Breakdowns (EUR) ===")
    for col, dist in eur_analyzer.categorical_breakdowns().items():
        print(f"\n{col}:\n{dist}")
