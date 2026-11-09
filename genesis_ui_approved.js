/* Project Genesis UI 2026-11-08: runtime-only overlays over the immutable approved 1672x941 artwork. */
(function(){
 'use strict';
 const BUILD='V014.028';
 const ROOT='assets/ui/approved/';
 const ARTS=Object.freeze({Inventario:ROOT+'Inventario_V11_APROBADO_1672x941.png',Preparacion:ROOT+'Preparacion_APROBADA_1672x941.png',Fabricaciones:ROOT+'Fabricaciones_V07_APROBADA_1672x941.png'});
 const MATERIALS=Object.freeze({
  'Mineral de hierro':['assets/playcanvas/approved/materials/iron_ore/v008_55k_pbr1536_v007/mineral_hierro_v008_transparent_0.png','assets/playcanvas/approved/materials/iron_ore/v008_55k_pbr1536_v007/mineral_hierro_v008_55k_pbr1536_v007.glb'],
  'Lingote de hierro':['assets/playcanvas/approved/materials/iron/v175/iron_v175_transparent.png',null],
  'Carbón vegetal':['assets/playcanvas/approved/materials/charcoal/v011/carbon_vegetal_v011_poster.png','assets/playcanvas/approved/materials/charcoal/v011/carbon_vegetal_v011_final_3_piezas_web.glb'],
  'Madera seca de roble':['assets/playcanvas/approved/materials/oak/v004/madera_roble_v004_poster.png',null],
  'Madera seca de fresno':['assets/playcanvas/approved/materials/ash/v004/madera_fresno_v004_poster.png',null],
  'Cuero bovino curtido':['assets/playcanvas/approved/materials/leather_bovine/v003/cuero_bovino_v003_poster.png',null],
  'Cuero caprino curtido':['assets/playcanvas/approved/materials/leather_caprine/v003/cuero_caprino_v003_poster.png',null],
  'Cordel de cáñamo':['assets/playcanvas/approved/materials/hemp/v018/cordel_canamo_v018_poster.jpg','assets/playcanvas/approved/materials/cordel_canamo/v018/cordel_canamo_v018.glb'],
  'Hilo de lino':['assets/playcanvas/approved/materials/linen/v021/hilo_lino_v021_poster.jpg','assets/playcanvas/approved/materials/hilo_lino/v021/hilo_lino_v021.glb']
 });
 const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const pos=(x,y,w,h)=>`left:${(100*x/1672).toFixed(4)}%;top:${(100*y/941).toFixed(4)}%;width:${(100*w/1672).toFixed(4)}%;height:${(100*h/941).toFixed(4)}%`;
 const hit=(name,x,y,w,h,attrs='')=>`<button type="button" class="gApprovedHit" data-go="${esc(name)}" aria-label="${esc(name)}" ${attrs} style="${pos(x,y,w,h)}"></button>`;
 const tabs=()=>[
   hit('Inventario',182,38,317,76),hit('Preparacion',499,38,317,76),
   hit('Fabricaciones',816,38,337,76),hit('Comparacion',1153,38,303,76)
 ].join('');
 function materialVisual(name,hero){
   const [poster]=MATERIALS[name]||[];
   // The approved stock image is static. A source poster may have an opaque grey matte:
   // the local image is cleaned at runtime without modifying its approved master.
   return poster?`<img class="gApprovedMaterialArt" data-matte-source="${esc(poster)}" src="${esc(poster)}" alt="${esc(name)}" draggable="false">`:
     `<span class="gApprovedNoModel">${esc(name)}</span>`;
 }
 const matteCache=new Map();
 function cleanMaterialPoster(img){
   if(!img||img.dataset.matteAttached)return;
   img.dataset.matteAttached='1';
   const source=img.dataset.matteSource;
   if(!source)return;
   if(matteCache.has(source)){const cached=matteCache.get(source);if(cached)img.src=cached;return;}
   function clean(){
     if(!img.naturalWidth||!img.naturalHeight)return;
     try{
       const w=img.naturalWidth,h=img.naturalHeight;
       const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;
       const c=canvas.getContext('2d',{willReadFrequently:true});c.drawImage(img,0,0);
       const rgba=c.getImageData(0,0,w,h),d=rgba.data;
       const corners=[0,(w-1)*4,(w*(h-1))*4,(w*h-1)*4].map(i=>[d[i],d[i+1],d[i+2],d[i+3]]);
       // If the source already has transparency, keep it unchanged.
       if(corners.some(px=>px[3]<230)){matteCache.set(source,source);return;}
       const mean=[0,1,2].map(k=>Math.round(corners.reduce((acc,p)=>acc+p[k],0)/4));
       const similarity=corners.every(px=>Math.abs(px[0]-mean[0])+Math.abs(px[1]-mean[1])+Math.abs(px[2]-mean[2])<48);
       if(!similarity){matteCache.set(source,source);return;}
       const pixels=w*h,seen=new Uint8Array(pixels),queue=new Int32Array(pixels);
       let start=0,end=0;
       const near=p=>{const i=p*4;const dr=d[i]-mean[0],dg=d[i+1]-mean[1],db=d[i+2]-mean[2];return dr*dr+dg*dg+db*db<2600;};
       function add(p){if(p<0||p>=pixels||seen[p]||!near(p))return;seen[p]=1;queue[end++]=p;}
       for(let x=0;x<w;x++){add(x);add((h-1)*w+x);}
       for(let y=0;y<h;y++){add(y*w);add(y*w+w-1);}
       let removed=0;
       while(start<end){
         const p=queue[start++],x=p%w;d[p*4+3]=0;removed++;
         if(x>0)add(p-1);if(x<w-1)add(p+1);if(p>=w)add(p-w);if(p<pixels-w)add(p+w);
       }
       if(removed>pixels*.025&&removed<pixels*.98){
         c.putImageData(rgba,0,0);
         const cleaned=canvas.toDataURL('image/png');matteCache.set(source,cleaned);
         // Model identity is unchanged; only the flat poster matte is transparent.
         img.src=cleaned;
       }else matteCache.set(source,source);
     }catch(error){matteCache.set(source,source);console.warn('Material matte clean skipped',source,error);}
   }
   if(img.complete&&img.naturalWidth)clean();else img.addEventListener('load',clean,{once:true});
 }
 function cleanBoardPosters(board){
   board.querySelectorAll('img.gApprovedMaterialArt').forEach(cleanMaterialPoster);
 }
 function itemFamily(item){const raw=String(item?.family||item?.recipeFamily||item?.recipe||'').toLowerCase();return /escud/.test(raw)?'Escudos':/espad/.test(raw)?'Espadas':'Creaciones'}
 function entryView(e,ctx,hero){
   if(e.material)return materialVisual(e.name,hero);
   return hero?(typeof ctx.renderAsset==='function'?ctx.renderAsset(e.item):''):
     (e.item?.thumbnail||e.item?.poster?`<img src="${esc(e.item.thumbnail||e.item.poster)}" alt="${esc(e.name)}">`:
       '<span class="gApprovedItemGlyph">✦</span>');
 }
 function mount(tab,ctx,nav,body,attrs=''){
   const html=`<div id="genesisApprovedBoard" class="gApprovedBoard gApproved-${tab}" data-screen="${tab}" data-approved-source="${esc(ARTS[tab])}" ${attrs} style="background-image:url('${ARTS[tab]}')">${tabs()}${body}${hit('Cerrar',1603,0,69,36)}</div>`;
   ctx.modal(html,'preparationModal genesisApprovedModal');
   const board=document.getElementById('genesisApprovedBoard');if(!board)return null;
   board.dataset.build=BUILD;
   cleanBoardPosters(board);
   board.querySelectorAll('[data-go]').forEach(b=>b.onclick=()=>{
     const tab=b.dataset.go;
     if(tab==='Cerrar'){nav.close();return}
     if(tab==='Preparacion')nav.renderMenu();else if(tab==='Comparacion')nav.renderWorkspace('Comparacion');else nav.renderWorkspace(tab);
   });
   return board;
 }
 function inventory(ctx,nav){
   const stock=Object.entries(ctx.inventory||{}).filter(([,qty])=>Number(qty)>0);
   const creations=typeof ctx.getItems==='function'?(ctx.getItems()||[]).filter(Boolean):[];
   const state=ctx.genesisApprovedInventory||(ctx.genesisApprovedInventory={family:'Materiales',page:0,selected:null,sheet:false});
   const families=['Materiales','Espadas','Escudos'];
   if(!families.includes(state.family))state.family='Materiales';
   const entries=state.family==='Materiales'?stock.map(([name,qty])=>({key:'m:'+name,name,qty:Number(qty),material:true})):
     creations.filter(item=>itemFamily(item)===state.family).map((item,i)=>({key:'c:'+String(item.id||i),name:item.name,material:false,item}));
   const maxPage=Math.max(0,Math.ceil(entries.length/20)-1);state.page=Math.min(state.page,maxPage);
   const page=entries.slice(state.page*20,state.page*20+20);
   if(!page.some(e=>e.key===state.selected))state.selected=page[0]?.key||null;
   const chosen=page.find(e=>e.key===state.selected)||null;
   const familyButtons=families.map((f,i)=>`<button type="button" class="gApprovedFamily ${f===state.family?'is-selected':''}" data-family="${f}" aria-pressed="${f===state.family}" style="${pos(54,229+45*i,288,45)}" aria-label="Filtrar ${f}"></button>`).join('');
   const slots=Array.from({length:20},(_,i)=>{
     const e=page[i],x=410+(i%10)*122.0,y=589+Math.floor(i/10)*126;
     return `<button type="button" class="gApprovedSlot ${e?.key===state.selected?'is-selected':''}" style="${pos(x,y,107,109)}" ${e?'data-slot="'+i+'" aria-label="'+esc(e.name)+'"':'disabled aria-label="Casilla vacía"'}>${e?`<span class="gApprovedSlotAsset">${entryView(e,ctx,false)}</span><span class="gApprovedQty">${esc(e.material?e.qty:e.item?.rarity||'')}</span>`:''}</button>`;
   }).join('');
   const info=chosen?`<div class="gApprovedInfoValues" style="${pos(1305,208,260,88)}"><span>${esc(chosen.name)}</span><span>${esc(chosen.material?'Materiales':state.family)}</span><span>${esc(chosen.material?'—':chosen.item?.rarity||'—')}</span></div>`:'';
   const hero=chosen?`<div class="gApprovedHero ${chosen.material?'gApprovedMaterialHero':'gApprovedEquipmentHero'}" style="${pos(405,177,700,325)}">${entryView(chosen,ctx,true)}</div>`:'';
   const sheet=state.sheet&&chosen&&!chosen.material?`<section class="gApprovedSheet" aria-label="Ficha del objeto"><button class="gApprovedSheetClose" id="gApprovedSheetClose">×</button><h2>${esc(chosen.name)}</h2><p>${esc(chosen.item?.rarity||'')}</p><h3>Canales del objeto</h3>${(chosen.item?.channels||[]).map((c,i)=>{const metric=ctx.metricForChannel?.(chosen.item,c,i);return `<div><span>${esc(metric?.label||c[0])}</span><b>${esc(metric?.display??c[1])}</b></div>`}).join('')}<h3>Materiales utilizados</h3>${(chosen.item?.formula?.materials||[]).map(m=>`<div><span>${esc(m.material)}</span><b>${Number(m.qty)||0}×</b></div>`).join('')}</section>`:'';
   const body=familyButtons+slots+hero+info+
     (state.family==='Materiales'?'<div class="gApprovedMaterialRotationMask" aria-hidden="true"></div><div class="gApprovedMaterialFichaMask" aria-hidden="true"></div>':'')+
     `<button type="button" class="gApprovedInfoButton" id="gApprovedInfoButton" aria-label="Consultar ficha del objeto" style="${pos(1170,437,410,57)}" ${chosen&&!chosen.material?'':'disabled'}></button>`+
     `<button type="button" class="gApprovedPagePrev" id="gApprovedPagePrev" style="${pos(1482,845,45,25)}" ${state.page===0?'disabled':''} aria-label="Página anterior">‹</button>`+
     `<button type="button" class="gApprovedPageNext" id="gApprovedPageNext" style="${pos(1535,845,45,25)}" ${state.page===maxPage?'disabled':''} aria-label="Página siguiente">›</button>`+sheet;
   const board=mount('Inventario',ctx,nav,body,`data-family="${esc(state.family)}"`);if(!board)return;
   board.querySelectorAll('[data-family]').forEach(b=>b.onclick=()=>{state.family=b.dataset.family;state.page=0;state.selected=null;state.sheet=false;inventory(ctx,nav)});
   board.querySelectorAll('[data-slot]').forEach(b=>b.onclick=()=>{state.selected=page[Number(b.dataset.slot)]?.key||null;state.sheet=false;inventory(ctx,nav)});
   const details=board.querySelector('#gApprovedInfoButton');if(details)details.onclick=()=>{if(!chosen||chosen.material)return;state.sheet=true;inventory(ctx,nav)};
   const sheetClose=board.querySelector('#gApprovedSheetClose');if(sheetClose)sheetClose.onclick=()=>{state.sheet=false;inventory(ctx,nav)};
   board.querySelector('#gApprovedPagePrev').onclick=()=>{state.page--;state.selected=null;inventory(ctx,nav)};
   board.querySelector('#gApprovedPageNext').onclick=()=>{state.page++;state.selected=null;inventory(ctx,nav)};
 }
 function preparation(ctx,nav){
   const stock=Object.entries(ctx.inventory||{}).filter(([,q])=>Number(q)>0);
   const basic=stock.filter(([name])=>!/^(Lingote|Material preparado|Material tratado)/i.test(name)).slice(0,10);
   const treated=stock.filter(([name])=>/^(Lingote|Material preparado|Material tratado)/i.test(name)).slice(0,10);
   const slots=[...basic,...Array(Math.max(0,10-basic.length)).fill(null),...treated,...Array(Math.max(0,10-treated.length)).fill(null)];
   const raw=Number(ctx.inventory?.['Mineral de hierro']||0);
   // In the iron preparation tutorial, only RAW IRON ORE is a selectable input.
   // The product preview is the ingot, independent of the currently selected slot.
   if(ctx.selectedMaterial!=='Mineral de hierro')ctx.selectedMaterial='Mineral de hierro';
   const cells=slots.map((entry,i)=>{
     const x=38+(i%5)*105,y=(i<10?249:588)+(Math.floor(i%10/5))*103;
     const eligible=!!entry&&entry[0]==='Mineral de hierro'&&raw>0;
     return entry?`<button type="button" class="gApprovedPrepSlot ${eligible?'gPrepEligible':'gPrepLocked'}" ${eligible?'data-prep-raw="1"':'disabled'} style="${pos(x,y,90,88)}" aria-label="${esc(entry[0])}">${materialVisual(entry[0],false)}<b>${Number(entry[1])}</b></button>`:'';
   }).join('');
   const product=`<div class="gApprovedPrepProduct" role="img" aria-label="Resultado de preparación: Lingote de hierro" style="${pos(765,225,390,390)}">${materialVisual('Lingote de hierro',true)}</div>`;
   const data=`<div class="gApprovedPrepData" style="${pos(1245,203,340,487)}"><h3>Preparación de hierro</h3><p>Mineral disponible: <b>${raw}</b></p><p>Lingotes: <b>${Number(ctx.inventory?.['Lingote de hierro']||0)}</b></p><div class="gApprovedPrepQty"><button id="gPrepMinus" aria-label="Reducir cantidad">−</button><strong>${ctx.count||0}</strong><button id="gPrepPlus" aria-label="Aumentar cantidad">+</button></div><p>Elegí la cantidad para la tanda. La preparación no modifica la rareza.</p></div>`;
   const action=`<button type="button" class="gApprovedPrepAction" id="gPrepAction" style="${pos(1244,714,357,96)}" aria-label="Preparar" ${raw>0?'':'disabled'}></button>`;
   const board=mount('Preparacion',ctx,nav,cells+product+data+action,'data-prep-output="Lingote de hierro"');if(!board)return;
   board.querySelector('#gPrepMinus').onclick=()=>{ctx.count=Math.max(1,(ctx.count||1)-1);preparation(ctx,nav)};
   board.querySelector('#gPrepPlus').onclick=()=>{ctx.count=Math.min(raw,(ctx.count||0)+1);preparation(ctx,nav)};
   board.querySelector('#gPrepAction').onclick=nav.start;
   board.querySelectorAll('[data-prep-raw]').forEach(b=>b.onclick=()=>{
     ctx.selectedMaterial='Mineral de hierro';
     preparation(ctx,nav); // Stay on Preparación; never jump to Inventario.
   });
 }
 function renderThermal(ctx,nav,controls){
   const work=ctx?.work;
   if(!work||!controls)return false;
   const gauge=`<div class="gPrepThermalGauge" id="prepHeatGauge" role="meter" aria-label="Temperatura de la fragua" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(work.temperature)}" style="background:${controls.gradient}">
     <span class="gPrepThermalTarget" style="left:${work.target}%"></span>
     <span class="gPrepThermalNeedle" id="prepHeatNeedle"></span>
   </div>`;
   const panel=`<section class="gPrepThermalPanel" style="${pos(620,216,576,565)}" aria-label="Control térmico de la fragua">
     <h2>CONTROL DE LA FRAGUA</h2>
     <p>Mantené la temperatura cerca del verde para preparar el lingote.</p>
     ${gauge}
     <div class="gPrepThermalLegend"><span>FRÍO</span><span>IDEAL</span><span>CALIENTE</span></div>
     <div class="gPrepThermalProgressHeader"><span>AVANCE DE PREPARACIÓN</span><b id="prepCraftNumber">0.0 / 100</b></div>
     <div class="gPrepThermalProgressBar"><span id="prepCraftProgress" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" aria-label="Avance de preparación"></span></div>
     <div class="gPrepThermalBellows">${controls.bellows.map((p,i)=>`<button type="button" id="prepBellow${i}" aria-label="Fuelle ${esc(p.label.toLowerCase())}"><b>${esc(p.label)}</b><small>${esc(p.description)}</small><em>${esc(p.key)}</em></button>`).join('')}</div>
     <p class="gPrepThermalNote">El avance es continuo. Sin pulsar, la fragua se enfría.</p>
   </section>`;
   const details=`<section class="gPrepThermalDetails" style="${pos(1220,210,380,505)}">
     <h3>PREPARACIÓN EN CURSO</h3>
     <div><span>Producto</span><b>Lingote de hierro</b></div>
     <div><span>Lote</span><b>${work.count}</b></div>
     <div><span>Dificultad</span><b>${Math.round(work.batch.difficultyMultiplier*100)} %</b></div>
     <div><span>Temperatura</span><b id="prepHeatNumber">${Math.round(work.temperature)} / 100</b></div>
     <div><span>Objetivo</span><b>${Math.round(work.target)} / 100</b></div>
     <div><span>Intervenciones</span><b id="prepActions">0</b></div>
     <p class="gPrepThermalMessage" id="prepHeatMessage" aria-live="polite"></p>
     <p class="gPrepThermalEffectiveness" id="prepActionPoints" aria-live="polite"></p>
     <button type="button" id="prepAbandon">Cancelar tanda sin consumir mineral</button>
   </section>`;
   const board=mount('Preparacion',ctx,nav,panel+details,'data-prep-stage="running"');if(!board)return false;
   board.classList.add('gApproved-Thermal');
   board.querySelectorAll('.gApprovedHit:not([data-go="Cerrar"])').forEach(button=>button.disabled=true);
   controls.bellows.forEach((power,i)=>{
     const button=board.querySelector('#prepBellow'+i);
     if(button)button.onclick=()=>controls.intervene(power.key);
   });
   board.querySelector('#prepAbandon').onclick=controls.abandon;
   return true;
 }
 function renderResult(ctx,nav,opts){
   const work=opts?.work;
   if(!work)return false;
   const success=!!opts.success;
   const stock=Object.entries(ctx.inventory||{}).filter(([,qty])=>Number(qty)>0);
   const basics=stock.filter(([name])=>!/^(Lingote|Material preparado|Material tratado)/i.test(name)).slice(0,10);
   const prepared=stock.filter(([name])=>/^(Lingote|Material preparado|Material tratado)/i.test(name)).slice(0,10);
   const cells=[...basics,...Array(Math.max(0,10-basics.length)).fill(null),...prepared,...Array(Math.max(0,10-prepared.length)).fill(null)].map((entry,i)=>{
     if(!entry)return '';
     const x=38+(i%5)*105,y=(i<10?249:588)+(Math.floor(i%10/5))*103;
     return `<div class="gApprovedPrepSlot gPrepResultSlot" style="${pos(x,y,90,88)}" aria-label="${esc(entry[0])}: ${Number(entry[1])}">${materialVisual(entry[0],false)}<b>${Number(entry[1])}</b></div>`;
   }).join('');
   const headline=success?'Preparación completada':'Lote no aplicado';
   const center=`<div class="gApprovedPrepResultDisplay" style="${pos(750,205,397,460)}">
     ${success?materialVisual('Lingote de hierro',true):''}
     <div class="gPrepResultHeadline">${success?'✓':'!'} ${headline}</div>
     <p>${success?esc(work.count+' lingote'+(work.count===1?'':'s')+' incorporados al inventario.'):'El inventario cambió durante la tanda.'}</p>
   </div>`;
   const info=`<section class="gApprovedPrepResultInfo" style="${pos(1215,205,378,502)}" aria-label="Resultado de preparación">
     <h2>RESULTADO DE LA TANDA</h2><h3>${success?'Lingotes preparados':'Preparación interrumpida'}</h3>
     <div><span>Mineral restante</span><b>${Number(ctx.inventory?.['Mineral de hierro']||0)}</b></div>
     <div><span>Lingotes listos</span><b>${Number(ctx.inventory?.['Lingote de hierro']||0)}</b></div>
     <div><span>Intervenciones</span><b>${Number(work.clicks||0)}</b></div>
     <button id="prepResultBack">Volver a Preparación</button>
     <button id="prepResultClose">Cerrar menú</button>
   </section>`;
   const board=mount('Preparacion',ctx,nav,cells+center+info,'data-prep-stage="result"');if(!board)return false;
   board.classList.add('gApproved-PrepResult');
   board.querySelectorAll('.gApprovedHit:not([data-go="Cerrar"])').forEach(button=>button.disabled=true);
   board.querySelector('#prepResultBack').onclick=opts.back;
   board.querySelector('#prepResultClose').onclick=opts.close;
   return true;
 }
 function fabrications(ctx,nav){
   const catalog=typeof ctx.getRecipeCatalog==='function'?(ctx.getRecipeCatalog()||[]):[];
   const recipes=catalog.filter(r=>r&&r.id&&r.formula);
   const ids=new Set(recipes.map(r=>String(r.id)));
   // Q2/Q3: espada; Q5/Q6: escudo. When Ordan advances the quest, switch
   // recipe automatically instead of leaving the previous (blocked) selection.
   const activeId=String(ctx.activeRecipeId||'');
   if(ctx.genesisApprovedQuestRecipe!==activeId){
     ctx.genesisApprovedQuestRecipe=activeId;
     ctx.selectedRecipeId=ids.has(activeId)?activeId:recipes[0]?.id||null;
   }
   if(!ids.has(String(ctx.selectedRecipeId)))ctx.selectedRecipeId=ids.has(activeId)?activeId:recipes[0]?.id||null;
   const chosen=recipes.find(r=>String(r.id)===String(ctx.selectedRecipeId))||null;
   const formula=chosen?.formula||ctx.formula;
   const req=formula?.materials||[];
   const ready=req.length>0&&req.every(r=>Number(ctx.inventory?.[r.material]||0)>=Number(r.qty||0));
   const canCraft=chosen?(ctx.canCraftRecipe?.(chosen.id)===true):ctx.canCraftNow?.()===true;
   const isShield=/escud/i.test(String(chosen?.id||chosen?.subfamily||''));
   const isSword=/espad/i.test(String(chosen?.id||chosen?.subfamily||''));
   const chosenName=chosen?.subfamily||ctx.recipeName||'Sin receta';
   const recipeButtons=recipes.map((r,i)=>{
     const isS=/escud/i.test(String(r.id)+' '+String(r.subfamily));
     return `<button type="button" class="gApprovedRecipe ${String(ctx.selectedRecipeId)===String(r.id)?'is-selected':''}" data-recipe="${esc(r.id)}" style="${pos(93,isS?465:289,336,53)}" aria-label="Seleccionar ${esc(r.subfamily)}"></button>`;
   }).join('');
   // Every material of the generated recipe must be visible; never show only
   // the first two when seeded formulas contain three or four inputs.
   const compact=req.length>2;
   const rows=Array.from({length:Math.max(2,Math.min(4,req.length))},(_,i)=>{
     const r=req[i],y=compact?286+i*76:300+i*143,h=compact?74:115;
     if(!r)return `<div class="gApprovedRequired" style="${pos(1261,y,350,h)}"></div>`;
     const qty=Number(ctx.inventory?.[r.material]||0),needed=Number(r.qty||0);
     return `<div class="gApprovedRequired ${compact?'is-compact':''} ${qty>=needed?'is-supplied':'is-missing'}" style="${pos(1261,y,350,h)}"><h3>${esc(r.material)}</h3><p>Requerido: <b>${needed}</b></p><p>Stock real: <b>${qty}</b></p></div>`;
   }).join('');
   const state=`<div class="gApprovedCraftState ${ready&&canCraft?'is-ready':'is-blocked'}" style="${pos(1290,610,292,51)}">${ready&&canCraft?'✓ Disponible':ready?'Receta todavía bloqueada':'Faltan materiales'}</div>`;
   const hero=isShield?`<div class="gApprovedRecipeHeroSwap" style="${pos(456,114,643,706)}">${ctx.recipeAsset?.(chosen?.id)||''}<span>${esc(chosenName)}</span></div>`:'';
   const title=isShield?`<div class="gApprovedRecipeTitle" style="${pos(1153,120,432,85)}"><h2>${esc(chosenName)}</h2><p>Receta conocida</p></div>`:'';
   const body=recipeButtons+rows+state+hero+title+
     `<button type="button" class="gApprovedCraftAction" id="gApprovedCraftAction" style="${pos(1148,672,435,100)}" aria-label="Fabricar ${esc(chosenName)}" ${ready&&canCraft?'':'disabled'}></button>`;
   const board=mount('Fabricaciones',ctx,nav,body,`data-recipe="${esc(chosen?.id||'')}"`);if(!board)return;
   board.querySelectorAll('[data-recipe]').forEach(b=>b.onclick=()=>{ctx.selectedRecipeId=b.dataset.recipe;fabrications(ctx,nav)});
   board.querySelector('#gApprovedCraftAction').onclick=nav.craft;
 }
 function render(ctx,nav,tab){
   if(!ctx||!nav)return false;
   if(tab==='Inventario')inventory(ctx,nav);
   else if(tab==='Preparacion')preparation(ctx,nav);
   else if(tab==='Fabricaciones')fabrications(ctx,nav);
   else return false;
   return true;
 }
 window.GenesisApprovedUI=Object.freeze({render,renderThermal,renderResult,ARTS,BUILD});
})();
