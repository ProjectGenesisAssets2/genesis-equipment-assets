/* Project Genesis · Mercenary concept layout, v0.1.001.
   Uses the existing PlayCanvas mission/equipment callbacks; never generates item statistics.
   Only visual components. Future jewelry and clothing remain disabled. */
(function(global){
'use strict';
const ICONS={Base:'⚔',Luz:'☼',Sombra:'☾',Fuego:'♨',Hielo:'❄',Naturaleza:'❧',Tierra:'◆',Rayo:'ϟ'};
const COLORS={Base:'#b44634',Luz:'#d6ac53',Sombra:'#9362c3',Fuego:'#e56b27',Hielo:'#6ebacb',Naturaleza:'#669e51',Tierra:'#ac8650',Rayo:'#4389d6'};
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function rows(item){
 const channels=Array.isArray(item&&item.channels)?item.channels:[];
 return channels.map((c,index)=>({name:String(Array.isArray(c)?c[0]:(c.name||c.channel||'')),value:Number(Array.isArray(c)?c[1]:c.intensity),index})).filter(c=>c.name&&Number.isFinite(c.value)).map(c=>({...c,name:c.index===0?'Base':c.name}));
}
function comparisons(equipped,chosen){
 const a=rows(equipped),b=rows(chosen),order=[];
 a.concat(b).forEach(c=>{if(!order.includes(c.name))order.push(c.name);});
 order.sort((x,y)=>x==='Base'?-1:y==='Base'?1:0);
 return order.map(n=>({name:n,a:a.find(x=>x.name===n),b:b.find(x=>x.name===n)}));
}
function render(opts){
 const state={family:'first',selection:null,details:false,inventory:false,sheet:false,page:0,techOpen:new Set()};
 let a=opts.selectedFirst||null,b=opts.selectedSecond||null;
 let lastClick=null,lastClickAt=0;
 const poolA=opts.poolFirst||[],poolB=opts.poolSecond||[];
 
 function currentPool(){return state.family==='first'?poolA:poolB;}
 function current(){return state.family==='first'?a:b;}
 function setCurrent(item){if(state.family==='first')a=item;else b=item;opts.onDraft?.(state.family,item);}
 function equipped(){return state.family==='first'?opts.equippedFirst:opts.equippedSecond;}
 function image(item){return item&&typeof opts.itemIcon==='function'?'<img src="'+esc(opts.itemIcon(item.recipe))+'" alt="">':'<span>✧</span>';}
 function slot(label,glyph,locked,item,extra){
  return '<button type="button" class="mcSlot '+(locked?'isLocked':'isActive')+' '+(extra||'')+'" '+(locked?'disabled':'')+' aria-label="'+esc(label)+'"><span class="mcGlyph">'+(item?image(item):esc(glyph))+'</span><span class="mcSlotLabel">'+esc(label)+'</span></button>';
 }
 function currentItem(){return state.selection||current()||currentPool()[0]||null;}
 function fmtValue(r,side){const c=r[side];return c?(c.name==='Base'?String(c.value):'+'+c.value+'%'):'—';}
 function central(){
  const bodyUrl=opts.body==='ranger'?'https://cdn.jsdelivr.net/gh/Genesara/genesara-web@main/public/models/characters/male_ranger.glb':'https://cdn.jsdelivr.net/gh/Genesara/genesara-web@main/public/models/characters/male_peasant.glb';
  return '<section class="mcPanel mcCenter">'+
   '<div class="mcMercNav"><span class="mcMercName">'+esc(opts.mercName)+'</span><span class="mcMercIDs">'+[0,1,2].map(i=>'<button type="button" '+(i===opts.candidate?'class="on"':'disabled')+' aria-label="Mercenario '+(i+1)+'">'+(i+1)+'</button>').join('')+'</span></div>'+
   '<div class="mcMercField">'+
    '<div class="mcSlotsLeft">'+slot('Casco','♜',true)+slot('Brazales','✥',true)+slot('Anillo izquierdo','◈',true)+slot(opts.labelFirst,'⚔',false,a,'mcEquipSlot')+slot('Piernas','♟',true)+'</div>'+
    '<div class="mcHero"><div class="mcNeck">'+slot('Collar','♢',true)+'</div><model-viewer src="'+esc(bodyUrl)+'" camera-controls auto-rotate rotation-per-second="6deg" camera-orbit="15deg 80deg 3.8m" shadow-intensity=".7" exposure="1.1" interaction-prompt="none" alt="Modelo base GLB real del mercenario de PlayCanvas"></model-viewer><span class="mcModelNote">GLB base del juego · equipo visible en el mundo</span></div>'+
    '<div class="mcSlotsRight">'+slot('Pechera','♜',true)+slot('Guantes','✥',true)+slot('Anillo derecho','◈',true)+slot(opts.labelSecond,'⬡',false,b,'mcEquipSlot')+slot('Botas','♟',true)+'</div></div>'+
   '<div class="mcFooterButtons"><button data-action="sheet">FICHA DEL MERCENARIO</button><button data-action="inventory">INVENTARIO DEL MERCENARIO</button><button data-action="back">CERRAR / VOLVER</button></div></section>';
 }
 function left(){
  let familyA=opts.familyFirst||'Espadas',familyB=opts.familySecond||'Escudos',pool=currentPool();
  const starts=state.family==='first'?familyA:familyB;
  return '<section class="mcPanel mcLeft"><div class="mcHeading">EQUIPAMIENTO COMPATIBLE</div><div class="mcSubhead">FAMILIAS</div>'+
  '<div class="mcFamilies"><button type="button" data-family="first" class="'+(state.family==='first'?'active':'')+'">⚔ '+esc(familyA)+'</button><button type="button" data-family="second" class="'+(state.family==='second'?'active':'')+'">⬡ '+esc(familyB)+'</button></div>'+
  '<div class="mcSubhead">OBJETOS DISPONIBLES · '+esc(starts)+'</div><div class="mcInventoryGrid">'+
  Array.from({length:20},(_,i)=>{const item=pool[state.page*20+i];if(!item)return '<span class="mcEmptySlot" aria-label="Casilla vacía">✧</span>'; const selected=item===currentItem(),active=item===current();
    return '<button type="button" data-item="'+(state.page*20+i)+'" class="mcInventorySlot '+(selected?'selected ':'')+(active?'equipped':'')+'" title="'+esc(item.name)+'">'+image(item)+'</button>';}).join('')+
  '</div><div class="mcInvFooter"><button data-page="prev" '+(state.page===0?'disabled':'')+'>◂</button> '+(state.page+1)+' / '+Math.max(1,Math.ceil(pool.length/20))+' <button data-page="next" '+((state.page+1)*20>=pool.length?'disabled':'')+'>▸</button></div></section>';
 }
 function right(){
 const equippedItem=equipped(),selected=currentItem(),c=comparisons(equippedItem,selected);
 return '<section class="mcPanel mcRight"><div class="mcHeading">COMPARACIÓN DE EQUIPO</div>'+
 '<div class="mcDuel"><div><small>EQUIPADO</small><div class="mcItemImg">'+image(equippedItem)+'</div><span>'+esc(equippedItem?.name||'Sin equipar')+'</span><small>'+esc(equippedItem?.rarity||'')+'</small></div><b>»</b><div><small>SELECCIONADO</small><div class="mcItemImg">'+image(selected)+'</div><span>'+esc(selected?.name||'Sin objetos')+'</span><small>'+esc(selected?.rarity||'')+'</small></div></div>'+
 '<div class="mcSubhead">CANALES DE LA CREACIÓN</div><div class="mcCompareHead"><span>CANAL</span><span>ACTUAL</span><span>NUEVO</span></div>'+
 '<div class="mcChannels" role="region" aria-label="Comparación desplazable de canales">'+
 (c.length?c.map(row=>{let key=COLORS[row.name]?row.name:'Base',x=row.a&&row.b?row.b.value-row.a.value:null,defensive=!!opts.defensive||state.family==='second';
  return '<div class="mcChannel" style="--cc:'+COLORS[key]+'"><span class="mcChannelIcon">'+ICONS[key]+'</span><span class="mcChannelArt"><em>'+esc(row.name==='Base'?(defensive?'Protección · Base':'Daño · Base'):row.name)+'</em></span><span class="mcChannelNum">'+fmtValue(row,'a')+'</span><span class="mcChannelNum '+(x===null?'':x>0?'increase':x<0?'decrease':'same')+'">'+fmtValue(row,'b')+'</span></div>';
 }).join(''):'<p class="mcEmptyMessage">Seleccioná un objeto. Los valores se leerán de la fabricación, sin estadísticas inventadas.</p>')+'</div>'+
 '<div class="mcRightActions"><button data-action="inspect" '+(!selected?'disabled':'')+'>INSPECCIONAR</button><button class="mcPrimary" data-action="equip" '+(!a||!b?'disabled':'')+'>'+esc(opts.editing?'APLICAR CAMBIOS':'EQUIPAR AL MERCENARIO')+'</button></div></section>';
 }
 function overlay(){
  if(state.sheet){return '<div class="mcOverlay"><section><h2>FICHA DEL MERCENARIO</h2>'+ (typeof opts.getStatsHTML==='function'?opts.getStatsHTML(a,b):opts.statsHTML||'<p>No hay estadísticas registradas.</p>') +'<button data-action="dismiss">VOLVER</button></section></div>';}
  if(state.details&&currentItem()){
   const item=currentItem();
   return '<div class="mcOverlay"><section><h2>'+esc(item.name)+'</h2><p>'+esc(item.rarity||'')+'</p><div class="mcSheetRows">'+rows(item).map(c=>'<div><span>'+esc(c.name==='Base'?'Canal Base':c.name)+'</span><b>'+esc(c.name==='Base'?c.value:'+'+c.value+'%')+'</b></div>').join('')+'</div><button data-action="dismiss">VOLVER</button></section></div>';
  }
  if(state.inventory){
   return '<div class="mcOverlay"><section><h2>INVENTARIO DEL MERCENARIO</h2>'+(typeof opts.getMercInventoryHTML==='function'?opts.getMercInventoryHTML(a,b):'<div class="mcSheetRows"><div><span>'+esc(opts.labelFirst)+'</span><b>'+esc(a?.name||'Vacío')+'</b></div><div><span>'+esc(opts.labelSecond)+'</span><b>'+esc(b?.name||'Vacío')+'</b></div></div>')+'<p>Equipo asignado al personaje. Las otras casillas de la demo permanecen fijas.</p><button data-action="dismiss">VOLVER</button></section></div>';
  }
  return '';
 }
 function update(){
  opts.modal('<div class="mercConcept"><div class="mcBoard" aria-label="Equipamiento de mercenario"><header class="mcTitle"><div>PROJECT GENESIS</div><h1>INVENTARIO DEL MERCENARIO</h1></header><div class="mcColumns">'+left()+central()+right()+'</div>'+overlay()+'</div></div>','mercenaryModal mercConceptModal');
  const board=document.querySelector('.mcBoard');if(!board)return;
  board.querySelectorAll('[data-family]').forEach(el=>el.addEventListener('click',()=>{state.family=el.dataset.family;state.selection=null;state.page=0;update()}));
  board.querySelectorAll('[data-page]').forEach(el=>el.addEventListener('click',()=>{state.page=Math.max(0,state.page+(el.dataset.page==='next'?1:-1));state.selection=null;update()}));
  board.querySelectorAll('[data-item]').forEach(el=>{el.addEventListener('click',()=>{const item=currentPool()[+el.dataset.item];if(!item)return;const now=Date.now(),again=lastClick===item&&now-lastClickAt<360;setCurrent(item);state.selection=item;if(again)state.details=true;lastClick=item;lastClickAt=now;update()})});
  board.querySelectorAll('.mcEquipSlot').forEach((el,i)=>el.addEventListener('click',()=>{state.family=i===0?'first':'second';state.selection=current();update()}));
  board.querySelectorAll('[data-action]').forEach(el=>el.addEventListener('click',()=>{
   switch(el.dataset.action){
    case 'sheet':state.sheet=true;return update();
    case 'inventory':state.inventory=true;return update();
    case 'dismiss':state.inventory=false;state.details=false;state.sheet=false;return update();
    case 'inspect':state.details=true;return update();
    case 'back':return opts.onBack?.();
    case 'equip':if(!a||!b)return;return opts.onConfirm?.(a,b);
   }
  }));
 }
 update();
 return {refresh:update};
}
global.GenesisMercenaryConcept={open:render,version:'PLAYCANVAS_MERCENARY_CONCEPT_V001'};
})(window);
