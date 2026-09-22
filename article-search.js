/* Local article search. No network calls or persistent query storage. */
(function(root){
  const normalize=value=>String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase().replace(/ß/g,'ss');
  function merge(current,archive){
    const byId=new Map();
    for(const item of [...current,...archive]) if(!byId.has(item.id)) byId.set(item.id,item);
    return [...byId.values()];
  }
  function search(items,query,topic='',category=''){
    const words=normalize(query).trim().split(/\s+/).filter(Boolean);
    return items.filter(item=>{
      if(topic&&item.tab!==topic || category&&item.cat!==category) return false;
      const text=normalize([item.titel?.de,item.titel?.en,item.kurz?.de,item.kurz?.en,item.rel?.de,item.rel?.en,item.qn,item.sub?.de,item.sub?.en].join(' '));
      return words.every(word=>text.includes(word));
    }).sort((a,b)=>String(b.added||b.datum||'').localeCompare(String(a.added||a.datum||'')));
  }
  function validArchive(value){
    const cats={ai:['ind','fs','gps','lshc','tmt','cross'],esm:['sn','results','market'],sov:['snsov','cloud','ai'],tech:['mcp','gov','dev']};
    const bi=o=>o&&typeof o.de==='string'&&typeof o.en==='string';
    return Array.isArray(value)&&value.every(i=>i&&typeof i.id==='string'&&/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(i.id)&&cats[i.tab]?.includes(i.cat)&&typeof i.datum==='string'&&/^\d{4}(?:-\d{2})?(?:-\d{2})?$/.test(i.datum)&&(!i.added||typeof i.added==='string')&&bi(i.titel)&&bi(i.kurz)&&bi(i.rel)&&(!i.metric||(bi(i.metric)&&bi(i.msub)))&&(!i.sub||bi(i.sub))&&typeof i.quelle==='string'&&/^https:\/\/[^\s"<>]+$/.test(i.quelle));
  }
  const api={merge,search,validArchive};
  if(typeof module!=='undefined'&&module.exports) module.exports=api;
  else root.ArticleSearch=api;
})(globalThis);
