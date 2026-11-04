"""Reference paper ledger. No keys, account endpoints or order-routing code."""
import argparse, csv, json, math, urllib.request

def validate(rows, now):
    if not isinstance(rows,list) or not 35 <= len(rows) <= 1000:
        raise ValueError('Expected 35 to 1000 source candles')
    by_time={}
    for r in rows:
        if len(r)<6 or not all(isinstance(x,(int,float)) and math.isfinite(x) for x in r[:6]):
            raise ValueError('Invalid candle values')
        t,lo,hi,o,c,v=r[:6]
        if not float(t).is_integer() or t<0 or lo<=0 or hi<lo or not lo<=o<=hi or not lo<=c<=hi or v<0:
            raise ValueError('Invalid candle bounds')
        record={'t':t,'l':lo,'h':hi,'o':o,'c':c,'v':v}
        if t in by_time and by_time[t]!=record: raise ValueError('Conflicting duplicate candle')
        if t+3600<=now: by_time[t]=record
    bars=[by_time[t] for t in sorted(by_time)][-300:]
    if len(bars)<35 or any(b['t']-a['t']!=3600 for a,b in zip(bars,bars[1:])):
        raise ValueError('Not enough closed contiguous hourly candles')
    return bars

def simulate(bars,fast=10,slow=30,fee_bps=10,slip_bps=5):
    if not 2<=fast<slow<=100 or not all(math.isfinite(x) and 0<=x<=100 for x in [fee_bps,slip_bps]):
        raise ValueError('Invalid strategy parameters')
    fee,slip=fee_bps/10000,slip_bps/10000
    cash,qty,high,drawdown=10000.,0.,10000.,0.
    pending=None;ledger=[];equity=[];fs=[];ss=[]
    for i,b in enumerate(bars):
        if pending and pending['side']=='BUY' and qty==0:
            price=b['o']*(1+slip);qty=cash/(price*(1+fee));cost=qty*price;commission=cost*fee
            cash-=cost+commission;ledger.append(dict(side='BUY',signalTime=pending['t'],fillTime=b['t'],price=price,qty=qty,fee=commission))
        if pending and pending['side']=='SELL' and qty:
            price=b['o']*(1-slip);value=qty*price;commission=value*fee;cash+=value-commission
            ledger.append(dict(side='SELL',signalTime=pending['t'],fillTime=b['t'],price=price,qty=qty,fee=commission));qty=0.
        pending=None
        average=lambda n:sum(x['c'] for x in bars[i+1-n:i+1])/n if i+1>=n else None
        f,s=average(fast),average(slow);fs.append(f);ss.append(s)
        if i>=slow:
            if fs[i-1]<=ss[i-1] and f>s:pending=dict(side='BUY',t=b['t'])
            elif fs[i-1]>=ss[i-1] and f<s:pending=dict(side='SELL',t=b['t'])
        value=cash+qty*b['c'];high=max(high,value);drawdown=max(drawdown,(high-value)/high);equity.append(value)
    liquidation=cash+qty*bars[-1]['c']*(1-slip)*(1-fee)
    return dict(cash=cash,qty=qty,equity=equity,ledger=ledger,liquidation=liquidation,returnPct=(liquidation/10000-1)*100,drawdownPct=drawdown*100)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--as-of',type=float,required=True);p.add_argument('--fast',type=int,default=10);p.add_argument('--slow',type=int,default=30);args=p.parse_args()
    with open(args.input) as f:rows=json.load(f)
    print(json.dumps(simulate(validate(rows,args.as_of),args.fast,args.slow),indent=2))
