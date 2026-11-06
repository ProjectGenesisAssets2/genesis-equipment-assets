// Project Genesis - V20C experimental. Surface thermal patches and short organic flame tongues.
// Direct incremental successor to V20B. No approved source GLB/PBR/V12B/Rayo edits.
// The V20B long orange edge ribbons are deliberately removed to avoid electric-line appearance.
const vertexGLSL=`
attribute vec3 aPosition;
attribute vec2 aUv0;
uniform mat4 matrix_model;
uniform mat4 matrix_viewProjection;
varying vec2 vUv;
void main(void) {
 vUv=aUv0;
 gl_Position=matrix_viewProjection*matrix_model*vec4(aPosition,1.0);
}
`;
const noiseGLSL=`
float hash21(vec2 p) {return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float noise2(vec2 p) {
 vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);
 return mix(mix(hash21(i),hash21(i+vec2(1.,0.)),f.x),
            mix(hash21(i+vec2(0.,1.)),hash21(i+vec2(1.,1.)),f.x),f.y);
}
float fbm(vec2 p) {
 float a=.5,v=0.;
 for(int k=0;k<3;k++){v+=a*noise2(p);p*=2.07;a*=.50;}
 return v/.875;
}
`;
const heatFragmentGLSL=`
precision highp float;
varying vec2 vUv;
uniform float uTime;
uniform float uIntensity;
${noiseGLSL}
void main(void) {
 float power=clamp(uIntensity*.01,0.,1.);
 if(power<=.0001) discard;
 float y=clamp(vUv.x,0.,1.),x=vUv.y*2.-1.,t=uTime;
 // Glowing temperature is PATCHY and stuck to the original metal;
 // no thin straight lines and no emissive radial orbit.
 vec2 flow=vec2(x*3.8+sin(y*9.7+t*.34)*.23,y*11.2-t*.44);
 float low=fbm(flow);
 float detail=fbm(flow*2.2+vec2(3.7,-t*.18));
 float pockets=smoothstep(.36,.72,low*.77+detail*.23);
 float respiration=.88+.12*sin(t*2.6+y*13.5);
 float sideBand=smoothstep(.16,.48,abs(x))*(1.-smoothstep(.87,.985,abs(x)));
 float irregular=smoothstep(.19,.56,pockets*respiration);
 float mask=irregular*sideBand;
 // The central ridge retains its untouched metal appearance.
 float temp=clamp((low-.30)*2.0+detail*.24,0.,1.);
 vec3 deep=vec3(.51,.055,.013);
 vec3 ember=vec3(1.00,.24,.038);
 vec3 orange=vec3(1.35,.52,.095);
 vec3 color=mix(deep,ember,smoothstep(.12,.62,temp));
 color=mix(color,orange,smoothstep(.70,.96,temp)*.62);
 float alpha=clamp(power*(.12+.31*power)*mask,0.,.40);
 if(alpha<.007)discard;
 gl_FragColor=vec4(color*(.52+.66*power),alpha);
}
`;
const tongueFragmentGLSL=`
precision highp float;
varying vec2 vUv;
uniform float uTime;
uniform float uIntensity;
${noiseGLSL}
void main(void) {
 float power=clamp(uIntensity*.01,0.,1.);
 if(power<=.0001)discard;
 float v=fract(vUv.x);
 float seed=floor(vUv.x);
 float across=vUv.y*2.-1.;
 float t=uTime+seed*3.27;
 // A short teardrop flame that flickers and bends, not a current.
 float curl=.32*v*v*sin(t*2.8+v*5.4+seed*.74);
 float lateral=abs(across-curl);
 float waviness=fbm(vec2(v*6.2+seed*2.1,t*.85+across*.9));
 float radius=(.82-.50*v)*(1.-.18*waviness);
 float silhouette=1.-smoothstep(radius*.44,radius,lateral);
 float root=smoothstep(.005,.12,v);
 float tip=1.-smoothstep(.62+.10*sin(t*.9),.98,v);
 float flicker=.73+.27*fbm(vec2(v*8.2-t*1.35,across*2.+seed*1.4));
 float pockets=smoothstep(.20,.57,fbm(vec2(v*6.1-t*.82,across*2.5+seed*1.7)));
 float alpha=clamp(power*(.52+.16*power)*silhouette*root*tip*flicker*pockets,0.,.58);
 if(alpha<.009) discard;
 float heat=clamp(1.0-v*.98+.08*sin(t*2.+across*4.),0.,1.);
 vec3 red=vec3(.90,.12,.014);
 vec3 amber=vec3(1.24,.39,.041);
 vec3 yellow=vec3(1.62,.82,.18);
 vec3 color=mix(red,amber,smoothstep(.04,.60,heat));
 color=mix(color,yellow,smoothstep(.63,.97,heat));
 gl_FragColor=vec4(color*(.75+.92*power),alpha);
}
`;

export const FUEGO_V20C_SPEC=Object.freeze({
 id:'Genesis_Fuego_V20C_CalorYFlamas',approved:false,range:[0,100],
 reference:'V20B SHA 51b8f30fa81a215b2ddf4f556946f7b92cabcde0',
 source:'sword V03 original + PBR V175; HDRI Cycles V18 is distinct reference',
 visualDesign:'Mottled temperature on blade surface + isolated short organic flames',
 noElectricLines:true,noHelicalOrbit:true,disjointFromRayoOrbitByIntent:true,
 needsActualSpatialAndVisualProof:true,standalone:true,
 baseSwordUntouched:true,baseMaterialsUntouched:true,
 playcanvasShader:'GLSL procedural FBM',usesImagegen:false,
 runtimeApproved:false
});

