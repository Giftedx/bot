# Universal Economy System

## Overview

The Universal Economy System provides a unified virtual currency and economy management system that integrates with all game systems (OSRS, Pokemon, etc.). The system handles currency transactions, item trading, rewards, and economic balancing across different game integrations.

## System Architecture

```mermaid
graph TB
    subgraph Economy["Economy Core"]
        CM[Currency Manager]
        TM[Transaction Manager]
        MM[Market Manager]
        VM[Value Manager]
    end

    subgraph Integration["Game Integration"]
        OSRS[OSRS Economy]
        PKM[Pokemon Economy]
        PET[Pet Economy]
        REW[Reward System]
    end

    subgraph Services["Economy Services"]
        EX[Exchange Service]
        TR[Trading Service]
        ST[Store Service]
        AH[Auction House]
    end

    subgraph Data["Data Layer"]
        DB[(Database)]
        Cache[(Redis Cache)]
        MQ[Message Queue]
    end

    CM --> TM
    TM --> MM
    MM --> VM
    
    OSRS --> CM
    PKM --> CM
    PET --> CM
    REW --> CM
    
    EX --> TM
    TR --> TM
    ST --> MM
    AH --> MM
    
    CM --> DB
    TM --> Cache
    MM --> MQ
```

## Features

### 1. Currency Management
- Multi-currency support
- Exchange rates
- Balance tracking
- Transaction history

### 2. Transaction System
- Secure transfers
- Cross-game transactions
- Batch processing
- Rollback support

### 3. Market System
- Item trading
- Price tracking
- Market analysis
- Auction house

### 4. Value System
- Dynamic pricing
- Item valuation
- Economic indicators
- Inflation control

## Configuration

### Environment Variables
```env
ECONOMY_DB_URL=postgres://user:pass@host:5432/economy
ECONOMY_CACHE_TTL=3600
ECONOMY_RATE_LIMIT=100
ECONOMY_DEFAULT_CURRENCY=gold
```

### Economy Settings
```yaml
economy_settings:
  currencies:
    - name: "gold"
      symbol: "G"
      decimals: 0
    - name: "credits"
      symbol: "CR"
      decimals: 2
  exchange_rates:
    gold_to_credits: 0.01
    credits_to_gold: 100
  transaction_limits:
    min_amount: 1
    max_amount: 1000000000
    daily_limit: 100000000
```

## Currency Management

### 1. Balance Operations
```python
async def manage_balance(user_id: str, currency: str, amount: float, operation: str) -> bool:
    """Manage user balance operations."""
    try:
        # Get current balance
        balance = await get_balance(user_id, currency)
        
        # Validate operation
        if not validate_operation(balance, amount, operation):
            raise EconomyError("Invalid operation")
            
        # Process operation
        match operation:
            case "add":
                new_balance = balance + amount
            case "subtract":
                new_balance = balance - amount
            case "set":
                new_balance = amount
                
        # Update balance
        await update_balance(user_id, currency, new_balance)
        
        # Record transaction
        await record_transaction(user_id, currency, amount, operation)
        
        return True
        
    except EconomyError as e:
        await handle_economy_error(e)
        return False
```

### 2. Exchange System
```python
async def exchange_currency(
    user_id: str,
    from_currency: str,
    to_currency: str,
    amount: float
) -> float:
    """Exchange between currencies."""
    # Get exchange rate
    rate = await get_exchange_rate(from_currency, to_currency)
    
    # Calculate conversion
    converted_amount = amount * rate
    
    # Process exchange
    async with transaction():
        # Deduct from currency
        await subtract_balance(user_id, from_currency, amount)
        
        # Add to currency
        await add_balance(user_id, to_currency, converted_amount)
        
        # Record exchange
        await record_exchange(
            user_id, from_currency, to_currency,
            amount, converted_amount
        )
        
    return converted_amount
```

## Transaction System

### 1. Transfer Processing
```python
async def process_transfer(
    from_user: str,
    to_user: str,
    currency: str,
    amount: float
) -> bool:
    """Process currency transfer between users."""
    async with transaction():
        # Verify sender balance
        if not await verify_balance(from_user, currency, amount):
            raise InsufficientFundsError()
            
        # Process transfer
        await subtract_balance(from_user, currency, amount)
        await add_balance(to_user, currency, amount)
        
        # Record transfer
        await record_transfer(from_user, to_user, currency, amount)
        
        # Update statistics
        await update_transfer_stats(currency, amount)
        
        return True
```

