// V44 user-requested REAL original 3D GLB sword: combine native PlayCanvas
// V20C.1 Fuego, approved V07 Rayo, and provisional V21 WebGL Hielo.
// Hielo V42 remains a separate Cycles material, NOT a GLB shader.
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path');
const {PNG}=require('pngjs');
(async()=>{
 const root='triple-v44-output'; fs.mkdirSync(root,{recursive:true});
 const fps=16,frames=48;
 const browser=await chromium.launch({headless:true,args:['--enable-webgl','--use-angle=swiftshader',
  '--ignore-gpu-blocklist','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:1280,height:720},deviceScaleFactor:1});
 const errors=[];
 page.on('pageerror',e=>errors.push(e.stack||e.message));
 page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 page.on('requestfailed',r=>errors.push((r.failure()?.errorText||'?')+' '+r.url()));
 await page.goto('http://127.0.0.1:8765/tests/triple-v44/',{waitUntil:'domcontentloaded',timeout:90000});
 await page.waitForFunction(()=>window.__genesisReady||window.__genesisError,null,{timeout:90000});
 const source=await page.evaluate(()=>window.__genesisReady||window.__genesisError);
 console.log('GENESIS_V44_SOURCE',JSON.stringify(source));
 if(!source || source.originalLoaded!==true || source.sourceSha256!==
 'e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b' ||
 source.triangles!==2150 || source.meshes!==2 ||
 source.rayoApproved?.approvedVisual!==true || source.rayoHelix?.turns!==3.15 ||
 source.fireVeins?.flameTongues!==8 || source.fireTriangles!==824 ||
 source.iceFacets?.patches!==10 || source.iceTriangles!==240 ||
 source.hieloSpec?.approved!==false || source.sourceGLBEdited!==false ||
 source.bloom!==true)
  throw Error('SOURCE_OR_CHANNEL_MISMATCH '+JSON.stringify(source));
 const capture=async(file,time,fire,ray,ice)=>{
  const state=await page.evaluate(q=>window.__genesisStep(q),{time,fire,ray,ice});
  if(state.fire!==fire||state.ray!==ray||state.ice!==ice ||
     state.sliderFire!==fire||state.sliderRay!==ray||state.sliderIce!==ice)
   throw Error('STATE_NOT_SAME '+JSON.stringify(state));
  await page.locator('#viewport').screenshot({path:path.join(root,file),timeout:120000});
 };
 const proofTime=1.4;
 await capture('V44_Base_OriginalV03_V175.png',proofTime,0,0,0);
 await capture('V44_Solo_FuegoV20C1.png',proofTime,65,0,0);
 await capture('V44_Solo_RayoV07.png',proofTime,0,70,0);
 await capture('V44_Solo_HieloV21_WebGL.png',proofTime,0,0,100);
 await capture('V44_TresEfectos_V03_Hero.png',proofTime,65,70,100);
 for(let i=0;i<frames;i++){
   await capture('V44_triple_frame_'+String(i).padStart(3,'0')+'.png',
      i/fps,65,70,100);
   if(i%8===0)console.log('GENESIS_V44_REAL_WEBGL_CAPTURE',i,'/',frames);
 }
 const base=PNG.sync.read(fs.readFileSync(path.join(root,'V44_Base_OriginalV03_V175.png')));
 const checks=[];
 for(const [kind,file] of [
  ['Fuego','V44_Solo_FuegoV20C1.png'],
  ['Rayo','V44_Solo_RayoV07.png'],
  ['Hielo','V44_Solo_HieloV21_WebGL.png'],
  ['Fuego_Rayo_Hielo','V44_TresEfectos_V03_Hero.png']]){
  const im=PNG.sync.read(fs.readFileSync(path.join(root,file)));
  if(im.width!==1280||im.height!==720)throw Error('BAD_CAPTURE_DIMENSIONS');
  let changed=0;
  for(let y=45;y<672;y++)for(let x=530;x<750;x++){
    const k=(y*base.width+x)*4;
    let sum=Math.abs(im.data[k]-base.data[k])+
           Math.abs(im.data[k+1]-base.data[k+1])+
           Math.abs(im.data[k+2]-base.data[k+2]);
    if(sum>45)changed++;
  }
  const min=kind==='Hielo'?35:kind==='Fuego'?90:80;
  if(changed<min)throw Error('INVISIBLE_3D_CHANNEL '+kind+' changed='+changed);
  checks.push({kind,changedPixels:changed});
 }
 if(errors.length)throw Error('WEBGL_CAPTURE_BROWSER_ERRORS '+JSON.stringify(errors.slice(0,6)));
 const audit={
  schema:'Genesis_V44_OriginalGLB_RealPlayCanvasThreeEffectsAnimated',
  source_original_glb_sha256:source.sourceSha256,geometry_modified:false,
  source_materials:source.materials,
  engine:'PlayCanvas WebGL2',capture:'Chromium SwiftShader real GPU-path rendering',
  original_blender_v12b_preset_not_ported_to_glb:true,
  effects_are_shaders_not_three_separate_glb_files:true,
  fire:{version:'V20C.1',unchangedModule:'vfx/experimental/Genesis_Fuego_V20C_CalorYFlamas.mjs',
        intensity:65,sourceApprovedFlag:source.fuegoSpec.approved},
  rayo:{version:'V07',unchangedModule:'vfx/approved/Genesis_Rayo_Helicoidal_V07.mjs',
        intensity:70,approved:source.rayoApproved.approvedVisual},
  hielo:{version:'V21 experimental WebGL preview',notOriginalCyclesV42:true,
         intensity:100,approved:false,module:'vfx/experimental/Genesis_Hielo_V21_Cristalizacion.mjs'},
  source,frames,fps,checks,errors,approvedTripleFusion:false,
  new_3d_assets_exported:false,
  original_glb_not_distributed:true
 };
 fs.writeFileSync(path.join(root,'v44_real_3d_capture_audit.json'),JSON.stringify(audit,null,2));
 await browser.close();
 console.log('GENESIS_V44_CAPTURE_SUCCESS',JSON.stringify(checks));
})().catch(err=>{console.error('GENESIS_V44_CAPTURE_FAILURE',err.stack||err);process.exit(1)});
