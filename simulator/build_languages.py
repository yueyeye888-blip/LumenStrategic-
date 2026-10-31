from pathlib import Path
import json,re
R=Path(__file__).parent
translations=json.loads((R/'translations.json').read_text())
translations.update({'门槛':'Hurdle'})
def english(text):
 for cn,en in sorted(translations.items(),key=lambda item:len(item[0]),reverse=True):text=text.replace(cn,en)
 return text.replace('Senior${','Senior ${').replace('Subordinated${','Subordinated ${')
html=(R/'source/index.html').read_text()
html=html.replace('<div class="brand">LUMEN</div>','<div class="brandRow"><div class="brand">LUMEN</div><select id="languageSelect" aria-label="语言 / Language"><option value="zh" selected>简体中文</option><option value="en">English</option></select></div>',1)
css='''.brandRow{display:flex;align-items:center;justify-content:space-between;gap:14px}#languageSelect{max-width:145px;min-height:44px;padding:9px 12px;border:1px solid #d4e0d8;border-radius:10px;background:#fff;color:#17664f;font-size:14px}html[lang=en] .heading{font-size:clamp(22px,4.8vw,28px)}html[lang=en] .line>label,html[lang=en] .line>span:not(.value){max-width:100%;line-height:1.5}html[lang=en] .annualReturn td:first-child{font-size:11px}html[lang=en] td:first-child,html[lang=en] th:first-child{width:42%;overflow-wrap:normal}html[lang=en] .breakdownToggle{line-height:1.5}html[lang=en] .sub{font-size:10px;line-height:1.7}@media(max-width:500px){html[lang=en] table{font-size:11px}html[lang=en] .panel{padding:20px 14px}html[lang=en] .annualReturn td:not(:first-child){font-size:16px}#languageSelect{max-width:125px;font-size:13px;padding:9px}.brand{font-size:28px}html[lang=en] .value{font-size:23px}}'''
html=html.replace('</style>',css+'</style>')
restore="""const state=new URLSearchParams(location.search);for(const [id,min,max] of [['amount',200000,2000000],['rate',-100,100]]){const raw=state.get(id);if(raw!==null){const value=Number(raw);if(Number.isFinite(value)&&value>=min&&value<=max)$(id).value=value;}}calc();$('languageSelect').onchange=()=>{const base=new URL(document.documentElement.lang==='en'?'../':'./',location.href),next=new URL($('languageSelect').value==='en'?'en/':'./',base);next.searchParams.set('amount',$('amount').value);next.searchParams.set('rate',$('rate').value);next.hash=location.hash;location.assign(next.href);};"""
assert ';calc();</script>' in html
html=html.replace(';calc();</script>',';'+restore+'</script>')
html=html.replace('calculator.js?v=5','calculator.js?v=6').replace('export-image.js?v=2','export-image.js?v=3')
(R/'dist/index.html').write_text(html)
eng=english(html).replace('lang="zh-CN"','lang="en"').replace('src="calculator.js?v=6"','src="../calculator.js?v=6"').replace('src="export-image.js?v=3"','src="../export-image-en.js?v=3"')
# Native language labels remain readable in each language.
eng=eng.replace('<option value="zh" selected>简体中文</option><option value="en">English</option>','<option value="zh">简体中文</option><option value="en" selected>English</option>')
remaining=re.findall(r'[\u3400-\u9fff]+',eng.replace('简体中文','').replace('语言',''))
assert not remaining,remaining
(R/'dist/en').mkdir(exist_ok=True)
(R/'dist/en/index.html').write_text(eng)
image=(R/'source/export-image.js').read_text()
(R/'dist/export-image.js').write_text(image)
image_en=english(image).replace('Actual Annualised Return  ','Annualised Return  ')
assert not re.findall(r'[\u3400-\u9fff]+',image_en),re.findall(r'[\u3400-\u9fff]+',image_en)
(R/'dist/export-image-en.js').write_text(image_en)

def add_production_metadata(path, *, canonical, alternate, title, description, icon):
 page=R/path
 content=page.read_text()
 marker=f'<title>{title}</title>'
 metadata=marker+(
  f'<link rel="canonical" href="{canonical}">'
  '<link rel="alternate" hreflang="zh-Hans" href="https://lumstratai.com/">'
  '<link rel="alternate" hreflang="en" href="https://lumstratai.com/en/">'
  '<link rel="alternate" hreflang="x-default" href="https://lumstratai.com/">'
  f'<link rel="icon" type="image/png" sizes="256x256" href="{icon}?v=1">'
  f'<link rel="apple-touch-icon" href="{icon}?v=1">'
  '<meta property="og:type" content="website">'
  f'<meta property="og:url" content="{canonical}">'
  f'<meta property="og:title" content="{title}">'
  f'<meta property="og:description" content="{description}">'
 )
 assert marker in content
 content=content.replace(marker,metadata,1)
 page.write_text(content)

add_production_metadata(
 Path('dist/index.html'),
 canonical='https://lumstratai.com/',
 alternate='zh-Hans',
 title='LUMEN | 投资收益情景模拟',
 description='LUMEN Strategic Capital 优先与劣后投资收益情景模拟器。',
 icon='favicon.png',
)
add_production_metadata(
 Path('dist/en/index.html'),
 canonical='https://lumstratai.com/en/',
 alternate='en',
 title='LUMEN | Investment Return Scenarios',
 description='LUMEN Strategic Capital Senior / Subordinated investment return scenario simulator.',
 icon='../favicon.png',
)
print('Generated Chinese / English pages and localized image renderer.')
