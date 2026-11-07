/* Project Genesis V024 — noncombat mercenary explorer, experimental only.
 * Real inventory item instances are mounted on the character's verified GLTF
 * hand sockets. Equip calibration comes from per-item transforms (not guessed).
 * No attacks, combat effects, or invisible replacement weapons.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) root.GenesisMercenaryExplorerV024 = api;
})(typeof globalThis !== 'undefined' ? globalThis : null, function () {
  'use strict';
  var CLIPS = Object.freeze({
    idle: 'GENESIS_MERC_IDLE_V024',
    walk: 'GENESIS_MERC_WALK_V024',
    inspectSword: 'GENESIS_MERC_INSPECT_SWORD_V024',
    inspectShield: 'GENESIS_MERC_INSPECT_SHIELD_V024',
    walkEquipped: 'GENESIS_MERC_WALK_EQUIPPED_V024'
  });
  var SOCKETS = Object.freeze({sword:'GENESIS_SOCKET_WEAPON_R',shield:'GENESIS_SOCKET_SHIELD_L'});
  function finite3(v, label) {
    if (!Array.isArray(v) || v.length !== 3 || !v.every(Number.isFinite))
      throw new Error('Genesis V024: invalid ' + label);
    return v;
  }
  function mount(character, slot, item) {
    if (slot !== 'sword' && slot !== 'shield') throw new Error('Unknown equipment slot');
    if (!item || !item.entity || !item.inventoryId) throw new Error('Equipment must be a real inventory item instance');
    var socket = character.findByName(SOCKETS[slot]);
    if (!socket) throw new Error('Missing glTF socket: ' + SOCKETS[slot]);
    if (!item.calibration) throw new Error('Missing approved item grip calibration: ' + item.inventoryId);
    var tr = item.calibration;
    finite3(tr.position, 'position');finite3(tr.euler, 'euler');finite3(tr.scale, 'scale');
    socket.addChild(item.entity);
    item.entity.setLocalPosition(tr.position[0],tr.position[1],tr.position[2]);
    item.entity.setLocalEulerAngles(tr.euler[0],tr.euler[1],tr.euler[2]);
    item.entity.setLocalScale(tr.scale[0],tr.scale[1],tr.scale[2]);
    item.entity.enabled = true;
    return item;
  }
  function Explorer(character, layer) {
    if (!character || typeof character.findByName !== 'function')
      throw new Error('Genesis V024: mercenary RenderEntity required');
    this.character = character;
    this.layer = layer || null;
    this.equipment = {sword:null,shield:null};
    this.current = null;
  }
  Explorer.prototype.equip = function (slot,item) {
    if (!(slot in this.equipment)) throw new Error('Unsupported equipment slot');
    var prev=this.equipment[slot];
    if (prev) this.unequip(slot);
    try {this.equipment[slot]=mount(this.character,slot,item);}
    catch (e) { if (prev) this.equipment[slot]=mount(this.character,slot,prev);throw e; }
    return this.equipment[slot].inventoryId;
  };
  Explorer.prototype.unequip = function (slot) {
    if (!(slot in this.equipment)) throw new Error('Unsupported equipment slot');
    var item=this.equipment[slot];
    if (item && item.entity) {
      var parent=item.entity.parent;
      if (parent && typeof parent.removeChild==='function') parent.removeChild(item.entity);
    }
    this.equipment[slot]=null;
    return item;
  };
  Explorer.prototype.clipFor = function (intent) {
    if (intent==='walk') return (this.equipment.sword || this.equipment.shield) ? CLIPS.walkEquipped : CLIPS.walk;
    if (intent==='inspectSword' && !this.equipment.sword) throw new Error('No sword to inspect');
    if (intent==='inspectShield' && !this.equipment.shield) throw new Error('No shield to inspect');
    if (!Object.prototype.hasOwnProperty.call(CLIPS,intent)) throw new Error('No explorer clip: '+intent);
    return CLIPS[intent];
  };
  Explorer.prototype.play = function (intent,blendSeconds) {
    var clip=this.clipFor(intent);this.current=clip;
    if (this.layer && typeof this.layer.transition==='function')
      this.layer.transition(clip,Number.isFinite(blendSeconds)?blendSeconds:.18);
    return clip;
  };
  return {Explorer:Explorer,CLIPS:CLIPS,SOCKETS:SOCKETS};
});
