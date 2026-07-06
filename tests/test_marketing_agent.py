import sys
import os
import pandas as pd

# Append project root dynamically to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.marketing_agent import recommend_marketing

def test_marketing_agent():
    print("Starting marketing agent testing...")
    
    # 1. Mock DataFrame resembling transactional sales entries
    mock_data = pd.DataFrame({
        "Order Number": [1001, 1001, 1002, 1002, 1003, 1004],
        "Sales": [1000.0, 2000.0, 150.0, 50.0, 5000.0, 300.0],
        "Product Code": ["PROD_A", "PROD_B", "PROD_A", "PROD_B", "PROD_C", "PROD_D"],
        "Country": ["USA", "USA", "USA", "USA", "Canada", "Canada"],
        "Status": ["Shipped", "Shipped", "Cancelled", "Cancelled", "Shipped", "Shipped"]
    })
    
    # Test passing a raw DataFrame
    marketing_insights = recommend_marketing(mock_data)
    
    print("\n--- Testing with DataFrame ---")
    print(f"Underperforming Products: {marketing_insights['underperforming_products']}")
    # Bottom product should be PROD_D (300) or PROD_A/B (1002 entries sum to 150 & 50 respectively)
    # PROD_B total is 2000+50 = 2050. PROD_A is 1000+150 = 1150. PROD_C is 5000. PROD_D is 300.
    # Lowest should be PROD_D (300) or PROD_A (1150) or PROD_B (2050). Let's check:
    assert "PROD_D" in marketing_insights["underperforming_products"]
    
    print(f"Cross-sell Opportunities: {marketing_insights['cross_sell_opportunities']}")
    # PROD_A and PROD_B are bought together in order 1001 and 1002
    assert len(marketing_insights["cross_sell_opportunities"]) > 0
    best_pair = marketing_insights["cross_sell_opportunities"][0]
    assert best_pair["product_1"] == "PROD_A"
    assert best_pair["product_2"] == "PROD_B"
    assert best_pair["co_occurrences"] == 2
    
    print(f"Suggested Promotions: {marketing_insights['suggested_promotions']}")
    assert len(marketing_insights["suggested_promotions"]) >= 2 # Clearance, AOV boost, Customer win-back
    
    print(f"Geographical Expansion: {marketing_insights['market_expansion_opportunities']}")
    assert len(marketing_insights["market_expansion_opportunities"]) > 0
    
    print(f"Risks Detected: {marketing_insights['marketing_risks']}")
    # USA is 3200 out of 8500 (37%), Canada is 5300 out of 8500 (62%) -> Canada concentration risk!
    # PROD_C is 5000 out of 8500 (58%) -> PROD_C concentration risk!
    # Cancelled orders = 2 entries out of 6 (33%) -> high cancellation risk!
    risks = [r["risk_type"] for r in marketing_insights["marketing_risks"]]
    print(f"Detected Risks: {risks}")
    assert "High Product Concentration" in risks
    assert "High Geographical Concentration" in risks
    assert "High Transaction Cancellation" in risks
    
    print(f"Key Marketing Observations: {marketing_insights['key_marketing_observations']}")
    assert len(marketing_insights["key_marketing_observations"]) > 0
    
    # 2. Test passing pre-calculated insights dictionary only (without DataFrame)
    print("\n--- Testing with pre-calculated insights dict only ---")
    mock_sales_insights = {
        "total_sales": 10000.0,
        "total_orders": 20,
        "average_order_value": 500.0,
        "top_products_by_revenue": {"PROD_A": 6000.0, "PROD_B": 4000.0},
        "top_countries_by_revenue": {"USA": 9000.0, "Canada": 1000.0},
        "monthly_sales_trend": {"2026-01": 8000.0, "2026-02": 2000.0},
        "deal_size_distribution": {"Large": 10, "Small": 10},
        "order_status_summary": {"Shipped": 19, "Cancelled": 1}
    }
    
    dict_marketing_insights = recommend_marketing(mock_sales_insights)
    print(f"Default Top-Seller Bundle Cross-sell (fallback): {dict_marketing_insights['cross_sell_opportunities']}")
    assert len(dict_marketing_insights["cross_sell_opportunities"]) == 1
    assert dict_marketing_insights["cross_sell_opportunities"][0]["type"] == "Top-Seller Bundle"
    assert dict_marketing_insights["cross_sell_opportunities"][0]["product_1"] == "PROD_A"
    assert dict_marketing_insights["cross_sell_opportunities"][0]["product_2"] == "PROD_B"
    
    # Assert seasonal month campaign recommendations are mapped
    print(f"Seasonal Recommendations: {dict_marketing_insights['seasonal_campaign_recommendations']}")
    periods = [c["period"] for c in dict_marketing_insights["seasonal_campaign_recommendations"]]
    assert "2026-01" in periods # Peak
    assert "2026-02" in periods # Trough
    
    print("All marketing agent tests passed successfully!")

if __name__ == "__main__":
    test_marketing_agent()
