
from __future__ import annotations
from dataclasses import dataclass,field
from typing import Literal,TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from datetime import date

EPS = 1e-6

@dataclass
class Action:
    direction: Literal["long", "short"]
    side: Literal["buy", "sell"]
    ticker: str
    price: float
    volume: float
    date: date
    short_start_date: date|None = None
    short_value: float|None = None

    def __post_init__(self):
        if self.direction == "short" and self.side == "buy":
            assert self.short_start_date is not None, "Short start date is required"
            assert self.short_value is not None, "Short value is required"

@dataclass
class Security:
    ticker: str
    volume: float
    price: float
    market_price: float

    def __post_init__(self):
        assert self.volume >= 0.0, "Volume must be greater than or equal to 0"
        assert self.price >= 0.0, "Price must be greater than or equal to 0"
    
    def __add__(self, other: Security) -> Security:
        volume = self.volume + other.volume
        price = (self.price * self.volume + other.price * other.volume) / volume
        return Security(
            ticker=self.ticker,
            volume=volume,
            price=price,
            market_price=self.market_price
        )
    
    def __sub__(self, other: Security) -> Security:
        volume = self.volume - other.volume
        if volume >= 0.0 and volume < EPS:
            volume = 0.0
            price = 0.0
        elif volume > EPS:
            price = self.price
        else:
            raise ValueError("Volume must be greater than or equal to 0")
        return Security(
            ticker=self.ticker,
            volume=volume,
            price=price,
            market_price=other.market_price
        )


@dataclass
class Liability:
    ticker: str
    volume: float
    price: float
    market_price: float
    start_date: date
    __start_timestamp: int = field(init=False)

    def __post_init__(self):
        assert self.volume >= 0.0, "Volume must be greater than or equal to 0"
        assert self.price >= 0.0, "Price must be greater than or equal to 0"
        start_date = datetime.combine(self.start_date, datetime.min.time())
        self.__start_timestamp = int(start_date.timestamp())

    def __add__(self, other: Liability) -> Liability:
        volume = self.volume + other.volume
        assert volume > EPS, "Volume must be greater than 0"
        price = (self.price * self.volume + other.price * other.volume) / volume
        avg_timestamp = (
            self.volume * self.__start_timestamp + other.volume * other.__start_timestamp) / volume
        start_date = datetime.fromtimestamp(avg_timestamp).date()
        return Liability(
            ticker=self.ticker,
            volume=volume,
            price=price,
            market_price=self.market_price,
            start_date=start_date
        )
    
    def __sub__(self, other: Liability) -> Liability:
        volume = self.volume - other.volume
        if volume >= 0.0 and volume < EPS:
            volume = 0.0
            price = 0.0
        elif volume > EPS:
            price = self.price
        else:
            raise ValueError("Volume must be greater than or equal to 0")
        return Liability(
            ticker=self.ticker,
            volume=volume,
            price=price,
            market_price=other.market_price,
            start_date=self.start_date
        )

@dataclass
class Trade:
    """
    when put in price don't take slippage into account
    """
    ticker: str
    direction: Literal["long", "short"]
    side: Literal["buy", "sell"]
    volume: float
    price: float
    fee: float
    slippage: float
    date: date
    target:Security|Liability

    def __post_init__(self):
        assert self.volume >= 0.0, "Volume must be greater than or equal to 0"
        assert self.price >= 0.0, "Price must be greater than or equal to 0"
        assert self.fee >= 0.0, "Fee must be greater than or equal to 0"
        assert self.slippage >= 0.0, "Slippage must be greater than or equal to 0"
        price = self.price
        if self.side == "buy":
            price += self.slippage
        elif self.side == "sell":
            price -= self.slippage
        self.__setattr__("price", price)

    @property
    def transaction_fee(self) -> float:
        return self.fee

