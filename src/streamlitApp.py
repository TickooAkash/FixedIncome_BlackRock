import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from portfolioAnalysis import PortfolioAnalyzer

@st.cache_data
def load_portfolio(file_path, portfolio_name):
    df = pd.read_csv(file_path)
    return PortfolioAnalyzer(df, portfolio_name)

st.set_page_config(page_title="Portfolio Analysis Dashboard", layout="wide")

st.title("BlackRock Fixed Income Portfolio Analysis")

portfolio_choice = st.sidebar.radio("Select Portfolio", ["USD Portfolio", "EUR Portfolio"])

if portfolio_choice == "USD Portfolio":
    analyzer = load_portfolio("data/clean/PORT_USD_clean.csv", "USD Portfolio")
else:
    analyzer = load_portfolio("data/clean/PORT_EUR_clean.csv", "EUR Portfolio")

analysis_choice = st.sidebar.selectbox(
    "Select Analysis",
    [
        "Portfolio Summary",
        "Credit Distribution",
        "Sector Exposure",
        "Top Holdings",
        "Duration",
        "Maturity Buckets",
        "KRD Profile"
    ]
)


if analysis_choice == "Portfolio Summary":
    st.subheader("Portfolio Summary")
    st.dataframe(pd.DataFrame([analyzer.summary()]))

elif analysis_choice == "Credit Distribution":
    st.subheader("Credit Distribution")
    data = analyzer.credit_distribution()
    st.dataframe(data)
    st.bar_chart(data)

elif analysis_choice == "Sector Exposure":
    st.subheader("Sector Exposure")
    data = analyzer.sector_exposure()
    st.dataframe(data)
    st.bar_chart(data)

elif analysis_choice == "Top Holdings":
    st.subheader("Top Holdings")
    data = analyzer.top_holdings()
    st.dataframe(data)
    st.bar_chart(data)

elif analysis_choice == "Duration":
    st.subheader("Portfolio Duration")
    st.json(analyzer.duration())

elif analysis_choice == "Maturity Buckets":
    st.subheader("Maturity Buckets")
    data = analyzer.maturity_buckets()
    st.dataframe(data)
    st.bar_chart(data)

elif analysis_choice == "KRD Profile":
    st.subheader("KRD Profile")
    data = analyzer.krd_profile()
    st.dataframe(data)
    st.line_chart(data)