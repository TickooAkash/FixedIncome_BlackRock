import pandas as pd
import re
from pathlib import Path


class PortfolioLoader:
    def __init__(self, data_dir="data", raw_filename="Portfolio_holdings.xlsx"):
        """
        Initialize loader with paths.
        """
        self.data_dir = Path(data_dir)
        self.raw_file = self.data_dir / "raw" / raw_filename
        self.clean_dir = self.data_dir / "clean"
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "raw").mkdir(exist_ok=True)  # Ensure raw directory exists
        self.clean_dir.mkdir(exist_ok=True)

        if not self.raw_file.exists():
            raise FileNotFoundError("Excel file not found: {}".format(self.raw_file))

        self.xls = pd.ExcelFile(self.raw_file)
        print("Available sheets: {}".format(self.xls.sheet_names))

    def load_and_clean(self, sheet_name):
        """
        Load a portfolio sheet and do some basic cleaning.
        Note: The Excel file has extra rows before the real header (start at row 5).
        """
        df = pd.read_excel(self.raw_file, sheet_name=sheet_name, header=4)
        df.columns = df.iloc[0]
        df = df.drop(0).reset_index(drop=True)
        df.columns = [str(c).strip() for c in df.columns]

        krd_cols = [c for c in df.columns if re.match(r"^\d+[MY]$", str(c).strip())]
        rename_map = {c: "KRD Contribution {}".format(c) for c in krd_cols}
        df = df.rename(columns=rename_map)

        if "Maturity" in df.columns:
            df["Maturity"] = pd.to_datetime(df["Maturity"], errors="coerce")

        for col in df.columns:
            if col not in ["CUSIP", "Security Description", "Ticker"]:
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    pass

        return df

    def save_cleaned(self, df, name):
        """
        Save cleaned DataFrame to /data/clean folder.
        """
        output_file = self.clean_dir / "{}_clean.csv".format(name)
        df.to_csv(output_file, index=False)
        print("Saved cleaned file: {}".format(output_file))


if __name__ == "__main__":
    loader = PortfolioLoader()

    usd_port = loader.load_and_clean("PORT_USD")
    eur_port = loader.load_and_clean("PORT_EUR")

    print("USD portfolio: {} bonds, {} columns".format(usd_port.shape[0], usd_port.shape[1]))
    print("EUR portfolio: {} bonds, {} columns".format(eur_port.shape[0], eur_port.shape[1]))

    loader.save_cleaned(usd_port, "PORT_USD")
    loader.save_cleaned(eur_port, "PORT_EUR")

    print("Cleaned files saved in /data/clean")