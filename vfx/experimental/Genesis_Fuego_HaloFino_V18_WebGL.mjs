// Project Genesis — V19 fire adaptation of Fuego V18 halo; experimental WebGL, NOT APPROVED.
// Reusable independent PlayCanvas WebGL2 ShaderMaterial + cutting-edge 3D ribbons.
// Animated WebGL preview based on narrow V18 V06 silhouette, preserving the old V08 shader structure. Replaces bulky spheres with
// narrow, dynamically flickering emissive veins. Does not edit V03 geometry or PBR V175.

const vertexGLSL=`
attribute vec3 aPosition;
attribute vec2 aUv0;
uniform mat4 matrix_model;
uniform mat4 matrix_viewProjection;
varying vec2 vUv;
void main(void){
 vUv=aUv0;
 gl_Position=matrix_viewProjection*matrix_model*vec4(aPosition,1.0);
}
`;
const fragmentGLSL=`
precision highp float;
varying vec2 vUv;
uniform float uTime;
uniform float uIntensity;
float rand(float v){ return fract(sin(v*127.7+34.38)*43758.5453); }
void main(void){
 float power=clamp(uIntensity*.01,0.0,1.0);
 if(power<=0.0001) discard;
 float y=vUv.x, across=abs(vUv.y*2.0-1.0), t=uTime;
 // Color progression on cutting edges: ember red -> copper orange -> yellow-hot filaments.
 // Sinusoids are deliberately spatially modulated so it NEVER becomes a solid neon border.
 float wave=sin(y*41.0-t*10.3+sin(y*97.0+t*2.1)*.55);
 float wave2=sin(y*102.0-t*7.2+sin(y*22.0+t*3.3)*1.3);
 float wave3=sin(y*175.0+t*5.6);
 float burn=smoothstep(-.28,.71,wave*.70+wave2*.22+wave3*.08);
 float embers=pow(max(0.0,burn),1.55);
 float flicker=.72+.28*abs(sin(t*8.2+y*49.0));
 float thin=pow(max(0.0,1.0-across),7.5);
 float soft=pow(max(0.0,1.0-across),2.5);
 // A few darting, discontinuous streaks; grows with channel intensity.
 float travelling=pow(max(0.0,sin(y*87.0-t*(9.5+power*4.0))),5.0);
 float vein=(.22+embers*.78)*(thin*.72+soft*.27);
 float sparks=travelling*pow(max(0.0,1.0-across),9.0)*(.12+.24*power);
 float brightness=power*(.68+1.03*power)*flicker;
 float hot=clamp(embers*.70+.30*travelling,0.0,1.0);
 vec3 amber=vec3(.95,.18,.018)*soft*.27;
 vec3 copper=vec3(1.20,.49,.045)*vein;
 vec3 core=vec3(1.65,1.10,.28)*(thin*hot*.53+sparks);
 vec3 rgb=(amber+copper+core)*brightness;
 float alpha=clamp((vein*.39+sparks*.32)*power,0.0,.52);
 if(alpha<.007) discard;
 gl_FragColor=vec4(rgb,alpha);
}
`;

export const FUEGO_V18_WEBGL_SPEC={
 id:'Genesis_Fuego_HaloFino_V18_WebGL',approved:false,range:[0,100],
 placements:'two cutting edges + two inner heat veins on real sword',
 visualTarget:'Blender V18 V06 halo 60 percent thinner than V17; real-time GLSL approximation only',
 haloWidthScaleVsLegacyWebGLV01:0.40,haloWidthReductionPercent:60,
 animated:true,metalUnchanged:true,sourceV03Preserved:true,
 shader:'fragmentGLSL',notATextureMask:true
};

