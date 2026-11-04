"""Pandas indicators feeding the causal reference ledger; no order endpoint."""
import argparse,json
import pandas as pd
from backtest import validate,simulate
p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--as-of',required=True,type=float);a=p.parse_args()
with open(a.input) as f: rows=json.load(f)
bars=validate(rows,a.as_of);frame=pd.DataFrame(bars)
frame['sma_fast']=frame['c'].rolling(10,min_periods=10).mean()
frame['sma_slow']=frame['c'].rolling(30,min_periods=30).mean()
frame['cross_up']=(frame.sma_fast>frame.sma_slow)&(frame.sma_fast.shift(1)<=frame.sma_slow.shift(1))
frame['cross_down']=(frame.sma_fast<frame.sma_slow)&(frame.sma_fast.shift(1)>=frame.sma_slow.shift(1))
ledger=simulate(bars)
expected=[];holding=False
for i in range(1,len(frame)):
    row=frame.iloc[i-1]
    if row.cross_up and not holding:expected.append(('BUY',int(frame.iloc[i].t)));holding=True
    elif row.cross_down and holding:expected.append(('SELL',int(frame.iloc[i].t)));holding=False
assert expected==[(x['side'],int(x['fillTime'])) for x in ledger['ledger']]
print(json.dumps({'rows':len(frame),'pandas_signal_parity':True,'ledger':ledger},indent=2))
