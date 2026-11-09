
/* Genesis Inventory: geometría 1:1 del arte limpio aprobado 1672×941, datos LIVE. */
(function () {
  'use strict';
  const ROOT = 'assets/ui/preparacion/01_Capas/';
  const APPROVED_ART='assets/ui/inventario/INVENTARIO_BASE_LIMPIA_APROBADA_16x9.png';
  let approvedArtPromise=null;
  function installApprovedArt(board){
    if(!approvedArtPromise)approvedArtPromise=new Promise(function(resolve,reject){
      const image=new Image();
      image.onload=function(){
        if(image.naturalWidth!==1672||image.naturalHeight!==941){
          reject(new Error('Inventario aprobado: dimensiones de imagen inesperadas'));
          return;
        }
        resolve(APPROVED_ART);
      };
      image.onerror=function(){reject(new Error('No se encontró el PNG limpio original del Inventario'))};
      image.src=APPROVED_ART;
    });
    approvedArtPromise.then(function(url){
      if(!board.isConnected)return;
      board.style.backgroundImage='url("'+url+'")';
      board.style.backgroundSize='100% 100%';
      board.classList.add('genInvCanonical');
      board.dataset.approvedArt='original-1672x941';
    }).catch(function(err){console.warn('[Genesis Inventory] Fallback visual sin arte aprobado:',err)});
  }
  const TABS = [
    ['Inventario','Pestanas/Pestana_Inventario.png'],
    ['Preparacion','Pestanas/Pestana_Preparacion.png'],
    ['Fabricaciones','Pestanas/Pestana_Fabricaciones.png'],
    ['Comparacion','Pestanas/Pestana_Comparacion.png']
  ];
  const posters = {
    'Mineral de hierro':'assets/playcanvas/approved/materials/iron_ore/v008_55k_pbr1536_v007/mineral_hierro_v008_transparent_0.png',
    'Lingote de hierro':'assets/playcanvas/approved/materials/iron/v175/iron_v175_transparent.png',
    'Carbón vegetal':'assets/playcanvas/approved/materials/charcoal/v011/carbon_vegetal_v011_poster.png',
    'Madera seca de roble':'assets/playcanvas/approved/materials/oak/v004/madera_roble_v004_poster.png',
    'Madera seca de fresno':'assets/playcanvas/approved/materials/ash/v004/madera_fresno_v004_poster.png',
    'Cuero bovino curtido':'assets/playcanvas/approved/materials/leather_bovine/v003/cuero_bovino_v003_poster.png',
    'Cuero caprino curtido':'assets/playcanvas/approved/materials/leather_caprine/v003/cuero_caprino_v003_poster.png',
    'Cordel de cáñamo':'assets/playcanvas/approved/materials/hemp/v018/cordel_canamo_v018_poster.jpg',
    'Hilo de lino':'assets/playcanvas/approved/materials/linen/v021/hilo_lino_v021_poster.jpg'
  };
  // GLB de las mismas versiones aprobadas o referenciadas en el inventario.
  // Roble/fresno/cueros: candidatas aisladas hasta validación visual y runtime.
  // Lingote V175 mantiene poster hasta disponer del GLB final aprobado.
  const models = Object.freeze({
    'Mineral de hierro':'assets/playcanvas/approved/materials/iron_ore/v008_55k_pbr1536_v007/mineral_hierro_v008_55k_pbr1536_v007.glb',
    'Carbón vegetal':'assets/playcanvas/approved/materials/charcoal/v011/carbon_vegetal_v011_final_3_piezas_web.glb',

    'Cordel de cáñamo':'assets/playcanvas/approved/materials/cordel_canamo/v018/cordel_canamo_v018.glb',
    'Hilo de lino':'assets/playcanvas/approved/materials/hilo_lino/v021/hilo_lino_v021.glb'
  });
  function esc(x) {
    return String(x == null ? '' : x).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]});
  }
  function classify(item) {
    // The object owns its actual family. Fallback is the existing recipe name,
    // never a fixed per-profession menu list.
    const raw=String(item.family || item.recipeFamily || item.recipe || item.category || 'Creaciones').trim();
    if (/^espada(s)?\b/i.test(raw)) return 'Espadas';
    if (/^escudo(s)?\b/i.test(raw)) return 'Escudos';
    return raw;
  }
  function channelSummary(item) {
    const channels=Array.isArray(item.channels)?item.channels:[];
    if(!channels.length)return '<p class="genInvEmptyChannels">Este objeto todavía no tiene canales registrados.</p>';
    return channels.map(function(c,index){
      const name=Array.isArray(c)?c[0]:(c.name||c.channel||'');
      const intensity=Array.isArray(c)?c[1]:c.intensity;
      const text=Number.isFinite(Number(intensity))?String(intensity):'';
      return '<div class="genInvChannel"><span>'+esc(index===0 && String(name).toLowerCase()==='base'?'Canal base':name)+'</span><b>'+esc(text)+'</b></div>';
    }).join('');
  }
  function storySummary(item) {
    const candidates=[item.nge?.story,item.nge?.description,item.ngeStory,item.narrative,item.description,item.history];
    const found=candidates.find(function(v){return typeof v==='string' && v.trim()});
    return found?'<p class="genInvNgeText">'+esc(found)+'</p>':
      '<p class="genInvNgeText genInvNoStory">Sin relato NGE disponible en este objeto.</p>';
  }
  function familyItems(ctx) {
    const all=typeof ctx.getItems==='function' ? (ctx.getItems() || []) : [];
    return all.filter(Boolean);
  }
  function materialArt(name, hero) {
    const poster=posters[name];
    const model=models[name];
    // GenesisDevice intentionally avoids model-viewer on mobile to protect the
    // shared PlayCanvas WebGL budget. Preserve the real model on desktop,
    // and show the registered static poster instead of a blank mobile viewport.
    if(hero&&model&&!window.GenesisDevice?.safePreviews){
      // Camera closeup only: the approved meshes, UVs and PBR remain byte-identical.
      // 50% camera radius magnifies the source GLB within the established ORA window.
      const heroOrbit='0deg 75deg 50%';
      // El visor renderiza geometría 3D, NO una perspectiva CSS sobre un JPG.
      // Las fibras no muestran el JPG opaco ni siquiera como póster de carga.
      const fallbackPoster=/^(Cordel de cáñamo|Hilo de lino)$/.test(name)?'':(poster?' poster="'+esc(poster)+'"':'');
      return '<model-viewer class="genInvMaterialHeroModel" data-material-name="'+esc(name)+'" src="'+esc(model)+'"'+fallbackPoster+
        ' loading="eager" reveal="auto" camera-controls interaction-prompt="none" camera-orbit="' + heroOrbit + '" field-of-view="30deg" environment-image="neutral" shadow-intensity="0" exposure="1.22" alt="'+esc(name)+'"></model-viewer>';
    }
    return poster ? '<img class="'+(hero?'genInvMaterialHero':'genInvMaterialThumb')+'" src="'+esc(poster)+'" alt="'+esc(name)+'" draggable="false">' :
      '<span class="genInvEmptyPreview">'+esc(name)+'</span>';
  }
  function render(ctx, nav) {
    const inventory=ctx.inventory || {};
    const allItems=familyItems(ctx);
    const stock=Object.entries(inventory).filter(function(pair){return Number(pair[1])>0});
    const families=[...(stock.length?['Materiales']:[]),...new Set(allItems.map(classify).filter(Boolean))];
    const state=ctx.genInvState || (ctx.genInvState={family:'Materiales',page:0,search:''});
    if(!families.includes(state.family))state.family=families[0]||'Materiales';
    const materialMode=state.family==='Materiales';
    const source=materialMode?stock.map(function(pair){return {key:'material:'+pair[0],name:pair[0],qty:Number(pair[1]),material:true}}):
      allItems.map(function(i,index){return {key:'creation:'+String(i.id||i.uuid||index)+':'+index,name:i.name,rarity:i.rarity,item:i,material:false}}).filter(function(e){return classify(e.item)===state.family});
    const search=state.search.toLocaleLowerCase();
    const filtered=source.filter(function(e){return String(e.name).toLocaleLowerCase().includes(search)});
    const pages=Math.max(1,Math.ceil(filtered.length/20));
    state.page=Math.max(0,Math.min(state.page,pages-1));
    const visible=filtered.slice(state.page*20,(state.page+1)*20);
    if(!visible.some(function(v){return v.key===state.selectedKey}))state.selectedKey=visible[0]?.key||null;
    const chosen=visible.find(function(e){return e.key===state.selectedKey})||visible[0];
    const navMarkup=TABS.map(function(t){
      return '<button class="genInvTab" data-nav="'+esc(t[0])+'" aria-current="'+(t[0]==='Inventario'?'page':'false')+'" aria-label="'+esc(t[0])+'"><img src="'+ROOT+t[1]+'" alt="'+esc(t[0])+'"></button>';
    }).join('');
    const familiesMarkup=families.map(function(f){
      const icon=f==='Materiales'?'◆':f==='Espadas'?'⚔':f==='Escudos'?'◈':'✦';
      return '<button class="genInvFamily" data-family="'+esc(f)+'" aria-pressed="'+(f===state.family)+'"><span class="genInvFamIcon">'+icon+'</span><span>'+esc(f)+'</span></button>';
    }).join('');
    const item=chosen?.item;
    const viewer=chosen?(materialMode?materialArt(chosen.name,true):
      (typeof ctx.renderAsset==='function'?ctx.renderAsset(item):'<span class="genInvEmptyPreview">'+esc(chosen.name)+'</span>')) :
      '<p class="genInvEmptyPreview">La familia seleccionada no contiene objetos</p>';
    const title=chosen?esc(chosen.name):'Seleccioná un objeto';
    const facts=chosen?(materialMode?
      '<div class="genInvInfoLine"><span>Nombre</span><b>'+esc(chosen.name)+'</b></div>'+
      '<div class="genInvInfoLine"><span>Familia</span><b>Materiales</b></div>'+
      '<div class="genInvInfoLine"><span>Rareza</span><b>—</b></div>'+
      '<div class="genInvChannels" role="list"><div class="genInvChannel"><span>Cantidad disponible</span><b>'+esc(chosen.qty)+'</b></div></div>':
      '<div class="genInvInfoLine"><span>Nombre</span><b>'+esc(chosen.name)+'</b></div>'+
      '<div class="genInvInfoLine"><span>Familia</span><b>'+esc(state.family)+'</b></div>'+
      '<div class="genInvInfoLine"><span>Rareza</span><b>'+esc(item.rarity||'')+'</b></div>'+
      '<h3 class="genInvSubhead">CANALES DEL OBJETO</h3>'+
      '<div class="genInvChannels" role="list">'+channelSummary(item)+'</div>'+
      '<h3 class="genInvSubhead">RELATO NGE</h3>'+storySummary(item)) : '';

    const slots=Array.from({length:20},function(_,i){
      const entry=visible[i];
      if(!entry)return '<button class="genInvSlot" disabled aria-label="Casilla vacía"></button>';
      const selected=entry.key===state.selectedKey;
      const content=entry.material?materialArt(entry.name,false):
        (entry.item.thumbnail || entry.item.poster
          ? '<img src="'+esc(entry.item.thumbnail||entry.item.poster)+'" alt="" loading="lazy" draggable="false">'
          : '<span class="genInvCreationGlyph" aria-hidden="true"></span>');
      return '<button class="genInvSlot'+(selected?' selected':'')+'" data-select="'+i+'" aria-label="'+esc(entry.name)+'" aria-pressed="'+selected+'"><span class="genInvSlotArtwork">'+content+'</span><span class="genInvSlotQty">'+esc(entry.material?entry.qty:(entry.rarity||''))+'</span></button>';
    }).join('');
    const html='<div class="genInv" id="genInv">'+
      '<header class="genInvNav">'+navMarkup+'</header>'+
      '<main class="genInvMain">'+
        '<aside class="genInvFamilies"><h2 class="genInvHead">FAMILIAS</h2>'+familiesMarkup+
          '</aside>'+
        '<section class="genInvViewer"><p class="genInvViewerTitle">'+title+'</p><div class="genInvImageWrap" data-preview-mode="'+(materialMode?'material':'object')+'">'+viewer+'</div><p class="genInvViewLabel">'+(materialMode?'Vista 3D del material':'Objeto fabricado · visor 360°')+'</p></section>'+
        '<aside class="genInvInfo"><h2 class="genInvInfoTitle">INFORMACIÓN</h2>'+facts+
          (chosen&&!materialMode?'<button class="genInvInfoMore" id="genInvDetails"><span>CONSULTAR FICHA DEL OBJETO</span></button>':'')+
          '</aside>'+
        '<section class="genInvGrid"><div class="genInvGridControls"><h2 class="genInvGridTitle">'+esc(state.family)+'</h2>'+
          '<input class="genInvFilter" id="genInvFilter" aria-label="Filtrar objetos" placeholder="Filtrar '+(materialMode?'materiales':'creaciones')+'..." value="'+esc(state.search)+'">'+
          '<span class="genInvNotice">'+filtered.length+' tipos registrados</span></div>'+
          '<div class="genInvSlots">'+slots+'</div>'+
          '<div class="genInvPage" data-pages="'+pages+'"><button id="genInvPrev" '+(state.page===0?'disabled':'')+'>◀</button>'+
          '<span>Página '+(state.page+1)+' / '+pages+'</span><button id="genInvNext" '+(state.page===pages-1?'disabled':'')+'>▶</button></div></section>'+
      '</main></div>';
    ctx.modal(html,'preparationModal genInvModal');
    const board=document.querySelector('#genInv');
    if(!board)return;
    installApprovedArt(board);
    board.querySelectorAll('[data-nav]').forEach(function(b){b.onclick=function(){
      if(b.dataset.nav==='Preparacion')nav.renderMenu();
      else if(b.dataset.nav!=='Inventario')nav.renderWorkspace(b.dataset.nav);
    }});
    board.querySelectorAll('[data-family]').forEach(function(b){b.onclick=function(){
      state.family=b.dataset.family;state.page=0;state.selectedKey=null;state.search='';render(ctx,nav);
    }});
    board.querySelectorAll('[data-select]').forEach(function(b){b.onclick=function(){
      state.selectedKey=visible[Number(b.dataset.select)]?.key;render(ctx,nav);
    }});

    // Solo la geometría REAL gira dentro de la casilla ±45 grados.
    // Un poster estático jamás se simula como objeto 3D; modelos de las casillas
    // se montan bajo demanda, evitando ocho contextos WebGL al abrir inventario.
    board.querySelectorAll('.genInvSlot[data-select]').forEach(function(button){
      const art=button.querySelector('.genInvSlotArtwork');
      const entry=visible[Number(button.dataset.select)];
      const source=entry?.material ? models[entry.name] : null;
      if(!art||!source||window.GenesisDevice?.safePreviews)return;
      const initial=art.innerHTML;
      const originalOrbit='0deg 75deg auto';
      function ensure3D(){
        if(art.querySelector('model-viewer')||art.dataset.glbError)return;
        if(!window.customElements?.get('model-viewer')){
          art.dataset.glbError='viewer-library-unavailable';
          return;
        }
        const visual=document.createElement('model-viewer');
        visual.className='genInvMaterialSlotModel';
        visual.src=source;
        visual.setAttribute('loading','eager');
        visual.setAttribute('reveal','auto');
        visual.setAttribute('interaction-prompt','none');
        visual.setAttribute('camera-orbit',originalOrbit);
        visual.setAttribute('field-of-view','30deg');
        visual.setAttribute('environment-image','neutral');
        visual.setAttribute('shadow-intensity','0');
        visual.setAttribute('exposure','1.22');
        visual.setAttribute('alt',entry.name);
        visual.addEventListener('load',function(){art.dataset.glbLoaded='true';},{once:true});
        visual.addEventListener('error',function(){
          art.dataset.glbError='failed-to-load';
          art.innerHTML=initial;
        },{once:true});
        art.style.setProperty('--gen-slot-yaw','0deg');
        art.replaceChildren(visual);
      }
      button.addEventListener('pointerenter',function(e){
        if(e.pointerType!=='touch')ensure3D();
      });
      button.addEventListener('pointermove',function(event){
        if(event.pointerType==='touch')return;
        ensure3D();
        const visual=art.querySelector('model-viewer');
        if(!visual)return;
        const rect=button.getBoundingClientRect();
        if(!rect.width)return;
        const p=Math.max(0,Math.min(1,(event.clientX-rect.left)/rect.width));
        const angle=(-45+90*p).toFixed(1)+'deg';
        visual.setAttribute('camera-orbit',angle+' 75deg auto');
      });
      const reset=function(){
        const visual=art.querySelector('model-viewer');
        if(visual)visual.setAttribute('camera-orbit',originalOrbit);
        art.style.setProperty('--gen-slot-yaw','0deg');
      };
      button.addEventListener('pointerleave',reset);
      button.addEventListener('pointercancel',reset);
      button.addEventListener('blur',reset);
    });

    const heroModel=board.querySelector('.genInvImageWrap model-viewer.genInvMaterialHeroModel');
    if(heroModel){
      heroModel.addEventListener('load',function(){heroModel.dataset.glbLoaded='true';},{once:true});
      heroModel.addEventListener('error',function(){
        const material=heroModel.getAttribute('data-material-name');
        const poster=posters[material];
        heroModel.outerHTML=poster?'<img class="genInvMaterialHero" data-model-error="load" src="'+esc(poster)+'" alt="'+esc(material)+'">':
          '<span class="genInvEmptyPreview">Error al cargar el modelo 3D</span>';
      },{once:true});
    }

    // Autoencuadre no destructivo del póster en el expositor. Únicamente
    // cambia la escala de presentación, no los PNG/JPG originales aprobados.
    const hero=board.querySelector('.genInvImageWrap[data-preview-mode="material"] img.genInvMaterialHero');
    if(hero){
      const fit=function(){
        if(!hero.naturalWidth||!hero.naturalHeight)return;
        const canvas=document.createElement('canvas');
        const d=160, sx=hero.naturalWidth/d, sy=hero.naturalHeight/d;
        canvas.width=d;canvas.height=d;
        const ctx2=canvas.getContext('2d',{willReadFrequently:true});
        if(!ctx2)return;
        ctx2.drawImage(hero,0,0,d,d);
        const rgba=ctx2.getImageData(0,0,d,d).data;
        let transparent=0;
        for(let i=3;i<rgba.length;i+=4)if(rgba[i]<230)transparent++;
        const hasAlpha=transparent>rgba.length/4*0.015;
        // Para JPG, estimar sólo el recorte de exposición a partir del
        // fondo cercano a las esquinas; nunca reescribir los píxeles.
        let base=[0,0,0],corners=[0,d-1,d*(d-1),d*d-1];
        corners.forEach(idx=>{for(let k=0;k<3;k++)base[k]+=rgba[4*idx+k]/4});
        let xmin=d,ymin=d,xmax=0,ymax=0,found=0;
        for(let y=0;y<d;y++)for(let x=0;x<d;x++){
          const i=4*(y*d+x),a=rgba[i+3];
          const delta=Math.hypot(rgba[i]-base[0],rgba[i+1]-base[1],rgba[i+2]-base[2]);
          const filled=hasAlpha?a>52:delta>52;
          if(!filled)continue;
          xmin=Math.min(xmin,x);xmax=Math.max(xmax,x);
          ymin=Math.min(ymin,y);ymax=Math.max(ymax,y);found++;
        }
        if(found<30)return;
        const occupancy=Math.max((xmax-xmin+1)/d,(ymax-ymin+1)/d);
        const zoom=Math.max(1.5,Math.min(5.2,1.30/Math.max(0.12,occupancy)));
        const ox=((xmin+xmax)/2/d-.5);
        const oy=((ymin+ymax)/2/d-.5);
        hero.style.setProperty('--gen-hero-zoom',zoom.toFixed(3));
        hero.style.setProperty('--gen-hero-offset-x',(-ox*zoom*100).toFixed(2)+'%');
        hero.style.setProperty('--gen-hero-offset-y',(-oy*zoom*100).toFixed(2)+'%');
        hero.dataset.fitSource=hasAlpha?'alpha':'corner-color';
        hero.dataset.zoom=zoom.toFixed(3);
      };
      if(hero.complete)fit();else hero.addEventListener('load',fit,{once:true});
    }

    board.querySelector('#genInvPrev').onclick=function(){state.page--;state.selectedKey=null;render(ctx,nav)};
    board.querySelector('#genInvNext').onclick=function(){state.page++;state.selectedKey=null;render(ctx,nav)};
    const input=board.querySelector('#genInvFilter');
    input.onchange=function(){state.search=input.value;state.page=0;state.selectedKey=null;render(ctx,nav)};

    const details=board.querySelector('#genInvDetails');
    if(details&&item)details.onclick=function(){
      const pane=document.createElement('section');pane.className='genInvOverlay';
      ctx.sheetTab='channels';
      pane.innerHTML='<button id="genInvCloseDetails" aria-label="Cerrar ficha">✕ CERRAR</button>'+
        nav.sheetForItem(ctx,item);
      // Public object info never exposes crafting formulas, internal traces, or MU stats.
      pane.querySelector('.workspaceSheetTabs')?.remove();
      const story = [item.nge?.story,item.nge?.description,item.ngeStory,item.narrative,item.description,item.history]
        .find(function(v){return typeof v==='string' && v.trim()});
      const storyBox=pane.querySelector('.workspaceNgeScroll');
      if(storyBox && story) storyBox.textContent=story;
      board.appendChild(pane);
      pane.querySelector('#genInvCloseDetails').onclick=function(){pane.remove()};
    };
  }
  window.GenesisInventory16={render:render,version:'INVENTARIO_16x9_V014031_ORA_APROBADO_1A1',dataSource:'session.inventory + session.getItems'};
})();