@dataclass
class Account:
    cash: float
    securities: dict[str, Security] = field(default_factory=dict)
    liabilities: dict[str, Liability] = field(default_factory=dict)
    holding_history: list[dict] = field(default_factory=list)
    value_history: list[dict] = field(default_factory=list)
    long_fee_cum: float = 0.0
    short_fee_cum: float = 0.0
    initial_cash: float = field(init=False)

    def __post_init__(self):
        assert self.cash >= 1.0, "Cash must be greater than or equal to 1"
        self.initial_cash = self.cash
    
    @property
    def total_value(self) -> float:
        return self.cash - self.liability_value + self.securities_value
    
    @property
    def liability_value(self) -> float:
        value = 0.0
        for liability in self.liabilities.values():
            value += liability.volume * liability.market_price
        return value

    @property
    def securities_value(self) -> float:
        value = 0.0
        for security in self.securities.values():
            value += security.volume * security.market_price
        return value
    
    def _clean_up(self):
        remove_list = []
        for ticker, security in self.securities.items():
            if security.volume < EPS:
                remove_list.append(ticker)
        for ticker in remove_list:
            del self.securities[ticker]
        remove_list = []
        for ticker, liability in self.liabilities.items():
            if liability.volume < EPS:
                remove_list.append(ticker)
        for ticker in remove_list:
            del self.liabilities[ticker]

    def on_trade(self, trade: Trade):
        ticker = trade.ticker
        target = trade.target
        trade_flag = self.cash >= 0

        if trade.direction == "long":
            assert isinstance(target, Security), "Target must be a Security"
            if trade.side == "buy" and trade_flag:
                if self.cash < (trade.price * trade.volume + trade.fee):
                    print("cash is not enough trade is not executed")
                    return
                self.cash -= (trade.price * trade.volume + trade.fee)
                self.long_fee_cum += trade.fee
                if ticker not in self.securities:
                    self.securities[ticker] = target
                else:
                    self.securities[ticker] += target
            elif trade.side == "sell":
                
                # if ticker not in self.securities:
                #     print("warning: selling security not in stock")
                #     return
            
                assert ticker in self.securities, "Security must be in the account"
                self.cash += trade.price * trade.volume - trade.fee
                self.long_fee_cum += trade.fee
                self.securities[ticker] -= target
        elif trade.direction == "short":
            assert isinstance(target, Liability), "Target must be a Liability"
            if trade.side == "sell" and trade_flag:
                self.cash += (trade.price * trade.volume + trade.fee)
                self.short_fee_cum += trade.fee
                if ticker not in self.liabilities:
                    self.liabilities[ticker] = target
                else:
                    self.liabilities[ticker] += target
            elif trade.side == "buy":
                if self.cash < (trade.price * trade.volume + trade.fee):
                    print("cash is not enough you are bankrupt and in debt")
                
                # if ticker not in self.securities:
                #     print("warning: Liability not in stock")
                #     return
                assert ticker in self.liabilities, "Liability must be in the account"
                self.cash -= (trade.price * trade.volume + trade.fee)
                self.short_fee_cum += trade.fee
                self.liabilities[ticker] -= target
        self._clean_up()
    
    def on_trades(self, trades: list[Trade]):
        for trade in trades:
            self.on_trade(trade)
    
    def snapshot(self, date: date):
        value = {
            "date": date,
            "cash": self.cash,
            "liability_value": - self.liability_value,
            "securities_value": self.securities_value,
            "total_value": self.total_value,
            "long_fee_cum": self.long_fee_cum,
            "short_fee_cum": self.short_fee_cum,
            "long_fee_rate_cum": self.long_fee_cum / self.initial_cash,
            "short_fee_rate_cum": self.short_fee_cum / self.initial_cash,
        }

        holding = []
        for ticker, security in self.securities.items():
            holding.append({
                "date": date,
                "direction": "long",
                "ticker": ticker,
                "volume": security.volume,
                "price": security.price,
                "market_price": security.market_price
            })
        for ticker, liability in self.liabilities.items():
            holding.append({
                "date": date,
                "direction": "short",
                "ticker": ticker,
                "volume": liability.volume,
                "price": liability.price,
                "market_price": liability.market_price
            })
        self.holding_history.extend(holding)
        self.value_history.append(value)
