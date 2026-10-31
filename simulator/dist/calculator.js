// Agreed distribution benchmark and Carry hurdle fixed at 8%.
const DISTRIBUTION_BENCHMARK=8;
function calculate(amount, target, rate) {
  if (![amount,target,rate].every(Number.isFinite) || amount<200000 || amount>2000000 || target!==DISTRIBUTION_BENCHMARK || rate< -100 || rate>100) throw new RangeError('Parameters outside supported scope');
  const P=amount*.98,T=2*P,gain=T*rate/100,base=P*target/100;
  let a=0,b=0;
  if(gain>=0){a=gain>=2*base?base+(gain-2*base)*.3:Math.min(gain,base);b=gain-a;}
  else {b=Math.max(-P,gain);a=gain-b;}
  const af=rate>target?Math.max(0,a)*.2:0;
  // Compare amounts directly to avoid threshold division rounding.
  const bfr=rate>target?(b>=P*.6?.3:.2):0,bf=rate>target?Math.max(0,b)*bfr:0;
  const refund=rate>target?Math.min(af,Math.max(0,base-(a-af))):0;
  const an=a-af+refund,bn=b-bf;
  const aBase=Math.min(Math.max(0,a),base),bBase=Math.min(Math.max(0,b),base);
  const aExcess=Math.max(0,a-aBase),bExcess=Math.max(0,b-bBase);
  return {P,T,gain,a,b,af,bfr,bf,refund,an,bn,aBase,bBase,aExcess,bExcess};
}
if(typeof module!=='undefined') module.exports={calculate,DISTRIBUTION_BENCHMARK};
