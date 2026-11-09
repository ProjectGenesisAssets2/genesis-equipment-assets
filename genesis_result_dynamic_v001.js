/* Project Genesis · Resultado de Creaciones V4 · prueba aislada
   El objeto y los canales provienen exclusivamente del cierre real del motor.
   ORA PNG son piezas opcionales. Si faltan en el repo no se inventa otro arte.
*/
(function(root){
  "use strict";
  const ORDER={
    Base:["01_Base.png","#cc9c55"],Luz:["02_Luz.png","#f8cf68"],
    Sombra:["03_Sombra.png","#9d69eb"],Fuego:["04_Fuego.png","#f47737"],
    Hielo:["05_Hielo.png","#4dcfe9"],Naturaleza:["06_Naturaleza.png","#72c96d"],
    Tierra:["07_Tierra.png","#b98a61"],Rayo:["08_Rayo.png","#b68aff"]
  };
  const rootArt="assets/ui/resultado/oras/";
  const approvedSwordPoster="./assets/playcanvas/approved/equipment/espada_v03_hierro_v175_v12b_cycles_hdri32.png";
  const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const normalName=n=>n==="Daño"||n==="Protección"?"Base":n;
  const normalize=(item)=>{
    if(!item || !Array.isArray(item.channels))throw Error("Resultado V4: falta item.channels del motor");
    const seen=new Set();
    const channels=item.channels.map((raw,i)=>{
      const name=normalName(Array.isArray(raw)?String(raw[0]||""):String(raw?.name||raw?.nombre||raw?.id||""));
      const value=Number(Array.isArray(raw)?raw[1]:raw?.value??raw?.valor);
      if(!ORDER[name]||seen.has(name)||!Number.isFinite(value)||value<0)throw Error("Resultado V4: canal inválido/duplicado "+name);
      seen.add(name);
      // Demo V016: las técnicas/estados secundarios (Quemadura, Veneno, etc.)
      // están excluidos. Solo existen canales elementales reales, sin subfilas.
      return {key:name,value,sequence:i,techniques:[]};
    });
    if(!channels.length)throw Error("Resultado V4: fabricación sin Canal Base");
    const savedBase=channels[0].key==="Base";
    if(!savedBase)throw Error("Resultado V4: primer canal no es Base");
    return {id:String(item.id||""),name:String(item.name||item.nombre||"Objeto"),
      rarity:String(item.rarity||item.rareza||"Inútil"),recipe:String(item.recipe||item.recetaId||""),
      channels,description:String(item.description||item.descripcionNGE||""),
      asset:typeof item.modelAsset==="string"?item.modelAsset:
        typeof item.asset?.glb==="string"?item.asset.glb:"",
      source:item};
  };
  const approvedModel=(s)=>{
    // V12B es una aprobación visual de materiales, NO permiso para redistribuir fuente Fab.
    // Exigimos un manifiesto de exportación aprobado y derechos de distribución confirmados.
    if(s.recipe!=="espada_hierro")return false;
    const e=root.GenesisApprovedRuntimeModels?.espada_hierro;
    return !!(e && e.status==="approved" && e.gameExportApproved===true &&
      e.distributionRightsConfirmed===true &&
      e.sourceSha256==="e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b" &&
      /^[a-f0-9]{64}$/.test(e.exportSha256||"") && e.exportSha256!==e.sourceSha256 &&
      e.materialPreset==="Genesis_Espada_V03_Hierro_V175_V12B" &&
      e.url===s.asset &&
      /^\.?\/?assets\/playcanvas\/approved\/equipment\/[\w/-]+\.glb$/i.test(s.asset) &&
      !s.asset.includes(".."));
  };
  function viewer(s,renderAsset){
    if(approvedModel(s)){
      const poster=s.recipe==="espada_hierro"?approvedSwordPoster:"";
      return '<model-viewer data-result-approved-glb="true" src="'+esc(s.asset)+'"'+
        (poster?' poster="'+esc(poster)+'"':'')+
        ' camera-controls interaction-prompt="none" shadow-intensity=".75" environment-image="neutral" exposure="1.16" camera-orbit="25deg 75deg auto" alt="'+esc(s.name)+'"></model-viewer>'+
        '<span class="grViewerStatus" aria-live="polite">Modelo GLB aprobado · arrastrá para rotar</span>';
    }
    if(s.recipe==="espada_hierro")return '<iframe class="grSwordInteractive" data-sword-v12b="true" src="./genesis_sword_runtime_v001.html?v=016001" title="Inspección interactiva 3D de la espada V175 V12B" allow="fullscreen"></iframe>'+
      '<span class="grViewerStatus" aria-live="polite">V12B · Arrastrá para girar · Rueda para zoom · Fuente 3D real experimental</span>';
    // Para otros objetos, emplear exclusivamente el adaptador del juego.
    const fallback=typeof renderAsset==="function"?renderAsset(s.source):"";
    return '<div class="grOtherItem">'+fallback+'</div><span class="grViewerStatus">Visual del objeto del inventario</span>';
  }
  function row(c){
    const [file,color]=ORDER[c.key];

    return '<div class="grChannelGroup" data-result-channel="'+esc(c.key)+'" data-result-value="'+esc(c.value)+'">'+
      '<div class="grChannelRow" style="--grColor:'+color+'">'+
       '<img class="grOra" src="'+rootArt+file+'" alt="" aria-hidden="true" loading="eager">'+
       '<div class="grChannelFallback" aria-hidden="true"></div>'+
       '<span class="grChannelLabel">'+esc(c.key)+'</span>'+
       '<strong class="grChannelNumber">'+esc(c.value)+'</strong>'+
      '</div></div>';
  }
  function html(item,renderAsset){
    const s=normalize(item);
    return '<div class="grScreen" data-result-id="'+esc(s.id)+'" data-result-recipe="'+esc(s.recipe)+'">'+
      '<div class="grLeft"><div class="grSectionLabel">RESULTADO DE FABRICACIÓN</div>'+
       '<div class="grViewer" role="group" aria-label="Objeto fabricado">'+viewer(s,renderAsset)+'</div>'+
       '<div class="grViewerFooter">VISOR DE OBJETO · '+esc(s.rarity.toUpperCase())+'</div></div>'+
      '<div class="grRight"><div class="grHeader"><div class="grHeading">'+esc(s.name)+'</div><span class="grRarity">'+esc(s.rarity)+'</span></div>'+
       '<div class="grChannelTitle">CANALES OBTENIDOS <small>'+s.channels.length+' ACTIVOS</small></div>'+
       '<div class="grChannelScroll" aria-label="Canales de esta fabricación">'+s.channels.map(row).join("")+'</div>'+
       '<div class="grDescription"><strong>RELATO DE NGE</strong><p>'+esc(s.description||"Sin descripción NGE registrada.")+'</p></div>'+
       '<div class="grControls"><button type="button" id="resultContinue">CONTINUAR</button></div></div></div>';
  }
  function decorate(modalElement,item,renderAsset){
    if(!modalElement||!item)return false;
    const s=normalize(item);
    modalElement.classList.add("genesisResultModal");
    modalElement.innerHTML=html(item,renderAsset);
    modalElement.querySelectorAll(".grOra").forEach(img=>{
      img.addEventListener("load",()=>{
        img.closest(".grChannelRow")?.classList.add("grHasOra");
      },{once:true});
      img.addEventListener("error",()=>{img.hidden=true;},{once:true});
      if(img.complete && img.naturalWidth>0)img.closest(".grChannelRow")?.classList.add("grHasOra");
      else if(img.complete)img.hidden=true;
    });
    const mv=modalElement.querySelector("model-viewer");
    if(mv)mv.addEventListener("error",()=>{
      const box=mv.closest(".grViewer");
      if(!box)return;
      if(s.recipe==="espada_hierro"){
        box.innerHTML='<img class="grSwordPoster" src="'+esc(approvedSwordPoster)+'" alt="Render original V175/V12B">'+
          '<span class="grViewerStatus" role="status">GLB no disponible · render original conservado</span>';
      }else{
        box.innerHTML='<p class="grViewerError">No se pudo cargar el modelo aprobado.</p>';
      }
    },{once:true});
    return true;
  }
  root.GenesisResultDynamic=Object.freeze({normalize,html,decorate,ORDER,version:"V4.1-experimental"});
})(typeof window!=="undefined"?window:globalThis);
