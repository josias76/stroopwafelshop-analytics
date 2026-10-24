from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_CANDIDATES = [
    PROJECT_ROOT / ".env",
    PROJECT_ROOT.parent / ".env",
]


def load_environment() -> None:
    for env_path in ENV_CANDIDATES:
        if env_path.exists():
            load_dotenv(env_path, override=False)
            break


def make_engine():
    url = URL.create(
        "postgresql+psycopg2",
        username=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "password"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database="stroopwafelshop",
    )
    return create_engine(url)


@st.cache_data(show_spinner=False)
def load_transactions_dataset() -> pd.DataFrame:
    query = """
        select
            sales_id,
            sold_date,
            sold_at,
            sold_weekday,
            employee_id,
            employee_name,
            payment_type,
            revenue,
            total_discount,
            sales_line_count,
            has_line_items
        from analytics.mart_sales_transactions
        order by sold_at
    """

    return pd.read_sql_query(
        query,
        make_engine(),
        parse_dates=["sold_date", "sold_at"],
    )


@st.cache_data(show_spinner=False)
def load_sales_detail_dataset() -> pd.DataFrame:
    query = """
        select
            detail.sales_line_id,
            detail.sales_id,
            detail.sold_date,
            detail.sold_at,
            detail.sold_weekday,
            detail.payment_type,
            detail.employee_id,
            detail.employee_name,
            detail.product_id,
            detail.product_name,
            detail.promotion_id,
            detail.promotion_name,
            detail.promotion_bucket,
            detail.quantity_sold,
            product.unit_cost,
            detail.unit_price,
            detail.unit_discount,
            detail.revenue,
            detail.total_discount,
            round(detail.revenue - (detail.quantity_sold * product.unit_cost), 3) as gross_profit,
            detail.has_promotion
        from analytics.mart_sales_detail as detail
        left join analytics.dim_products as product
            on detail.product_id = product.product_id
        order by detail.sold_at
    """

    return pd.read_sql_query(
        query,
        make_engine(),
        parse_dates=["sold_date", "sold_at"],
    )


@st.cache_data(show_spinner=False)
def load_sales_performance_dataset() -> pd.DataFrame:
    query = """
        select
            sales_performance_key,
            sold_date,
            sold_weekday,
            employee_id,
            employee_name,
            product_id,
            product_name,
            promotion_id,
            promotion_name,
            promotion_bucket,
            payment_type,
            quantity_sold,
            revenue,
            total_discount,
            sales_line_count
        from analytics.mart_sales_performance
        order by sold_date, employee_name, product_name
    """

    return pd.read_sql_query(
        query,
        make_engine(),
        parse_dates=["sold_date"],
    )


def format_currency(value: float) -> str:
    return f"{value:,.2f} €".replace(",", " ").replace(".", ",")


def format_integer(value: float) -> str:
    return f"{int(value):,}".replace(",", " ")


def compute_average_transaction_value(total_revenue: float, total_transactions: float) -> float:
    if total_transactions == 0:
        return 0.0
    return total_revenue / total_transactions


