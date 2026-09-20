const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
const handlers={};const cached={marker:'previous archive'};let stored=cached;let next={ok:true,clone:()=>({marker:'fresh archive'})};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../sw.js'),'utf8'),{URL,location:{origin:'https://esm.business'},self:{addEventListener:(name,fn)=>handlers[name]=fn},fetch:async()=>{if(next instanceof Error)throw next;return next},caches:{open:async()=>({put:async(_,value)=>{stored=value}}),match:async()=>stored}});
async function request(){let response;const work=[];handlers.fetch({request:{url:'https://esm.business/data/archive.json?v=123',method:'GET'},respondWith:p=>response=p,waitUntil:p=>work.push(p)});const value=await response;await Promise.all(work);return value;}
(async()=>{
 await request();assert.equal(stored.marker,'fresh archive');
 next={ok:false,status:503};assert.equal((await request()).marker,'fresh archive');
 assert.equal(stored.marker,'fresh archive','server errors must not overwrite cache');
 next=new Error('offline');assert.equal((await request()).marker,'fresh archive');
 console.log('Archive cache passed: successful caching, HTTP-error fallback, offline fallback.');
})().catch(e=>{console.error(e);process.exit(1)});
