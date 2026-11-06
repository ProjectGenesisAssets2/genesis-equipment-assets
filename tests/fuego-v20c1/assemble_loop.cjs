// Project Genesis V20C.1 — loop assembly using authentic frames from real PlayCanvas.
// We crossfade equivalent 12-frame segments of the animation to avoid the
// jump from non-periodic procedural noise when a GIF/MP4 returns to frame 0.
// The original V20C shader and sword are NOT modified.
const fs=require('node:fs');
const path=require('node:path');
const {PNG}=require('pngjs');
const root='fuego-v20c1-output';
const fps=24,loopFrames=72,overlap=12;
const modes=['Fuego_060','Fuego_100'];
function file(mode,type,i){
 return path.join(root,mode+'_'+type+'_frame_'+String(i).padStart(3,'0')+'.png');
}
function png(pathname){
 return PNG.sync.read(fs.readFileSync(pathname));
}
function meanDelta(a,b){
 if(a.width!==b.width||a.height!==b.height)throw Error('MISMATCHED_IMAGE_SIZE');
 // Measured over the blade, not misleadingly diluted by static UI/background.
 let total=0,count=0;
 for(let y=39;y<504;y+=2)for(let x=608;x<683;x+=2){
  const k=(y*a.width+x)*4;
  const dr=Math.abs(a.data[k]-b.data[k]);
  const dg=Math.abs(a.data[k+1]-b.data[k+1]);
  const db=Math.abs(a.data[k+2]-b.data[k+2]);
  total+=(dr+dg+db)/3;count++;
 }
 return total/count;
}
const output={schema:'Genesis_V20C1_RealWebGL24FPS_SeamCrossfade',
 sourceShaderUnmodified:true,sourceModelUnmodified:true,
 fps,loopFrames,overlapFrames:overlap,
 note:'Crossfades real source time 3.0-3.5s to real source time 0-0.5s in FIRST 12 output frames. The preceding frame is t=2.958s, then frame 0 matches t=3.0s. No synthetic interpolation between game states.',
 modes:[]};
for(const mode of modes){
 let dimensions=null;
 for(let i=0;i<loopFrames;i++){
  const original=png(file(mode,'source',i));
  if(!dimensions)dimensions=[original.width,original.height];
  if(dimensions[0]!==original.width||dimensions[1]!==original.height)throw Error('DIMENSIONS_CHANGED '+mode);
  if(i<overlap){
   const tail=png(file(mode,'source',loopFrames+i));
   const alpha=(i+1)/overlap; // 1/12 original at start, 12/12 at end.
   for(let k=0;k<original.data.length;k+=4){
    for(let c=0;c<3;c++){
     original.data[k+c]=Math.round(alpha*original.data[k+c]+(1-alpha)*tail.data[k+c]);
    }
   }
  }
  fs.writeFileSync(file(mode,'',i).replace('__frame_','_frame_'),PNG.sync.write(original,{colorType:6}));
 }
 const originalEnd=png(file(mode,'source',loopFrames-1));
 const oldFirst=png(file(mode,'source',0));
 const newFirst=png(file(mode,'',0).replace('__frame_','_frame_'));
 const newNext=png(file(mode,'',1).replace('__frame_','_frame_'));
 const newBeforeHandoff=png(file(mode,'',overlap-1).replace('__frame_','_frame_'));
 const newAfterHandoff=png(file(mode,'',overlap).replace('__frame_','_frame_'));
 const firstMid=png(file(mode,'',Math.floor(loopFrames/2)).replace('__frame_','_frame_'));
 const originalMid=png(file(mode,'source',Math.floor(loopFrames/2)));
 const metric={
  mode,
  oldSeamMeanAbsRGB:meanDelta(originalEnd,oldFirst),
  correctedSeamMeanAbsRGB:meanDelta(originalEnd,newFirst),
  firstTransitionMeanAbsRGB:meanDelta(newFirst,newNext),
  handoffMeanAbsRGB:meanDelta(newBeforeHandoff,newAfterHandoff),
  unchangedMidpointMeanAbsRGB:meanDelta(firstMid,originalMid)
 };
 metric.relativeSeamImprovement=metric.oldSeamMeanAbsRGB>1e-7?
  1-metric.correctedSeamMeanAbsRGB/metric.oldSeamMeanAbsRGB:0;
 if(metric.unchangedMidpointMeanAbsRGB>.0001)
  throw Error('V20C_IMAGE_PIXELS_CHANGED_OUTSIDE_TRANSITION '+JSON.stringify(metric));
 if(metric.oldSeamMeanAbsRGB>1 &&
   metric.correctedSeamMeanAbsRGB >= metric.oldSeamMeanAbsRGB*.92)
  throw Error('NO_MEASURABLE_LOOP_SEAM_IMPROVEMENT '+JSON.stringify(metric));
 if(metric.correctedSeamMeanAbsRGB>metric.firstTransitionMeanAbsRGB*5+7)
  throw Error('CORRECTED_LOOP_STILL_ABRUPT '+JSON.stringify(metric));
 output.modes.push(metric);
 console.log('GENESIS_V20C1_SEAM_MEASURED',JSON.stringify(metric));
}
fs.writeFileSync(path.join(root,'loop_audit.json'),JSON.stringify(output,null,2));
console.log('GENESIS_V20C1_REAL_FRAMES_LOOP_VALIDATED',JSON.stringify({fps,loopFrames,modes:output.modes}));
