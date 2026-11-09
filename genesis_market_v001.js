/* Project Genesis · V0.14.022 · comerciante en el mercado.
   Reutiliza un personaje del propio juego; ninguna descarga externa ni arte de menús aprobado.
   Catálogo y compras provienen de genesis_market_domain_v001.js.
*/
import { Entity, StandardMaterial, Color } from 'playcanvas';
import './genesis_market_domain_v001.js?v=0.14.022';

const POS = Object.freeze({x:25.5,y:0,z:36.3});
const STALL = Object.freeze({x:28.35,y:0,z:37.6});

function mat(name,r,g,b,gloss=.14){
  const m=new StandardMaterial();m.name=name;
  m.diffuse=new Color(r,g,b);m.gloss=gloss;m.useMetalness=false;m.update();return m;
}
function box(parent,name,x,y,z,w,h,d,material,cast=true){
  const e=new Entity(name);
  e.addComponent('render',{type:'box',material,castShadows:cast,receiveShadows:true});
  e.setLocalPosition(x,y,z);e.setLocalScale(w,h,d);parent.addChild(e);return e;
}
function escapeText(value){
  return String(value==null?'':value).replace(/[&<>"']/g,function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
  });
}
function attachStyle(){
  if(document.getElementById('genesis-market-style-v001'))return;
  const style=document.createElement('style');style.id='genesis-market-style-v001';
  style.textContent=[
   '.genesisMarketModal{width:min(960px,96vw);background:#121516;color:#eddfbb;border:1px solid #685032}',
   '.genesisMarketBoard{padding:clamp(15px,3vw,28px);font-family:system-ui,Arial,sans-serif}',
   '.genesisMarketTop{display:flex;gap:14px;justify-content:space-between;align-items:start}',
   '.genesisMarketTop small{color:#b99760;font-size:11px;letter-spacing:.12em}',
   '.genesisMarketTop h2{font:normal 28px Georgia,serif;margin:5px 0;color:#ead49f}',
   '.genesisMarketBoard p{font-size:13px;line-height:1.5;color:#c8bda8;margin:8px 0 16px}',
   '.genesisMarketGrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;max-height:55vh;overflow:auto;overscroll-behavior:contain}',
   '.genesisMarketCard{border:1px solid #6b5638;background:#222421;padding:13px;min-height:150px;display:flex;flex-direction:column;justify-content:space-between;gap:12px}',
   '.genesisMarketCard strong{font:normal 17px Georgia,serif;color:#f2dfb7;overflow-wrap:anywhere}',
   '.genesisMarketCard small{color:#b6b4aa;font-size:11px}',
   '.genesisMarketQty{display:flex;gap:7px;align-items:center;justify-content:space-between}',
   '.genesisMarketQty button{min-width:33px;height:34px;border:1px solid #9d7d47;background:#302b22;color:#f5dfb3;font-size:19px}',
   '.genesisMarketQty b{font-size:14px}',
   '.genesisMarketBuy{width:100%;background:#46341c;border:1px solid #d4ab65;color:#ffe2aa;padding:10px;font-weight:700;cursor:pointer}',
   '.genesisMarketBuy:hover,.genesisMarketQty button:hover{filter:brightness(1.18)}',
   '.genesisMarketClose{background:#2a2924;border:1px solid #886d48;color:#ebd7b0;padding:9px 14px;cursor:pointer}',
   '.genesisMarketFoot{margin-top:14px;color:#c9aa70;font-size:12px;min-height:20px}',
   '.genesisMarketModal button:focus-visible{outline:2px solid #f1c676;outline-offset:2px}',
   '@media(max-width:580px){.genesisMarketGrid{grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}.genesisMarketCard{padding:9px;min-height:141px}.genesisMarketTop h2{font-size:22px}}'
  ].join('\n');
  document.head.appendChild(style);
}
function buildStall(world){
  const wood=mat('Puesto de mercado - roble usado',.26,.16,.09);
  const edge=mat('Puesto - herrajes envejecidos',.26,.25,.22,.28);
  const flax=mat('Puesto - toldo lino crudo',.60,.52,.38);
  const ochre=mat('Puesto - franjas ocres',.47,.28,.14);
  const crate=mat('Puesto - cajas de transporte',.39,.26,.14);
  const stock=mat('Puesto - sacos con mineral',.24,.22,.18);
  const root=new Entity('Mercado · puesto de suministros provisional');
  world.addChild(root);root.setPosition(STALL.x,STALL.y,STALL.z);
  box(root,'Mesa madera maciza',0,1.02,0,2.35,.17,1.26,wood);
  for(const x of [-.98,.98])for(const z of [-.43,.43]){
    box(root,'Pata estructural',x,.52,z,.13,1.04,.13,wood);
    box(root,'Poste vertical toldo',x,1.82,z,.10,1.75,.10,wood);
  }
  box(root,'Toldo de lona cruda',0,2.72,0,2.84,.13,1.77,flax,false);
  for(const x of [-1.15,-.46,.23,.92]){
    const strip=box(root,'Cinta textil ocre',x,2.795,0,.26,.015,1.68,ochre,false);
  }
  box(root,'Frente madera',0,.86,-.61,2.35,.34,.06,wood);
  box(root,'Herraje frontal',0,.95,-.648,2.15,.035,.014,edge);
  for(const [x,z] of [[-.82,-.18],[.18,.18],[.77,-.08]]){
    box(root,'Caja de materiales del mercado',x,1.24,z,.56,.30,.45,crate);
    box(root,'Saco con material sin etiqueta',x,1.42,z,.40,.13,.30,stock,false);
  }
  box(root,'Cajon inferior',-1.10,.31,.63,.72,.62,.58,crate);
  return root;
}
function buildMerchant(world,source){
  const merchantRoot=new Entity('Mercader de suministros · NPC interactivo V001');
  world.addChild(merchantRoot);merchantRoot.setPosition(POS.x,POS.y,POS.z);
  // Orientado hacia el acceso oeste del mercado, sin bloquear el corredor.
  merchantRoot.setLocalEulerAngles(0,90,0);
  let hasModel=false;
  if(source && typeof source.clone==='function'){
    const character=source.clone();
    character.name='Comerciante - rig humanoide existente';
    merchantRoot.addChild(character);
    character.setLocalPosition(0,0,0);
    character.setLocalEulerAngles(0,180,0);
    character.setLocalScale(1,1,1);
    hasModel=character.findComponents('render').some(c=>c.meshInstances&&c.meshInstances.length);
    // Copias de materiales independientes: no cambia al protagonista.
    if(hasModel)for(const r of character.findComponents('render'))for(const mi of r.meshInstances||[]){
      const old=mi.material;
      if(old&&typeof old.clone==='function'){
        const own=old.clone();
        if(own.diffuse){own.diffuse.r*=.87;own.diffuse.g*=.79;own.diffuse.b*=.67;}
        if(typeof own.gloss==='number')own.gloss=Math.min(own.gloss,.31);
        own.update();mi.material=own;
      }
    }
    if(!hasModel)character.destroy();
  }
  // Delantal, cinturón y bolsa: silueta claramente comercial.
  const apron=mat('Mercader · delantal cuero mate',.25,.12,.07);
  const leather=mat('Mercader · bolsa de venta',.33,.20,.10);
  const bronze=mat('Mercader · hebilla',.43,.29,.13,.33);
  box(merchantRoot,'Delantal frontal',0,.89,-.29,.67,.79,.072,apron);
  box(merchantRoot,'Pretina delantal',0,1.34,-.30,.69,.095,.13,leather);
  box(merchantRoot,'Bolsa lateral',-.44,.84,-.05,.23,.35,.33,leather);
  box(merchantRoot,'Hebilla',-.32,1.34,-.37,.08,.08,.025,bronze);
  if(!hasModel){
    // Último recurso visible, no se disfraza como GLB real.
    box(merchantRoot,'Cuerpo provisional',0,1.18,0,.61,1.03,.37,leather);
    const skin=mat('Mercader rostro provisional',.57,.37,.27);
    const head=new Entity('Cabeza provisional');
    head.addComponent('render',{type:'sphere',material:skin,castShadows:true});
    head.setLocalPosition(0,1.91,0);head.setLocalScale(.37,.43,.36);merchantRoot.addChild(head);
    box(merchantRoot,'Pantalon',0,.42,0,.54,.76,.34,apron);
  }
  return {entity:merchantRoot,fullCharacter:hasModel};
}

