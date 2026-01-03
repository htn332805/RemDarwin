export totalCurrentAssets=34986000000
export totalCurrentLiabilities=35064000000
export current_assets=$totalCurrentAssets
export current_liabilities=$totalCurrentLiabilities
echo "Current Assets: $current_assets"
echo "Current Liabilities: $current_liabilities"
export workingCapital=$(($current_assets - $current_liabilities))
echo "Working Capital: $workingCapital"
echo "\nCalculating Current Ratio:"
python3 command.py -m current_ratio $totalCurrentAssets $totalCurrentLiabilities


export inventory=3164000000
echo "\nCalculating Quick Ratio:"
python3 command.py -m quick_ratio $totalCurrentAssets $inventory $totalCurrentLiabilities


export cash_and_cash_equivalents=9473000000
echo "\nCalculating Cash Ratio:"
python3 command.py -m cash_ratio $cash_and_cash_equivalents $totalCurrentLiabilities

export gross_profit=36790000000
export total_revenue=56654000000
echo "\nCalculating Gross Profit Margin:"
python3 command.py -m gross_profit_margin $gross_profit $total_revenue


export operating_income=11760000000
echo "\nCalculating Operating Profit Margin:"
python3 command.py -m operating_profit_margin $operating_income $total_revenue

export net_income=10180000000
export total_revenue=56654000000
echo "\nCalculating Net Profit Margin:"
python3 command.py -m net_profit_margin $net_income $total_revenue

export total_assets=122291000000
echo "\nCalculating Return on Assets (ROA):"
python3 command.py -m return_on_assets $net_income $total_assets 

export shareholders_equity=46843000000 
echo "\nCalculating Return on Equity (ROE):"
python3 command.py -m return_on_equity $net_income $shareholders_equity

export total_debt=29643000000
echo "\nCalculating Debt to Equity Ratio:"
python3 command.py -m debt_to_equity_ratio $total_debt $total_assets

#extract from historical_market_cap.csv
export market_cap=273111440000 
echo "\nCalculating Price to Sales Ratio:"
python3 command.py -m price_to_sales_ratio $market_cap $total_revenue


export number_of_shares_outstanding=3976000000
echo "\nCalculating Earnings Per Share (EPS):"
python3 command.py -m earnings_per_share $net_income $number_of_shares_outstanding

#stock price from historical stock price
export market_price_per_share=76.105
echo "\nCalculating Price to Earnings (P/E) Ratio:"
python3 command.py -m price_earnings_ratio $market_price_per_share $net_income $number_of_shares_outstanding 

#dividends per share is extract from the dvididend historical data using closet matched date
export dividends_per_share=0.26
echo "\nCalculating Dividend Yield:"
python3 command.py -m dividend_yield $dividends_per_share $market_price_per_share

export accounts_receivable=11462000000
echo "\nCalculating Days of Sales Outstanding:"
python3 command.py -m days_of_sales_outstanding $accounts_receivable $total_revenue

export COGS=19864000000
echo "\nDays of Inventory Outstanding:"
python3 command.py -m days_of_inventory_outstanding $inventory $COGS

export gross_profit=36790000000
echo "\nAlternate Days of Inventory Outstanding:"
python3 command.py -m days_of_inventory_outstanding_alt $inventory $total_revenue $gross_profit

export account_payables=16416000000
echo "\nCalculating Days of Payables Outstanding:"
python3 command.py -m days_of_payables_outstanding $account_payables $COGS

echo "\nCalculating receivables_turnover :"
python3 command.py -m receivables_turnover $total_revenue $accounts_receivable

echo "\nCalculating Payables Turnover:"
python3 command.py -m payables_turnover $COGS $account_payables

echo "\nCalculating inventory_turnover :"
python3 command.py -m inventory_turnover $COGS $inventory

echo "\nCalculating Asset Turnover:"
python3 command.py -m asset_turnover $total_revenue $total_assets

export property_plant_equipment_net=3414000000
echo "\nCalculating Fixed Asset Turnover:"
python3 command.py -m fixed_asset_turnover $total_revenue $property_plant_equipment_net

