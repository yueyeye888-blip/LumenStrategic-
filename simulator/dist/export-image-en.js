/* Render from the same calculator as the live table; no external image service. */
(function(){
'use strict';
function renderResultImage(amount,target,rate){
 const x=calculate(amount,target,rate),c=document.createElement('canvas');
 c.width=1080;c.height=6000;const g=c.getContext('2d');if(!g)throw Error('Canvas unavailable');
 const green='#17664f',ink='#172b26',muted='#74847e';
 const money=n=>(n<0?'−':'')+'S$'+Math.abs(n).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
 const signed=n=>(n>0?'+':'')+money(n),pct=n=>(n>0?'+':'')+n.toFixed(2)+'%';
 function text(t,a,b,size=25,color=ink,align='left',weight=400){g.font=weight+' '+size+'px -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif';g.fillStyle=color;g.textAlign=align;g.textBaseline='top';g.fillText(t,a,b);}
 function box(a,b,w,h,color,r=20){g.fillStyle=color;g.beginPath();g.roundRect(a,b,w,h,r);g.fill();}
 function rule(y){g.fillStyle='#e4ebe6';g.fillRect(76,y,928,2);}
 function wrap(t,a,y,width,size=21,color=muted){let line='';for(const ch of t){g.font=size+'px -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif';if(g.measureText(line+ch).width>width){text(line,a,y,size,color);y+=size*1.6;line=ch;}else line+=ch;}if(line){text(line,a,y,size,color);y+=size*1.6;}return y;}
 function pair(y,label,a,b,sub=false){if(sub)box(64,y-10,952,58,'#f4f8f5',8);text(label,80,y,sub?23:25,sub?muted:ink);text(a,690,y,25,ink,'right');text(b,998,y,25,ink,'right');}
 box(0,0,1080,6000,'#f3f6f4',0);box(36,36,1008,5928,'white',28);
 g.textBaseline='top';g.font='52px Georgia,serif';g.fillStyle=green;g.fillText('LUMEN',76,70);text('STRATEGIC CAPITAL',78,140,19,muted);
 box(800,78,204,44,'#eef4f0',22);text('Single-Year Scenario',902,88,20,green,'center');g.fillStyle='#ac9564';g.fillRect(76,189,928,3);
 text('Investment Return Scenario Report',76,222,42);text('Current scenario · Currency: Singapore dollars (S$)',76,287,23,muted);
 box(64,350,952,296,'#f3f7f5');text('Scenario Parameters',86,372,27,green);
 [['Senior Initial Subscription',money(amount)],['Agreed Return Allocation Basis / Carry Hurdle',target+'%'],['Fund Annual Net Portfolio Return',(rate>0?'+':'')+rate+'%']].forEach(([k,v],i)=>{text(k,86,426+i*61,25,muted);text(v,988,426+i*61,28,green,'right',700);});
 text('Senior / Subordinated Returns',76,684,30);
 [['Senior Return',x.an,64],['Subordinated Return',x.bn,550]].forEach(([label,value,left])=>{const color=value<0?'#b84d4d':green;box(left,743,466,222,'#eef5f0');text(label,left+22,764,26,green);text(signed(value),left+22,816,32,color,'left',700);text('Annualised Return  '+pct(value/x.P*100),left+22,881,26,color);});
 text('Annualised returns use net invested capital after the upfront fee as the denominator; Carry is deducted.',76,985,21,muted);
 text('Capital and Allocation Breakdown',76,1044,30);pair(1110,'Item','Senior','Subordinated');rule(1156);
 const rows=[['Net Invested Capital',money(x.P),money(x.P)],['Pre-Carry Profit / Loss',signed(x.a),signed(x.b)]];
 if(x.gain<0)rows.push(['  Net Loss',signed(x.a),signed(x.b),true]);
 else rows.push(['  Base Return',money(x.aBase),money(x.bBase),true],['  Excess Profit',money(x.aExcess),money(x.bExcess),true]);
 rows.push(['Carry Rate',rate>target?'20%':'0%',(x.bfr*100)+'%'],['Accrued Carry',money(x.af),money(x.bf)],['Carry Reversal',money(x.refund),money(0)],['Actual Carry',money(x.af-x.refund),money(x.bf)],['Illustrative Closing Capital',money(x.P+x.an),money(x.P+x.bn)]);
 let y=1180;rows.forEach(row=>{pair(y,...row);if(!row[3])rule(y+44);y+=60;});
 y+=12;y=wrap('Total Portfolio Capital '+money(x.T)+' · Portfolio Profit / Loss '+signed(x.gain),80,y,920,23,green);
 y=wrap('Upfront Management Fee '+money(amount*.02)+', deducted from the Senior subscription.',80,y+12,920,22);
 y=wrap(document.getElementById('calculatorNotice').textContent,80,y+32,920,22);
 const out=document.createElement('canvas');out.width=1080;out.height=y+80;out.getContext('2d').drawImage(c,0,0);
 return out;
}
window.renderResultImage=renderResultImage;
let imageURL=null;
const dialog=document.getElementById('imageDialog'),button=document.getElementById('downloadImage'),status=document.getElementById('imageStatus');
button.onclick=async()=>{
 button.disabled=true;button.textContent='Generating image…';status.textContent='';
 try{
  const amount=+document.getElementById('amount').value,target=DISTRIBUTION_BENCHMARK,rate=+document.getElementById('rate').value;
  const canvas=renderResultImage(amount,target,rate);
  const blob=await new Promise((resolve,reject)=>canvas.toBlob(b=>b?resolve(b):reject(Error('PNG generation failed')),'image/png'));
  if(imageURL)URL.revokeObjectURL(imageURL);imageURL=URL.createObjectURL(blob);
  const link=document.getElementById('saveImage');link.href=imageURL;link.download='LUMEN_'+amount+'_Basis'+target+'_FundReturn'+rate+'.png';
  document.getElementById('resultImage').src=imageURL;
  dialog.showModal();link.click();status.textContent='Image ready. If the download does not start, save it from the preview or press and hold the image.';
 }catch(e){status.textContent='Image generation failed. Please retry or copy the results.';}
 finally{button.disabled=false;button.textContent='Download Results Image';}
};
document.getElementById('closeImage').onclick=()=>dialog.close();
})();
