// Captures real PlayCanvas WebGL2 rendering; no 3D approximations, no GLB edits.
const { chromium } = require('playwright');
const fs=require('fs'),path=require('path');
(async()=>{
 const browser=await chromium.launch({headless:true,args:[
 '--enable-webgl','--use-angle=swiftshader','--ignore-gpu-blocklist','--enable-unsafe-swiftshader'
 ]});
 const context=await browser.newContext({viewport:{width:1280,height:720},deviceScaleFactor:1, reducedMotion:'reduce'});
 const page=await context.newPage();
 page.on('pageerror',e=>console.log('PAGE_ERROR',e.stack||e.message));
 page.on('console',m=>{if(m.type()==='error')console.log('BROWSER_ERROR',m.text()); else if(/GENESIS_PC_VFX_LOAD/.test(m.text()))console.log(m.text())});
 page.on('requestfailed',r=>console.log('LOAD_FAILED',r.url(),r.failure()?.errorText));
 await page.goto('http://127.0.0.1:8765/tests/pc-vfx-video/',{waitUntil:'domcontentloaded',timeout:120000});
 await page.waitForFunction(()=>window.__genesisReady || window.__genesisError,{timeout:120000});
 const ready=await page.evaluate(()=>window.__genesisReady||window.__genesisError);
 console.log('GENESIS_PLAYCANVAS_REAL_V03_LOADED',JSON.stringify(ready));
 if(!ready || ready.loaded!==true ||ready.sourceMeshes===0){} // safeguard below
 if(!ready || ready.loaded!==true || ready.meshes<1 ||ready.triangles<2000)throw Error('ORIGINAL_V03_NOT_LOADED '+JSON.stringify(ready));
 const n=Number(process.env.FRAMES||30);
 const renderRoot='vfx-video-output';
 fs.mkdirSync(renderRoot,{recursive:true});
 const audit={source:'exact original Fab sword V03 in PlayCanvas',platform:'PlayCanvas WebGL2',
   source_sha256:'e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b',
   original_triangles:ready.triangles,original_meshes:ready.meshes,frames_per_variant:n,
   variants:[],glb_edited:false,texture_masks_used:false,particles:'procedural entities',lighting:'PC studio with dynamic colored lights',
   note:'PlayCanvas realtime lookdev. The video glow is postprocessed separately; no external 3D geometry files exported.'};
 for(let v=0;v<4;v++){
  const folder=path.join(renderRoot,'variant_'+(v+1));
  fs.mkdirSync(folder,{recursive:true});
  let last;
  for(let f=0;f<n;f++){
    last=await page.evaluate(async ({variant,frame})=>window.__genesisStep(variant,frame),{variant:v,frame:f});
    await page.screenshot({path:path.join(folder,'frame_'+String(f).padStart(3,'0')+'.png'),timeout:60000});
    if(f%10===0)console.log('GENESIS_WEBGL_FRAME',v+1,f,last.variant);
  }
  audit.variants.push(last);
  console.log('GENESIS_WEBGL_VARIANT_DONE',v+1,n,last.variant);
 }
 fs.writeFileSync(path.join(renderRoot,'playcanvas_audit.json'),JSON.stringify(audit,null,2));
 await browser.close();
})().catch(e=>{console.error('GENESIS_PLAYCANVAS_TEST_FAILED',e.stack||e);process.exit(1)});
