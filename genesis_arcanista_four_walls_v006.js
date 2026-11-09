/* Project Genesis Arcanista full geology wall V006 integration.
 * V005 scanned slate facade, four 3D walls, physically opened narrow slits,
 * restrained blue ancient runes. Door V027 and its animations are untouched.
 * Runs only when Arcanista's existing Village proxy has been constructed.
 */
const MODEL_URL='https://raw.githubusercontent.com/ProjectgenesisAssets/genesis-workshop-assets/feature/workshop-arcanist-four-walls-v006/public/models/arcanista-four-walls-v006/batched/arcanista_four_walls_preview.glb';
const state={
 version:'v0.16-arcanista-006',phase:'waiting-for-village',installed:false,
 frontPreserved:true,frontVersion:'V005',
 wallsExpected:4,roofReused:true,magicDoorUnchanged:true,
 textures:'CC0_SCANNED_PBR',magicalGlow:'SPARSE_BLUE_INLAYS',
 error:null,originalShellHidden:false,trianglesValidatedByWorkflow:true,
 geometryOnly:true,physicsNotChanged:true,modelMeshes:0
};
globalThis.__genesisArcanistaFourWallsV006=state;
const pause=t=>new Promise(done=>setTimeout(done,t));
function findApp(){
 const element=document.querySelector('#genesisApp')||document.querySelector('pc-app');
 return element?.app||element?.application||null;
}
function findArcane(app){
 const item=app?.root?.findByName('Arcanista · fachada cerrada');
 return item?.parent?item:null;
}
function loadGlb(app){
 return new Promise((resolve,reject)=>{
  app.assets.loadFromUrl(MODEL_URL,'container',(err,asset)=>{
   if(err||!asset?.resource)return reject(Error('Arcane four walls: '+String(err||'Empty glTF')));
   const mesh=asset.resource.instantiateRenderEntity();
   const components=mesh.findComponents('render');
   if(!components?.length){mesh.destroy();return reject(Error('Arcanista GLB empty'))}
   for(const c of components){c.castShadows=true;c.receiveShadows=true}
   state.modelMeshes=components.reduce((n,c)=>n+(c.meshInstances?.length||0),0);
   resolve(mesh);
  });
 });
}
async function mount(){
 for(let step=0;step<1200;step++){
  const app=findApp();
  const village=findArcane(app);
  if(!app||!village){await pause(750);continue}
  if(village.findByName('GENESIS_ARCANISTA_FOUR_WALLS_V006')){
   state.phase='already-installed';state.installed=true;return;
  }
  // The first child of village proxies is the old plain facade. Existing
  // portal, V027 animated door, roof and landmarks must stay unchanged.
  const oldFacade=village.children[0];
  const oldRoof=village.children[1];
  const oldDoor=village.children[2];
  if(!oldFacade||!oldRoof||!oldDoor)throw Error('Arcane village hierarchy incomplete');
  state.phase='loading-real-blender-pbr';
  const mesh=await loadGlb(app);
  const group=new village.constructor('GENESIS_ARCANISTA_FOUR_WALLS_V006');
  // Side lengths are identical to Herrero V012. Blender W=7.875, depth
  // 6.890625; village standard shell W=12 x D=10.5. Keep roof elevation.
  group.setLocalScale(12/7.875,1,12/7.875);
  group.setLocalPosition(0,0,0);
  mesh.name='Arcanista V006 all four real slate walls';
  mesh.setLocalPosition(0,0,0);
  group.addChild(mesh);
  village.addChild(group);
  const oldVisualState=oldFacade.enabled;
  oldFacade.enabled=false;
  // No changes to door mesh, portal animation, collider, original roof,
  // roof pitch, interaction interfaces, character logic, or economic code.
  state.originalShellHidden=true;
  state.roofReused=oldRoof.enabled;
  // The generic oldDoor child is intentionally disabled by the V027
  // portal system. Verify the ACTUAL animated magical door instead.
  const magicDoor=village.findByName('Arcanista · puerta mágica V027 · cerrada');
  state.doorEntityName=magicDoor?.name||'MISSING_V027_MAGIC_DOOR';
  state.magicDoorExists=!!magicDoor;
  state.magicDoorEnabled=magicDoor?.enabled===true;
  state.installed=true;state.phase='mounted-four-rock-walls';
  state.villageTransform={
   x:village.getPosition().x,z:village.getPosition().z,
   groupScaleX:group.getLocalScale().x};
  const restore=()=>{oldFacade.enabled=oldVisualState;group.destroy()};
  window.addEventListener('pagehide',restore,{once:true});
  return;
 }
 state.phase='village-unavailable-after-15min';
}
mount().catch(error=>{state.phase='error';state.error=String(error?.stack||error);
 console.error('[GENESIS_ARCANISTA_V006]',error)});
