import { env } from "cloudflare:workers";
const reply=(body:object,status=200)=>Response.json(body,{status,headers:{"Cache-Control":"no-store"}});
export async function POST(request:Request){
 const origin=request.headers.get("origin");
 if(origin && origin!==new URL(request.url).origin)return reply({ok:false},403);
 if(!request.headers.get("content-type")?.startsWith("application/json"))return reply({ok:false},415);
 if(Number(request.headers.get("content-length")||0)>20000)return reply({ok:false},413);
 let raw:string;try{raw=await request.text();}catch{return reply({ok:false},400);}
 if(raw.length>12000)return reply({ok:false},413);
 let body:Record<string,unknown>;try{body=JSON.parse(raw);}catch{return reply({ok:false},400);}
 if(!body||typeof body!=="object"||Array.isArray(body))return reply({ok:false},400);
 const limits:Record<string,number>={id:36,name:120,email:200,investorType:150,topic:150,size:100,message:1500,language:10};
 const data:Record<string,string>={};
 for(const [key,max] of Object.entries(limits)){
  if(typeof body[key]!=="string"||(body[key] as string).length>max)return reply({ok:false},400);
  data[key]=(body[key] as string).trim();
 }
 if(!/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(data.id)||!data.name||!data.message||!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)||!["zh-Hans","zh-Hant","en"].includes(data.language))return reply({ok:false},400);
 if(!env.DB)return reply({ok:false},503);
 try{
  const existing=await env.DB.prepare("SELECT id FROM applications WHERE id = ?").bind(data.id).first();
  if(existing)return reply({ok:true});
  const recent=await env.DB.prepare("SELECT count(*) AS total FROM applications WHERE email = ? AND created_at > ?").bind(data.email.toLowerCase(),new Date(Date.now()-3600000).toISOString()).first<{total:number}>();
  if((recent?.total||0)>=5)return reply({ok:false},429);
  await env.DB.prepare("INSERT INTO applications (id,name,email,investor_type,topic,investment_size,message,language,created_at) VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO NOTHING").bind(data.id,data.name,data.email.toLowerCase(),data.investorType,data.topic,data.size,data.message,data.language,new Date().toISOString()).run();
  return reply({ok:true},201);
 }catch{return reply({ok:false},503);}
}