export function createFuegoV20C(pc,app,bladeAabb) {
 function shader(name,frag) {
  const mat=new pc.ShaderMaterial({
   uniqueName:name,
   attributes:{aPosition:pc.SEMANTIC_POSITION,aUv0:pc.SEMANTIC_TEXCOORD0},
   vertexGLSL,fragmentGLSL:frag
  });
  mat.blendType=pc.BLEND_ADDITIVEALPHA;
  mat.cull=pc.CULLFACE_NONE;mat.depthTest=true;mat.depthWrite=false;
  mat.setParameter('uTime',0);mat.setParameter('uIntensity',0);mat.update();
  return mat;
 }
 function addMesh(name,positions,uvs,indices,material) {
  const mesh=new pc.Mesh(app.graphicsDevice);
  mesh.setPositions(positions);mesh.setUvs(0,uvs);mesh.setIndices(indices);mesh.update();
  const e=new pc.Entity(name);
  e.addComponent('render',{meshInstances:[new pc.MeshInstance(mesh,material)],castShadows:false,receiveShadows:false});
  app.root.addChild(e);return e;
 }
 const heatMat=shader('Genesis_Fuego_V20C_HotMetal_Patches',heatFragmentGLSL);
 const flameMat=shader('Genesis_Fuego_V20C_Short_OrganicFlames',tongueFragmentGLSL);
 const lo=bladeAabb.center.y-bladeAabb.halfExtents.y;
 const hi=bladeAabb.center.y+bladeAabb.halfExtents.y;
 const yStart=Math.max(lo+.13,-.38),yEnd=Math.min(hi-.095,.865);
 const cx=bladeAabb.center.x,cz=bladeAabb.center.z;
 const hotSteps=220,hotP=[],hotUvs=[],hotIds=[];
 for(let k=0;k<=hotSteps;k++){
  const p=k/hotSteps;
  const y=yStart+p*(yEnd-yStart);
  const taper=1.0-.46*Math.pow(Math.max(0,(p-.76)/.24),1.45);
  const width=.049*taper;
  const z=cz+.080;
  hotP.push(cx-width,y,z,cx+width,y,z);
  hotUvs.push(p,0,p,1);
  if(k<hotSteps){const a=k*2;hotIds.push(a,a+1,a+2,a+1,a+3,a+2);}
 }
 const heatEntity=addMesh('GENESIS_V20C_BLADE_HEAT_PATCHES',hotP,hotUvs,hotIds,heatMat);
 // Eight compact shape-controlled plumes on the blade, intentionally staggered.
 // For an armour/shield/jewel the future semantic binding reprojects these to that asset.
 const tongueCount=8,tongueSteps=24;
 const p=[],uvs=[],ids=[];
 for(let n=0;n<tongueCount;n++){
  const side=n%2===0?-1:1;
  const origin=p.length/3;
  const yBase=.14+.111*Math.floor(n/2)+(side>0?.05:0);
  const tongueHeight=.12+.035*Math.sin(n*2.3)**2;
  const anchor=.028*side;
  for(let k=0;k<=tongueSteps;k++){
   const q=k/tongueSteps;
   const normalizedY=Math.min(.965,yBase+q*tongueHeight);
   const y=yStart+normalizedY*(yEnd-yStart);
   const x=cx+anchor+.004*Math.sin(q*4.4+n*1.9);
   const half=.0175*Math.sin(Math.PI*Math.pow(q,.8))**.55;
   const z=cz+.082+.0013*Math.sin(q*7.+n);
   p.push(x-half,y,z,x+half,y,z);
   uvs.push(n+q*.999,0,n+q*.999,1);
   if(k<tongueSteps){const a=origin+k*2;ids.push(a,a+1,a+2,a+1,a+3,a+2);}
  }
 }
 const flameEntity=addMesh('GENESIS_V20C_BLADE_SMALL_FLAMES',p,uvs,ids,flameMat);
 const light=new pc.Entity('GENESIS_V20C_SOFT_HEAT_LIGHT');
 light.addComponent('light',{type:'omni',color:new pc.Color(1,.23,.035),intensity:0,range:1.35,castShadows:false});
 light.setPosition(cx,.24,cz+.13);app.root.addChild(light);
 function set(time,intensity){
  const t=Number.isFinite(Number(time))?Math.max(0,Number(time)):0;
  const level=Number.isFinite(Number(intensity))?Math.min(100,Math.max(0,Number(intensity))):0;
  heatMat.setParameter('uTime',t);heatMat.setParameter('uIntensity',level);
  flameMat.setParameter('uTime',t);flameMat.setParameter('uIntensity',level);
  light.light.intensity=.12*(level/100)*(.85+.15*Math.sin(t*3.5)**2);
 }
 set(0,0);
 const stats={
  modelUnmodified:true,baseV175Unmodified:true,
  heatPatches:1,hotSteps,heatTriangles:hotIds.length/3,
  flameTongues:tongueCount,tongueSteps,tongueTriangles:ids.length/3,
  triangles:(hotIds.length+ids.length)/3,
  heatOnBladeFace:true,outerElectricalOrbitAbsent:true,
  noLegacyLongRibbons:true,intensityRange:[0,100],
  yStart,yEnd,depthTest:true,
  heatFrontZ:cz+.080,flamesFrontZ:cz+.082
 };
 return {material:heatMat,heatMaterial:heatMat,flameMaterial:flameMat,heatEntity,flameEntity,light,stats,set};
}
