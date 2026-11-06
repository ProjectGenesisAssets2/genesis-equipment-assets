// V21 seamless previews: real PlayCanvas frames with crossfade at the last/first seam.
const {PNG}=require('pngjs'),fs=require('fs'),path=require('path');
const folder='affinidades-v21-output',frames=40,overlap=8;
const modes=['hielo','luz','sombra','naturaleza','tierra'];
const frame=(id,type,n)=>path.join(folder,id+'_'+type+'_frame_'+String(n).padStart(3,'0')+'.png');
function read(id,n){return PNG.sync.read(fs.readFileSync(frame(id,'source',n)));}
function mad(a,b) {
 let sum=0,total=0;
 for(let y=18;y<510;y+=2)for(let x=605;x<682;x+=2){
  const i=(y*a.width+x)*4;
  for(let c=0;c<3;c++){sum+=Math.abs(a.data[i+c]-b.data[i+c]);total++;}
 }
 return sum/total;
}
const checks=[];
for(const id of modes){
 const originalLast=read(id,frames-1),oldFirst=read(id,0);
 for(let n=0;n<frames;n++){
  const original=read(id,n);
  if(n<overlap){
   const tail=read(id,frames+n);
   const w=(n+1)/overlap;
   for(let i=0;i<original.data.length;i+=4){
    original.data[i]=Math.round(w*original.data[i]+(1-w)*tail.data[i]);
    original.data[i+1]=Math.round(w*original.data[i+1]+(1-w)*tail.data[i+1]);
    original.data[i+2]=Math.round(w*original.data[i+2]+(1-w)*tail.data[i+2]);
   }
  }
  fs.writeFileSync(frame(id,'loop',n),PNG.sync.write(original));
 }
 const last=PNG.sync.read(fs.readFileSync(frame(id,'loop',frames-1))),
  first=PNG.sync.read(fs.readFileSync(frame(id,'loop',0))),
  next=PNG.sync.read(fs.readFileSync(frame(id,'loop',1)));
 const oldDelta=mad(originalLast,oldFirst),newDelta=mad(last,first),nextDelta=mad(first,next);
 if(newDelta>oldDelta*.95+.25)throw Error('V21_STITCH_FAILED_'+id+' '+JSON.stringify({oldDelta,newDelta,nextDelta}));
 const check={id,oldSeamMAD:oldDelta,newSeamMAD:newDelta,firstTransitionMAD:nextDelta,
  seamImprovementFraction:oldDelta>1e-8?1-newDelta/oldDelta:0};
 checks.push(check);
 console.log('GENESIS_V21_SEAM_CHECK',JSON.stringify(check));
}
const audit=JSON.parse(fs.readFileSync(path.join(folder,'capture_audit.json'),'utf8'));
audit.loopChecks=checks;
fs.writeFileSync(path.join(folder,'audit.json'),JSON.stringify(audit,null,2));
console.log('GENESIS_V21_FIVE_LOOPS_STITCHED',JSON.stringify(checks));