/* Merchant V02 approved art, 75962 triangles / 2,049,508 bytes.
 * Loaded asynchronously so stall, story quest, game controls and market modal
 * are never held hostage by a model download. Original fallback is removed
 * only after the real GLB has valid renderable mesh instances.
 */
const MERCHANT_V02_GLB='./assets/playcanvas/approved/characters/merchant_v02_75962.glb?v=0.14.022';
function loadMerchantV02(app,merchantRoot,visual){
  visual.phase='loading';
  visual.assetUrl=MERCHANT_V02_GLB;
  try{
    app.assets.loadFromUrl(MERCHANT_V02_GLB,'container',(error,asset)=>{
      if(error||!asset?.resource){
        visual.phase='fallback';
        visual.error=String(error||'GLB container missing');
        console.warn('Genesis merchant V02: keeping fallback',visual.error);
        return;
      }
      let model;
      try{
        model=asset.resource.instantiateRenderEntity();
        if(!model)throw new Error('GLB container provided no render entity');
        model.name='Mercader V02 · Meshoptimizer 75962 tri';
        // The asset faces local -Z; parent +90 degrees turns toward the west
        // market access. No borrowed humanoid, apron cubes or rig animations.
        model.setLocalPosition(0,0,0);
        model.setLocalEulerAngles(0,0,0);
        merchantRoot.addChild(model);
        const components=model.findComponents('render');
        const instances=components.flatMap(r=>r.meshInstances||[]);
        if(!instances.length)throw new Error('GLB has no renderable mesh instances');
        function extents(){
          let minY=Infinity,maxY=-Infinity;
          for(const mi of instances){
            const box=mi.aabb;if(!box)continue;
            minY=Math.min(minY,box.getMin().y);
            maxY=Math.max(maxY,box.getMax().y);
          }
          return {minY,maxY};
        }
        const initial=extents();
        const originalHeight=initial.maxY-initial.minY;
        if(!Number.isFinite(originalHeight)||originalHeight<=.1)
          throw new Error('Invalid model height / bounds');
        const scale=1.84/originalHeight;
        if(!Number.isFinite(scale)||scale<.05||scale>30)
          throw new Error('Unreasonable merchant model scale '+scale);
        model.setLocalScale(scale,scale,scale);
        const scaled=extents();
        if(!Number.isFinite(scaled.minY))throw new Error('Model floor bounds unavailable');
        model.setLocalPosition(0,merchantRoot.getPosition().y-scaled.minY,0);
        // Remove placeholder only AFTER a complete successful import.
        for(const old of [...merchantRoot.children]){
          if(old!==model)old.destroy();
        }
        visual.phase='ready';
        visual.modelName=model.name;
        visual.meshInstances=instances.length;
        visual.renderComponents=components.length;
        visual.heightMeters=1.84;
        visual.triangles=75962;
        visual.error=null;
      }catch(cause){
        if(model?.parent)model.destroy();
        visual.phase='fallback';
        visual.error=String(cause);
        console.warn('Genesis merchant V02: model setup failed',cause);
      }
    });
  }catch(error){
    visual.phase='fallback';visual.error=String(error);
    console.warn('Genesis merchant V02: loading unavailable',error);
  }
}

