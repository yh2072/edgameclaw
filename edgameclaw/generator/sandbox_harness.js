// Created by Yuqi Hang (github.com/yh2072)
/**
 * Sandbox harness for testing generated game code (simulations + pixel art).
 *
 * Mocks the EdGameClaw runtime (DOM, canvas, game globals) so that
 * registerMinigame callbacks and pixel art draw functions can be executed
 * in Node.js without a browser.
 *
 * Usage:
 *   node sandbox_harness.js <sim_code.js>                    # simulation mode (default)
 *   node sandbox_harness.js --mode sim <sim_code.js>         # simulation mode (explicit)
 *   node sandbox_harness.js --mode pixel_art <art_code.js>   # pixel art mode
 *   node sandbox_harness.js --mode cover <cover_code.js>     # cover art mode
 *
 * Exit 0 = OK, Exit 1 = runtime error (message on stderr)
 */

"use strict";

// ── Lightweight DOM mock ──────────────────────────────────────────────

function makeStyle() {
  return new Proxy({}, { set: () => true, get: () => "" });
}

function makeClassList() {
  const set = new Set();
  return {
    add: (c) => set.add(c),
    remove: (c) => set.delete(c),
    toggle: (c) => (set.has(c) ? set.delete(c) : set.add(c)),
    contains: (c) => set.has(c),
  };
}

function makeCtx2d() {
  const noop = () => {};
  const self = {
    clearRect: noop, fillRect: noop, strokeRect: noop,
    beginPath: noop, closePath: noop, moveTo: noop, lineTo: noop,
    arc: noop, arcTo: noop, ellipse: noop,
    quadraticCurveTo: noop, bezierCurveTo: noop,
    fill: noop, stroke: noop, clip: noop, save: noop, restore: noop,
    setLineDash: noop, getLineDash: () => [], lineDashOffset: 0,
    translate: noop, rotate: noop, scale: noop,
    setTransform: noop, resetTransform: noop, transform: noop,
    fillText: noop, strokeText: noop, roundRect: noop,
    drawImage: noop, putImageData: noop, createImageData: () => ({ data: new Uint8ClampedArray(4) }),
    getImageData: () => ({ data: new Uint8ClampedArray(4) }),
    createLinearGradient: () => ({ addColorStop: noop }),
    createRadialGradient: () => ({ addColorStop: noop }),
    createPattern: () => ({}),
    measureText: () => ({ width: 50 }),
    isPointInPath: () => false,
    // LLM sometimes calls g.grect/g.gpx/g.rect/g.px instead of the global grect(g,...)/gpx(g,...)
    grect: function (x, y, w, h, c) {},
    gpx: function (x, y, c) {},
    rect: function (x, y, w, h, c) {},
    px: function (x, y, c) {},
    setColor: function (c) { return this; },
    // properties
    fillStyle: "", strokeStyle: "", lineWidth: 1, lineCap: "butt",
    lineJoin: "miter", font: "", textAlign: "start", textBaseline: "alphabetic",
    globalAlpha: 1, globalCompositeOperation: "source-over",
    shadowColor: "transparent", shadowBlur: 0, shadowOffsetX: 0, shadowOffsetY: 0,
    canvas: { width: 640, height: 400 },
  };
  return new Proxy(self, { set: () => true });
}

