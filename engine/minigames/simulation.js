// =============================================================================
// EdGameClaw — AI Game-Based Learning Studio
// Created by Yuqi Hang (github.com/yh2072)
// https://github.com/yh2072/edgameclaw
// =============================================================================
registerMinigame('simulation', function(ct, data) {
  var T = (typeof GAME !== 'undefined' && GAME.theme) ? GAME.theme : {};
  var acc = T.accent || '#ff6a9a';
  var suc = T.success || '#90e0a0';
  var hl = T.highlight || '#ffc0d0';
  var dim = T.muted || '#c080a0';
  var brd = T.border || '#5a2848';
  var bg = T.bg || '#1a0818';
  var cardBg = T.cardBg || 'rgba(255,255,255,0.03)';
  var errColor = T.error || '#ff6060';
  var txt = T.text || '#f0e0f0';

  var scenarios = data.scenarios || [];
  var params = data.parameters || [];

  // --- If real scenarios are provided, use scenario-based flow ---
  if (scenarios.length > 0) {
    var currentScenario = 0;
    var playerChoices = [];
    var phase = params.length > 0 ? 'setup' : 'scenario';
    var paramValues = {};
    params.forEach(function(p) { paramValues[p.id] = p.default || p.min || 0; });

    function renderScenario() {
      var pct = Math.round((currentScenario / scenarios.length) * 100);
      if (phase === 'results') pct = 100;
      var h = '<div style="font-family:inherit;padding:12px 16px;max-width:720px;margin:0 auto">';
      h += '<div class="mg-header">';
      if (data.portrait) h += '<div id="mg-portrait"></div>';
      h += '<div class="mg-header-text"><div class="mg-title">' + (data.title || 'Simulation') + '</div></div></div>';
      h += '<div class="mg-instruction">' + (data.subtitle || '') + '</div>';
      h += '<div style="display:flex;align-items:center;gap:10px;margin:8px 0">';
      h += '<div style="flex:1;height:5px;background:rgba(255,255,255,0.06);border-radius:3px;overflow:hidden">';
      h += '<div style="height:100%;width:' + pct + '%;background:linear-gradient(90deg,' + acc + ',' + suc + ');border-radius:3px;transition:width .4s ease"></div></div>';
      h += '<span style="color:' + dim + ';font-size:11px">' + pct + '%</span></div>';

      if (phase === 'scenario') {
        var sc = scenarios[currentScenario];
        h += '<div style="background:' + cardBg + ';border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:16px;margin-bottom:12px">';
        h += '<div style="color:' + dim + ';font-size:11px;margin-bottom:8px">' + (currentScenario+1) + '/' + scenarios.length + '</div>';
        h += '<div style="color:' + txt + ';font-size:14px;line-height:1.6;margin-bottom:10px">' + sc.situation + '</div>';
        h += '<div style="color:' + hl + ';font-size:14px;font-weight:600;margin-bottom:4px">' + sc.question + '</div></div>';
        var chosen = playerChoices[currentScenario];
        sc.options.forEach(function(opt, oi) {
          var ic = chosen && chosen.id === opt.id;
          var bc = ic ? (opt.correct ? suc : errColor) : 'rgba(255,255,255,0.08)';
          var bgc = ic ? (opt.correct ? 'rgba(144,224,160,0.08)' : 'rgba(255,96,96,0.08)') : 'rgba(255,255,255,0.02)';
          h += '<div class="sim-opt" data-idx="' + oi + '" style="border:1px solid ' + bc + ';background:' + bgc + ';border-radius:12px;padding:12px 16px;margin-bottom:8px;' + (chosen ? 'pointer-events:none;' : 'pointer-events:auto;cursor:pointer;') + '">';
          h += '<div style="font-size:13px;color:' + txt + ';line-height:1.5">' + opt.text + '</div>';
          if (ic) {
            h += '<div style="margin-top:8px;color:' + (opt.correct ? suc : errColor) + ';font-size:12px">' + (opt.correct ? '✓ ' : '✗ ') + opt.feedback + '</div>';
            if (opt.outcome) h += '<div style="color:' + dim + ';font-size:11px;font-style:italic;margin-top:4px">' + opt.outcome + '</div>';
          }
          h += '</div>';
        });
        if (chosen) {
          h += '<div style="text-align:center;margin-top:12px">';
          if (currentScenario < scenarios.length - 1) h += '<button class="mg-btn" id="sim-next" style="pointer-events:auto;padding:10px 28px">→</button>';
          else h += '<button class="mg-btn" id="sim-finish" style="pointer-events:auto;padding:10px 28px">' + (_ui.seeResults || 'Results') + '</button>';
          h += '</div>';
        }
      }
      if (phase === 'results') {
        var correct = playerChoices.filter(function(c) { return c && c.correct; }).length;
        h += '<div style="text-align:center;padding:16px 0">';
        h += '<div class="mg-complete">' + (_ui.complete || 'Complete!') + '</div>';
        h += '<div style="font-size:36px;font-weight:700;color:' + acc + ';margin:12px 0">' + correct + '/' + scenarios.length + '</div>';
        h += '<button class="mg-btn" id="sim-done" style="pointer-events:auto;padding:10px 28px;margin-top:12px">' + (_ui.continue || 'Continue →') + '</button>';
        h += '</div>';
      }
      h += '</div>';
      ct.innerHTML = h;
      if (data.portrait) { var pe = ct.querySelector('#mg-portrait'); if (pe) pe.appendChild(makePortrait(data.portrait)); }
      ct.querySelectorAll('.sim-opt').forEach(function(el) {
        el.addEventListener('click', function() {
          var idx = parseInt(el.dataset.idx), sc = scenarios[currentScenario], opt = sc.options[idx];
          playerChoices[currentScenario] = opt;
          Audio.playSFX(opt.correct ? 'correct' : 'wrong');
          if (opt.correct) spawnParticles(384, 250, 'sparkle', 12);
          renderScenario();
        });
      });
      var nb = ct.querySelector('#sim-next');
      if (nb) nb.addEventListener('click', function() { Audio.playSFX('click'); currentScenario++; renderScenario(); });
      var fb = ct.querySelector('#sim-finish');
      if (fb) fb.addEventListener('click', function() { Audio.playSFX('complete'); phase = 'results'; renderScenario(); });
      var db = ct.querySelector('#sim-done');
      if (db) db.addEventListener('click', function() {
        _mgScore = Math.round((playerChoices.filter(function(c) { return c && c.correct; }).length / scenarios.length) * 100);
        closeMiniGame();
      });
      if (phase === 'results') spawnParticles(384, 250, 'confetti', 40);
    }
    renderScenario();
    return;
  }

  // -- Created by Yuqi Hang (github.com/yh2072) --
  // --- Fallback: interactive exploration when no scenarios ---
  var title = data.title || 'Simulation';
  var subtitle = data.subtitle || '';
  var explored = 0;
  var totalSteps = 5;
  var sliderVal = 50;
  var history = [];
  var canvasW = 320, canvasH = 180;

  ct.innerHTML = '<div style="font-family:inherit;padding:12px 16px;max-width:720px;margin:0 auto;color:' + txt + '">' +
    '<div class="mg-header">' +
    (data.portrait ? '<div id="fb-portrait"></div>' : '') +
    '<div class="mg-header-text"><div class="mg-title">' + title + '</div></div></div>' +
    '<div class="mg-instruction" style="margin-bottom:8px">' + subtitle + '</div>' +
    '<div style="display:flex;gap:12px;flex-wrap:wrap">' +
      '<div style="flex:1;min-width:280px">' +
        '<canvas id="fb-canvas" width="' + (canvasW*2) + '" height="' + (canvasH*2) + '" style="width:100%;max-width:' + canvasW + 'px;height:auto;border:1px solid ' + brd + ';border-radius:8px;background:' + bg + '"></canvas>' +
      '</div>' +
      '<div style="flex:1;min-width:200px;display:flex;flex-direction:column;gap:8px">' +
        '<div style="background:' + cardBg + ';border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:12px">' +
          '<div style="font-size:11px;color:' + dim + ';margin-bottom:6px;text-transform:uppercase;letter-spacing:1px">' + (_ui.parameter || 'Parameter') + '</div>' +
          '<input type="range" id="fb-slider" min="0" max="100" value="50" style="pointer-events:auto;width:100%;accent-color:' + acc + '">' +
          '<div id="fb-val" style="text-align:center;color:' + acc + ';font-size:18px;font-weight:700;margin-top:4px">50%</div>' +
        '</div>' +
        '<div style="background:' + cardBg + ';border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:12px">' +
          '<div style="font-size:11px;color:' + dim + ';margin-bottom:6px">' + (_ui.exploration || 'Exploration') + '</div>' +
          '<div id="fb-progress" style="height:6px;background:rgba(255,255,255,0.06);border-radius:3px;overflow:hidden;margin-bottom:6px">' +
            '<div id="fb-bar" style="height:100%;width:0%;background:linear-gradient(90deg,' + acc + ',' + suc + ');border-radius:3px;transition:width .4s"></div></div>' +
          '<div id="fb-status" style="font-size:12px;color:' + dim + '">' + (_ui.dragToExplore || 'Drag the slider to explore different values') + '</div>' +
        '</div>' +
        '<div id="fb-log" style="background:' + cardBg + ';border:1px solid rgba(255,255,255,0.06);border-radius:10px;padding:10px;max-height:100px;overflow-y:auto;font-size:11px;line-height:1.5;color:' + dim + '"></div>' +
      '</div>' +
    '</div>' +
    '<div id="fb-complete" style="display:none;text-align:center;margin-top:12px;padding:14px;background:rgba(144,224,160,0.06);border:1px solid ' + suc + ';border-radius:10px">' +
      '<div style="color:' + suc + ';font-size:16px;margin-bottom:8px">✓ ' + (_ui.complete || 'Exploration Complete!') + '</div>' +
      '<div style="font-size:12px;color:' + dim + ';margin-bottom:10px">' + subtitle + '</div>' +
      '<button class="mg-btn" id="fb-done" style="pointer-events:auto;padding:10px 28px">' + (_ui.continue || 'Continue →') + '</button>' +
    '</div>' +
  '</div>';

  if (data.portrait) { var pe = ct.querySelector('#fb-portrait'); if (pe) pe.appendChild(makePortrait(data.portrait)); }

  var canvas = ct.querySelector('#fb-canvas');
  var ctx2 = canvas.getContext('2d');
  ctx2.scale(2, 2);
  var slider = ct.querySelector('#fb-slider');
  var valDisplay = ct.querySelector('#fb-val');
  var bar = ct.querySelector('#fb-bar');
  var logEl = ct.querySelector('#fb-log');
  var statusEl = ct.querySelector('#fb-status');

  var zones = [
    {min:0, max:20, msg:(_ui.veryLow||'Very low range — minimal effect')},
    {min:20, max:40, msg:(_ui.low||'Low range — effect begins to appear')},
    {min:40, max:60, msg:(_ui.medium||'Medium range — balanced state')},
    {min:60, max:80, msg:(_ui.high||'High range — strong effect observed')},
    {min:80, max:100, msg:(_ui.veryHigh||'Very high range — maximum impact')}
  ];
  var visitedZones = {};

  function drawCanvas(val) {
    var w = canvasW, h = canvasH;
    ctx2.clearRect(0, 0, w, h);
    ctx2.fillStyle = bg;
    ctx2.fillRect(0, 0, w, h);

    // Animated bar chart showing response curve
    var barCount = 10;
    var barW = (w - 40) / barCount;
    for (var i = 0; i < barCount; i++) {
      var x = 20 + i * barW;
      var center = val / 100;
      var dist = Math.abs((i / (barCount - 1)) - center);
      var barH = Math.max(8, (1 - dist * 1.8) * (h - 40));
      if (barH < 0) barH = 8;
      var ratio = barH / (h - 40);

      var r = Math.round(parseInt(acc.slice(1,3),16) * ratio + 40 * (1 - ratio));
      var g = Math.round(parseInt(acc.slice(3,5),16) * ratio + 20 * (1 - ratio));
      var b = Math.round(parseInt(acc.slice(5,7),16) * ratio + 40 * (1 - ratio));
      ctx2.fillStyle = 'rgb(' + r + ',' + g + ',' + b + ')';
      ctx2.fillRect(x + 2, h - 20 - barH, barW - 4, barH);
    }

    // Cursor line
    var cx = 20 + (val / 100) * (w - 40);
    ctx2.strokeStyle = hl;
    ctx2.lineWidth = 2;
    ctx2.setLineDash([4, 4]);
    ctx2.beginPath();
    ctx2.moveTo(cx, 10);
    ctx2.lineTo(cx, h - 20);
    ctx2.stroke();
    ctx2.setLineDash([]);

    // Axis label
    ctx2.fillStyle = dim;
    ctx2.font = '10px PixelZH, Courier New, monospace';
    ctx2.textAlign = 'center';
    ctx2.fillText(val + '%', cx, h - 6);

    // History dots
    ctx2.fillStyle = 'rgba(255,255,255,0.15)';
    history.forEach(function(hv) {
      var hx = 20 + (hv / 100) * (w - 40);
      ctx2.beginPath();
      ctx2.arc(hx, h - 24, 3, 0, Math.PI * 2);
      ctx2.fill();
    });
  }

  function addLog(msg) {
    var d = document.createElement('div');
    d.style.color = hl;
    d.style.marginBottom = '3px';
    d.textContent = '▸ ' + msg;
    logEl.appendChild(d);
    logEl.scrollTop = logEl.scrollHeight;
  }

  function checkZone(val) {
    for (var i = 0; i < zones.length; i++) {
      if (val >= zones[i].min && val < zones[i].max) {
        if (!visitedZones[i]) {
          visitedZones[i] = true;
          explored++;
          addLog(zones[i].msg);
          Audio.playSFX('click');
          spawnParticles(384, 250, 'sparkle', 6);
          bar.style.width = Math.round((explored / totalSteps) * 100) + '%';
          statusEl.textContent = explored + '/' + totalSteps;
          if (explored >= totalSteps) {
            Audio.playSFX('complete');
            spawnParticles(384, 250, 'confetti', 30);
            ct.querySelector('#fb-complete').style.display = 'block';
          }
        }
        break;
      }
    }
  }

  slider.addEventListener('input', function() {
    sliderVal = parseInt(slider.value);
    valDisplay.textContent = sliderVal + '%';
    if (history.length === 0 || Math.abs(history[history.length-1] - sliderVal) > 10) {
      history.push(sliderVal);
    }
    drawCanvas(sliderVal);
    checkZone(sliderVal);
  });

  ct.querySelector('#fb-done').addEventListener('click', function() {
    _mgScore = Math.round((explored / totalSteps) * 100);
    Audio.playSFX('complete');
    closeMiniGame();
  });

  drawCanvas(sliderVal);
});
