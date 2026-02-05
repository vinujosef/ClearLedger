import pytest
import pandas as pd
from datetime import date
from core import calculate_fifo, parse_contract_note

# --- TEST 1: FIFO LOGIC ---
def test_fifo_buy_sell_logic():
    """
    Scenario:
    1. Buy 10 @ 100 (Jan 1)
    2. Buy 10 @ 120 (Jan 2)
    3. Sell 10 (Jan 3) -> Should sell the Jan 1 batch
    Result: Should hold 10 @ 120
    """
    trades_data = [
        {'symbol': 'TATA', 'date': date(2025, 1, 1), 'type': 'BUY', 'quantity': 10, 'gross_amount': 1000},
        {'symbol': 'TATA', 'date': date(2025, 1, 2), 'type': 'BUY', 'quantity': 10, 'gross_amount': 1200},
        {'symbol': 'TATA', 'date': date(2025, 1, 3), 'type': 'SELL', 'quantity': 10, 'gross_amount': 1500},
    ]
    trades_df = pd.DataFrame(trades_data)
    
    # No charges for this basic test
    notes_df = pd.DataFrame(columns=['date', 'net_total_paid'])
    
    holdings = calculate_fifo(trades_df, notes_df)
    
    assert 'TATA' in holdings
    batches = holdings['TATA']
    
    # We expect 1 batch remaining (the second one)
    total_qty = sum(b['qty'] for b in batches)
    avg_price = sum(b['qty'] * b['price'] for b in batches) / total_qty
    
    assert total_qty == 10
    assert avg_price == 120.0  # The first batch @ 100 was sold

# --- TEST 2: PRORATING CHARGES ---
def test_prorating_charges():
    """
    Scenario:
    1. Buy Stock A: 1000 Rs
    2. Buy Stock B: 1000 Rs
    3. Total Charges for day: 20 Rs
    Result: Each should bear 10 Rs cost.
    """
    d = date(2025, 1, 1)
    trades_data = [
        {'symbol': 'A', 'date': d, 'type': 'BUY', 'quantity': 10, 'gross_amount': 1000},
        {'symbol': 'B', 'date': d, 'type': 'BUY', 'quantity': 10, 'gross_amount': 1000},
    ]
    trades_df = pd.DataFrame(trades_data)
    
    notes_data = [{'date': d, 'net_total_paid': 20}]
    notes_df = pd.DataFrame(notes_data)
    
    holdings = calculate_fifo(trades_df, notes_df)
    
    # Check Price for A
    # Base Price: 1000 / 10 = 100
    # Allocated Charge: 10 Rs / 10 units = 1 Rs
    # Expected Net Price: 101
    price_a = holdings['A'][0]['price']
    assert price_a == 101.0

# --- TEST 3: CONTRACT NOTE PARSING ---
def test_parse_contract_note():
    # Minimal CSV simulation of Zerodha format
    # Note: Column indices must match the logic (Row 1 Col 3 for date, Col 10 for values)
    
    line_header = "0,1,2,3,4,5,6,7,8,9,10,11,12,13\n"
    line_date = ",,,07-11-2025,,,,,,,,,,\n"
    
    # We place '-20' at index 10 (the 11th position)
    # 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
    line_brok = "Taxable value of Supply,,,,,,,,,,-20,,,\n"
    
    fake_file = (line_header + line_date + line_brok).encode('utf-8')
    
    result = parse_contract_note(fake_file)
    
    assert result['date'] == date(2025, 11, 7)
    assert result['total_brokerage'] == 20.0