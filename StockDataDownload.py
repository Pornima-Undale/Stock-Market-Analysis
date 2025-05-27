import yfinance as yf
import talib
import numpy as np

# Define the symbol you want to check
symbol = "RELIANCE.NS"  # Example: Reliance Industries on NSE

# Load data using yfinance
data = yf.download(symbol, start='2023-01-01', progress=False)

# Extract close prices and FLATTEN it to 1D array
close_prices = data['Close'].values.flatten()

# Print array info for debugging
print(f"Close prices shape: {close_prices.shape}")
print(f"Close prices dtype: {close_prices.dtype}")
print(f"First 5 close prices: {close_prices[:5]}")
print(f"Last 5 close prices: {close_prices[-5:]}")

# Calculate RSI with TA-Lib
talib_rsi = talib.RSI(close_prices, timeperiod=14)

# Print last values - use scalar value instead of Series
print(f"\nStock: {symbol}")
print(f"Current Price: {close_prices[-1]:.2f}")
print(f"TA-Lib RSI (14): {talib_rsi[-1]:.2f}")

# Also print a few recent RSI values for context
print("\nRecent RSI values (TA-Lib):")
for i in range(-5, 0):
    date_str = data.index[i].strftime('%Y-%m-%d')
    print(f"{date_str}: {talib_rsi[i]:.2f}")