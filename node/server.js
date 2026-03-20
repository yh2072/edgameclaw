// =============================================================================
// EdGameClaw — AI Game-Based Learning Studio
// Created by Yuqi Hang (github.com/yh2072)
// https://github.com/yh2072/edgameclaw
// =============================================================================
'use strict';

const http = require('http');
const { advance, next } = require('./engine-state.js');

const PORT = parseInt(process.env.PORT || '3100', 10);

function parseBody(req) {
  return new Promise((resolve, reject) => {
    let buf = '';
    req.on('data', (ch) => { buf += ch; });
    req.on('end', () => {
      try {
        resolve(buf ? JSON.parse(buf) : {});
      } catch (e) {
        reject(e);
      }
    });
    req.on('error', reject);
  });
}

function json(res, status, data) {
  res.writeHead(status, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(data));
}

const server = http.createServer(async (req, res) => {
  const url = req.url || '';
  const method = req.method || 'GET';

  if (method === 'GET' && (url === '/' || url === '/health')) {
    return json(res, 200, { ok: true, service: 'engine-state' });
  }

  if (method === 'POST' && url === '/state') {
    let body;
    try {
      body = await parseBody(req);
    } catch (e) {
      return json(res, 400, { error: 'Invalid JSON' });
    }
    const script = body.script;
    const scriptIndex = parseInt(body.scriptIndex, 10) || 0;
    if (!Array.isArray(script)) {
      return json(res, 400, { error: 'script must be an array' });
    }
    let result = advance(script, scriptIndex);
    while (result.skip && result.nextIndex < script.length) {
      result = advance(script, result.nextIndex);
    }
    return json(res, 200, {
      cmd: result.cmd,
      nextIndex: result.nextIndex,
      state: result.state,
      done: result.done,
    });
  }

  if (method === 'POST' && url === '/next') {
    let body;
    try {
      body = await parseBody(req);
    } catch (e) {
      return json(res, 400, { error: 'Invalid JSON' });
    }
    const script = body.script;
    const scriptIndex = parseInt(body.scriptIndex, 10) || 0;
    if (!Array.isArray(script)) {
      return json(res, 400, { error: 'script must be an array' });
    }
    const result = next(script, scriptIndex);
    return json(res, 200, {
      cmd: result.cmd,
      nextIndex: result.nextIndex,
      state: result.state,
      done: result.done,
    });
  }

  json(res, 404, { error: 'Not found' });
});

server.listen(PORT, () => {
  console.log('Engine state server listening on port', PORT);
});
