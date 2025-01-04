from .http_api import Settings as PTSettings, login, update_config
from polars import DataFrame, col, from_epoch, Config
from jinja2 import Environment, FileSystemLoader
from .settings import BotSetting, settings
from urllib.request import urlopen
from dataclasses import dataclass
from joblib import Memory
from typing import Any
from math import log10
import json
import os

tmp_disk = Memory('./tmp/cache')
FOLDER = './conf'
TIMEFRAMES = list(map(int, '60 300 900 3600 14400 86400 604800'.split()))

@dataclass
class Strategy:
    pairs: str
    dca: str
    indicators: str

    def __repr__(self):
        return ("\n".join([ 
            'PAIRS', self.pairs, "\n", 
            'DCA', self.dca, "\n", 
            'INDICATORS', self.indicators, "\n" ]))

@tmp_disk.cache
def fetch_json(url: str) -> Any:
    print(f'FETCHING PREDICTIONS: {url}')
    # High time out as sometimes it might train
    with urlopen(url, timeout=900) as response:
        return json.loads(response.read().decode('utf-8'))

def nearest_timeframe(interval: int, muliplier: float) -> int:
    return min(TIMEFRAMES, key=lambda x: abs(x - (interval * muliplier * 1.5)))

def fetch_predictions(interval: int | None = 86400, url: str | None = None):
    assert None == (interval and url), 'Set interval or URL'
    url = url or f'{settings.predictions_api}/crypto/{interval}'
    # Filter out coins with single letter as they confuse PT as a strategy name
    return (DataFrame(fetch_json(url)['predictions']).filter(col('symbol').str.len_chars() > 1).with_columns(
        from_epoch(col('date'), time_unit='ms'),
        weighting=(col('price_prediction').abs() / col('price_prediction').abs().mean()).clip(upper_bound=2)))

def longs(table: DataFrame, threshold: float = 10) -> DataFrame:
    return table.filter(col('price_prediction') > threshold, col('entry_prediction') == 'GOOD')

def shorts(table: DataFrame, threshold: float = 10) -> DataFrame:
    return table.filter(col('price_prediction') < -threshold, col('entry_prediction') == 'BAD')

def prepare(table: DataFrame, settings: BotSetting) -> dict[str, Any]:
    long_bias = longs(table)['price_prediction'].sum()
    short_bias = shorts(table)['price_prediction'].sum()
    count_normalised = (100 * col('count') / col('count').sum()).round(2)
    entry_summary = table['entry_prediction'].value_counts().with_columns(count=count_normalised)
    return dict(
        coins=table.clone(),
        round=round, min=min, max=max,log10=log10,
        long_short_ratio=round(log10(abs(long_bias / short_bias)), 3), # >1 is Long bias, <1 is short bias
        entry_summary=dict(entry_summary.to_numpy().tolist()), # Frivolous way to to depend on numpy :-)
        nearest_timeframe=nearest_timeframe,
        interval=settings.interval,
        settings=settings,
        shorts=shorts,
        longs=longs)

def comment(lines: str):
    return "\n".join([ f'# {line}' for line in str(lines).splitlines() ])

def render_file(settings: BotSetting, category: str, table: DataFrame) -> str:
    env = Environment(loader=FileSystemLoader(f'{FOLDER}/{settings.template}'))
    env.filters['comment'] = comment
    env.filters['nearest_timeframe'] = nearest_timeframe
    with Config(tbl_cols=20, tbl_rows=200, float_precision=2, tbl_width_chars=256):
        template = env.get_template(f'{category}.properties')
        return template.render(prepare(table, settings))

def render(settings: BotSetting, table: DataFrame | None = None) -> Strategy:
    table = table or fetch_predictions(interval=settings.interval)
    return Strategy(**{
        category: render_file(settings, category, table)
        for category in 'pairs dca indicators'.split() })

if '__main__' == __name__:
    # upload = str(os.environ.get('UPLOAD')).upper() == 'YES'
    for info in settings.configs:
        print(f'CONFIG :: {info.name}')
        strategy = render(info)
        print(str(strategy))
        if info.upload:
            print(f'Uploading to {info.host} as {info.label}')
            bot = PTSettings(host=info.host, password=info.password, name=info.name)
            login(bot) and update_config(bot, info.label, strategy.pairs, strategy.dca, strategy.indicators)