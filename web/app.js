"use strict";

var HOURS = [
  "早子时 (23-01)","丑时 (01-03)","寅时 (03-05)","卯时 (05-07)","辰时 (07-09)",
  "巳时 (09-11)","午时 (11-13)","未时 (13-15)","申时 (15-17)","酉时 (17-19)",
  "戌时 (19-21)","亥时 (21-23)","晚子时 (23-01)"
];
var GRID = { // branch -> [row, col]
  "巳":[1,1],"午":[1,2],"未":[1,3],"申":[1,4],
  "辰":[2,1],"酉":[2,4],"卯":[3,1],"戌":[3,4],
  "寅":[4,1],"丑":[4,2],"子":[4,3],"亥":[4,4]
};
var HUA = {"化禄":"hua-lu","化权":"hua-quan","化科":"hua-ke","化忌":"hua-ji"};
var CN_NUM = ["一","二","三","四","五","六","七","八"];

var state = { cal:"solar", gender:"女", leap:0, palm:null, palmType:null, hand:"right", chart:null };

function $(id){ return document.getElementById(id); }
function esc(s){ return String(s==null?"":s).replace(/[&<>]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;"}[c];}); }

// ---- form wiring ----
var hourSel = $("hour");
HOURS.forEach(function(h,i){ var o=document.createElement("option"); o.value=i; o.textContent=h; hourSel.appendChild(o); });
hourSel.value = 9;

function seg(containerId, key, attr){
  $(containerId).addEventListener("click", function(e){
    var b = e.target.closest("button"); if(!b) return;
    [].forEach.call(this.children, function(c){ c.classList.remove("on"); });
    b.classList.add("on");
    state[key] = b.dataset[attr];
  });
}
seg("genderseg","gender","g");
seg("leapseg","leap","leap");
seg("handseg","hand","hand");
$("calseg").addEventListener("click", function(e){
  var b = e.target.closest("button"); if(!b) return;
  [].forEach.call(this.children, function(c){ c.classList.remove("on"); });
  b.classList.add("on"); state.cal = b.dataset.cal;
  $("leapwrap").classList.toggle("hidden", state.cal !== "lunar");
});

$("drop").addEventListener("click", function(){ $("palm").click(); });
$("palm").addEventListener("change", function(){
  var f = this.files[0]; if(!f) return;
  var drop = $("drop");
  drop.textContent = "处理图片中…";
  var url = URL.createObjectURL(f);
  var img = new Image();
  img.onload = function(){
    URL.revokeObjectURL(url);
    // 压缩到长边 ≤1280、JPEG 0.82，避免超过 Vercel 4.5MB 请求上限
    var max = 1280, scale = Math.min(1, max / Math.max(img.width, img.height));
    var w = Math.round(img.width * scale), h = Math.round(img.height * scale);
    var cv = document.createElement("canvas"); cv.width = w; cv.height = h;
    cv.getContext("2d").drawImage(img, 0, 0, w, h);
    var dataUrl = cv.toDataURL("image/jpeg", 0.82);
    state.palm = dataUrl.split(",")[1];
    state.palmType = "image/jpeg";
    drop.classList.add("has"); drop.textContent = "已选择：" + f.name;
  };
  img.onerror = function(){ URL.revokeObjectURL(url); drop.textContent = "图片读取失败，换一张试试"; };
  img.src = url;
});

// ---- submit ----
$("form").addEventListener("submit", function(e){
  e.preventDefault();
  var payload = { date: $("date").value, hour: hourSel.value, gender: state.gender,
                  calendar: state.cal, leap: Number(state.leap) };
  $("go").disabled = true; $("go").textContent = "排盘中…";
  post("/api/chart", payload).then(function(chart){
    state.chart = chart;
    renderChart(chart, payload.date);
    requestReading(chart, null);
  }).catch(function(err){
    alert("排盘失败：" + err.message);
  }).finally(function(){
    $("go").disabled = false; $("go").textContent = "排 盘";
  });
});

function post(url, body){
  return fetch(url, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)})
    .then(function(r){ return r.text().then(function(t){
      var j;
      try { j = JSON.parse(t); }
      catch(e){
        if(r.status === 413) throw new Error("图片太大了，换一张更小的手相照片再试");
        throw new Error("服务器返回异常（" + r.status + "），请稍后重试");
      }
      if(!r.ok) throw new Error(j.error || ("HTTP " + r.status));
      return j;
    });});
}

// ---- chart render ----
function currentAge(chart, dateStr){
  var by = parseInt((dateStr||"").slice(0,4), 10);
  return by ? (new Date().getFullYear() - by) + 1 : null; // 虚岁
}
function cell(label, val){
  return '<div class="info-cell"><div class="info-cell-label">'+label+'</div>' +
         '<div class="info-cell-value">'+esc(val)+'</div></div>';
}

