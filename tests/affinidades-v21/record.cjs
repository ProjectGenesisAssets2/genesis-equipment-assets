// Project Genesis V21: REAL PlayCanvas/Chromium 24fps capture of 5 new effects.
// Exact GLB V03/PBR V175 SHA; no images generated, no shader approval implied.
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path');
const {PNG}=require('pngjs');
(async()=>{
 const root='afinidades-v21-output';fs.mkdirSync(root,{recursive:true});
 const fps=24,loopFrames=40,overlapFrames=8,frames=loopFrames+overlapFrames;
 const modes=['hielo','luz','sombra','naturaleza','tierra'];
 const browser=await chromium.launch({headless:true,args:[
   '--enable-webgl','--use-angle=swiftshader','--ignore-gpu-blocklist','--enable-unsafe-swiftshader'
 ]});
 const page=await browser.newPage({viewport:{width:1280,height:720},deviceScaleFactor:1});
 const errors=[];
 page.on('pageerror',err=>{errors.push(err.message);console.error('GENESIS_V21_PAGE_ERROR',err.stack||err.message)});
 page.on('console',msg=>{
  if(msg.type()==='error'){errors.push(msg.text());console.error('GENESIS_V21_BROWSER_ERROR',msg.text());}
  else if(msg.text().includes('GENESIS_V21_'))console.log(msg.text());
 });
 page.on('requestfailed',r=>{errors.push(r.url());console.error('GENESIS_V21_NETWORK_ERROR',r.url())});
 await page.goto('http://127.0.0.1:8765/tests/affinidades-v21/',{waitUntil:'domcontentloaded',timeout:90000});
 await page.waitForFunction(()=>window.__genesisReady||window.__genesisError,null,{timeout:90000});
 const original=await page.evaluate(()=>window.__genesisReady||window.__genesisError);
 if(!original||original.originalLoaded!==true||original.originalTriangles!==2150||
    original.originalMeshes!==2||original.originalSha256!=='e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b'||
    original.noRayoInstantiated!==true||original.noFuegoInstantiated!==true||
    original.sourceGLBEdited!==false||original.sourceMaterialsEdited!==false||
    original.channelIDs?.join(',')!==modes.join(',')||
    original.bloom!==true)throw Error('V21_ORIGINAL_OR_CHANNELS_INVALID_'+JSON.stringify(original));
 for(const name of modes){
  const effect=original.effects[name],zone=effect.zoneRange,occupied=effect.occupiedY;
  if(effect.triangles<30||effect.patches<5||effect.originalMeshEdited!==false||
     effect.originalMaterialEdited!==false||effect.fireAndRayoCoexistenceTested!==false||
     effect.onlySwordPrototype!==true||occupied[0]<zone[0]-.0001||occupied[1]>zone[1]+.0001||
     effect.maxAbsX>.039001||effect.centerOnly!==true)
    throw Error('V21_EFFECT_ZONE_INVALID_'+name+'_'+JSON.stringify(effect));
 }
 const captured=[];
 for(const mode of modes){
  for(let i=0;i<frames;i++){
   const time=i/fps;
   const state=await page.evaluate(args=>window.__genesisStep(args),{time,channel:mode,intensity:60});
   if(state.channel!==mode||state.intensity!==60||state.slider!==60||
      state.othersZero!==true||Math.abs(state.time-time)>1e-8)
      throw Error('V21_WRONG_ANIMATION_STATE_'+mode+'_'+i+' '+JSON.stringify(state));
   const frame=mode+'_source_frame_'+String(i).padStart(3,'0')+'.png';
   await page.screenshot({path:path.join(root,frame),timeout:60000});
   if(i===22)fs.copyFileSync(path.join(root,frame),path.join(root,'Proof_'+mode+'_060.png'));
  }
  const state=await page.evaluate(args=>window.__genesisStep(args),{time:22/fps,channel:mode,intensity:100});
  if(state.intensity!==100||state.slider!==100||!state.othersZero)
   throw Error('V21_100_INVALID_'+mode);
  await page.screenshot({path:path.join(root,'Proof_'+mode+'_100.png'),timeout:60000});
  captured.push({channel:mode,fps,frames,loopFrames,overlapFrames,
    band:original.effects[mode].zoneRange,triangles:original.effects[mode].triangles});
  console.log('GENESIS_V21_CAPTURED',JSON.stringify(captured[captured.length-1]));
 }
 await page.evaluate(args=>window.__genesisStep(args),{time:22/fps,channel:'hielo',intensity:0});
 await page.screenshot({path:path.join(root,'Proof_Base_V175.png'),timeout:60000});
 const png=name=>PNG.sync.read(fs.readFileSync(path.join(root,name)));
 const base=png('Proof_Base_V175.png');
 function delta(test){
  let changed=0,sum=0;
  for(let y=18;y<510;y++)for(let x=605;x<682;x++){
   const i=(y*base.width+x)*4;
   const dr=Math.abs(test.data[i]-base.data[i]),
   dg=Math.abs(test.data[i+1]-base.data[i+1]),db=Math.abs(test.data[i+2]-base.data[i+2]);
   if(dr+dg+db>12)changed++;sum+=dr+dg+db;
  }
  return {changedPixels:changed,deltaSum:sum};
 }
 const visibility={};
 for(const mode of modes){
  visibility[mode]={at60:delta(png('Proof_'+mode+'_060.png')),
    at100:delta(png('Proof_'+mode+'_100.png'))};
  // Weak candidates are surfaced to reviewer, not passed off as approved.
  if(visibility[mode].at100.changedPixels<5)
   throw Error('V21_CHANNEL_INVISIBLE_'+mode+'_'+JSON.stringify(visibility[mode]));
 }
 if(errors.length)throw Error('V21_BROWSER_ERRORS_'+JSON.stringify(errors.slice(0,15)));
 const audit={
  schema:'Genesis_V21_FiveDistinctSwordAffinityPrototypes_ActualWebGL2',
  originalSwordSha256:original.originalSha256,
  originalTriangles:original.originalTriangles,
  originalMaterials:original.materials,
  originalModelPreserved:true,originalMaterialsPreserved:true,
  approvedLightningShaderUnchanged:true,approvedFireShaderUnchanged:true,
  independentOnly:true,otherObjectFamiliesAdapted:false,
  combinedSevenVerified:false,
  fps,loopFrames,overlapFrames,frames,modes,captured,
  zones:original.zones,stats:original.effects,visibility,errors,
  userVisualApproval:false,shaderStatus:'five experimental candidates only'
 };
 fs.writeFileSync(path.join(root,'capture_audit.json'),JSON.stringify(audit,null,2));
 await browser.close();
 console.log('GENESIS_V21_ALL_FIVE_CAPTURED',JSON.stringify({visibility,frames,channels:modes}));
})().catch(err=>{console.error('GENESIS_V21_TEST_FAILED',err.stack||err);process.exit(1)});