### 2. Batch Processing
```python
async def process_batch_transactions(transactions: List[Transaction]) -> BatchResult:
    """Process multiple transactions in batch."""
    results = BatchResult()
    
    async with transaction():
        for tx in transactions:
            try:
                # Process individual transaction
                success = await process_transaction(tx)
                
                # Record result
                if success:
                    results.successful.append(tx)
                else:
                    results.failed.append(tx)
                    
            except EconomyError as e:
                results.errors.append((tx, e))
                
    return results
```

## Market System

### 1. Item Trading
```python
async def create_trade(
    seller_id: str,
    item_id: str,
    price: float,
    currency: str
) -> Trade:
    """Create a new trade listing."""
    # Verify item ownership
    if not await verify_ownership(seller_id, item_id):
        raise OwnershipError()
        
    # Create trade listing
    trade = Trade(
        seller_id=seller_id,
        item_id=item_id,
        price=price,
        currency=currency
    )
    
    # Lock item
    await lock_item(item_id)
    
    # Save trade
    await save_trade(trade)
    
    return trade
```

### 2. Price Tracking
```python
async def track_prices(item_id: str) -> PriceHistory:
    """Track item price history."""
    # Get recent trades
    trades = await get_item_trades(item_id)
    
    # Calculate statistics
    stats = calculate_price_stats(trades)
    
    # Update price history
    await update_price_history(item_id, stats)
    
    # Check price alerts
    await check_price_alerts(item_id, stats)
    
    return stats
```

## Value System

### 1. Dynamic Pricing
```python
async def calculate_dynamic_price(item_id: str) -> float:
    """Calculate dynamic item price."""
    # Get market data
    market_data = await get_market_data(item_id)
    
    # Get supply/demand
    supply = await get_item_supply(item_id)
    demand = await get_item_demand(item_id)
    
    # Calculate base price
    base_price = calculate_base_price(market_data)
    
    # Apply modifiers
    price = apply_price_modifiers(
        base_price,
        supply=supply,
        demand=demand,
        market_trend=market_data.trend
    )
    
    return price
```

### 2. Economic Indicators
```python
async def calculate_economic_health() -> EconomicStats:
    """Calculate economic health indicators."""
    # Get transaction data
    transactions = await get_recent_transactions()
    
    # Calculate metrics
    velocity = calculate_money_velocity(transactions)
    inflation = calculate_inflation_rate(transactions)
    activity = calculate_market_activity(transactions)
    
    # Update indicators
    await update_economic_indicators(
        velocity=velocity,
        inflation=inflation,
        activity=activity
    )
    
    return EconomicStats(
        velocity=velocity,
        inflation=inflation,
        activity=activity
    )
```

## Integration Points

### Input Systems
- Game rewards
- Trading systems
- Store purchases
- User actions

### Output Systems
- Balance updates
- Market updates
- Economic indicators
- Transaction records

## Error Handling

### Economy Errors
```python
class EconomyError(Exception):
    """Base class for economy errors"""
    pass

class InsufficientFundsError(EconomyError):
    """Insufficient funds for operation"""
    pass

class TransactionError(EconomyError):
    """Transaction processing error"""
    pass

class MarketError(EconomyError):
    """Market operation error"""
    pass
```

### Error Recovery
1. Transaction rollback
2. Balance restoration
3. Market correction
4. State reconciliation

## Performance

### Optimization
- Transaction batching
- Cache management
- Asynchronous processing
- Load distribution

### Metrics
- Transaction throughput
- Response latency
- Cache hit ratio
- Error rate

## Testing

### Unit Tests
```python
def test_currency_exchange():
    result = exchange_currency(
        user_id="user1",
        from_currency="gold",
        to_currency="credits",
        amount=1000
    )
    
    assert result.success
    assert result.converted_amount == 10  # 1000 gold = 10 credits
```

### Integration Tests
```python
async def test_market_system():
    trade = await create_trade(
        seller_id="user1",
        item_id="item1",
        price=1000,
        currency="gold"
    )
    
    assert trade.status == "active"
    assert await verify_item_locked("item1")
```

## Related Documentation
- [OSRS Economy](../osrs/economy.md)
- [Pokemon Economy](../pokemon/economy.md)
- [Trading System](../trading/README.md)
- [API Documentation](../api/economy/README.md)

## Changelog

### v1.0.0 - 2024-02-16
- Initial economy system implementation
- Multi-currency support
- Transaction system
- Market system
- Value tracking

_Last Updated: February 2024_ 