// Project Genesis - Sombra V21, experimental surface-bound effect.
// Independent shader; NO approved fire or rayo source file modifications.
// Visual design: brumas de sombra oscura violácea en huecos del nervio.
import {createV21SurfaceChannel,v21NoiseGLSL} from './Genesis_AffinitySurfaceCore_V21.mjs';
const fragmentGLSL=`
precision highp float;
varying vec2 vUv;
uniform float uTime;
uniform float uIntensity;
${v21NoiseGLSL}
void main(void){
 float power=clamp(uIntensity*.01,0.,1.);
 if(power<=.0001)discard;
 float seed=floor(vUv.x),v=fract(vUv.x),x=vUv.y*2.-1.,t=uTime;
 float swirl=.30*sin(v*10.8-t*2.2+seed*.92);
 float a=abs(x-swirl*.60*v);
 float mist=genesisFbm(vec2(x*4.+seed*2.1+sin(t*.5)*.35,v*6.3-t*.42));
 float veil=1.-smoothstep(.25,.88,a);
 float fade=smoothstep(.02,.23,v)*(1.-smoothstep(.73,.99,v));
 float thicken=smoothstep(.23,.64,mist);
 float alpha=clamp(power*(.24+.34*power)*veil*fade*(.28+.72*thicken),0.,.53);
 if(alpha<.008)discard;
 // A non-neon umbral effect: muted violet absorption-like eddies and faint edges.
 vec3 dark=vec3(.075,.055,.18),rim=vec3(.49,.24,.82);
 float rimFactor=pow(1.-veil,2.)*.42+.18*thicken;
 gl_FragColor=vec4(mix(dark,rim,rimFactor)*(1.2+.3*power),alpha);
}
`;
export const SOMBRA_V21_SPEC=Object.freeze({
  id:'Genesis_Sombra_V21_Brumas',affinity:'sombra',approved:false,
  scope:'only original V03 sword test',intensity:[0,100],
  source:'V21 affinity zone contract, concept implementation not user approved',
  manifest:'vfx/experimental/Genesis_AffinitySlots_V01.mjs',
  semanticSlot:'fuller_recess',
  visual:'brumas de sombra oscura violácea en huecos del nervio',
  preservesGLB:true,preservesPBRV175:true,
  independent:true,composabilityTested:false,otherObjectFamiliesImplemented:false
});
const patches=[
 {
  "y": 0.53725,
  "height": 0.043036,
  "x": -0.02,
  "halfWidth": 0.014926,
  "curve": 0.004,
  "shape": "wisp",
  "z": 0.086
 },
 {
  "y": 0.54625,
  "height": 0.043185,
  "x": 0,
  "halfWidth": 0.012333,
  "curve": 0.004,
  "shape": "wisp",
  "z": 0.08793265306171306
 },
 {
  "y": 0.55525,
  "height": 0.040778,
  "x": 0.02,
  "halfWidth": 0.014518,
  "curve": 0.004,
  "shape": "wisp",
  "z": 0.08895634918996537
 },
 {
  "y": 0.56425,
  "height": 0.045283,
  "x": -0.009,
  "halfWidth": 0.015768,
  "curve": 0.004,
  "shape": "wisp",
  "z": 0.08858962809994661
 },
 {
  "y": 0.57325,
  "height": 0.038979,
  "x": 0.011,
  "halfWidth": 0.012814,
  "curve": 0.004,
  "shape": "wisp",
  "z": 0.08700496445046771
 },
 {
  "y": 0.58225,
  "height": 0.046663,
  "x": -0.02,
  "halfWidth": 0.01338,
  "curve": 0.004,
  "shape": "wisp",
  "z": 0.08494765031693113
 },
 {
  "y": 0.59125,
  "height": 0.038109,
  "x": 0,
  "halfWidth": 0.015985,
  "curve": 0.004,
  "shape": "wisp",
  "z": 0.08338527268275923
 },
 {
  "y": 0.60025,
  "height": 0.046965,
  "x": 0.02,
  "halfWidth": 0.013818,
  "curve": 0.004,
  "shape": "wisp",
  "z": 0.08305264216212699
 },
 {
  "y": 0.60925,
  "height": 0.038395,
  "x": -0.009,
  "halfWidth": 0.012544,
  "curve": 0.004,
  "shape": "wisp",
  "z": 0.08410620008638303
 }
];
export function createSombraV21(pc,app,bladeAabb){
 return createV21SurfaceChannel(pc,app,bladeAabb,{
  id:'sombra',fragmentGLSL,patches,lightColor:[0.25,0.18,0.47],
  lightIntensity:0.07,
 });
}
