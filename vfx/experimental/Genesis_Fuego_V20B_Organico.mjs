// Project Genesis — V20B organic tongue flames on V18/V19 thin geometry; standalone experimental WebGL, NOT APPROVED.
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
void main(void){
 float power=clamp(uIntensity*.01,0.0,1.0);
 if(power<=0.0001) discard;
 float y=vUv.x, t=uTime;
 float x=abs(vUv.y*2.0-1.0);
 float edge=max(0.0,1.0-x);
 // Continuous upward-travelling, curling heat cells, not pulsing static neon lines.
 float curl=sin(y*37.0-t*7.8+1.12*sin(y*16.5-t*2.15));
 float breathing=sin(y*79.0-t*12.7+.8*sin(y*28.0+t*1.5));
 float turbulence=sin(y*137.0+t*18.2)*.16;
 float flame=smoothstep(-.48,.73,curl*.63+breathing*.31+turbulence);
 float lobe=smoothstep(-.35,.8,sin(y*26.0-t*5.8+curl*.64));
 float thermal=.32+.52*flame+.16*lobe;
 float flicker=.89+.11*sin(t*9.2+y*42.0)*sin(t*6.7+y*23.0);
 float veil=pow(edge,2.1)*thermal;
 float core=pow(edge,6.2)*(.25+.75*flame);
 float filaments=pow(edge,9.0)*pow(max(0.0,sin(y*74.0-t*10.5+curl)),3.0);
 // V19 lacked visual presence; V20B increases emission and alpha without
 // changing any vertex width, projected halo extent, or approved base metal.
 float brightness=power*(1.06+1.42*power)*flicker;
 vec3 ember=vec3(1.18,.22,.018)*veil;
 vec3 copper=vec3(1.46,.56,.047)*(.67*veil+.33*core);
 vec3 hot=vec3(2.15,1.22,.20)*(core*.72+filaments*.52);
 vec3 rgb=(ember*.35+copper+hot)*brightness;
 float alpha=clamp(power*(veil*.65+core*.48+filaments*.18),0.0,.79);
 if(alpha<.008) discard;
 gl_FragColor=vec4(rgb,alpha);
}
`;


const tongueFragmentGLSL=`
precision highp float;
varying vec2 vUv;
uniform float uTime;
uniform float uIntensity;
void main(void){
 float power=clamp(uIntensity*.01,0.,1.);
 if(power<=.0001) discard;
 float v=clamp(vUv.x,0.,1.),u=vUv.y,t=uTime;
 float curl=.11*sin(v*10.2-t*3.8+.45*sin(v*18.-t*2.2))*v;
 float dist=abs(u-.5-curl);
 float radius=.35*(1.-.35*v);
 float edge=1.-smoothstep(radius*.30,radius,dist);
 float root=smoothstep(.01,.13,v);
 float tip=1.-smoothstep(.66,.99,v);
 float flicker=.68+.32*smoothstep(-.45,.68,
     .63*sin(v*18.-t*5.9)+.37*sin(v*38.-t*8.4+u*3.));
 float alpha=clamp(power*.58*edge*root*tip*flicker,0.,.56);
 if(alpha<.008)discard;
 vec3 ember=vec3(1.23,.22,.018);
 vec3 center=vec3(1.68,.74,.095);
 vec3 color=mix(center,ember,smoothstep(.05,.95,v));
 gl_FragColor=vec4(color*(.8+1.25*power),alpha);
}
`;

export const FUEGO_V20B_SPEC={
 id:'Genesis_Fuego_V20B_Organico',approved:false,range:[0,100],
 placements:'two cutting edges + two inner heat veins on real sword',
 visualTarget:'V18 V06 Blender flame thin envelope, flowing orange warm body; V20B WebGL runtime approximation, not Cycles',
 haloWidthScaleVsLegacyWebGLV01:0.40,haloWidthReductionPercent:60,
 shaderVersion:'V20B_Organic_ThinPlusInteriorTongues',isolatedTest:true,
 reversible:true,baseSwordUntouched:true,
 animated:true,metalUnchanged:true,sourceV03Preserved:true,
 shader:'fragmentGLSL',notATextureMask:true
};

export function createFuegoV20B(pc,app,bladeAabb){
 const material=new pc.ShaderMaterial({
  uniqueName:'Genesis_Fuego_V20B_Organic_Veil_GLSL',
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
 const entity=new pc.Entity('GENESIS_FUEGO_V20B_THIN_RIBBONS');
 entity.addComponent('render',{meshInstances:[new pc.MeshInstance(mesh,material)],
    castShadows:false,receiveShadows:false});
 app.root.addChild(entity);
 const tongueMaterial=new pc.ShaderMaterial({
  uniqueName:'Genesis_Fuego_V20B_InteriorTongs',
  attributes:{aPosition:pc.SEMANTIC_POSITION,aUv0:pc.SEMANTIC_TEXCOORD0},
  vertexGLSL,fragmentGLSL:tongueFragmentGLSL
 });
 tongueMaterial.blendType=pc.BLEND_ADDITIVEALPHA;
 tongueMaterial.cull=pc.CULLFACE_NONE;
 tongueMaterial.depthTest=true;
 tongueMaterial.depthWrite=false;
 tongueMaterial.setParameter('uTime',0);
 tongueMaterial.setParameter('uIntensity',0);
 tongueMaterial.update();
 const tonguesPerSide=7,tongueSteps=16;
 const tonguePositions=[],tongueUvs=[],tongueIndices=[];
 for(const side of [-1,1])for(let n=0;n<tonguesPerSide;n++){
  const originIndex=tonguePositions.length/3;
  const begin=.065+.116*n+(side<0?.012:0);
  const tongueHeight=.14+.045*(.5+.5*Math.sin(n*2.4+side*.6));
  for(let j=0;j<=tongueSteps;j++){
   const q=j/tongueSteps;
   const u=Math.min(.975,begin+tongueHeight*q);
   const y=yStart+u*(yEnd-yStart);
   const taper=1.0-.46*Math.pow(Math.max(0,(u-.76)/.24),1.45);
   const edgeX=.060*taper;
   // Fit inside edge bands: do not intrude on Rayo V07 exterior orbit.
   const inward=.020+.0025*Math.sin(q*4.3+n*2.9);
   const sway=.002*Math.sin(q*3.1+n*1.6+side*2.7);
   const x=centreX+side*(edgeX-inward+sway);
   const width=.0092*Math.pow(Math.max(0,Math.sin(Math.PI*q)),.40);
   const z=centreZ+.081+.0008*Math.sin(q*5.8+n*1.2);
   tonguePositions.push(x-width,y,z,x+width,y,z);
   tongueUvs.push(q,0,q,1);
   if(j<tongueSteps){
    const k=originIndex+2*j;
    tongueIndices.push(k,k+1,k+2,k+1,k+3,k+2);
   }
  }
 }
 const tongueMesh=new pc.Mesh(app.graphicsDevice);
 tongueMesh.setPositions(tonguePositions);
 tongueMesh.setUvs(0,tongueUvs);
 tongueMesh.setIndices(tongueIndices);
 tongueMesh.update();
 const tongueEntity=new pc.Entity('GENESIS_FUEGO_V20B_BLADE_FACE_TONGUES');
 tongueEntity.addComponent('render',{meshInstances:[new pc.MeshInstance(tongueMesh,tongueMaterial)],
   castShadows:false,receiveShadows:false});
 app.root.addChild(tongueEntity);
 const fireLight=new pc.Entity('GENESIS_FUEGO_V20B_HEAT_LIGHT');
 fireLight.addComponent('light',{type:'omni',color:new pc.Color(1,.30,.055),
    intensity:0,range:1.65,castShadows:false});
 fireLight.setPosition(centreX,.25,centreZ+.13);app.root.addChild(fireLight);
 function set(time,intensity){
  const value=Math.max(0,Math.min(100,Number(intensity)||0));
  const seconds=Math.max(0,Number(time)||0);
  material.setParameter('uTime',seconds);
  material.setParameter('uIntensity',value);
  tongueMaterial.setParameter('uTime',seconds);
  tongueMaterial.setParameter('uIntensity',value);
  fireLight.light.intensity=.18*(value/100)*(.78+.22*Math.sin(seconds*8.3)**2);
 }
 set(0,0);
 const stats={ribbons:ribbonSpecs.length,segments:steps,
  haloWidthScale:0.40,haloWidthReductionPercent:60,
  animated:true,soloEffect:true,geomWidths:ribbonSpecs.map(s=>s.width),
  flameTongues:2*tonguesPerSide,
  tongueTriangles:tongueSteps*2*tonguesPerSide*2,
  tonguePosition:'front face inside edge bands, outside orbit reserved for Rayo',
  triangles:steps*2*ribbonSpecs.length+tongueSteps*2*tonguesPerSide*2,
  bladeOnly:true,intensityRange:[0,100],
  yStart,yEnd,material:material.name,depthTest:true};
 return {material,entity,tongueMaterial,tongueEntity,light:fireLight,stats,set};
}
