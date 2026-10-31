import { cpSync, mkdirSync } from 'node:fs';
mkdirSync('public',{recursive:true});
for(const path of ['assets','styles.css','app.js'])cpSync('website/'+path,'public/'+path,{recursive:true});
