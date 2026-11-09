/* Project Genesis · mercenary equipment domain v001.
 * Headless logic, no demo stats or fabricated inventory. ES5-compatible browser global.
 * Host bridges: getItems(), getMercenaries(), saveMercenaries(next),
 * renderMercenary(merc,element), openObjectSheet(item), close()/render().
 */
(function(root){
'use strict';
const FAMILY={sword:'Espadas',shield:'Escudos'};
const CHANNELS=['Base','Luz','Sombra','Fuego','Hielo','Naturaleza','Tierra','Rayo'];
function identifier(item){return item && (item.id||item.uuid||item.instanceId);}
function family(item){const v=String(item&&(item.family||item.recipeFamily||item.recipe||item.category)||'').toLowerCase();return /^espada(s)?\b/.test(v)?'Espadas':/^escudo(s)?\b/.test(v)?'Escudos':null;}
function channelEntries(item){
  const arr=Array.isArray(item&&item.channels)?item.channels:[];
  return arr.map(function(c,i){
    const raw=Array.isArray(c)?c[0]:c.name||c.channel;
    const value=Array.isArray(c)?c[1]:c.intensity;
    const key=String(raw||'').trim();
    if(!key || !Number.isFinite(Number(value))) return null;
    return {key:key.toLowerCase()==='base'?'Base':key,intensity:Number(value),index:i,techniques:!Array.isArray(c)&&Array.isArray(c.techniques)?c.techniques:[]};
  }).filter(Boolean);
}
function compare(a,b){
 const left=channelEntries(a),right=channelEntries(b),keys=[];
 left.concat(right).forEach(function(c){if(!keys.includes(c.key))keys.push(c.key)});
 keys.sort(function(x,y){if(x==='Base')return -1;if(y==='Base')return 1;const a=left.concat(right).find(c=>c.key===x),b=left.concat(right).find(c=>c.key===y);return a.index-b.index});
 return keys.map(function(key){
  const l=left.find(c=>c.key===key),r=right.find(c=>c.key===key);
  return {channel:key,equipped:l?l.intensity:null,selected:r?r.intensity:null,delta:l&&r?r.intensity-l.intensity:null,presentEquipped:!!l,presentSelected:!!r,techniquesSelected:r?r.techniques:[]};
 });
}
function normalizeMerc(merc){return {id:merc.id,name:merc.name||'Mercenario',equipment:Object.assign({weapon:null,shield:null},merc.equipment||{}),inventoryIds:Array.isArray(merc.inventoryIds)?merc.inventoryIds.slice():[],original:merc};}
function validRoster(roster){return Array.isArray(roster)&&roster.every(m=>m&&m.id!==undefined&&m.id!==null);}
function create(adapter){
 if(!adapter||typeof adapter.getItems!=='function'||typeof adapter.getMercenaries!=='function')throw Error('Mercenary adapter missing');
 let state={mercId:null,family:'Espadas',selectedId:null};
 function roster(){const r=adapter.getMercenaries();if(!validRoster(r))throw Error('Invalid mercenary roster');return r.map(normalizeMerc)}
 function current(){const rs=roster();return rs.find(m=>String(m.id)===String(state.mercId))||rs[0]||null}
 function items(){return (adapter.getItems()||[]).filter(i=>i&&identifier(i)!=null)}
 function lookup(id){return items().find(i=>String(identifier(i))===String(id))||null}
 function occupied(){const ids=new Set();roster().forEach(m=>{Object.values(m.equipment).forEach(id=>{if(id!=null)ids.add(String(id))})});return ids}
 function available(){const busy=occupied();return items().filter(i=>family(i)===state.family && !busy.has(String(identifier(i))))}
 function selected(){return lookup(state.selectedId)}
 function equipped(){const m=current();return m?lookup(m.equipment[state.family==='Espadas'?'weapon':'shield']):null}
 function chooseMerc(id){if(!roster().some(m=>String(m.id)===String(id)))return false;state.mercId=id;state.selectedId=null;return true}
 function chooseFamily(f){if(f!=='Espadas'&&f!=='Escudos')return false;state.family=f;state.selectedId=null;return true}
 function select(id){const i=available().find(x=>String(identifier(x))===String(id));if(!i)return false;state.selectedId=identifier(i);return true}
 function equip(){
  const m=current(),i=selected();if(!m||!i||!select(identifier(i)))return {ok:false,reason:'unavailable'};
  const slot=state.family==='Espadas'?'weapon':'shield';
  const all=adapter.getMercenaries();const fresh=all.map(x=>{
   if(String(x.id)!==String(m.id))return x;
   const next=Object.assign({},x,{equipment:Object.assign({},x.equipment||{}, {[slot]:identifier(i)})});
   return next;
  });
  if(typeof adapter.saveMercenaries!=='function')return {ok:false,reason:'persistence_not_connected'};
  const result=adapter.saveMercenaries(fresh);
  if(result===false)return {ok:false,reason:'save_failed'};
  state.selectedId=null;
  return {ok:true,mercenaryId:m.id,slot:slot,itemId:identifier(i),previousId:m.equipment[slot]};
 }
 function snapshot(){const m=current(),candidate=selected(),worn=equipped();return {mercenary:m,family:state.family,selected:candidate,equipped:worn,available:available(),comparison:compare(worn,candidate),slots:{helmet:'fixed',chest:'fixed',arms:'fixed',gloves:'fixed',legs:'fixed',boots:'fixed',necklace:'fixed',ringLeft:'fixed',ringRight:'fixed',weapon:'equipable',shield:'equipable'}}}
 return {state:state,snapshot:snapshot,chooseMerc:chooseMerc,chooseFamily:chooseFamily,select:select,equip:equip,compare:compare,channelEntries:channelEntries};
}
root.GenesisMercenaryEquipment={create:create,compare:compare,channelEntries:channelEntries,version:'MERCENARY_EQUIPMENT_DOMAIN_V001'};
})(typeof window==='undefined'?globalThis:window);