function renderChart(chart, dateStr){
  var age = currentAge(chart, dateStr);
  var limitBranch = null, limitPalace = null;
  if(age) chart.palaces.forEach(function(p){
    if(p.decadal_range && age>=p.decadal_range[0] && age<=p.decadal_range[1]){ limitBranch=p.earthly_branch; limitPalace=p; }
  });

  // info bar
  var soul = chart.palaces.filter(function(p){return p.tags.indexOf("命宫")>=0;})[0];
  var soulStars = soul && soul.major_stars.length ? soul.major_stars.join("·") : "空宫借对宫";
  var limitText = limitPalace ? (limitPalace.earthly_branch+"宫 "+(limitPalace.major_stars.join("")||"借对宫")) : "—";
  $("infobar").innerHTML =
    cell("五 行 局", chart.five_elements) +
    cell("命 宫", chart.soul_palace_branch+"宫") +
    cell("命 主 星", soulStars) +
    cell("当 前 大 限", limitText);

  // grid
  var grid = $("grid"); grid.innerHTML = "";
  chart.palaces.forEach(function(p){
    var g = GRID[p.earthly_branch]; if(!g) return;
    var cls = ["palace"];
    if(p.tags.indexOf("命宫")>=0) cls.push("active");
    if(p.earthly_branch===limitBranch) cls.push("current-limit");
    var el = document.createElement("div");
    el.className = cls.join(" ");
    el.style.gridRow = g[0]; el.style.gridColumn = g[1];

    function mut(name){ var m=p.mutagens.filter(function(x){return x.star===name;})[0]; return m?m.mutagen:null; }
    var stars = "";
    p.major_stars.forEach(function(s){ var m=mut(s);
      stars += '<span class="star main">'+s+'</span>' + (m?'<span class="star four-hua">'+s+m+'</span>':''); });
    p.minor_stars.forEach(function(s){ var m=mut(s);
      stars += '<span class="star">'+s+'</span>' + (m?'<span class="star four-hua">'+s+m+'★</span>':''); });
    if(!p.major_stars.length && !p.minor_stars.length) stars = '<span class="star empty">空宫</span>';

    var badges = "";
    if(p.tags.indexOf("命宫")>=0) badges += '<span class="palace-badge badge-ming">命宫</span>';
    if(p.tags.indexOf("身宫")>=0) badges += '<span class="palace-badge badge-body">身宫</span>';
    if(p.earthly_branch===limitBranch && p.tags.indexOf("命宫")<0 && p.tags.indexOf("身宫")<0)
      badges += '<span class="palace-badge badge-limit">当前大限</span>';

    el.innerHTML = '<div class="palace-name">'+p.name+'</div>' +
                   '<div class="palace-dizhi">'+p.earthly_branch+'</div>' +
                   '<div class="palace-stars">'+stars+'</div>' + badges;
    grid.appendChild(el);
  });

  // center
  var sb = (chart.chinese_date||"").split(" ")[0] || "";
  var pills = (chart.year_mutagens||[]).map(function(m){
    return '<span class="hua-tag '+(HUA[m.mutagen]||"")+'">'+esc(m.star+m.mutagen)+'</span>';
  }).join("");
  var center = document.createElement("div");
  center.className = "palace-center";
  center.innerHTML =
    '<div class="center-bagua">☯</div>' +
    '<div class="center-title">'+esc(sb)+'生人</div>' +
    '<div class="center-info">' +
      (chart.solar_date?'公历 '+chart.solar_date+'<br>':'') +
      (chart.lunar_date?'农历 '+chart.lunar_date+'<br>':'') +
      (chart.hour_name||'') + '生 · ' + chart.five_elements +
    '</div>' +
    '<div class="four-hua-bar">'+pills+'</div>';
  grid.appendChild(center);

  $("chartView").classList.remove("hidden");
  $("chartView").scrollIntoView({behavior:"smooth", block:"start"});
}

// ---- reading ----
function clientId(){
  var k = "zw_cid", v = null;
  try {
    v = localStorage.getItem(k);
    if(!v){ v = "c" + Date.now().toString(36) + Math.random().toString(36).slice(2,8); localStorage.setItem(k, v); }
  } catch(e){}
  return v;
}

function requestReading(chart, calibration){
  var rv = $("readView"), rb = $("readBody");
  rv.classList.remove("hidden");
  rb.innerHTML = '<div class="loading"><span class="spin"></span>' +
    (calibration ? 'AI 正在根据你的回答重新解读，约 1 分钟…' : 'AI 正在解读命盘，约需 1 分钟，请耐心等…') + '</div>';
  rv.scrollIntoView({behavior:"smooth", block:"start"});
  post("/api/reading", {chart:chart, palm_image:state.palm, palm_media_type:state.palmType,
                        hand:state.hand, calibration:calibration, client_id:clientId()})
    .then(function(r){ state.readingId = r._id || null; renderReading(r, !!calibration); })
    .catch(function(err){
      rb.innerHTML = '<div class="err">解读失败：'+esc(err.message)+'<br><br>' +
        '（命盘已排好。AI 解读需要在服务器设置 ANTHROPIC_API_KEY 后重试。）</div>';
    });
}

