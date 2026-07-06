import sys
import os
import pandas as pd

# Append project root dynamically to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.sales_agent import analyze_sales

def test_sales_agent():
    print("Starting sales agent testing...")
    
    # Mock data resembling typical Kaggle sales datasets
    mock_data = pd.DataFrame({
        "Order Number": [101, 101, 102, 103, 104, 105],
        "Sales": [1200.50, 800.00, 3500.00, 7500.00, 150.00, 4200.00],
        "Order Date": ["2026-01-10", "2026-01-10", "2026-01-15", "2026-02-05", "2026-02-12", "2026-03-01"],
        "Product Code": ["PROD_A", "PROD_B", "PROD_A", "PROD_C", "PROD_B", "PROD_C"],
        "Country": ["USA", "USA", "Canada", "UK", "UK", "Canada"],
        "Status": ["Shipped", "Shipped", "Pending", "Shipped", "Cancelled", "Shipped"],
        "Deal Size": ["Small", "Small", "Medium", "Large", "Small", "Medium"]
    })
    
    insights = analyze_sales(mock_data)
    
    # Print metrics
    print(f"Total Sales: {insights['total_sales']} (Expected: 17350.5)")
    assert insights["total_sales"] == 17350.5
    
    print(f"Total Orders: {insights['total_orders']} (Expected: 5)")
    assert insights["total_orders"] == 5
    
    print(f"AOV: {insights['average_order_value']} (Expected: 3470.1)")
    assert abs(insights["average_order_value"] - 3470.1) < 0.01
    
    print(f"Monthly Trend: {insights['monthly_sales_trend']}")
    assert insights["monthly_sales_trend"] == {"2026-01": 5500.5, "2026-02": 7650.0, "2026-03": 4200.0}
    
    print(f"Top Product: {insights['top_products_by_revenue']}")
    assert list(insights["top_products_by_revenue"].keys())[0] == "PROD_C"
    
    print(f"Top Country: {insights['top_countries_by_revenue']}")
    assert list(insights["top_countries_by_revenue"].keys())[0] == "Canada"
    
    print(f"Observations: {insights['key_observations']}")
    assert len(insights["key_observations"]) == 5
    
    # Test fallback categorization (when Deal Size is missing)
    mock_data_no_deal = mock_data.drop(columns=["Deal Size"])
    insights_fallback = analyze_sales(mock_data_no_deal)
    print(f"Fallback Deal Distribution: {insights_fallback['deal_size_distribution']}")
    # 1200.50 (Small), 800 (Small), 3500 (Medium), 7500 (Large), 150 (Small), 4200 (Medium)
    # Small: 3, Medium: 2, Large: 1
    assert insights_fallback["deal_size_distribution"] == {"Small": 3, "Medium": 2, "Large": 1}

    # Test error raising when sales column is missing
    mock_data_invalid = mock_data.drop(columns=["Sales"])
    try:
        analyze_sales(mock_data_invalid)
        print("ERROR: Should have failed for missing Sales column")
        assert False
    except ValueError as e:
        print(f"Caught expected missing column exception: {e}")

    print("All sales agent tests passed successfully!")

if __name__ == "__main__":
    test_sales_agent()
