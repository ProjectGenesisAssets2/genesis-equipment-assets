/* Project Genesis · quest puente entre dos espadas y dos escudos.
 * Sólo las recetas reales de la semilla del Herrero intervienen en el pedido.
 */
(function(root){
 'use strict';
 const steps=Object.freeze({talk:11.25,escort:11.5,shop:11.75});
 const escortPath=Object.freeze([
  {x:.55,z:-.60},{x:.50,z:1.60},{x:.75,z:3.45},
  {x:7.0,z:3.6},{x:7.0,z:16.0},{x:7.0,z:26.0},
  {x:7.0,z:36.0},{x:17.0,z:36.0},
  {x:23.0,z:36.0},{x:24.25,z:35.15}
 ].map(p=>Object.freeze(p)));
 function shieldNeeds(session,inventory){
  if(!session||session.profession!=='Herrero'||!Array.isArray(session.formulas?.escudo_hierro?.materials))return[];
  const target=Object.create(null);
  for(const part of session.formulas.escudo_hierro.materials){
   if(!part||typeof part.material!=='string'||!Number.isSafeInteger(part.qty)||part.qty<=0)continue;
   const material=part.material==='Lingote de hierro'?'Mineral de hierro':part.material;
   target[material]=(target[material]||0)+2*part.qty;
  }
  const current=inventory&&typeof inventory==='object'?inventory:{};
  return Object.keys(target).sort((a,b)=>a.localeCompare(b,'es')).map(material=>{
   // Los lingotes que el jugador ya preparó también cubren la necesidad de mineral.
   const amounts=material==='Mineral de hierro'
     ?[current['Mineral de hierro'],current['Lingote de hierro']]
     :[current[material]];
   const have=amounts.reduce((n,v)=>n+(Number.isSafeInteger(v)&&v>0?v:0),0);
   const needed=target[material];
   return{material,needed,have,missing:Math.max(0,needed-have)};
  });
 }
 function ready(session,inventory){
  const needs=shieldNeeds(session,inventory);
  return needs.length>0 && needs.every(n=>n.missing===0);
 }
 const api=Object.freeze({version:'GENESIS_MARKET_QUEST_V001',steps,escortPath,shieldNeeds,ready});
 root.GenesisMarketQuest=api;
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof window==='undefined'?globalThis:window);