function renderReading(r, calibrated){
  var rb = $("readBody"); var html = "";
  if(calibrated) html += '<div class="calibrated-note">✓ 已根据你的回答校准 · 准确度已提升</div>';

  html += '<div class="reading-grid">';
  (r.cards||[]).forEach(function(card,i){
    var cls = ["reading-card"];
    if(card.full) cls.push("full");
    if(card.highlight) cls.push("highlight");
    if(card.teal) cls.push("teal-highlight");
    html += '<div class="'+cls.join(" ")+'" data-num="'+(CN_NUM[i]||(i+1))+'">';
    html += '<div class="card-title">'+esc(card.title)+'</div>';
    if(card.badge) html += '<div class="card-stars-badge">'+esc(card.badge)+'</div>';
    html += '<div class="card-body">'+(card.body||"")+'</div>';
    (card.probabilities||[]).forEach(function(p){
      html += '<div class="prob-bar"><span class="prob-label">'+esc(p.label)+'</span>' +
              '<div class="prob-track"><div class="prob-fill" style="width:'+p.pct+'%"></div></div>' +
              '<span class="prob-pct">'+p.pct+'%</span></div>';
    });
    if(state.readingId) html += '<div class="flag-row"><span class="flag-btn" data-card="'+esc(card.title)+'">🚩 这里不准</span></div>';
    html += '</div>';
  });
  html += '</div>';

  if(r.hand_reading && r.hand_reading.items && r.hand_reading.items.length){
    html += '<div class="section-title">手相互证</div><div class="hand-section"><div class="hand-grid">';
    r.hand_reading.items.forEach(function(it){
      html += '<div class="hand-card"><div class="hand-card-title">'+esc(it.title)+'</div>' +
              '<div class="hand-card-body">'+(it.body||"")+'</div>';
      if(it.status==="match") html += '<div class="conflict-tag match">'+esc(it.status_text||"")+'</div>';
      else if(it.status==="conflict"){
        html += '<div class="conflict-tag conflict">'+esc(it.status_text||"")+'</div>';
        if(it.resolution) html += '<div class="hand-card-body" style="margin-top:6px;font-size:11px">取舍：'+esc(it.resolution)+'</div>';
      }
      html += '</div>';
    });
    html += '</div></div>';
  }

  if(r.calibration_questions && r.calibration_questions.length){
    html += '<div class="section-title">校准追问</div>' +
            '<div class="calibration"><div class="cal-title">校准问答</div>' +
            '<div class="cal-desc">回答其中几个（可留空），点下方按钮，AI 会据此修正解读、把准确度推到 85%+。</div>' +
            '<div class="cal-questions">';
    r.calibration_questions.forEach(function(q,i){
      html += '<div class="cal-q-block"><div class="cal-q"><div class="cal-num">'+(i+1)+'</div>' +
              '<div class="cal-text">'+esc(q.text)+(q.hint?'<span>'+esc(q.hint)+'</span>':'')+'</div></div>' +
              '<input class="cal-input" data-q="'+esc(q.text)+'" placeholder="你的回答…"></div>';
    });
    html += '</div><button id="calibrateBtn" class="go" style="margin-top:20px">根据我的回答 · 重新解读</button></div>';
  }
  rb.innerHTML = html;

  document.querySelectorAll(".flag-btn").forEach(function(b){
    b.addEventListener("click", function(){
      var note = prompt("这段哪里不准？写一句帮我改进（可写预期/实际）：");
      if(note === null || !note.trim()) return;
      b.textContent = "已记录，谢谢 🙏"; b.classList.add("done");
      post("/api/feedback", {client_id: clientId(), reading_id: state.readingId,
                             card_title: b.dataset.card, note: note.trim()}).catch(function(){});
    });
  });

  var btn = $("calibrateBtn");
  if(btn) btn.addEventListener("click", function(){
    var answers = [];
    document.querySelectorAll(".cal-input").forEach(function(inp){
      if(inp.value.trim()) answers.push({question: inp.dataset.q, answer: inp.value.trim()});
    });
    if(!answers.length){ alert("至少回答一个问题，再点重新解读哦～"); return; }
    requestReading(state.chart, answers);
  });
}

// ---- 打赏 tip jar ----
(function(){
  var modal = $("tipModal");
  if(!modal) return;
  var open  = function(){ modal.classList.remove("hidden"); };
  var close = function(){ modal.classList.add("hidden"); };
  if($("tipBtn")) $("tipBtn").addEventListener("click", open);
  if($("tipClose")) $("tipClose").addEventListener("click", close);
  modal.addEventListener("click", function(e){ if(e.target === modal) close(); });
})();
