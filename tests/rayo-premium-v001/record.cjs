// Project Genesis PC / exact original V03 / GPU shader and bloom render audit
const {chromium}=require('playwright');
const fs=require('fs'),path=require('path');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--enable-webgl','--use-angle=swiftshader','--ignore-gpu-blocklist','--enable-unsafe-swiftshader']});
 const context=await browser.newContext({viewport:{width:1280,height:720},deviceScaleFactor:1});
 const page=await context.newPage();
 const errors=[];
 page.on('pageerror',e=>{errors.push(e.message);console.log('PAGE_ERROR',e.stack||e.message)});
 page.on('console',m=>{if(m.type()==='error'||/compile|shader.error/i.test(m.text())){errors.push(m.text());console.log('GPU_CONSOLE_ERROR',m.text())}
   else if(/GENESIS_RAYO_PREMIUM_READY/.test(m.text()))console.log(m.text())});
 page.on('requestfailed',req=>{errors.push(req.url()+':'+req.failure()?.errorText);console.log('LOAD_FAILED',req.url(),req.failure()?.errorText)});
 await page.goto('http://127.0.0.1:8765/tests/rayo-premium-v001/',{waitUntil:'domcontentloaded',timeout:120000});
 await page.waitForFunction(()=>window.__rayoReady || window.__rayoError,null,{timeout:120000});
 const ready=await page.evaluate(()=>window.__rayoReady||{failed:window.__rayoError});
 console.log('GENESIS_RAYO_READY',JSON.stringify(ready));
 if(!ready.loaded||ready.triangles!==2150||ready.meshes!==2)throw Error('ORIGINAL_GLB_VERIFICATION_FAILED '+JSON.stringify(ready));
 fs.mkdirSync('rayo-premium-out/frames',{recursive:true});
 await page.evaluate(()=>window.__rayoStep(-1));
 await page.screenshot({path:'rayo-premium-out/without_fx.png'});
 let count=0;
 for(let i=0;i<48;i++){
   await page.evaluate(i=>window.__rayoStep(i),i);
   const file='rayo-premium-out/frames/frame_'+String(i).padStart(3,'0')+'.png';
   await page.screenshot({path:file,timeout:60000});
   count++;
   if(i%12===0)console.log('GENESIS_RAYO_WEBGL2_RENDERED',i);
 }
 if(errors.some(e=>/shader|compile|GL_INVALID|WEBGL|error.*webgl|SyntaxError/i.test(e)))throw Error('GPU_ERROR '+JSON.stringify(errors).slice(0,1600));
 const report={engine:'PlayCanvas WebGL2',source:'original Genesis V03',source_sha256:'e2228f078b2572768416c48c0e63c2d908f214e2c0625a2ab754c877a099112b',original_geometry:ready,frames:count,fps:24,emissive:'GPU ShaderMaterial procedural GLSL, no baked masks',bloom:ready.bloom,original_glb_modified:false,art_reference:'image-gen-8.png, Rayo blue sword approved visual reference',browser_errors:errors};
 fs.writeFileSync('rayo-premium-out/render_audit.json',JSON.stringify(report,null,2));
 console.log('GENESIS_RAYO_PREMIUM_48_FRAMES_DONE',JSON.stringify(report));
 await browser.close();
})().catch(e=>{console.error('GENESIS_RAYO_PREMIUM_FAILED',e.stack||e);process.exit(1)});
