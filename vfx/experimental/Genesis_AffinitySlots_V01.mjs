// Project Genesis - Experimental contract V01. Design/validation plus V21 experimental sword prototypes (not a seven-channel-combination implementation).
// Five new isolated shader candidates now exist for the sword only. Seven-way compositing not implemented.
// Objects provide semantic anchors + masks. No material/base GLB modifications.
export const CHANNELS=Object.freeze([
 {id:'rayo',space:'external-orbit',motion:'helical-arcs',reference:'Rayo V07 approved'},
 {id:'fuego',space:'surface-edge',motion:'ascending-tongues',reference:'Fuego V20C.1 approved visually for this sword'},
 {id:'hielo',space:'surface-crystal',motion:'growing-frost',reference:'V21 independent sword candidate, not approved'},
 {id:'luz',space:'surface-points',motion:'short-radiant-pulses',reference:'V21 independent sword candidate, not approved'},
 {id:'sombra',space:'surface-recess',motion:'low-opacity-wisps',reference:'V21 independent sword candidate, not approved'},
 {id:'naturaleza',space:'surface-filaments',motion:'branching-growth',reference:'V21 independent sword candidate, not approved'},
 {id:'tierra',space:'surface-seams',motion:'mineral-vibrations',reference:'V21 independent sword candidate, not approved'}
]);
export const FAMILIES=Object.freeze({
 sword:Object.freeze({
  rayo:'orbit_around_blade',fuego:'edge_microband',hielo:'blade_upper_facet',
  luz:'guard_highlights',sombra:'fuller_recess',naturaleza:'blade_minor_filaments',
  tierra:'guard_seam'
 }),
 shield:Object.freeze({
  rayo:'outer_contour_orbit',fuego:'rim_microband',hielo:'upper_left_panel',
  luz:'boss_accent',sombra:'under_boss_recess',naturaleza:'lower_left_panel',
  tierra:'bracing_seams'
 }),
 armor:Object.freeze({
  rayo:'torso_exterior_track',fuego:'plate_edges_microband',hielo:'upper_right_plate',
  luz:'rivets_accent',sombra:'plate_recess',naturaleza:'lower_left_plate',
  tierra:'plate_seams'
 }),
 jewel:Object.freeze({
  rayo:'mini_outer_orbit',fuego:'rim_microband',hielo:'gem_upper_facet',
  luz:'gem_highlight',sombra:'setting_recess',naturaleza:'gem_lower_facet',
  tierra:'setting_seam'
 })
});
export const CHANNEL_POLICY=Object.freeze({
 channelCount:7,
 baseChannelIsElemental:false,
 intensityRange:[0,100],
 preserveMaterial:true,
 preserveGeometry:true,
 requiresPerAssetSemanticMask:true,
 requiresPerAssetBounds:true,
 requiresCameraSpaceHaloBudget:true,
 noForcedRecoloringOfOtherChannels:true,
 noAutomerge:true,
 runtimeFullyImplemented:false
});
export function clampIntensity(value){
 const n=Number(value);
 return Number.isFinite(n)?Math.max(0,Math.min(100,n)):0;
}
export function inspectProfile(family){
 const profile=FAMILIES[family];
 if(!profile)throw Error('Unknown object family '+family);
 const ids=CHANNELS.map(c=>c.id);
 if(ids.length!==7||new Set(ids).size!==7)throw Error('Channel definitions not unique');
 const keys=Object.keys(profile);
 if(keys.length!==7||keys.some(k=>!ids.includes(k))||ids.some(k=>!keys.includes(k)))
  throw Error('Incomplete channel-to-object mapping '+family);
 const semanticMasks=ids.map(id=>profile[id]);
 if(semanticMasks.some(x=>!x||typeof x!=='string')||new Set(semanticMasks).size!==7)
  throw Error('Two affinities share a semantic zone '+family);
 return {family,slots:profile,channelIds:ids,masksUnique:true,
  physicalOverlapVerified:false,haloCrosstalkVerified:false,
  requiresRealGeometryVerification:true};
}