export income_tax_expense=920000000
export income_before_tax=11100000000
echo "\nCalculating Effective Tax Rate:"
python3 command.py -m effective_tax_rate $income_tax_expense $income_before_tax

echo "\nCalculating Return on Capital Employed (ROCE):"
python3 command.py -m return_on_capital_employed $operating_income $total_assets $totalCurrentLiabilities

export interest_expense=1593000000
echo "\nCalculating Interest Coverage Ratio:"
python3 command.py -m interest_coverage $operating_income $interest_expense

export long_term_debt=24036000000
echo "\nCalculating long term debt to capitalization ratio:"
python3 command.py -m long_term_debt_to_capitalization $long_term_debt $shareholders_equity


echo "\nCalculating total debt to capitalization ratio:"
python3 command.py -m total_debt_to_capitalization $total_debt $shareholders_equity

export operating_cash_flow=14193000000
echo "\nCalculating cash flow to debt ratio:"
python3 command.py -m cash_flow_to_debt_ratio $operating_cash_flow $total_debt  

echo "\nCalculating company equity multiplier:"
python3 command.py -m company_equity_multiplier $total_assets $shareholders_equity

echo "\nCalculating price cash flow ratio:"
python3 command.py -m price_cash_flow_ratio $market_cap $operating_cash_flow

export enterprise_value=293281440000
export ebitda=15378000000
echo "\nCalculating enterprise value multiple:"
python3 command.py -m enterprise_value_multiple $enterprise_value $ebitda

echo "\nCalculating revenue per share:"
python3 command.py -m revenue_per_share $total_revenue $number_of_shares_outstanding

echo "\nCalculating net_income per share:"
python3 command.py -m net_income_per_share $net_income $number_of_shares_outstanding

echo "\nCalculating operating cash flow per share:"
python3 command.py -m operating_cash_flow_per_share $operating_cash_flow $number_of_shares_outstanding

export free_cash_flow=13288000000
echo "\nCalculating free cash flow per share:"
python3 command.py -m free_cash_flow_per_share $free_cash_flow $number_of_shares_outstanding

export cash_and_short_term_investments=17237000000 
echo "\nCalculating cash per share:"
python3 command.py -m cash_per_share $cash_and_short_term_investments $number_of_shares_outstanding

echo "\nCalculating book value per share:"
python3 command.py -m book_value_per_share $shareholders_equity $number_of_shares_outstanding

echo "\nCalculating pretax profit margin:"
python3 command.py -m pretax_profit_margin $income_before_tax $total_revenue

echo "\nCaclulating net_income per ebt:"
python3 command.py -m net_income_per_ebt $net_income $income_before_tax

echo "\nCalculating ebt per ebit:"
python3 command.py -m ebt_per_ebit $income_before_tax $operating_income

echo "\nCalculating ebit per revenue:"
python3 command.py -m ebit_per_revenue $operating_income $total_revenue

export EPS=2.56
echo "\nCalculating payout ratio:"
python3 command.py -m payout_ratio $dividends_per_share  $(python3 command.py -m earnings_per_share $net_income $number_of_shares_outstanding)

echo "\nCalculating operating cash flow sales ratio:"
python3 command.py -m operating_cash_flow_sales_ratio $operating_cash_flow $total_revenue

echo "\nCalculating free cash flow to operating cash flow ratio:"
python3 command.py -m free_cash_flow_operating_cash_flow_ratio $free_cash_flow $operating_cash_flow  

export capital_expenditures=212000000
echo "\nCalculating capital expenditures coverage ratio:"
python3 command.py -m capital_expenditure_coverage_ratio $operating_cash_flow $capital_expenditures

echo "\nCalculating ev to sales:"
python3 command.py -m ev_to_sales $enterprise_value $total_revenue  

echo "\nCalculating ev to operating cash flow:"
python3 command.py -m ev_to_operating_cash_flow $enterprise_value $operating_cash_flow  

echo "\nCalculating ev to free cash flow:"
python3 command.py -m ev_to_free_cash_flow $enterprise_value $free_cash_flow

export assumed_growth_rate=0.1
echo "\nCalculating price earnings to growth ratio:"
python3 command.py -m price_earnings_to_growth_ratio $(python3 command.py -m price_earnings_ratio $market_price_per_share $net_income $number_of_shares_outstanding 
) $assumed_growth_rate