def main() -> None:
    load_environment()

    st.set_page_config(
        page_title="Stroopwafelshop Analytics",
        layout="wide",
    )

    st.title("Pilotage analytique local de Stroopwafelshop")
    st.caption("Pipeline open source: PostgreSQL + dbt-core + Streamlit")

    sales_detail = load_sales_detail_dataset()
    sales_performance = load_sales_performance_dataset()
    transactions = load_transactions_dataset()

    min_date = transactions["sold_date"].min().date()
    max_date = transactions["sold_date"].max().date()

    st.sidebar.header("Filtres")
    selected_dates = st.sidebar.date_input(
        "Période",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
    else:
        start_date = end_date = min_date

    selected_products = st.sidebar.multiselect(
        "Produits",
        options=sorted(sales_detail["product_name"].dropna().unique().tolist()),
    )
    selected_employees = st.sidebar.multiselect(
        "Employés",
        options=sorted(sales_detail["employee_name"].dropna().unique().tolist()),
    )

    filtered_detail = sales_detail.loc[
        sales_detail["sold_date"].dt.date.between(start_date, end_date)
    ].copy()
    filtered_performance = sales_performance.loc[
        sales_performance["sold_date"].dt.date.between(start_date, end_date)
    ].copy()
    filtered_transactions = transactions.loc[
        transactions["sold_date"].dt.date.between(start_date, end_date)
    ].copy()

    if selected_products:
        filtered_detail = filtered_detail[filtered_detail["product_name"].isin(selected_products)]
        filtered_performance = filtered_performance[
            filtered_performance["product_name"].isin(selected_products)
        ]

    if selected_employees:
        filtered_detail = filtered_detail[
            filtered_detail["employee_name"].isin(selected_employees)
        ]
        filtered_performance = filtered_performance[
            filtered_performance["employee_name"].isin(selected_employees)
        ]
        filtered_transactions = filtered_transactions[
            filtered_transactions["employee_name"].isin(selected_employees)
        ]

    total_units = float(filtered_performance["quantity_sold"].sum())
    total_revenue = float(filtered_performance["revenue"].sum())
    gross_profit = float(filtered_detail["gross_profit"].sum())
    if selected_products:
        total_transactions = float(filtered_detail["sales_id"].nunique())
    else:
        total_transactions = float(filtered_transactions["sales_id"].nunique())
    average_transaction_value = compute_average_transaction_value(
        total_revenue,
        total_transactions,
    )

    kpi_1, kpi_2, kpi_3, kpi_4, kpi_5 = st.columns(5)
    kpi_1.metric("Ventes totales (unités)", format_integer(total_units))
    kpi_2.metric("Chiffre d'affaires", format_currency(total_revenue))
    kpi_3.metric("Transactions", format_integer(total_transactions))
    kpi_4.metric("Bénéfice brut", format_currency(gross_profit))
    kpi_5.metric(
        "Valeur moyenne / transaction",
        format_currency(average_transaction_value),
    )

    sales_over_time = (
        filtered_performance.groupby("sold_date", as_index=False)
        .agg(revenue=("revenue", "sum"), quantity_sold=("quantity_sold", "sum"))
        .sort_values("sold_date")
    )
    top_products = (
        filtered_performance.groupby("product_name", as_index=False)
        .agg(revenue=("revenue", "sum"), quantity_sold=("quantity_sold", "sum"))
        .sort_values("revenue", ascending=False)
        .head(10)
    )
    employee_performance = (
        filtered_performance.groupby("employee_name", as_index=False)
        .agg(
            revenue=("revenue", "sum"),
            quantity_sold=("quantity_sold", "sum"),
            sales_line_count=("sales_line_count", "sum"),
        )
        .sort_values("revenue", ascending=False)
    )
    promotions_impact = (
        filtered_performance.groupby("promotion_bucket", as_index=False)
        .agg(
            revenue=("revenue", "sum"),
            total_discount=("total_discount", "sum"),
            quantity_sold=("quantity_sold", "sum"),
        )
        .sort_values("revenue", ascending=False)
    )

    chart_left, chart_right = st.columns(2)

    with chart_left:
        st.subheader("Ventes dans le temps")
        fig_sales_time = px.line(
            sales_over_time,
            x="sold_date",
            y="revenue",
            markers=True,
            labels={"sold_date": "Date", "revenue": "Chiffre d'affaires"},
        )
        st.plotly_chart(fig_sales_time, use_container_width=True)

    with chart_right:
        st.subheader("Top produits")
        fig_products = px.bar(
            top_products,
            x="product_name",
            y="revenue",
            text_auto=".2s",
            labels={"product_name": "Produit", "revenue": "Chiffre d'affaires"},
        )
        st.plotly_chart(fig_products, use_container_width=True)

    chart_left, chart_right = st.columns(2)

    with chart_left:
        st.subheader("Performance employés")
        fig_employees = px.bar(
            employee_performance,
            x="employee_name",
            y="revenue",
            color="quantity_sold",
            labels={
                "employee_name": "Employé",
                "revenue": "Chiffre d'affaires",
                "quantity_sold": "Unités vendues",
            },
        )
        st.plotly_chart(fig_employees, use_container_width=True)

    with chart_right:
        st.subheader("Impact des promotions")
        fig_promotions = px.bar(
            promotions_impact,
            x="promotion_bucket",
            y="revenue",
            color="total_discount",
            labels={
                "promotion_bucket": "Promotion",
                "revenue": "Chiffre d'affaires",
                "total_discount": "Remise totale",
            },
        )
        st.plotly_chart(fig_promotions, use_container_width=True)

    st.subheader("Données détaillées")
    st.dataframe(
        filtered_detail.sort_values("sold_at", ascending=False),
        use_container_width=True,
        hide_index=True,
    )


if __name__ == "__main__":
    main()