// Base element factory — named _makeElementBase to avoid hoisting collision
// with the patched makeElement below (two function declarations with the same
// name would cause the second to overwrite the first via hoisting, making
// _origMakeElement capture itself and recurse infinitely).
function _makeElementBase(tag, attrs) {
  const children = [];
  const listeners = {};
  const el = {
    tagName: (tag || "DIV").toUpperCase(),
    id: (attrs && attrs.id) || "",
    style: makeStyle(),
    classList: makeClassList(),
    dataset: {},
    children,
    childNodes: children,
    parentNode: null,
    innerHTML: "",
    innerText: "",
    textContent: "",
    value: "",
    checked: false,
    disabled: false,
    outerHTML: `<${tag || "div"}></${tag || "div"}>`,
    width: tag === "canvas" ? 640 : 100,
    height: tag === "canvas" ? 400 : 100,
    scrollTop: 0,
    scrollHeight: 0,
    clientWidth: tag === "canvas" ? 640 : 768,
    clientHeight: tag === "canvas" ? 400 : 576,
    offsetWidth: tag === "canvas" ? 640 : 768,
    offsetHeight: tag === "canvas" ? 400 : 576,

    getAttribute: (k) => (attrs && attrs[k]) || null,
    setAttribute: (k, v) => { if (!attrs) attrs = {}; attrs[k] = v; },
    removeAttribute: () => {},
    hasAttribute: (k) => !!(attrs && attrs[k]),

    addEventListener: (type, fn) => {
      if (!listeners[type]) listeners[type] = [];
      listeners[type].push(fn);
    },
    removeEventListener: () => {},
    dispatchEvent: (ev) => {
      const fns = listeners[ev.type] || [];
      fns.forEach((fn) => fn(ev));
    },

    getContext: (type) => (type === "2d" ? makeCtx2d() : null),
    getBoundingClientRect: () => ({
      left: 0, top: 0, right: 640, bottom: 400, width: 640, height: 400, x: 0, y: 0,
    }),
    toDataURL: () => "data:image/png;base64,",

    querySelector: (sel) => {
      if (sel === "canvas" || sel.includes("canvas")) return makeElement("canvas");
      return makeElement("div", { id: sel.replace(/^#/, "") });
    },
    querySelectorAll: (sel) => [makeElement("div")],
    closest: () => null,

    appendChild: (child) => { children.push(child); child.parentNode = el; return child; },
    removeChild: (child) => { const i = children.indexOf(child); if (i >= 0) children.splice(i, 1); return child; },
    insertBefore: (child) => { children.unshift(child); return child; },
    replaceChild: (n, o) => { const i = children.indexOf(o); if (i >= 0) children[i] = n; return o; },
    remove: () => {},
    cloneNode: () => makeElement(tag, attrs),
    contains: () => true,

    focus: () => {},
    blur: () => {},
    click: () => {},
  };
  return el;
}

// ── Element ID registry (mirrors real browser getElementById behaviour) ───────

const _elemById = {};

function _registerElemId(el, id) {
  if (id) _elemById[id] = el;
}

// Patched makeElement: wraps _makeElementBase to track element IDs.
// Must NOT be a function declaration reusing the name of _makeElementBase
// (avoids hoisting collision). Using const ensures no redeclaration issues.
const _origMakeElement = _makeElementBase;
function makeElement(tag, attrs) {
  const el = _origMakeElement(tag, attrs);
  // Track id set via attrs
  if (attrs && attrs.id) _elemById[attrs.id] = el;

  // Intercept future el.id = '...' assignments
  let _id = (attrs && attrs.id) || "";
  Object.defineProperty(el, "id", {
    get: () => _id,
    set: (v) => {
      _id = v;
      if (v) _elemById[v] = el;
    },
    configurable: true,
  });

  // Intercept innerHTML assignment: scan for id="..." patterns and register stubs
  let _innerHTML = "";
  Object.defineProperty(el, "innerHTML", {
    get: () => _innerHTML,
    set: (html) => {
      _innerHTML = html || "";
      // Quick regex scan – good enough for generated game code
      const idRe = /\bid=["']([^"']+)["']/g;
      let m;
      while ((m = idRe.exec(_innerHTML)) !== null) {
        const eid = m[1];
        if (!_elemById[eid]) {
          const stub = _origMakeElement("div", { id: eid });
          _elemById[eid] = stub;
        }
      }
    },
    configurable: true,
  });

  return el;
}

// ── Game engine globals mock ──────────────────────────────────────────

const _registered = {};
let _mgScore = 0;

global.GAME = {
  theme: {
    accent: "#ff6a9a", highlight: "#ffc0d0", success: "#90e0a0",
    successBg: "rgba(80,200,120,0.12)", errorBg: "rgba(255,80,80,0.12)",
    text: "#f0e0f0", muted: "#c080a0", bg: "#1a0818",
    containerBg: "#10060e", border: "#5a3050", inputBorder: "#8a4a70",
    buttonBg: "#5a2848", buttonHover: "#7a3a60",
    cardBg: "#2a1028",
  },
  minigames: {},
};

global.Audio = {
  playSFX: () => {},
  playBGM: () => {},
  stopBGM: () => {},
};

global.spawnParticles = () => {};
global.closeMiniGame = () => {};
global.makePortrait = () => makeElement("canvas");

global.registerMinigame = function (name, fn) {
  _registered[name] = fn;
};

global.requestAnimationFrame = (fn) => {
  return 1; // return a fake ID, don't actually run the callback
};
global.cancelAnimationFrame = () => {};

global.setTimeout = (fn, ms) => 1;
global.clearTimeout = () => {};
global.setInterval = (fn, ms) => 1;
global.clearInterval = () => {};

global.document = {
  createElement: (tag) => makeElement(tag),
  createTextNode: (t) => ({ textContent: t }),
  body: makeElement("body"),
  getElementById: (id) => _elemById[id] || null,
  querySelector: () => makeElement("div"),
  querySelectorAll: () => [],
};

global.window = global;
try { global.navigator = { userAgent: "sandbox" }; } catch (e) { /* read-only in some Node versions */ }
global.Image = class { set src(v) {} get width() { return 1; } get height() { return 1; } };
global.Event = class { constructor(type) { this.type = type; } };
global.MouseEvent = class extends global.Event {};
global.TouchEvent = class extends global.Event {};

Object.defineProperty(global, "_mgScore", {
  get: () => _mgScore,
  set: (v) => { _mgScore = v; },
});

// ── Pixel art globals (used by backgrounds/icons/chars code) ─────────

function gpx(g, x, y, c) { if (g && g.fillRect) { g.fillStyle = c; g.fillRect(x, y, 1, 1); } }
function grect(g, x, y, w, h, c) { if (g && g.fillRect) { g.fillStyle = c; g.fillRect(x, y, w, h); } }
function px(x, y, c) {}
function rect(x, y, w, h, c) {}

global.gpx = gpx;
global.grect = grect;
global.px = px;
global.rect = rect;
// BACKGROUNDS may reference ctx; some LLM output uses getCtx().setColor()
global.makeCtx2d = makeCtx2d;
global.ctx = makeCtx2d();
global.getCtx = function () { return global.ctx; };
function _noop() {}
function _dispatchFalse() { return false; }
global.addEventListener = _noop;
global.removeEventListener = _noop;
global.dispatchEvent = _dispatchFalse;

let acorn = null;
try { acorn = require("acorn"); } catch (e) { acorn = null; }

const _AST_FUNCTION_TYPES = new Set(["FunctionDeclaration", "FunctionExpression", "ArrowFunctionExpression"]);
const _AST_RESERVED_GLOBALS = new Set(["registerMinigame", "closeMiniGame", "launchMiniGame", "GAME", "spawnParticles", "makePortrait", "Audio"]);

function _astLine(node) {
  return node && node.loc && node.loc.start ? node.loc.start.line : 1;
}

function _astFixTemplate(kind, name, target) {
  if (kind === "RETURN") {
    return "Fix template: move the return inside a function or callback, or replace it with a branch guard.";
  }
  if (kind === "REDECL") {
    return "Fix template: rename the local binding (for example " + name + "Local) and keep using the engine global directly.";
  }
  if (kind === "LISTENER") {
    return "Fix template: const el = ct." + (target || "querySelector") + "('#id'); if (el) el.addEventListener('click', handler);";
  }
  return "Fix template: edit only the failing line and keep the rest unchanged.";
}

function _isDirectListenerChain(node) {
  if (!node || node.type !== "CallExpression") return "";
  const callee = node.callee;
  if (!callee || callee.type !== "MemberExpression" || callee.computed) return "";
  if (!callee.property || callee.property.type !== "Identifier" || callee.property.name !== "addEventListener") return "";
  const object = callee.object;
  if (!object || object.type !== "CallExpression") return "";
  const inner = object.callee;
  if (!inner || inner.type !== "MemberExpression" || inner.computed) return "";
  if (!inner.property || inner.property.type !== "Identifier") return "";
  const target = inner.property.name;
  if (target === "querySelector" || target === "querySelectorAll" || target === "getElementById") return target;
  return "";
}

function _collectAstIssue(code) {
  if (!acorn) return null;
  let ast;
  try {
    ast = acorn.parse(code, { ecmaVersion: "latest", sourceType: "script", locations: true, allowReturnOutsideFunction: true });
  } catch (e) {
    const line = e && e.loc && e.loc.line ? e.loc.line : 1;
    return {
      phase: "SYNTAX",
      message: "AST syntax error at line " + line + ": " + e.message + " | " + _astFixTemplate("SYNTAX", "", ""),
    };
  }

  const issues = [];
  const state = { functionDepth: 0 };

  function walk(node, ancestors) {
    if (!node || typeof node.type !== "string") return;
    const parent = ancestors.length ? ancestors[ancestors.length - 1] : null;
    const grandparent = ancestors.length > 1 ? ancestors[ancestors.length - 2] : null;
    const isFunctionLike = _AST_FUNCTION_TYPES.has(node.type);
    if (isFunctionLike) state.functionDepth += 1;

    if (node.type === "ReturnStatement" && state.functionDepth === 0) {
      const line = _astLine(node);
      issues.push({
        phase: "SYNTAX",
        message: "AST top-level return detected at line " + line + ". " + _astFixTemplate("RETURN", "", ""),
      });
    }

    if (node.type === "FunctionDeclaration" && parent && parent.type === "Program" && node.id && _AST_RESERVED_GLOBALS.has(node.id.name)) {
      const line = _astLine(node);
      const name = node.id.name;
      issues.push({
        phase: "SYNTAX",
        message: "AST engine global re-declared: '" + name + "' at line " + line + ". " + _astFixTemplate("REDECL", name, ""),
      });
    }

    if (node.type === "VariableDeclarator" && parent && parent.type === "VariableDeclaration" && grandparent && grandparent.type === "Program" && node.id && node.id.type === "Identifier" && _AST_RESERVED_GLOBALS.has(node.id.name)) {
      const line = _astLine(node);
      const name = node.id.name;
      issues.push({
        phase: "SYNTAX",
        message: "AST engine global re-declared: '" + name + "' at line " + line + ". " + _astFixTemplate("REDECL", name, ""),
      });
    }

    if (node.type === "ClassDeclaration" && parent && parent.type === "Program" && node.id && _AST_RESERVED_GLOBALS.has(node.id.name)) {
      const line = _astLine(node);
      const name = node.id.name;
      issues.push({
        phase: "SYNTAX",
        message: "AST engine global re-declared: '" + name + "' at line " + line + ". " + _astFixTemplate("REDECL", name, ""),
      });
    }

    const directTarget = _isDirectListenerChain(node);
    if (directTarget) {
      const line = _astLine(node);
      issues.push({
        phase: "SYNTAX",
        message: "AST direct addEventListener() on a " + directTarget + "() result detected at line " + line + ". " + _astFixTemplate("LISTENER", "", directTarget),
      });
    }

    const nextAncestors = ancestors.concat(node);
    for (const key of Object.keys(node)) {
      if (key === "type" || key === "start" || key === "end" || key === "loc" || key === "range") continue;
      const value = node[key];
      if (!value) continue;
      if (Array.isArray(value)) {
        for (const child of value) walk(child, nextAncestors);
      } else if (typeof value.type === "string") {
        walk(value, nextAncestors);
      }
    }

    if (isFunctionLike) state.functionDepth -= 1;
  }

  walk(ast, []);
  return issues[0] || null;
}

// ── Execute ──────────────────────────────────────────────────────────

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const mode = process.argv[2] === "--mode" ? process.argv[3] : "sim";
const file = process.argv[2] === "--mode" ? process.argv[4] : process.argv[2];

if (!file) {
  process.stderr.write("Usage: node sandbox_harness.js [--mode sim|pixel_art] <code.js>\n");
  process.exit(2);
}

let code;
try {
  code = fs.readFileSync(file, "utf-8");
} catch (e) {
  process.stderr.write("SANDBOX_ERROR:LOAD:" + e.message + "\n");
  process.exit(1);
}

const _astIssue = _collectAstIssue(code);
if (_astIssue) {
  process.stderr.write("SANDBOX_ERROR:" + _astIssue.phase + ":" + _astIssue.message + "\n");
  process.exit(1);
}

// Phase 0a: LLM placeholder scan
// Catches patterns like "Implement the logic here" left as raw JS by the LLM.
// These are syntactically ambiguous — single words pass vm.Script but multi-word
// natural-language lines (e.g. "Implement the X Y") are syntax errors at runtime.
const _PLACEHOLDER_RE = /^\s*(Implement|TODO|FIXME|Add|Insert|Write|Replace|Put|Handle|Place)\s+\w+\s+\w/m;
if (_PLACEHOLDER_RE.test(code)) {
  const m = code.match(_PLACEHOLDER_RE);
  process.stderr.write(
    "SANDBOX_ERROR:SYNTAX:Placeholder text detected as raw code: " +
    (m ? m[0].trim().slice(0, 80) : "") + "\n"
  );
  process.exit(1);
}

// Phase 0b: reserved engine name re-declaration check
// In Node.js vm.runInThisContext, `const FOO` in the script scope does NOT
// conflict with `global.FOO`, so the sandbox passes. But in the browser, both
// engine.js globals and the injected game script share a Script scope, so
// re-declaring any engine name with const/let/var/function is a SyntaxError.
const _ENGINE_GLOBALS = [
  "registerMinigame", "closeMiniGame", "launchMiniGame", "GAME",
  "spawnParticles", "makePortrait", "Audio",
];
const _REDECL_RE = new RegExp(
  "(?:^|[;{]|\\n)\\s*(?:const|let|var|function)\\s+(" +
  _ENGINE_GLOBALS.map(n => n.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|") +
  ")\\s*[=(]",
  "m"
);
const _redeclMatch = code.match(_REDECL_RE);
if (_redeclMatch) {
  process.stderr.write(
    "SANDBOX_ERROR:SYNTAX:Engine global re-declared: '" + _redeclMatch[1] +
    "' — use the global directly, do not redeclare it\n"
  );
  process.exit(1);
}

// Phase 0c: direct listener chain check
// CodeAct-style fix: always null-check query results before binding events.
const _DIRECT_LISTENER_RE = /(?:querySelector|getElementById|querySelectorAll)\s*\([^)]*\)\s*\.\s*addEventListener\s*\(/m;
if (_DIRECT_LISTENER_RE.test(code)) {
  process.stderr.write(
    "SANDBOX_ERROR:SYNTAX:Direct addEventListener() on a query result detected. " +
    "Fix template: const el = ct.querySelector('#id'); if (el) el.addEventListener('click', handler).\n"
  );
  process.exit(1);
}

// Phase 1: syntax check
try {
  new vm.Script(code, { filename: path.basename(file) });
} catch (e) {
  process.stderr.write(
    "SANDBOX_ERROR:SYNTAX:" + e.message + "\n" +
    (e.stack || "").split("\n").slice(0, 3).join("\n") + "\n"
  );
  process.exit(1);
}

// Phase 2: execute top-level code
// For pixel_art and cover modes, we append validation code into the same
// script so that `const`/`let` declarations are accessible in scope.
if (mode === "pixel_art") {
  const validationSuffix = `
;(function() {
  var _g = typeof makeCtx2d === "function" ? makeCtx2d() : {};
  var _found = [];
  var _errors = [];

  if (typeof ICONS !== "undefined") {
    _found.push("ICONS");
    if (ICONS && typeof ICONS === "object") {
      Object.keys(ICONS).forEach(function(k) {
        if (typeof ICONS[k] === "function") {
          try { ICONS[k](_g, 24, 24); } catch(e) { _errors.push("ICONS." + k + ": " + e.message); }
        }
      });
    }
  }
  if (typeof CHAR_DRAW_FNS !== "undefined") {
    _found.push("CHAR_DRAW_FNS");
    if (CHAR_DRAW_FNS && typeof CHAR_DRAW_FNS === "object") {
      Object.keys(CHAR_DRAW_FNS).forEach(function(k) {
        if (typeof CHAR_DRAW_FNS[k] === "function") {
          try { CHAR_DRAW_FNS[k](_g); } catch(e) { _errors.push("CHAR_DRAW_FNS." + k + ": " + e.message); }
        }
      });
    }
  }
  if (typeof PORTRAITS !== "undefined") {
    _found.push("PORTRAITS");
    if (PORTRAITS && typeof PORTRAITS === "object") {
      Object.keys(PORTRAITS).forEach(function(k) {
        if (typeof PORTRAITS[k] === "function") {
          try { PORTRAITS[k](_g, 32, 32); } catch(e) { _errors.push("PORTRAITS." + k + ": " + e.message); }
        }
      });
    }
  }
  if (typeof BACKGROUNDS !== "undefined") {
    _found.push("BACKGROUNDS");
    if (Array.isArray(BACKGROUNDS)) {
      const ctx = makeCtx2d();
      BACKGROUNDS.forEach(function(fn, i) {
        if (typeof fn === "function") {
          try { fn(ctx); } catch(e) { _errors.push("BACKGROUNDS[" + i + "]: " + e.message); }
        }
      });
    }
  }
  if (typeof drawTitleLogo === "function") {
    _found.push("drawTitleLogo");
    try { drawTitleLogo(_g, 320, 220); } catch(e) { _errors.push("drawTitleLogo: " + e.message); }
  }

  global.__SB_FOUND = _found;
  global.__SB_ERRORS = _errors;
})();
`;
  const fullCode = code + validationSuffix;
  try {
    new vm.Script(fullCode, { filename: path.basename(file) });
  } catch (e) {
    // Fallback: maybe the suffix conflicted, re-report original syntax check
  }
  try {
    vm.runInThisContext(fullCode, { filename: path.basename(file), timeout: 5000 });
  } catch (e) {
    process.stderr.write(
      "SANDBOX_ERROR:EXEC:" + e.message + "\n" +
      (e.stack || "").split("\n").slice(0, 3).join("\n") + "\n"
    );
    process.exit(1);
  }

  const found = global.__SB_FOUND || [];
  const errors = global.__SB_ERRORS || [];

  if (errors.length > 0) {
    process.stderr.write(
      "SANDBOX_ERROR:RUNTIME:pixel_art:" + errors.join(" | ") + "\n"
    );
    process.exit(1);
  }

  process.stdout.write("SANDBOX_OK:" + found.join(",") + "\n");
  process.exit(0);

} else if (mode === "cover") {
  const coverSuffix = `
;(function() {
  var _g = typeof makeCtx2d === "function" ? makeCtx2d() : {};
  if (typeof drawCover !== "function") {
    global.__SB_COVER_ERR = "drawCover function not defined";
  } else {
    try { drawCover(_g, 128, 96); } catch(e) { global.__SB_COVER_ERR = e.message; global.__SB_COVER_STACK = (e.stack||""); }
  }
})();
`;
  const fullCode = code + coverSuffix;
  try {
    new vm.Script(fullCode, { filename: path.basename(file) });
  } catch (e) {}
  try {
    vm.runInThisContext(fullCode, { filename: path.basename(file), timeout: 5000 });
  } catch (e) {
    process.stderr.write(
      "SANDBOX_ERROR:EXEC:" + e.message + "\n" +
      (e.stack || "").split("\n").slice(0, 3).join("\n") + "\n"
    );
    process.exit(1);
  }

  if (global.__SB_COVER_ERR) {
    process.stderr.write(
      "SANDBOX_ERROR:RUNTIME:cover:" + global.__SB_COVER_ERR + "\n" +
      (global.__SB_COVER_STACK || "").split("\n").slice(0, 5).join("\n") + "\n"
    );
    process.exit(1);
  }

  process.stdout.write("SANDBOX_OK:drawCover\n");
  process.exit(0);

} else {
  // ── Simulation mode: execute code, then invoke registerMinigame callbacks
  try {
    vm.runInThisContext(code, { filename: path.basename(file), timeout: 5000 });
  } catch (e) {
    process.stderr.write(
      "SANDBOX_ERROR:EXEC:" + e.message + "\n" +
      (e.stack || "").split("\n").slice(0, 3).join("\n") + "\n"
    );
    process.exit(1);
  }

  const names = Object.keys(_registered);
  if (names.length === 0) {
    process.stderr.write("SANDBOX_ERROR:NO_REGISTER:No registerMinigame() call detected\n");
    process.exit(1);
  }

  for (const name of names) {
    const ct = makeElement("div");
    ct.clientWidth = 768;
    ct.clientHeight = 576;
    const data = { title: "Test", subtitle: "", portrait: "mentor" };
    try {
      _registered[name](ct, data);
    } catch (e) {
      process.stderr.write(
        "SANDBOX_ERROR:RUNTIME:" + name + ":" + e.message + "\n" +
        (e.stack || "").split("\n").slice(0, 5).join("\n") + "\n"
      );
      process.exit(1);
    }
  }

  process.stdout.write("SANDBOX_OK:" + names.join(",") + "\n");
  process.exit(0);
}
