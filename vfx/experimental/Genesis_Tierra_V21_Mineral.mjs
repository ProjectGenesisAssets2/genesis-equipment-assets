// Project Genesis - Tierra V21, experimental surface-bound effect.
// Independent shader; NO approved fire or rayo source file modifications.
// Visual design: fracturas minerales angulares y resonancia de vetas sólidas.
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
 vec2 p=vec2(x*2.3+seed*1.7,v*7.1);
 float edge=1.-smoothstep(.48,.95,abs(x));
 float fractureA=1.-smoothstep(.018,.13,abs(fract(p.x*1.2+p.y*.68)-.5));
 float fractureB=1.-smoothstep(.023,.14,abs(fract(p.x*.76-p.y*.43)-.5));
 float facets=step(.55,genesisNoise(floor(p*2.4)+seed));
 float resonance=.68+.32*pow(.5+.5*sin(t*2.1+seed*.49),4.);
 float cracked=clamp(fractureA*.52+fractureB*.34+facets*.12,0.,1.);
 float alpha=clamp(power*(.31+.39*power)*edge*cracked*resonance,0.,.68);
 if(alpha<.008)discard;
 vec3 ochre=vec3(.83,.42,.12),stone=vec3(.64,.62,.44),gold=vec3(1.39,.96,.44);
 vec3 rgb=mix(ochre,stone,facets*.43);
 rgb=mix(rgb,gold,(fractureA+fractureB)*.27);
 gl_FragColor=vec4(rgb*(.62+.58*power),alpha);
}
`;
export const TIERRA_V21_SPEC=Object.freeze({
  id:'Genesis_Tierra_V21_Mineral',affinity:'tierra',approved:false,
  scope:'only original V03 sword test',intensity:[0,100],
  source:'V21 affinity zone contract, concept implementation not user approved',
  manifest:'vfx/experimental/Genesis_AffinitySlots_V01.mjs',
  semanticSlot:'guard_seam',
  visual:'fracturas minerales angulares y resonancia de vetas sólidas',
  preservesGLB:true,preservesPBRV175:true,
  independent:true,composabilityTested:false,otherObjectFamiliesImplemented:false
});
const patches=[
 {
  "y": 0.149864,
  "height": 0.026554,
  "x": -0.02,
  "halfWidth": 0.015859,
  "curve": 0.001,
  "shape": "shard",
  "z": 0.086
 },
 {
  "y": 0.157318,
  "height": 0.026646,
  "x": 0,
  "halfWidth": 0.013103,
  "curve": 0.001,
  "shape": "shard",
  "z": 0.08793265306171306
 },
 {
  "y": 0.164773,
  "height": 0.025161,
  "x": 0.02,
  "halfWidth": 0.015425,
  "curve": 0.001,
  "shape": "shard",
  "z": 0.08895634918996537
 },
 {
  "y": 0.172227,
  "height": 0.02794,
  "x": -0.009,
  "halfWidth": 0.016753,
  "curve": 0.001,
  "shape": "shard",
  "z": 0.08858962809994661
 },
 {
  "y": 0.179682,
  "height": 0.024051,
  "x": 0.011,
  "halfWidth": 0.013615,
  "curve": 0.001,
  "shape": "shard",
  "z": 0.08700496445046771
 },
 {
  "y": 0.187136,
  "height": 0.028792,
  "x": -0.02,
  "halfWidth": 0.014216,
  "curve": 0.001,
  "shape": "shard",
  "z": 0.08494765031693113
 },
 {
  "y": 0.194591,
  "height": 0.023514,
  "x": 0,
  "halfWidth": 0.016985,
  "curve": 0.001,
  "shape": "shard",
  "z": 0.08338527268275923
 },
 {
  "y": 0.202045,
  "height": 0.028978,
  "x": 0.02,
  "halfWidth": 0.014682,
  "curve": 0.001,
  "shape": "shard",
  "z": 0.08305264216212699
 },
 {
  "y": 0.2095,
  "height": 0.023691,
  "x": -0.009,
  "halfWidth": 0.013328,
  "curve": 0.001,
  "shape": "shard",
  "z": 0.08410620008638303
 },
 {
  "y": 0.216955,
  "height": 0.028451,
  "x": 0.011,
  "halfWidth": 0.016463,
  "curve": 0.001,
  "shape": "shard",
  "z": 0.08605044170145304
 }
];
export function createTierraV21(pc,app,bladeAabb){
 return createV21SurfaceChannel(pc,app,bladeAabb,{
  id:'tierra',fragmentGLSL,patches,lightColor:[0.88,0.61,0.26],
  lightIntensity:0.12,
 });
}
