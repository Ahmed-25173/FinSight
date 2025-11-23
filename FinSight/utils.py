import yfinance as yf
from decimal import Decimal
from .models import StockPriceCache

def fetch_and_update_stock_price(ticker):
    """
    Fetch the latest stock price using yfinance and update the cache.
    Returns a Decimal price or None if unavailable.
    """
    try:
        stock = yf.Ticker(ticker)
        live_price = stock.info.get('regularMarketPrice')
        if live_price is None:
            return None

        live_price_decimal = Decimal(str(live_price))  # Convert to Decimal

        cache, created = StockPriceCache.objects.get_or_create(ticker=ticker)
        cache.last_price = live_price_decimal
        cache.save()
        return live_price_decimal
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
        return None


def update_all_portfolio_stocks(portfolio):
    """
    Update the prices for all stocks in a given portfolio.
    """
    for symbol, _ in portfolio.diversification.items():
        fetch_and_update_stock_price(symbol)
