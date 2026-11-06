// Loop construction from real PlayCanvas captured screenshots. No fake render.
// The V20C shader is untouched; only the first half-second of presentation is crossfaded.
// At the loop seam, output last = original time T-1/fps and first = original time T.
const {PNG}=require('pngjs');
const fs=require('fs'),path=require('path');
const root='fuego-v20c1-output',fps=24,n=72,overlap=12;
const modes=['Fuego_060','Fuego_100'];
function file(mode,kind,i){return path.join(root,mode+'_'+kind+'_frame_'+String(i).padStart(3,'0')+'.png');}
function read(mode,i){return PNG.sync.read(fs.readFileSync(file(mode,'source',i)));}
function write(mode,i,p){fs.writeFileSync(file(mode,'loop',i),PNG.sync.write(p));}
function mad(a,b){
 if(a.width!==b.width||a.height!==b.height)throw Error('MISMATCHED_SCREENS');
 let s=0,np=0;
 for(let y=35;y<510;y+=2)for(let x=611;x<681;x+=2){
  const k=(y*a.width+x)*4;
  s+=Math.abs(a.data[k]-b.data[k])+Math.abs(a.data[k+1]-b.data[k+1])+Math.abs(a.data[k+2]-b.data[k+2]);np+=3;
 }
 return s/np;
}
const audit=JSON.parse(fs.readFileSync(path.join(root,'capture_audit.json'),'utf8'));
const seamChecks=[];
for(const mode of modes){
 for(let i=0;i<n;i++){
  if(i>=overlap){fs.copyFileSync(file(mode,'source',i),file(mode,'loop',i));continue;}
  const late=read(mode,n+i),early=read(mode,i);
  const f=i/(overlap-1),w=f*f*(3-2*f);
  const out=new PNG({width:late.width,height:late.height});
  for(let k=0;k<out.data.length;k+=4){
   out.data[k]=Math.round((1-w)*late.data[k]+w*early.data[k]);
   out.data[k+1]=Math.round((1-w)*late.data[k+1]+w*early.data[k+1]);
   out.data[k+2]=Math.round((1-w)*late.data[k+2]+w*early.data[k+2]);
   out.data[k+3]=255;
  }
  write(mode,i,out);
 }
 const last=PNG.sync.read(fs.readFileSync(file(mode,'loop',n-1)));
 const first=PNG.sync.read(fs.readFileSync(file(mode,'loop',0)));
 const prev=PNG.sync.read(fs.readFileSync(file(mode,'loop',n-2)));
 const naturalNext=read(mode,n);
 let exactPixels=0;
 for(let k=0;k<first.data.length;k++)if(first.data[k]!==naturalNext.data[k])exactPixels++;
 if(exactPixels!==0)throw Error('WRONG_TEMPORAL_LOOP_FIRST_FRAME '+exactPixels);
 const before=mad(prev,last),seam=mad(last,first),reference=mad(last,naturalNext);
 if(Math.abs(seam-reference)>1e-9)throw Error('SEAM_NOT_SAME_AS_REAL_NEXT_FRAME');
 const check={mode,fps,outputFrames:n,loopSeconds:n/fps,overlapFrames:overlap,
   firstEqualsRealTime3Seconds:true,adjacentFrameMAD:before,
   seamMAD:seam,naturalNextMAD:reference,discontinuityBeyondNaturalStep:false};
 seamChecks.push(check);
 console.log('GENESIS_V20C1_NATURAL_SEAM_CHECK',JSON.stringify(check));
}
audit.loopValidated=true;audit.seamChecks=seamChecks;
audit.delivery='24fps MP4 and 24fps GIF real WebGL source with a smooth wrap at 3.0 seconds';
fs.writeFileSync(path.join(root,'audit.json'),JSON.stringify(audit,null,2));
console.log('GENESIS_V20C1_SEAMLESS_CAPTURE_COMPLETE',JSON.stringify(seamChecks));
