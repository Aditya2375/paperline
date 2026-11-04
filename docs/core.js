export function validate(rows,now=Date.now()/1000){
 if(!Array.isArray(rows)||rows.length<35||rows.length>1000)throw Error('Expected 35 to 1000 source candles.');
 const map=new Map();for(const r of rows){if(!Array.isArray(r)||r.length<6||!r.slice(0,6).every(Number.isFinite))throw Error('Invalid candle values.');const[t,l,h,o,c,v]=r;if(!Number.isInteger(t)||t<0||l<=0||h<l||o<l||o>h||c<l||c>h||v<0)throw Error('Invalid candle bounds.');if(map.has(t)&&JSON.stringify(map.get(t))!==JSON.stringify({t,l,h,o,c,v}))throw Error('Conflicting duplicate candle.');if(t+3600<=now)map.set(t,{t,l,h,o,c,v});}
 const bars=[...map.values()].sort((a,b)=>a.t-b.t).slice(-300);if(bars.length<35)throw Error('Not enough closed hourly candles.');for(let i=1;i<bars.length;i++)if(bars[i].t-bars[i-1].t!==3600)throw Error('Hourly candles contain a gap. No trades simulated.');return bars;
}
export function simulate(bars,fast=10,slow=30,feeBps=10,slipBps=5){
 if(!Number.isInteger(fast)||!Number.isInteger(slow)||fast<2||slow<=fast||slow>100||![feeBps,slipBps].every(Number.isFinite)||feeBps<0||feeBps>100||slipBps<0||slipBps>100)throw Error('Invalid strategy parameters.');
 const fee=feeBps/10000,slip=slipBps/10000,initial=10000,ledger=[],equity=[],smaFast=[],smaSlow=[];let cash=initial,qty=0,pending=null,high=initial,drawdown=0,lastSignal=null,exposure=0;
 for(let i=0;i<bars.length;i++){
 const b=bars[i];if(pending&&pending.side==='BUY'&&!qty){const price=b.o*(1+slip),size=cash/(price*(1+fee)),cost=size*price,commission=cost*fee;cash-=cost+commission;qty=size;ledger.push({side:'BUY',signalTime:pending.t,fillTime:b.t,price,qty:size,fee:commission});}
 if(pending&&pending.side==='SELL'&&qty){const price=b.o*(1-slip),value=qty*price,commission=value*fee;cash+=value-commission;ledger.push({side:'SELL',signalTime:pending.t,fillTime:b.t,price,qty,fee:commission});qty=0;}pending=null;
 const average=n=>i+1>=n?bars.slice(i+1-n,i+1).reduce((s,x)=>s+x.c,0)/n:null;
 const f=average(fast),s=average(slow);smaFast.push(f);smaSlow.push(s);
 if(i>=slow){const oldF=smaFast[i-1],oldS=smaSlow[i-1];if(oldF<=oldS&&f>s){pending={side:'BUY',t:b.t};lastSignal=pending;}else if(oldF>=oldS&&f<s){pending={side:'SELL',t:b.t};lastSignal=pending;}}
 const value=cash+qty*b.c;high=Math.max(high,value);drawdown=Math.max(drawdown,(high-value)/high);equity.push(value);if(qty)exposure++;
 }
 const last=bars.at(-1),exitValue=qty*last.c*(1-slip)*(1-fee),liquidation=cash+exitValue;
 return{initial,cash,qty,equity,ledger,smaFast,smaSlow,lastSignal,pending,markEquity:equity.at(-1),liquidation,returnPct:(liquidation/initial-1)*100,drawdownPct:drawdown*100,exposurePct:exposure/bars.length*100,fees:ledger.reduce((s,x)=>s+x.fee,0)};
}
