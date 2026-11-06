import assert from 'node:assert/strict';
import {CHANNELS,FAMILIES,CHANNEL_POLICY,clampIntensity,inspectProfile} from '../../vfx/experimental/Genesis_AffinitySlots_V01.mjs';
assert.equal(CHANNELS.length,7);
assert.equal(CHANNEL_POLICY.runtimeFullyImplemented,false);
assert.deepEqual(CHANNEL_POLICY.intensityRange,[0,100]);
assert.equal(clampIntensity(-2),0);
assert.equal(clampIntensity(112),100);
assert.equal(clampIntensity(73.5),73.5);
assert.equal(clampIntensity(Number.NaN),0);
assert.equal(clampIntensity('bad'),0);
const intended=['rayo','fuego','hielo','luz','sombra','naturaleza','tierra'];
assert.deepEqual(CHANNELS.map(c=>c.id),intended);
for(const family of ['sword','shield','armor','jewel']){
 const proof=inspectProfile(family);
 assert.equal(proof.masksUnique,true);
 assert.equal(proof.requiresRealGeometryVerification,true);
 assert.equal(proof.physicalOverlapVerified,false);
 assert.equal(proof.haloCrosstalkVerified,false);
 assert.match(proof.slots.rayo,/orbit|track/);
}
assert.throws(()=>inspectProfile('unknown'),/Unknown object family/);
console.log('GENESIS_AFFINITY_SLOT_SCHEMA_V01_VERIFIED',Object.keys(FAMILIES).join(','),'channels=7; masks=unique semantic anchors; real overlap NOT yet verified');