echo "\nCalculating earning yield:"
python3 command.py -m earning_yield $(python3 command.py -m earnings_per_share $net_income $number_of_shares_outstanding) $market_price_per_share 

echo "\nCalculating income quality:"
python3 command.py -m income_quality $operating_cash_flow $net_income

export SGA=2980000000
echo "\nCalculating SGA to revenue ratio:"
python3 command.py -m sales_general_and_administrative_to_revenue $SGA $total_revenue

export RND_expenses=9300000000
echo "\nCalculating R&D to revenue ratio:"
python3 command.py -m research_and_development_to_revenue $RND_expenses $total_revenue

export goodwill_intangible_assets=68311000000
echo "\nCalculating intangibles to total assets ratio:"
python3 command.py -m intangibles_to_total_assets $goodwill_intangible_assets $total_assets 

export capital_expenditures=905000000
echo "\nCalculating capex to operating cash flow ratio:"
python3 command.py -m capex_to_operating_cash_flow $capital_expenditures $operating_cash_flow

echo "\nCalculating capex to revenue ratio:"
python3 command.py -m capex_to_revenue $capital_expenditures $total_revenue

export depreciation_amortization=2862000000
echo "\nCalculating capex to depreciation ratio:"
python3 command.py -m capex_to_depreciation $capital_expenditures $depreciation_amortization

export stock_based_compensation=0
echo "\nCalculating stock based compensation to revenue ratio:"
python3 command.py -m stock_based_compensation_to_revenue $stock_based_compensation $total_revenue

echo "\nCalculating return on invested capital (ROIC):"
python3 command.py -m roic $net_income $total_assets $totalCurrentLiabilities

echo "\nCalculating return on tangible assets:"
python3 command.py -m return_on_tangible_assets $net_income $total_assets $goodwill_intangible_assets

#0.75*Accounts Receivable assumed 25% discount for bad debts
#0.5*Inventory assumed 50% discount for liquidation
export total_liabilities=75448000000
echo "\nCalculating Graham net to net per share metric:"
python3 command.py -m graham_net_net_per_share $cash_and_cash_equivalents $accounts_receivable $inventory $total_liabilities $number_of_shares_outstanding

echo "\nCalculating working capital:"
python3 command.py -m working_capital $current_assets $current_liabilities

echo "\nCalculating tangible asset value:"
python3 command.py -m tangible_asset_value $total_assets $goodwill_intangible_assets

echo "\nCalculating net current asset value:"
python3 command.py -m net_current_asset_value $current_assets $current_liabilities

echo "\nCalculating invested capital:"
python3 command.py -m invested_capital $total_assets $current_liabilities

echo "\nCalculating capex per share:"
python3 command.py -m capex_per_share $capital_expenditures $number_of_shares_outstanding

#--------------------chained calculations--------------------
echo "\nCalculating price to book ratio:"
python3 command.py -m price_to_book_ratio $market_price_per_share  $shareholders_equity $number_of_shares_outstanding

echo "\nCalculating price to free cash flow ratio:"
python3 command.py -m price_to_free_cash_flow_ratio $market_price_per_share  $free_cash_flow $number_of_shares_outstanding

echo "\nCalculating price to operating cash flow ratio:"
python3 command.py -m price_to_operating_cash_flow_ratio $market_price_per_share  $operating_cash_flow $number_of_shares_outstanding

echo "\nCalculating free cash flow yield:"
python3 command.py -m free_cash_flow_yield $free_cash_flow  $number_of_shares_outstanding $market_price_per_share

echo "\nCalculating Graham number:"
python3 command.py -m graham_number $net_income $shareholders_equity $number_of_shares_outstanding

echo "\nCalculating Operating Cycle:"
python3 command.py -m operating_cycle $accounts_receivable $total_revenue $inventory $COGS

echo "\nCalculating Cash Conversion Cycle:"
echo "python3 command.py -m cash_conversion_cycle $accounts_receivable $total_revenue $inventory $COGS $account_payables"
python3 command.py -m cash_conversion_cycle $accounts_receivable $total_revenue $inventory $COGS $account_payables
