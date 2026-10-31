const assert=require('node:assert/strict');const {calculate}=require('./dist/calculator.js');
const near=(a,b)=>assert.ok(Math.abs(a-b)<1e-7,`${a} != ${b}`);
// Independently expected outcomes, gross subscription 200,000, target 8%.
const expected=[[-100,-196000,-196000,0,0],[-50,0,-196000,0,0],[0,0,0,0,0],[8,15680,15680,0,0],[25,28537.6,49862.4,7134.4,12465.6],[50,52057.6,91649.6,13014.4,39278.4],[100,99097.6,187689.6,24774.4,80438.4]];
const rows=[];
for(const [r,a,b,ac,bc] of expected){const x=calculate(200000,8,r);near(x.an,a);near(x.bn,b);near(x.af-x.refund,ac);near(x.bf,bc);rows.push({rate:r,LP:x.an,Sponsor:x.bn,LPcarry:ac,SponsorCarry:bc,LPend:x.P+x.an,SponsorEnd:x.P+x.bn});}
// Published examples A and B use 200,000 net capital.
let x=calculate(200000/.98,8,30);near(x.a,42400);near(x.b,77600);near(x.an,33920);near(x.bn,62080);
x=calculate(200000/.98,8,6);near(x.an,16000);near(x.bn,8000);near(x.af+x.bf,0);
// Fixed benchmark: conservation, first loss, Carry boundaries and breakdown.
let checks=0;
for(const amt of [200000,1000000,2000000])for(let r=-100;r<=100;r++){
 x=calculate(amt,8,r);near(x.a+x.b,x.gain);near(x.P+x.an+x.P+x.bn+x.af-x.refund+x.bf,x.T+x.gain);
 near(x.aBase+x.aExcess,Math.max(0,x.a));near(x.bBase+x.bExcess,Math.max(0,x.b));
 assert.ok(x.P+x.an>=-1e-7&&x.P+x.bn>=-1e-7);
 if(r<=8)near(x.af+x.bf,0);
 if(r>8)assert.ok(x.an>=x.P*.08-1e-7);
 if(r>=-50&&r<=0)near(x.an,0);
 checks++;
}
for(const r of [7,8])near(calculate(200000,8,r).af+calculate(200000,8,r).bf,0);
x=calculate(200000,8,9);assert.ok(x.af>0&&x.bf>0);near(x.an,15680);assert.ok(x.refund>0);
near(calculate(200000,8,45).bfr,.2);near(calculate(200000,8,46).bfr,.3);
for(const target of [7,9,10,13,20,25])assert.throws(()=>calculate(200000,target,30),RangeError);
const html=require('node:fs').readFileSync('./dist/index.html','utf8');assert.ok(!html.includes('id="target"'));assert.ok(html.includes('约定分配基准'));assert.ok(!html.includes('<details class="note"'));assert.ok(html.includes('一切解释权归Lumen Strategic Capital所有，详见产品文档。'));
console.log(JSON.stringify({checks,benchmark:'Fixed at 8%',examples:'A/B passed',scenarios:rows},null,2));
