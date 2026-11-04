const {chromium}=require('playwright');
const fs=require('fs'),path=require('path');
(async()=>{
 const browser=await chromium.launch({headless:true,args:[
   '--enable-webgl','--use-angle=swiftshader','--ignore-gpu-blocklist','--enable-unsafe-swiftshader'
 ]});
 const context=await browser.newContext({viewport:{width:1280,height:720},deviceScaleFactor:1});
 const page=await context.newPage();const errors=[];
 page.on('pageerror',e=>{console.log('PAGE_ERROR',e.stack||e.message);errors.push(String(e))});
 page.on('console',m=>{
   if(m.type()==='error'){console.log('BROWSER_ERROR',m.text());errors.push(m.text())}
   else if(m.text().includes('GENESIS_RAYO_'))console.log(m.text());
 });
 page.on('requestfailed',r=>{console.log('REQUEST_FAILED',r.url(),r.failure()?.errorText);errors.push(r.url())});
 await page.goto('http://127.0.0.1:8765/tests/rayo-premium-v01/',{waitUntil:'domcontentloaded',timeout:90000});
 await page.waitForFunction(()=>window.__genesisReady||window.__genesisError,null,{timeout:120000});
 const init=await page.evaluate(()=>window.__genesisReady||window.__genesisError);
 console.log('GENESIS_RAYO_V03_AUDIT',JSON.stringify(init));
 if(!init || init.loaded!==true || init.triangles!==2150||init.meshes!==2||init.proceduralShader!==true)
  throw Error('GENESIS_SOURCE_OR_SHADER_AUDIT_FAILED '+JSON.stringify(init));
 if(!init.bloom)throw Error('CAMERAFRAME_HDR_BLOOM_WAS_NOT_ACTIVATED');
 const root='rayo-premium-v01-output';fs.mkdirSync(root,{recursive:true});
 const frames=Number(process.env.FRAMES||32);
 let last;
 for(let frame=0;frame<frames;frame++){
  last=await page.evaluate(async x=>window.__genesisStep(x.frame,x.frames),{frame,frames});
  await page.screenshot({path:path.join(root,'frame_'+String(frame).padStart(3,'0')+'.png'),timeout:60000});
  if(frame%8===0)console.log('GENESIS_RAYO_PREMIUM_FRAME',frame,'of',frames);
 }
 const audit={
   schema:'Genesis_Rayo_GLSL_CameraFrame_Cinematic_V001',
   status:'experiment-not-approved',
   verified_original_sha256:'e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b',
   source:init,realPlayCanvasWebGL2:true,
   generatedBy:'Chromium WebGL2 PlayCanvas ShaderMaterial GLSL, camera bloom and real PBR GLB',
   noGeometryChanges:true,sourceImageTexturesNotChanged:true,
   extraVfxGeometry:'one quad, two triangles, procedural shader',
   noStaticMasks:true,noSpheresOrTubes:true,
   fps:12,frames,displayResolution:[1280,720],
   animation:last,errors};
 fs.writeFileSync(path.join(root,'audit.json'),JSON.stringify(audit,null,2));
 console.log('GENESIS_RAYO_V01_COMPLETE',JSON.stringify({frames,errors:errors.length,bloom:init.bloom,triangles:init.triangles}));
 await browser.close();
 if(errors.length)throw Error('GENESIS_CONSOLE_ERRORS '+JSON.stringify(errors.slice(0,6)));
})().catch(e=>{console.error('GENESIS_RAYO_PREMIUM_FAILED',e.stack||e);process.exit(1)});
