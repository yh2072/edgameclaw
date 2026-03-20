// Created by Yuqi Hang (github.com/yh2072)
'use strict';

function advance(script, scriptIndex) {
  if (!Array.isArray(script) || scriptIndex < 0) {
    return { nextIndex: 0, cmd: null, state: 'title', done: true };
  }
  if (scriptIndex >= script.length) {
    return { nextIndex: scriptIndex, cmd: { type: 'end' }, state: 'end', done: true };
  }

  const cmd = script[scriptIndex];
  if (!cmd || !cmd.type) {
    return advance(script, scriptIndex + 1);
  }

  switch (cmd.type) {
    case 'bg':
      return { nextIndex: scriptIndex + 1, cmd, state: 'playing', done: false, skip: true };
    case 'chapter':
      return { nextIndex: scriptIndex + 1, cmd, state: 'playing', done: false, skip: true };
    case 'dialog':
      return { nextIndex: scriptIndex, cmd, state: 'dialog', done: false };
    case 'minigame':
      return { nextIndex: scriptIndex, cmd, state: 'minigame', done: false };
    case 'end':
      return { nextIndex: scriptIndex, cmd, state: 'end', done: true };
    default:
      return advance(script, scriptIndex + 1);
  }
}

function next(script, scriptIndex) {
  if (!Array.isArray(script) || scriptIndex >= script.length) {
    return { nextIndex: scriptIndex, cmd: null, state: 'end', done: true };
  }
  let nextIndex = scriptIndex + 1;
  let result = advance(script, nextIndex);
  while (result.skip && result.nextIndex < script.length) {
    nextIndex = result.nextIndex;
    result = advance(script, nextIndex);
  }
  return { nextIndex: result.nextIndex, cmd: result.cmd, state: result.state, done: result.done };
}

module.exports = { advance, next };
