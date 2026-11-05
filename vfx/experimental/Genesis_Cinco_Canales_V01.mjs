// Project Genesis V09 — five additional experimental 0–100 VFX shaders.
// Rayo V07 approved and Fuego V01 experimental stay in their ORIGINAL modules.
// Naturaleza is NOT poison: Veneno is a separate learned technique, not default visual.
export const OTHER_CHANNELS=['Luz','Sombra','Hielo','Naturaleza','Tierra'];
const CONFIG={
 Luz:{kind:0,color:[1,.84,.40],description:'Dorado radiante'},
 Sombra:{kind:1,color:[.54,.24,.95],description:'Vetas sombrías'},
 Hielo:{kind:2,color:[.30,.77,1],description:'Escarcha cristalina'},
 Naturaleza:{kind:3,color:[.28,.84,.28],description:'Energía orgánica sin veneno'},
 Tierra:{kind:4,color:[.91,.55,.19],description:'Fisuras terrosas'}
};
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
const fragmentTemplate=`
#define CHANNEL_KIND KIND_VALUE
precision highp float;
varying vec2 vUv;
uniform float uTime;
uniform float uIntensity;
uniform vec3 uHue;
void main(void){
 float energy=clamp(uIntensity/100.0,0.0,1.0);
 if(energy<.005)discard;
 float y=vUv.x, d=abs(vUv.y*2.0-1.0),t=uTime;
 float core=pow(max(0.0,1.0-d),8.0);
 float glow=pow(max(0.0,1.0-d),2.0);
 float pattern=0.0,pulse=1.0;
 #if CHANNEL_KIND == 0
   pattern=smoothstep(-.3,.66,sin(y*48.0-t*8.0)*.75+sin(y*107.0+t*3.0)*.25);
   pulse=.80+.20*abs(sin(y*14.0+t*4.0));
 #elif CHANNEL_KIND == 1
   pattern=smoothstep(-.39,.72,sin(y*31.0+t*3.1)+.3*sin(y*94.0-t*5.6));
   pulse=.59+.41*abs(sin(y*8.0+t*2.5));
 #elif CHANNEL_KIND == 2
   float facet=abs(fract(y*24.0-t*.75)-.5)*2.0;
   pattern=(1.0-smoothstep(.26,.95,facet))*(.65+.35*abs(sin(y*129.0-t*2.0)));
   pulse=.68+.32*abs(sin(y*18.0+t*3.4));
 #elif CHANNEL_KIND == 3
   pattern=smoothstep(-.45,.69,sin(y*24.0-t*4.0+sin(y*88.0+t)*.8));
   pulse=.62+.38*abs(sin(y*14.0+t*2.0));
 #else
   pattern=smoothstep(.08,1.10,sin(y*65.0+t*1.4)+.42*sin(y*137.0-t*3.1));
   pulse=.72+.28*abs(sin(y*29.0+t*2.0));
 #endif
 float bright=energy*(.52+1.55*energy)*pattern*pulse;
 float a=clamp((.15*glow+.72*core)*energy*pattern,0.0,.75);
 if(a<.008)discard;
 gl_FragColor=vec4(uHue*bright*(.55*glow+2.3*core),a);
}
`;
export function createOtherChannel(pc,name){
 const cfg=CONFIG[name];
 if(!cfg)throw Error('Unknown channel '+name);
 const material=new pc.ShaderMaterial({
  uniqueName:'GENESIS_'+name.toUpperCase()+'_VFX_V01',
  attributes:{aPosition:pc.SEMANTIC_POSITION,aUv0:pc.SEMANTIC_TEXCOORD0},
  vertexGLSL,
  fragmentGLSL:fragmentTemplate.replace('KIND_VALUE',String(cfg.kind))
 });
 material.blendType=pc.BLEND_ADDITIVEALPHA;
 material.depthTest=true;
 material.depthWrite=false;
 material.cull=pc.CULLFACE_NONE;
 material.setParameter('uTime',0);
 material.setParameter('uIntensity',0);
 material.setParameter('uHue',new Float32Array(cfg.color));
 material.update();
 return {name,approved:false,material,description:cfg.description,
   set(time,intensity){
     material.setParameter('uTime',Number(time)||0);
     material.setParameter('uIntensity',Math.min(100,Math.max(0,Number(intensity)||0)));
   }};
}
