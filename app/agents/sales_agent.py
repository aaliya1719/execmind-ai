"""Sales analysis agent for ExecMind AI.

Performs deterministic statistical calculations on ingested sales datasets
to extract key indicators, trends, distributions, and highlights.
"""

import pandas as pd
from typing import Dict, Any


def _find_column(df: pd.DataFrame, patterns: list, default: str = None) -> str:
    """Find a column in a DataFrame matching a list of case-insensitive patterns."""
    cols_clean = [str(c).lower().replace(" ", "").replace("_", "") for c in df.columns]
    for pattern in patterns:
        pattern_clean = pattern.lower().replace(" ", "").replace("_", "")
        if pattern_clean in cols_clean:
            idx = cols_clean.index(pattern_clean)
            return df.columns[idx]
    return default


def analyze_sales(data: pd.DataFrame, *args, **kwargs) -> Dict[str, Any]:
    """Analyze the sales DataFrame and return structured observations.
    
    Args:
        data: A pandas DataFrame containing sales records.
        
    Returns:
        A structured dictionary of sales insights.
        
    Raises:
        ValueError: If essential columns (like sales/revenue) are missing or invalid.
    """
    if data is None or data.empty:
        raise ValueError("Cannot analyze sales: DataFrame is empty or None.")
        
    # Resolve columns
    sales_col = _find_column(data, ["sales", "revenue", "total", "amount", "price_each", "priceeach", "turnover"])
    order_col = _find_column(data, ["ordernumber", "orderid", "id", "order_number", "invoice", "invoiceno", "order_no", "orderno"])
    date_col = _find_column(data, ["orderdate", "date", "order_date", "timestamp", "invoice_date", "invoicedate"])
    product_col = _find_column(data, ["productcode", "product", "product_code", "item", "product_name", "description", "item_code"])
    country_col = _find_column(data, ["country", "region", "nation"])
    deal_col = _find_column(data, ["dealsize", "deal_size", "size"])
    status_col = _find_column(data, ["status", "orderstatus", "order_status"])
    
    if not sales_col:
        raise ValueError(
            "Could not identify a Sales or Revenue column. Please make sure the dataset contains "
            "a numeric column representing sales value (e.g., 'Sales', 'Revenue', or 'Total')."
        )
        
    # Convert sales to numeric, coercing errors
    sales_series = pd.to_numeric(data[sales_col], errors='coerce').fillna(0)
    
    # 1. Total Sales
    total_sales = float(sales_series.sum())
    
    # 2. Total Orders
    if order_col:
        total_orders = int(data[order_col].nunique())
    else:
        total_orders = len(data)
        
    # Average Order Value
    avg_order_value = total_sales / total_orders if total_orders > 0 else 0.0
    
    # 3. Monthly Sales Trend
    monthly_trend = {}
    if date_col:
        dates = pd.to_datetime(data[date_col], errors='coerce')
        valid_dates_idx = dates.notna()
        if valid_dates_idx.any():
            temp_df = pd.DataFrame({
                "sales": sales_series[valid_dates_idx],
                "period": dates[valid_dates_idx].dt.to_period("M").astype(str)
            })
            monthly_trend = temp_df.groupby("period")["sales"].sum().round(2).to_dict()
            monthly_trend = dict(sorted(monthly_trend.items()))
            
    # 4. Top 5 Products by Revenue
    top_products = {}
    if product_col:
        prod_revenue = data.groupby(product_col)[sales_col].sum()
        top_products = prod_revenue.sort_values(ascending=False).head(5).round(2).to_dict()
        
    # 5. Top 5 Countries by Revenue
    top_countries = {}
    if country_col:
        country_revenue = data.groupby(country_col)[sales_col].sum()
        top_countries = country_revenue.sort_values(ascending=False).head(5).round(2).to_dict()
        
    # 6. Deal Size Distribution
    deal_distribution = {}
    if deal_col:
        deal_distribution = data.groupby(deal_col).size().to_dict()
    else:
        categories = []
        for val in sales_series:
            if val < 3000:
                categories.append("Small")
            elif val < 7000:
                categories.append("Medium")
            else:
                categories.append("Large")
        deal_distribution = pd.Series(categories).value_counts().to_dict()
        
    # 7. Order Status Summary
    status_summary = {}
    if status_col:
        status_summary = data.groupby(status_col).size().to_dict()
        
    # 8. Key Observations (Deterministic generation)
    observations = []
    
    observations.append(
        f"Total revenue generated is ${total_sales:,.2f} across {total_orders:,} unique transactions, "
        f"yielding an Average Order Value (AOV) of ${avg_order_value:,.2f}."
    )
    
    if top_products:
        top_prod_name = list(top_products.keys())[0]
        top_prod_rev = list(top_products.values())[0]
        top_prod_pct = (top_prod_rev / total_sales * 100) if total_sales > 0 else 0
        observations.append(
            f"The best performing product is '{top_prod_name}' with ${top_prod_rev:,.2f} in revenue, "
            f"accounting for {top_prod_pct:.1f}% of total sales."
        )
        
    if top_countries:
        top_country_name = list(top_countries.keys())[0]
        top_country_rev = list(top_countries.values())[0]
        top_country_pct = (top_country_rev / total_sales * 100) if total_sales > 0 else 0
        observations.append(
            f"The primary geographical market is '{top_country_name}', driving ${top_country_rev:,.2f} in revenue "
            f"({top_country_pct:.1f}% of global turnover)."
        )
        
    if monthly_trend:
        peak_month = max(monthly_trend, key=monthly_trend.get)
        peak_sales = monthly_trend[peak_month]
        observations.append(
            f"Sales peaked in {peak_month} reaching ${peak_sales:,.2f} in monthly volume."
        )
        
    if deal_distribution:
        dominant_deal = max(deal_distribution, key=deal_distribution.get)
        dominant_count = deal_distribution[dominant_deal]
        total_deals = sum(deal_distribution.values())
        dominant_pct = (dominant_count / total_deals * 100) if total_deals > 0 else 0
        observations.append(
            f"Transactions are heavily weighted towards the '{dominant_deal}' segment, "
            f"representing {dominant_count:,} orders ({dominant_pct:.1f}% of total deal volume)."
        )

    return {
        "total_sales": total_sales,
        "total_orders": total_orders,
        "average_order_value": avg_order_value,
        "monthly_sales_trend": monthly_trend,
        "top_products_by_revenue": top_products,
        "top_countries_by_revenue": top_countries,
        "deal_size_distribution": deal_distribution,
        "order_status_summary": status_summary,
        "key_observations": observations
    }