export function createFuegoHaloFinoV18(pc,app,bladeAabb){
 const material=new pc.ShaderMaterial({
  uniqueName:'Genesis_Fuego_Filo_GLSL_V01',
  attributes:{aPosition:pc.SEMANTIC_POSITION,aUv0:pc.SEMANTIC_TEXCOORD0},
  vertexGLSL,fragmentGLSL
 });
 material.blendType=pc.BLEND_ADDITIVEALPHA;
 material.cull=pc.CULLFACE_NONE;
 material.depthTest=true;
 material.depthWrite=false;
 material.setParameter('uTime',0);
 material.setParameter('uIntensity',0);
 material.update();
 const lo=bladeAabb.center.y-bladeAabb.halfExtents.y;
 const hi=bladeAabb.center.y+bladeAabb.halfExtents.y;
 const yStart=Math.max(lo+.13,-.38);
 const yEnd=Math.min(hi-.095,.865);
 const steps=220,positions=[],uvs=[],indices=[];
 const centreX=bladeAabb.center.x,centreZ=bladeAabb.center.z;
 // 4 independent narrow invisible ribbons — no material replacement and no sphere geometry.
 const ribbonSpecs=[
  {side:-1,inner:false,phase:.0,width:.0044},
  {side:+1,inner:false,phase:.32,width:.0044},
  {side:-1,inner:true, phase:.62,width:.0040},
  {side:+1,inner:true, phase:.88,width:.0040}
 ];
 for(let lane=0;lane<ribbonSpecs.length;lane++){
  const cfg=ribbonSpecs[lane],base=positions.length/3;
  for(let k=0;k<=steps;k++){
   const p=k/steps;
   const y=yStart+p*(yEnd-yStart);
   const taper=1.0-.46*Math.pow(Math.max(0,(p-.76)/.24),1.45);
   const baseX=(cfg.inner?.033:.060)*taper;
   const waviness=.40*(cfg.inner?.0019:.0014)*Math.sin(p*107.0+lane*3.5)
                +.40*.0011*Math.sin(p*239.0+lane*1.7);
   const x=centreX+cfg.side*(baseX+waviness);
   const z=centreZ+(cfg.inner?.072:.071);
   const width=cfg.width;
   // Across blade surface, not a floating billboard or red 3D tube.
   positions.push(x-width,y,z,x+width,y,z);
   uvs.push(p+cfg.phase,0,p+cfg.phase,1);
   if(k<steps){
    const i=base+2*k;
    indices.push(i,i+1,i+2,i+1,i+3,i+2);
   }
  }
 }
 const mesh=new pc.Mesh(app.graphicsDevice);
 mesh.setPositions(positions);
 mesh.setUvs(0,uvs);
 mesh.setIndices(indices);
 mesh.update();
 const entity=new pc.Entity('GENESIS_FUEGO_V18_THIN_RIBBONS');
 entity.addComponent('render',{meshInstances:[new pc.MeshInstance(mesh,material)],
    castShadows:false,receiveShadows:false});
 app.root.addChild(entity);
 const fireLight=new pc.Entity('GENESIS_FUEGO_V18_HEAT_LIGHT');
 fireLight.addComponent('light',{type:'omni',color:new pc.Color(1,.30,.055),
    intensity:0,range:1.65,castShadows:false});
 fireLight.setPosition(centreX,.25,centreZ+.13);app.root.addChild(fireLight);
 function set(time,intensity){
  const value=Math.max(0,Math.min(100,Number(intensity)||0));
  const seconds=Math.max(0,Number(time)||0);
  material.setParameter('uTime',seconds);
  material.setParameter('uIntensity',value);
  fireLight.light.intensity=.14*(value/100)*(.78+.22*Math.sin(seconds*8.3)**2);
 }
 set(0,0);
 const stats={ribbons:ribbonSpecs.length,segments:steps,
  haloWidthScale:0.40,haloWidthReductionPercent:60,geomWidths:ribbonSpecs.map(s=>s.width),
  triangles:steps*2*ribbonSpecs.length,
  bladeOnly:true,intensityRange:[0,100],
  yStart,yEnd,material:material.name,depthTest:true};
 return {material,entity,light:fireLight,stats,set};
}
