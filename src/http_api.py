'''
This provides a raw JSON interface to Profit Trailer 2.x
It assumes your PT instance is on HTTPS and not HTTP

bot = Settings(host='paper1.profittrailer.com', password='Password123', name='Wick Hunter')
'''
from dataclasses import dataclass
from  requests import Session
import json

@dataclass
class Settings:
    host: str
    password: str
    name: str
    session: Session = Session()
    scheme: str = 'https://'

def update_config(bot: Settings, label, pairs, dca, indicators):
    for category, data in { 'PAIRS': pairs, 'DCA': dca, 'INDICATORS': indicators }.items():
        url = f'{bot.scheme}{bot.host}/settings/save?fileName={category}&configName={label}'
        bot.session.post(url, data=data)

def order(bot: Settings, pair, action, portion = 100, category = 'IOC'):
    url = f'{bot.scheme}{bot.host}/action/{action}?currencyPair={pair}&executionType={category}&portion={portion}'
    return bot.session.post(url)

def sell(bot: Settings, pair, portion = 100, category = 'IOC'):
  return order(bot, pair, 'sell', portion, category)

def buy(bot: Settings, pair, portion = 100, category = 'IOC'):
    return order(bot, pair, 'buy', portion, category)

def get_dca_pairs(bot: Settings):
    url = f'{bot.scheme}{bot.host}/api/v2/data/dca'
    # buyProfit, profit, currentPrice, currency, leverage, firstBoughtDate, avgPrice, totalCost, currentValue
    return json.loads(bot.session.get(url).text)

def get_pairs(bot: Settings):
    url = f'{bot.scheme}{bot.host}/api/v2/data/pairs'
    return json.loads(bot.session.get(url).text)

def login(bot: Settings):
    url = f'{bot.scheme}{bot.host}/login'
    return bot.session.post(url, data = { 'password': bot.password })

def sell_profitable(bot: Settings):
    for item in get_dca_pairs(bot).items():
        if item.profit > 0:
            sell(bot, item['market'], 100, 'MARKET')

def switch_config(bot: Settings, label: str):
    url = f'{bot.scheme}{bot.host}/settings/config/switch?&configName={label}'
    return bot.session.post(url)