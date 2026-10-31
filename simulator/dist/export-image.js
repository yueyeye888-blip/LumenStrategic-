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
 box(800,78,204,44,'#eef4f0',22);text('单年度情景演示',902,88,20,green,'center');g.fillStyle='#ac9564';g.fillRect(76,189,928,3);
 text('投资收益模拟报告',76,222,42);text('按当前参数生成 · 金额单位：新加坡元（S$）',76,287,23,muted);
 box(64,350,952,296,'#f3f7f5');text('本次模拟参数',86,372,27,green);
 [['优先方初始认购金额',money(amount)],['约定分配基准 / Carry 门槛',target+'%'],['基金年度净收益率',(rate>0?'+':'')+rate+'%']].forEach(([k,v],i)=>{text(k,86,426+i*61,25,muted);text(v,988,426+i*61,28,green,'right',700);});
 text('双方收益',76,684,30);
 [['优先方收益',x.an,64],['劣后方收益',x.bn,550]].forEach(([label,value,left])=>{const color=value<0?'#b84d4d':green;box(left,743,466,222,'#eef5f0');text(label,left+22,764,26,green);text(signed(value),left+22,816,32,color,'left',700);text('实际年化  '+pct(value/x.P*100),left+22,881,26,color);});
 text('实际年化按净本金计算，已扣当期 Carry；未扣前置费。',76,985,21,muted);
 text('资金与分配明细',76,1044,30);pair(1110,'项目','优先方','劣后方');rule(1156);
 const rows=[['净投入资本',money(x.P),money(x.P)],['Carry 前损益',signed(x.a),signed(x.b)]];
 if(x.gain<0)rows.push(['  净亏损额',signed(x.a),signed(x.b),true]);
 else rows.push(['  基准收益',money(x.aBase),money(x.bBase),true],['  超额收益',money(x.aExcess),money(x.bExcess),true]);
 rows.push(['Carry 费率',rate>target?'20%':'0%',(x.bfr*100)+'%'],['Carry 初始计提',money(x.af),money(x.bf)],['Carry 冲回',money(x.refund),money(0)],['实际 Carry',money(x.af-x.refund),money(x.bf)],['期末模拟资本',money(x.P+x.an),money(x.P+x.bn)]);
 let y=1180;rows.forEach(row=>{pair(y,...row);if(!row[3])rule(y+44);y+=60;});
 y+=12;y=wrap('组合本金 '+money(x.T)+' · 组合损益 '+signed(x.gain),80,y,920,23,green);
 y=wrap('前置管理费 '+money(amount*.02)+'，已从优先方认购金额扣除。',80,y+12,920,22);
 y=wrap(document.getElementById('calculatorNotice').textContent,80,y+32,920,22);
 const out=document.createElement('canvas');out.width=1080;out.height=y+80;out.getContext('2d').drawImage(c,0,0);
 return out;
}
window.renderResultImage=renderResultImage;
let imageURL=null;
const dialog=document.getElementById('imageDialog'),button=document.getElementById('downloadImage'),status=document.getElementById('imageStatus');
button.onclick=async()=>{
 button.disabled=true;button.textContent='正在生成图片…';status.textContent='';
 try{
  const amount=+document.getElementById('amount').value,target=DISTRIBUTION_BENCHMARK,rate=+document.getElementById('rate').value;
  const canvas=renderResultImage(amount,target,rate);
  const blob=await new Promise((resolve,reject)=>canvas.toBlob(b=>b?resolve(b):reject(Error('PNG generation failed')),'image/png'));
  if(imageURL)URL.revokeObjectURL(imageURL);imageURL=URL.createObjectURL(blob);
  const link=document.getElementById('saveImage');link.href=imageURL;link.download='LUMEN_'+amount+'_基准'+target+'_基金收益'+rate+'.png';
  document.getElementById('resultImage').src=imageURL;
  dialog.showModal();link.click();status.textContent='图片已生成；若未自动下载，可在预览中点击保存，或长按图片保存。';
 }catch(e){status.textContent='图片生成未完成，请重试或使用复制结果。';}
 finally{button.disabled=false;button.textContent='下载结果图片';}
};
document.getElementById('closeImage').onclick=()=>dialog.close();
})();
