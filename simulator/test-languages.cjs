const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
function render(language,amount,rate){
 const html=fs.readFileSync(language==='en'?'dist/en/index.html':'dist/index.html','utf8');
 const inline=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(x=>x[1]).join('\n');
 const nodes={};const get=id=>nodes[id]||(nodes[id]={value:id==='amount'?'200000':id==='rate'?'30':'',style:{},textContent:'',setAttribute(){},addEventListener(){}});
 const context=vm.createContext({document:{getElementById:get,querySelectorAll:()=>[],documentElement:{lang:language==='en'?'en':'zh-CN'}},location:{search:`?amount=${amount}&rate=${rate}`,href:'https://example.test/'+(language==='en'?'en/':''),hash:''},URL,URLSearchParams,setTimeout(){}});
 vm.runInContext(fs.readFileSync('dist/calculator.js','utf8'),context);vm.runInContext(inline,context);
 const copy=vm.runInContext('last',context);
 assert.equal(get('amount').value,amount);assert.equal(get('rate').value,rate);
 assert.ok(language==='en'?copy.includes('Agreed Return Allocation Basis'):copy.includes('约定分配基准'));
 return ['aNet','bNet','aFee','bFee','aEnd','bEnd','aAnnual','bAnnual'].map(id=>get(id).textContent);
}
let checks=0;for(const amount of [200000,2000000])for(const rate of [-100,-50,0,8,25,50,100]){assert.deepEqual(render('en',amount,rate),render('zh',amount,rate));checks++;}
console.log(`${checks} bilingual scenarios match; URL parameters, copied language and numeric results verified.`);