export function mountGenesisMarket(options){
  const {app,village,character,getSession,getInventory,modal,closeModal,onInventoryChanged,toast,canTrade,getMarketNeeds,onPurchase}=options||{};
  if(!app||!village?.root||typeof getSession!=='function'||typeof getInventory!=='function')
    throw Error('Mercado: falta el entorno de PlayCanvas o adaptadores de juego');
  const domain=window.GenesisMarketDomain;
  if(!domain)throw Error('Mercado: lógica de la semilla no cargada');
  attachStyle();
  const stall=buildStall(village.root);
  const npc=buildMerchant(village.root,character);
  const visual={phase:'initializing',assetUrl:null,triangles:75962,meshInstances:0,error:null};
  loadMerchantV02(app,npc.entity,visual);
  const chosen=Object.create(null);
  let lastMessage='';
  const toRawStock=window.GenesisPreparation?.rawStock;
  function catalog(){return domain.catalog(getSession(),toRawStock);}
  function draw(){
    const current=getSession();
    const names=catalog();
    const inv=getInventory();
    const needs=typeof getMarketNeeds==='function'?getMarketNeeds():[];
    const needByName=new Map(needs.map(n=>[n.material,n]));
    const cards=names.map((name,index)=>{
      const missing=needByName.get(name)?.missing||0;
      const quantity=chosen[name]||Math.min(99,Math.max(1,missing)),now=Number(inv?.[name]||0);
      return '<article class="genesisMarketCard" data-slot="'+index+'">'+
       '<div><strong>'+escapeText(name)+'</strong><div><small>Tenés '+now+' · Precio: 0 oro</small></div>'+(needByName.has(name)?'<div><small>Para 2 escudos faltan '+missing+'</small></div>':'')+'</div>'+
       '<div><div class="genesisMarketQty"><button data-dec="'+index+'" aria-label="Restar una unidad">−</button>'+
       '<b>'+quantity+'</b><button data-inc="'+index+'" aria-label="Sumar una unidad">+</button></div>'+
       '<button class="genesisMarketBuy" data-buy="'+index+'">Obtener '+quantity+' · GRATIS</button></div></article>';
    }).join('');
    modal('<section class="genesisMarketBoard" id="genesisMarketBoard">'+
      '<div class="genesisMarketTop"><div><small>MERCADO · DEMOSTRACIÓN DE COMPRA</small>'+
      '<h2>Comerciante de materiales</h2></div>'+
      '<button class="genesisMarketClose" id="genesisMarketClose">Cerrar ✕</button></div>'+
      '<p>Solo materiales de las recetas conocidas y necesarias para la demo de <b>'+
        escapeText(current?.profession||'la partida')+'</b>. Por ahora, todas las compras cuestan <b>0 oro</b>.</p>'+
      '<div class="genesisMarketGrid">'+(cards||'<div class="genesisMarketCard">Esta partida todavía no tiene materiales conocidos.</div>')+
      '</div><div class="genesisMarketFoot" aria-live="polite">'+escapeText(lastMessage)+'</div></section>',
      'genesisMarketModal');
    const root=document.getElementById('genesisMarketBoard');
    root?.querySelector('#genesisMarketClose')?.addEventListener('click',()=>closeModal());
    root?.querySelectorAll('[data-inc]').forEach(btn=>btn.addEventListener('click',()=>{
      const name=names[Number(btn.dataset.inc)];
      if(!name)return;const required=needByName.get(name)?.missing||0;chosen[name]=Math.min(99,(chosen[name]||Math.min(99,Math.max(1,required)))+1);draw();
    }));
    root?.querySelectorAll('[data-dec]').forEach(btn=>btn.addEventListener('click',()=>{
      const name=names[Number(btn.dataset.dec)];
      if(!name)return;const required=needByName.get(name)?.missing||0;chosen[name]=Math.max(1,(chosen[name]||Math.min(99,Math.max(1,required)))-1);draw();
    }));
    root?.querySelectorAll('[data-buy]').forEach(btn=>btn.addEventListener('click',()=>{
      const name=names[Number(btn.dataset.buy)];
      const result=domain.buy({session:getSession(),inventory:getInventory(),material:name,
        quantity:chosen[name]||Math.min(99,Math.max(1,needByName.get(name)?.missing||0)),toRawStock:toRawStock});
      if(!result.ok){lastMessage='Compra rechazada: material o cantidad no disponible.';}
      else{
        lastMessage='Añadiste '+result.quantity+' × '+result.material+' al inventario.';
        delete chosen[name];
        if(typeof onPurchase==='function')onPurchase(result);
        if(typeof onInventoryChanged==='function')onInventoryChanged();
        if(typeof toast==='function')toast(lastMessage,1250);
      }
      draw();
    }));
  }
  function open(){
    if(typeof modal!=='function'||typeof closeModal!=='function')return false;
    if(!getSession()){toast?.('Elegí primero una profesión para crear la semilla.',1500);return false;}
    if(typeof canTrade==='function'&&!canTrade()){toast?.('Primero hablá con Ordan. Él te enseñará a reabastecerte en el mercado.',2100);return false;}
    lastMessage='';draw();return true;
  }
  const interactable=Object.freeze({
    id:'marketMerchant',radius:2.85,
    position:()=>({x:POS.x,y:1.30,z:POS.z}),
    prompt:()=> 'Hablar con el comerciante',
    interact:open
  });
  const status={version:'v0.14.022',npc:npc.fullCharacter?'rig_reused':'visible_fallback',
    center:POS,stall:STALL,seedBound:true,freePurchase:true};
  // Diagnóstico público de solo lectura: el test usa el mismo catálogo y ventana del juego.
  window.__genesisMarket=Object.freeze({...status,catalog,open,visual});
  return Object.freeze({interactable,open,catalog,stall,npc:npc.entity,status});
}
