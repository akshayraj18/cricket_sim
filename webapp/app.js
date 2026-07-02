let state = null;
let activeView = "squad";
let batSort = { key: "runs", dir: -1 };
let bowlSort = { key: "wickets", dir: -1 };
let squadSort = { key: "bat", dir: -1 };
let tableSort = { key: "points", dir: -1 };
let draftSort = { key: "ovr", dir: -1 };
let expandedTeam = "";
let draftTimer = { seconds: 60, paused: true, key: "", id: null };
let viewedScorecard = null;
let dragPayload = null;
let selectedFixtureWeek = null;
let savesLoaded = false;

const teams = [
  "Chennai Super Kings", "Mumbai Indians", "Royal Challengers Bengaluru",
  "Kolkata Knight Riders", "Sunrisers Hyderabad", "Rajasthan Royals",
  "Delhi Capitals", "Gujarat Titans", "Lucknow Super Giants", "Punjab Kings"
];

const NAV_ICONS = {
  draft: "🎯", retention: "🔁", season: "🏏", match: "🔴",
  standings: "🏆", stats: "📊", squad: "👥", history: "📜"
};
const NAV_SHORT = {
  draft: "Draft", retention: "Retain", season: "Matches", match: "Live",
  standings: "Table", stats: "Stats", squad: "Squad", history: "History"
};

async function api(path, body = null) {
  const opts = body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {};
  const res = await fetch(path, opts);
  const data = await res.json();
  if (!res.ok) {
    alert(data.error || "Request failed");
    throw new Error(data.error || "Request failed");
  }
  return data;
}

function $(id) { return document.getElementById(id); }
function esc(s) { return String(s ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;"); }
function myTeam() { return state.teams.find(t => t.name === state.user_team); }
function team(name) { return state.teams.find(t => t.name === name); }
function allPlayers() { return state ? [...(state.draft?.available || []), ...state.teams.flatMap(t => t.roster)] : []; }
function playerByName(name) { return allPlayers().find(p => p.name === name); }
function playerLink(name) { return name ? `<button class="name-link" onclick='event.stopPropagation();showPlayer(${JSON.stringify(name)})'>${esc(name)}</button>` : "-"; }

function shortName(name) {
  const parts = String(name || "").trim().split(/\s+/);
  if (parts.length <= 1) return esc(name);
  return esc(`${parts[0][0]}. ${parts.slice(1).join(" ")}`);
}

function table(headers, rows, sortPrefix = "") {
  const head = headers.map(h => {
    const key = Array.isArray(h) ? h[1] : "";
    const label = Array.isArray(h) ? h[0] : h;
    return `<th ${key ? `data-sort="${sortPrefix}${key}"` : ""}>${label}</th>`;
  }).join("");
  return `<thead><tr>${head}</tr></thead><tbody>${rows.map(row => `<tr>${row.map(cell => `<td>${cell}</td>`).join("")}</tr>`).join("")}</tbody>`;
}

function teamLabel(t) {
  return `<span class="team-chip"><span class="crest" style="background:linear-gradient(135deg,${t.primary},${t.accent})">${t.abbr}</span>${esc(t.name)}</span>`;
}

function applyTeamTheme() {
  if (!state || !state.user_team) return;
  const t = myTeam();
  if (!t) return;
  applyThemeColors(t);
}

function applyThemeColors(t) {
  const dark = colorLuma(t.primary) <= colorLuma(t.accent) ? t.primary : t.accent;
  const light = colorLuma(t.primary) <= colorLuma(t.accent) ? t.accent : t.primary;
  document.documentElement.style.setProperty("--team-primary", dark);
  document.documentElement.style.setProperty("--team-accent", light);
  document.documentElement.style.setProperty("--blue", dark);
  document.documentElement.style.setProperty("--gold", light);
}

function applyMatchTheme(match) {
  const name = match?.score?.batting_team || match?.innings?.at(-1)?.team || match?.card?.winner || state.user_team;
  applyThemeColors(team(name) || myTeam());
}

function colorLuma(hex) {
  const raw = String(hex || "#000").replace("#", "");
  const n = parseInt(raw.length === 3 ? raw.split("").map(x => x + x).join("") : raw, 16);
  const r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
  return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
}

function showPlayer(name) {
  const p = playerByName(name);
  if (!p) return;
  const t = team(p.team);
  const primary = t?.primary || "#111827";
  const accent = t?.accent || "#d1ab3e";
  const existing = $("playerModal");
  if (existing) existing.remove();
  document.body.insertAdjacentHTML("beforeend", `
    <div id="playerModal" class="modal-backdrop" onclick="closePlayerModal(event)">
      <section class="player-modal" style="--modal-primary:${primary};--modal-accent:${accent}">
        <button class="modal-close" onclick="document.getElementById('playerModal').remove()">Close</button>
        <h2>${esc(p.name)}</h2>
        <p>${esc(p.team || "Unassigned")} · ${p.overseas ? "Overseas" : "Indian"} · Age ${p.age} · Form ${p.form}</p>
        <div class="mini-grid">
          <span>OVR <b>${esc(p.ovr_progression || p.ovr)}</b></span><span>Bat <b>${esc(p.bat_progression || p.bat)}</b></span><span>Bowl <b>${esc(p.bowl_progression || p.bowl)}</b></span>
          <span>Role <b>${esc(p.role)}</b></span><span>Bat Hand <b>${esc(p.batting_hand)}</b></span><span>Bowl Hand <b>${esc(p.bowling_hand)}</b></span>
          <span>Bat Type <b>${esc(p.batting_archetype)}</b></span><span>Bowl Phase <b>${esc(p.bowling_phase)}</b></span><span>Ball <b>${esc(p.bowling_type)}</b></span>
        </div>
        <div class="profile-notes"><b>Strength</b><p>${esc(p.strengths || "-")}</p><b>Weakness</b><p>${esc(p.weaknesses || "-")}</p></div>
        <div class="mini-grid">
          <span>Runs <b>${p.runs || 0}</b></span><span>SR <b>${p.sr || 0}</b></span><span>HS <b>${p.hs || 0}</b></span><span>Wkts <b>${p.wickets || 0}</b></span><span>Econ <b>${p.econ || 0}</b></span><span>MVP <b>${p.mvp || 0}</b></span>
        </div>
      </section>
    </div>`);
}

function closePlayerModal(event) {
  if (event.target.id === "playerModal") event.target.remove();
}

function uniqueXi(names, roster) {
  const rosterNames = roster.map(p => p.name);
  const picked = [];
  (names || []).forEach(name => {
    if (rosterNames.includes(name) && !picked.includes(name) && picked.length < 11) picked.push(name);
  });
  rosterNames.forEach(name => {
    if (!picked.includes(name) && picked.length < 11) picked.push(name);
  });
  return picked;
}

function xiValidationError(names, label) {
  const clean = names.filter(Boolean);
  const duplicates = [...new Set(clean.filter((name, i) => clean.indexOf(name) !== i))];
  if (clean.length !== 11) return `${label} must contain 11 players.`;
  if (new Set(clean).size !== 11) return `${label} has duplicate players: ${duplicates.join(", ")}.`;
  const players = clean.map(playerByName).filter(Boolean);
  if (players.filter(p => ["Batsman", "Wicketkeeper", "All-Rounder"].includes(p.role)).length < 6) return `${label} needs at least 6 batting options.`;
  if (players.filter(p => p.overseas).length > 4) return `${label} cannot include more than 4 overseas players.`;
  return "";
}

function impactSubError(impactSubName, startingXi, roster) {
  if (!impactSubName) return "Choose an Impact Sub from your squad.";
  if (!roster.some(p => p.name === impactSubName)) return "Choose an Impact Sub from your squad.";
  if (startingXi.includes(impactSubName)) return "Impact Sub must not already be in the Starting XI.";
  return "";
}

function bowlingPlanError(names, label = "Bowling plan") {
  if (!names.length) return "";
  if (names.length !== 20) return `${label} must contain all 20 overs, or be left completely blank.`;
  const overbowled = [...new Set(names)].filter(name => names.filter(x => x === name).length > 4);
  if (overbowled.length) return `${label} has a bowler above the 4-over limit: ${overbowled.join(", ")}.`;
  const repeatAt = names.find((name, i) => i > 0 && name === names[i - 1]);
  return repeatAt ? `${label} cannot use ${repeatAt} in consecutive overs.` : "";
}

function shortDismissal(text, name = "") {
  const raw = String(text || "").trim();
  if (!raw || raw.toLowerCase() === "did not bat") return "";
  if (raw.toLowerCase() === "not out") return "NOT OUT";
  const prefix = `${name} `;
  return name && raw.startsWith(prefix) ? raw.slice(prefix.length) : raw;
}

function battingCardRows(rows, score = null) {
  const striker = score?.striker || "";
  const nonStriker = score?.non_striker || "";
  return (rows || []).map(b => {
    const inCrease = score?.pending_next_batter ? b.name === nonStriker : (b.name === striker || b.name === nonStriker);
    const howOut = b.dismissal ? shortDismissal(b.dismissal, b.name) : (inCrease ? "NOT OUT" : "");
    return [playerLink(b.name), esc(howOut), b.runs, b.balls, b.fours, b.sixes];
  });
}

function battingCardTable(rows, score = null) {
  return table(["Batter","How Out","R","B","4s","6s"], battingCardRows(rows, score));
}

function bowlingCardTable(rows) {
  const active = (rows || []).filter(b => (b.balls || 0) > 0 || b.overs);
  return table(["Bowler","O","R","W","Econ"], active.map(b => [playerLink(b.name), b.overs || `${Math.floor((b.balls || 0)/6)}.${(b.balls || 0)%6}`, b.runs, b.wickets, b.econ]));
}

function motmContribution(card) {
  const name = card?.motm || "";
  const parts = [];
  (card?.innings || []).forEach(i => {
    const bat = (i.full_batting || i.batting || []).find(b => b.name === name);
    if (bat && (bat.balls || bat.runs)) parts.push(`${bat.runs} (${bat.balls})`);
    const bowl = (i.full_bowling || i.bowling || []).find(b => b.name === name);
    if (bowl && ((bowl.balls || 0) > 0 || bowl.overs)) parts.push(`${bowl.wickets}/${bowl.runs} in ${bowl.overs || `${Math.floor((bowl.balls || 0)/6)}.${(bowl.balls || 0)%6}`}`);
  });
  return parts.length ? ` - ${parts.join(", ")}` : "";
}

function broadcastStrip(score) {
  const striker = score.bat_stats.find(p => p.name === score.striker) || {};
  const nonStriker = score.bat_stats.find(p => p.name === score.non_striker) || {};
  const bowler = score.bowl_stats.find(p => p.name === score.active_bowler) || {};
  const bowlerBalls = Number(bowler.balls || 0);
  const bowlerOvers = bowler.overs || `${Math.floor(bowlerBalls / 6)}.${bowlerBalls % 6}`;
  const overBalls = (score.current_over || []).map(e => `<span class="${e.kind === "wicket" ? "wicket-cell" : ""}">${esc(e.label)}</span>`).join("");
  const blankBalls = Array.from({ length: Math.max(0, 6 - (score.current_over || []).length) }, () => "<span></span>").join("");
  const neededRuns = score.target ? Math.max(0, score.target - score.runs) : 0;
  const ballsLeft = Math.max(0, 120 - score.balls);
  const needText = score.target ? `${neededRuns} needed off ${ballsLeft}` : `${ballsLeft} balls left`;
  return `
    <div class="broadcast-strip">
      <div class="team-name-strip"><b>${esc(score.batting_team)}</b></div>
      <div class="team-score"><strong>${score.runs}-${score.wickets}</strong><span>Over ${Math.floor(score.balls/6)}.${score.balls%6}</span></div>
      <div class="bat-strip">
        <div class="on-strike"><span class="strike-mark">&gt;</span><span class="bat-line">${playerLink(score.striker)} <b>${striker.runs || 0} (${striker.balls || 0})</b></span></div>
        <div><span class="strike-mark"></span><span class="bat-line">${playerLink(score.non_striker)} <b>${nonStriker.runs || 0} (${nonStriker.balls || 0})</b></span></div>
      </div>
      <div class="partnership-strip"><span>Partnership</span><b>${esc(score.partnership || "0 off 0")}</b></div>
      <div class="over-strip">
        <div class="bowler-line"><span>${playerLink(score.active_bowler || "") || `<button class="name-link">Choose bowler</button>`}</span><b>${bowler.wickets || 0}-${bowler.runs || 0}</b><small>${bowlerOvers} ov</small></div>
        <div class="ball-row">${overBalls}${blankBalls}</div>
      </div>
      <div class="target-strip"><b>${esc(score.phase)}</b>${score.target ? `<span>${neededRuns} needed off ${ballsLeft}</span><small>Target ${score.target}</small>` : `<span>${ballsLeft} balls left</span>`}</div>
    </div>`;
}

function helpPanel(title, items) {
  return `<div><b>${esc(title)}</b><ul>${items.map(item => `<li>${esc(item)}</li>`).join("")}</ul></div>`;
}

function renderGuide() {
  const guides = {
    draft: ["Search, sort, and filter the draft board before making your pick.", "Click a player name for a scouting popup with roles, skills, and team status.", "Use the drafted XI preview to check balance as your squad fills."],
    retention: ["Select exactly the required number of players before confirming.", "Retained players stay with you into the next draft; everyone else returns to the pool.", "MVP, age, role, and overall are useful tie-breakers."],
    season: ["Enter Match Hub to play your team match ball by ball.", "Quick Sim Current Match Day completes every fixture in the round, including your game.", "Click any completed fixture or recent scorecard to open the full scorecard."],
    league_complete: ["League stage is paused before playoffs so you can inspect the table and season stats.", "Use Start Playoffs when you are ready to move into the knockout bracket.", "After playoffs finish, retention will also wait for your confirmation."],
    match: state.live_match ? ["Follow the current match state from top to bottom.", "During lineup setup, drag players between XI and bench pools, then confirm.", "During play, choose aggression and bowlers, or use the skip buttons to simulate chunks."] : ["This screen shows a full scorecard when you open a completed match.", "Use Back to Match Centre to return to fixtures and recent results.", "Click player names inside scorecards for profile details."],
    standings: ["Click a team name to expand its squad snapshot.", "Click table headers to sort by record, points, NRR, or form.", "Form icons show recent results from completed fixtures."],
    stats: ["Search any player by name to pin a quick profile at the top.", "Click column headers to sort batting or bowling tables.", "Leader panels show award races and season-long category leaders."],
    squad: ["Set captain, vice-captain, and keeper before saving match presets.", "Drag a player from an XI into its bench pool to open a spot, then drag a bench player into the empty slot.", "The two XIs can be identical or differ by one impact-sub player; bowling plans need 20 legal overs or can be blank."],
    history: ["Finished seasons appear here after the final.", "Use this screen to track champions, runners-up, MVPs, and final tables across years.", "Current-season form and NRR reset when a new season begins."],
  };
  const items = state.phase === "league_complete" && activeView === "season" ? guides.league_complete : (guides[activeView] || ["Use the tabs to move between squad, matches, stats, and league history."]);
  $("screenGuide").innerHTML = helpPanel("Quick Guide", items);
}

function draftStartingXi(roster) {
  const selected = [];
  let overseasCount = 0;
  const add = p => {
    if (!p || selected.includes(p.name) || selected.length >= 11) return;
    if (p.overseas && overseasCount >= 4) return;
    selected.push(p.name);
    if (p.overseas) overseasCount++;
  };
  const isBatter = p => p.role === "Batsman" || p.role === "Wicketkeeper" || p.role === "All-Rounder";
  const isBowler = p => p.role.includes("Bowler") || p.role === "All-Rounder";
  [...roster].filter(p => p.role === "Wicketkeeper").sort((a,b)=>b.bat-a.bat).slice(0,1).forEach(add);
  [...roster].filter(p => isBatter(p)).sort((a,b)=>b.bat-a.bat).forEach(p => { if (selected.filter(n => isBatter(playerByName(n))).length < 6) add(p); });
  [...roster].filter(p => isBowler(p)).sort((a,b)=>b.bowl-a.bowl).forEach(p => { if (selected.filter(n => isBowler(playerByName(n))).length < 5) add(p); });
  [...roster].sort((a,b)=>b.ovr-a.ovr).forEach(add);
  // Arrange the XI by natural slot (CSV natural_slot: 1-2 openers, 3-5 middle,
  // 6-7 death, 8-11 tail), breaking ties within a slot by batting rating — a
  // strict natural-position assignment mirroring the server's smart_batting_order.
  const xi = selected.map(playerByName).filter(Boolean);
  xi.sort((a, b) => (a.preferred_position || 6) - (b.preferred_position || 6) || b.bat - a.bat);
  return xi.map(p => p.name);
}

function draggableList(id, names, length = names.length, editable = true, options = {}) {
  const items = Array.from({length}, (_, i) => names[i] || "");
  const group = options.group || id;
  const fixed = options.pool ? "0" : "1";
  const extra = name => `${options.showNaturalSlot ? naturalSlotChip(name) : ""}${options.showMeta ? playerLineupMeta(name) : ""}${playerBadges(name)}`;
  const rows = items.map((name, i) => `
    <div class="drag-item ${name ? "" : "empty"}" draggable="${editable && name ? "true" : "false"}" data-name="${esc(name)}">
      <span>${i + 1}</span><b>${name ? playerLink(name) + extra(name) : "Empty"}</b>
    </div>`).join("");
  const zonesAttr = options.showZones ? ` data-zones="${options.zones === OVER_PHASE_ZONES ? "overs" : "order"}"` : "";
  return `<div id="${id}" class="drag-list ${options.pool ? "pool-list" : ""} ${options.showZones ? "zoned-list" : ""}" data-editable="${editable ? "1" : "0"}" data-group="${esc(group)}" data-fixed="${fixed}" data-allow-duplicates="${options.allowDuplicates ? "1" : "0"}" data-copy-source="${options.copySource ? "1" : "0"}"${zonesAttr}>${rows}</div>`;
}

function playerBadges(name) {
  const t = myTeam();
  if (!t) return "";
  const player = playerByName(name);
  const bits = [];
  if (name === t.captain) bits.push("C");
  if (name === t.vice_captain) bits.push("VC");
  const selectedKeeper = $("squadKeeper")?.value || t.saved_wicketkeeper;
  if (player?.role === "Wicketkeeper" && name === selectedKeeper) bits.push("WK");
  return bits.length ? ` <small class="role-badges">${bits.join(" · ")}</small>` : "";
}

const ORDER_ZONES = [
  { key: "top", label: "Openers", range: [1, 2], className: "zone-top" },
  { key: "middle", label: "Middle Order", range: [3, 5], className: "zone-middle" },
  { key: "death", label: "Death Overs", range: [6, 7], className: "zone-death" },
  { key: "tail", label: "Tail", range: [8, 11], className: "zone-tail" },
];

const OVER_PHASE_ZONES = [
  { key: "powerplay", label: "Powerplay", range: [1, 6], className: "zone-top" },
  { key: "middle", label: "Middle Overs", range: [7, 15], className: "zone-middle" },
  { key: "death", label: "Death Overs", range: [16, 20], className: "zone-death" },
];

function zoneForSlot(slotNumber, zones = ORDER_ZONES) {
  return zones.find(z => slotNumber >= z.range[0] && slotNumber <= z.range[1]) || zones[Math.floor(zones.length / 2)];
}

function slotZoneChip(slotNumber) {
  const zone = zoneForSlot(slotNumber || 6);
  return `<span class="slot-chip ${zone.className}">${zone.label}</span>`;
}

function slotZoneLabel(slotNumber) {
  return zoneForSlot(slotNumber || 6).label;
}

function naturalSlotChip(name) {
  const player = playerByName(name);
  if (!player) return "";
  const pos = player.preferred_position || 6;
  const zone = zoneForSlot(pos);
  return ` <small class="slot-chip ${zone.className}" title="Naturally bats in the ${zone.label.toLowerCase()}">${zone.label}</small>`;
}

function playerLineupMeta(name) {
  const player = playerByName(name);
  if (!player) return "";
  return ` <small class="lineup-meta">${esc(player.role)} · ${esc(player.batting_archetype || "")} · Bat ${player.bat} / Bowl ${player.bowl}</small>`;
}

function dragListNames(id) {
  return [...document.querySelectorAll(`#${id} .drag-item`)].map(x => x.dataset.name).filter(Boolean);
}

function enableDragLists() {
  document.querySelectorAll(".drag-list[data-editable='1']").forEach(list => {
    list.addEventListener("dragover", e => e.preventDefault());
    list.addEventListener("drop", e => {
      if (e.target.closest(".drag-item") || !dragPayload || list.dataset.fixed === "1") return;
      e.preventDefault();
      dropIntoPool(list, null);
    });
    list.querySelectorAll(".drag-item").forEach(bindDragItem);
    renumberList(list);
  });
}

function bindDragItem(item) {
  item.draggable = !!item.dataset.name && item.closest(".drag-list")?.dataset.editable === "1";
  item.addEventListener("dragstart", e => {
    if (e.target.closest(".name-link")) {
      e.preventDefault();
      return;
    }
    if (!item.dataset.name) {
      e.preventDefault();
      return;
    }
    dragPayload = { item, name: item.dataset.name, list: item.closest(".drag-list") };
    item.classList.add("dragging");
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", item.dataset.name);
  });
  item.addEventListener("dragend", () => {
    item.classList.remove("dragging");
    dragPayload = null;
  });
  item.addEventListener("dragover", e => e.preventDefault());
  item.addEventListener("drop", e => {
    e.preventDefault();
    e.stopPropagation();
    const targetList = item.closest(".drag-list");
    if (!dragPayload || !targetList || targetList.dataset.editable !== "1") return;
    if (targetList.dataset.fixed === "1") dropIntoFixed(targetList, item);
    else dropIntoPool(targetList, item);
  });
}

function hasListName(list, name, exceptItem = null) {
  return [...list.querySelectorAll(".drag-item")].some(item => item !== exceptItem && item.dataset.name === name);
}

function sameDragGroup(targetList) {
  return dragPayload?.list?.dataset.group === targetList.dataset.group;
}

function dropIntoFixed(targetList, targetItem) {
  if (!sameDragGroup(targetList)) return;
  const sourceList = dragPayload.list;
  const sourceItem = dragPayload.item;
  if (sourceList === targetList) {
    swapItems(sourceItem, targetItem);
    refreshBowlingPlanPools();
    return;
  }
  if (targetItem.dataset.name) {
    alert("Drag a player out to the bench pool before filling that XI slot.");
    return;
  }
  if (targetList.dataset.allowDuplicates !== "1" && hasListName(targetList, dragPayload.name)) {
    alert("That player is already in this list.");
    return;
  }
  setDragItemName(targetItem, dragPayload.name);
  consumeSource();
  renumberList(targetList);
  refreshBowlingPlanPools();
}

function dropIntoPool(targetList, beforeItem) {
  if (!sameDragGroup(targetList)) return;
  const sourceList = dragPayload.list;
  const sourceItem = dragPayload.item;
  if (sourceList === targetList) {
    if (beforeItem && beforeItem !== sourceItem) targetList.insertBefore(sourceItem, beforeItem);
    renumberList(targetList);
    return;
  }
  if (targetList.dataset.allowDuplicates !== "1" && hasListName(targetList, dragPayload.name)) {
    if (sourceList.dataset.fixed === "1" && sourceList.dataset.copySource !== "1") {
      setDragItemName(sourceItem, "");
      renumberList(sourceList);
      refreshBowlingPlanPools();
    }
    return;
  }
  const node = createDragItem(dragPayload.name);
  if (beforeItem) targetList.insertBefore(node, beforeItem);
  else targetList.appendChild(node);
  bindDragItem(node);
  consumeSource();
  renumberList(targetList);
  refreshBowlingPlanPools();
}

function consumeSource() {
  const sourceList = dragPayload.list;
  const sourceItem = dragPayload.item;
  if (sourceList.dataset.copySource === "1") return;
  if (sourceList.dataset.fixed === "1") setDragItemName(sourceItem, "");
  else sourceItem.remove();
  renumberList(sourceList);
}

function swapItems(a, b) {
  if (!a || !b || a === b) return;
  const aName = a.dataset.name;
  setDragItemName(a, b.dataset.name);
  setDragItemName(b, aName);
  renumberList(a.closest(".drag-list"));
}

function createDragItem(name) {
  const item = document.createElement("div");
  item.className = "drag-item";
  item.innerHTML = `<span></span><b></b>`;
  setDragItemName(item, name);
  return item;
}

function setDragItemName(item, name) {
  item.dataset.name = name || "";
  item.classList.toggle("empty", !name);
  item.draggable = !!name;
  item.querySelector("b").innerHTML = name ? playerLink(name) + playerBadges(name) : "Empty";
}

function refreshDragBadges() {
  document.querySelectorAll(".drag-item").forEach(item => {
    if (item.dataset.name) setDragItemName(item, item.dataset.name);
  });
}

function renumberList(list) {
  list.querySelectorAll(".zone-divider").forEach(d => d.remove());
  const items = [...list.querySelectorAll(".drag-item")];
  items.forEach((item, i) => {
    const marker = item.querySelector("span");
    if (marker) marker.textContent = i + 1;
    item.draggable = !!item.dataset.name && list.dataset.editable === "1";
  });
  if (list.classList.contains("zoned-list")) {
    const zones = list.dataset.zones === "overs" ? OVER_PHASE_ZONES : ORDER_ZONES;
    let lastZoneKey = null;
    items.forEach((item, i) => {
      const zone = zoneForSlot(i + 1, zones);
      if (zone.key !== lastZoneKey) {
        lastZoneKey = zone.key;
        const divider = document.createElement("div");
        divider.className = `zone-divider ${zone.className}`;
        divider.innerHTML = `${zone.label} <small>(slots ${zone.range[0]}-${Math.min(zone.range[1], items.length)})</small>`;
        list.insertBefore(divider, item);
      }
    });
  }
}

function benchNames(roster, xi) {
  return roster.map(p => p.name).filter(name => !xi.includes(name));
}

function bowlingOptions(names) {
  return names.map(playerByName).filter(p => p && (p.role.includes("Bowler") || p.role === "All-Rounder")).map(p => p.name);
}

function impactOptions(roster) {
  return roster.map(p => `<option value="${esc(p.name)}">${esc(p.name)} · ${esc(p.role)} · ${slotZoneLabel(p.preferred_position)} · Bat ${p.bat}/Bowl ${p.bowl}</option>`).join("");
}

function refreshBowlingPlanPools() {
  [
    { xi: "startingXIList", pool: "squadBowlPlanPool", plan: "squadBowlPlan", extra: () => $("impactSubSelect")?.value || "" },
    { xi: "matchBowlXI", pool: "matchBowlPlanPool", plan: "matchBowlPlan" },
  ].forEach(({ xi, pool, plan, extra }) => {
    const poolList = $(pool);
    if (!poolList || !$(xi)) return;
    const names = bowlingOptions([...dragListNames(xi), ...(extra ? [extra()] : [])].filter(Boolean));
    poolList.innerHTML = "";
    names.forEach(name => {
      const node = createDragItem(name);
      poolList.appendChild(node);
      bindDragItem(node);
    });
    renumberList(poolList);
    document.querySelectorAll(`#${plan} .drag-item`).forEach(item => {
      if (item.dataset.name && !names.includes(item.dataset.name)) setDragItemName(item, "");
    });
    if ($(plan)) renumberList($(plan));
  });
}

function setDragListNames(id, names, length = names.length, options = {}) {
  const list = $(id);
  if (!list) return;
  if (options.showZones) list.classList.add("zoned-list");
  list.innerHTML = Array.from({ length }, (_, i) => {
    const name = names[i] || "";
    const extra = name ? `${options.showNaturalSlot ? naturalSlotChip(name) : ""}${playerBadges(name)}` : "";
    return `<div class="drag-item ${name ? "" : "empty"}" draggable="${name ? "true" : "false"}" data-name="${esc(name)}"><span>${i + 1}</span><b>${name ? playerLink(name) + extra : "Empty"}</b></div>`;
  }).join("");
  list.querySelectorAll(".drag-item").forEach(bindDragItem);
  renumberList(list);
}

function refillBenchPool(poolId, xiNames, group) {
  const t = myTeam();
  const names = benchNames(t.roster, xiNames);
  const pool = $(poolId);
  if (!pool) return;
  pool.dataset.group = group;
  pool.innerHTML = names.map(name => `<div class="drag-item" draggable="true" data-name="${esc(name)}"><span></span><b>${playerLink(name)}${playerBadges(name)}</b></div>`).join("");
  pool.querySelectorAll(".drag-item").forEach(bindDragItem);
  renumberList(pool);
}

async function autofillStartingXi() {
  await api("/api/presets", { starting_xi: null, impact_sub_name: null });
  state = await api("/api/state");
  render();
}

function clearStartingXi() {
  setDragListNames("startingXIList", [], 11);
  refillBenchPool("startingXIBenchPool", [], "squadStarting");
  if ($("impactSubSelect")) $("impactSubSelect").value = "";
  refreshBowlingPlanPools();
}

function autofillBowlingPlan() {
  const startingXi = dragListNames("startingXIList");
  const impactSub = $("impactSubSelect")?.value || "";
  const eligible = bowlingOptions([...startingXi, impactSub].filter(Boolean)).map(playerByName).filter(Boolean);
  const used = {};
  const plan = [];
  for (let over = 0; over < 20; over += 1) {
    const phase = over < 6 ? "Powerplay" : over < 15 ? "Middle Overs" : "Death Overs";
    const candidates = eligible.filter(p => (used[p.name] || 0) < 4 && p.name !== plan.at(-1));
    const pool = candidates.length ? candidates : eligible.filter(p => (used[p.name] || 0) < 4);
    if (!pool.length) break;
    const chosen = [...pool].sort((a, b) => bowlingPlanScore(b, phase) - bowlingPlanScore(a, phase))[0];
    plan.push(chosen.name);
    used[chosen.name] = (used[chosen.name] || 0) + 1;
  }
  setDragListNames("squadBowlPlan", plan, 20);
}

function clearBowlingPlan() {
  setDragListNames("squadBowlPlan", [], 20);
}

function bowlingPlanScore(p, phase) {
  let score = Number(p.bowl) || 0;
  const bowlType = `${p.bowling_type || ""} ${p.bowling_phase || ""}`;
  if (p.bowling_phase === phase) score += 10;
  if (phase === "Powerplay" && /Swing|Fast|Medium|Seam|New-ball/i.test(bowlType)) score += 5;
  if (phase === "Middle Overs" && /Spin|Orthodox|Leg|Off|Mystery/i.test(bowlType)) score += 7;
  if (phase === "Death Overs" && /Death|Fast|Variations|Yorker/i.test(bowlType)) score += 7;
  return score;
}

async function load() {
  seedTeamSelect();
  state = await api("/api/state");
  render();
}

function seedTeamSelect() {
  $("teamSelect").innerHTML = teams.map(name => `<option value="${esc(name)}">${esc(name)}</option>`).join("");
}

async function newLeague() {
  state = await api("/api/new", { team: $("teamSelect").value, difficulty: $("difficultySelect")?.value || "hard", draft_pool: $("draftPoolSelect")?.value || "current" });
  selectedFixtureWeek = null;
  viewedScorecard = null;
  activeView = defaultView();
  render();
}

async function loadLeague(name) {
  state = await api("/api/load", { name: name || "" });
  selectedFixtureWeek = null;
  viewedScorecard = null;
  activeView = defaultView();
  render();
}

async function saveLeague() {
  const suggested = state?.save_name || state?.user_team || "My Career";
  const name = prompt("Name this save:", suggested);
  if (name === null) return;
  if (!name.trim()) { alert("Enter a save name."); return; }
  state = await api("/api/save", { name: name.trim() });
  await refreshSavesPanel();
  render();
}

async function deleteSave(name) {
  if (!confirm(`Delete the save "${name}"? This cannot be undone.`)) return;
  await api("/api/delete-save", { name });
  await refreshSavesPanel();
}

async function refreshSavesPanel() {
  const panel = $("savesList");
  const hint = $("savesHint");
  if (!panel) return;
  try {
    const { saves } = await api("/api/saves");
    if (!saves.length) {
      hint.textContent = "No saves yet — start a league and save it to see it here.";
      panel.innerHTML = "";
      return;
    }
    hint.textContent = `${saves.length} save${saves.length === 1 ? "" : "s"} available.`;
    panel.innerHTML = saves.map(s => `
      <div class="save-row">
        <div class="save-row-info">
          <strong>${esc(s.name)}</strong>
          <small>${esc(s.team || "Unassigned")} · Season ${esc(s.season)} · ${esc((s.phase || "").replace(/_/g, " "))} · ${new Date(s.updated_at * 1000).toLocaleString()}</small>
        </div>
        <div class="save-row-actions">
          <button data-load="${esc(s.name)}">Load</button>
          <button data-delete="${esc(s.name)}" class="danger">Delete</button>
        </div>
      </div>`).join("");
    panel.querySelectorAll("[data-load]").forEach(btn => btn.onclick = () => loadLeague(btn.dataset.load));
    panel.querySelectorAll("[data-delete]").forEach(btn => btn.onclick = () => deleteSave(btn.dataset.delete));
  } catch {
    hint.textContent = "Couldn't load saves.";
  }
}

function defaultView() {
  if (!state || state.phase === "title") return "title";
  if (state.phase === "draft") return "draft";
  if (state.phase === "retention") return "retention";
  if (state.live_match) return "match";
  if (state.phase === "season" || state.phase === "league_complete" || state.phase === "playoffs") return "season";
  if (state.phase === "season_end") return "season";
  return "squad";
}

function visibleViews() {
  if (!state || state.phase === "title") return [];
  const views = [{ id: "squad", label: "My Squad" }, { id: "history", label: "League History" }];
  if (state.phase === "draft") views.unshift({ id: "draft", label: "Draft Room" });
  if (state.phase === "retention") views.unshift({ id: "retention", label: "Retentions" });
  if (state.phase === "season" || state.phase === "league_complete" || state.phase === "playoffs") {
    views.unshift({ id: "season", label: "Match Centre" });
    if (state.live_match || viewedScorecard) views.unshift({ id: "match", label: state.live_match ? "Live Match Hub" : "Scorecard" });
    views.push({ id: "standings", label: "Points Table" }, { id: "stats", label: "Stats Hub" });
  }
  if (state.phase === "season_end") {
    views.unshift({ id: "season", label: "Season Review" });
    views.push({ id: "standings", label: "Final Table" }, { id: "stats", label: "Stats Hub" });
  }
  return views;
}

function setView(view) {
  activeView = view;
  render();
}

function render() {
  $("titleScreen").classList.toggle("hidden", state && state.phase !== "title");
  $("appShell").classList.toggle("hidden", !state || state.phase === "title");
  if (!state || state.phase === "title") {
    if (!savesLoaded) { savesLoaded = true; refreshSavesPanel(); }
  } else {
    savesLoaded = false;
  }
  const displayYear = state?.season || 2026;
  document.title = `Cricket Franchise Sim ${displayYear}`;
  if ($("titleHeading")) $("titleHeading").textContent = "Cricket Franchise Universe";
  if (!state || state.phase === "title") return;
  applyTeamTheme();

  const views = visibleViews();
  if (!views.find(v => v.id === activeView)) activeView = defaultView();
  $("tabs").innerHTML = views.map(v => `<button class="${v.id === activeView ? "active" : ""}" onclick="setView('${v.id}')"><span class="nav-icon">${NAV_ICONS[v.id] || "•"}</span><span class="nav-label">${NAV_SHORT[v.id] || v.label}</span></button>`).join("");
  document.querySelectorAll(".view").forEach(v => v.classList.add("hidden"));
  const node = $(`view${activeView[0].toUpperCase()}${activeView.slice(1)}`);
  if (node) node.classList.remove("hidden");

  $("pageTitle").textContent = pageTitle();
  $("controlRoomLabel").textContent = `Season ${state.season} Control Room`;
  $("statusText").textContent = state.status;
  renderSummary();
  renderGuide();
  renderDraft();
  renderRetention();
  renderSeason();
  renderMatch();
  renderStandings();
  renderStats();
  renderSquad();
  renderHistory();
  attachSortHandlers();
}

function pageTitle() {
  if (state.phase === "draft") return state.draft_type === "mega" ? "Mega Draft Room" : "Post-Retention Draft";
  if (state.phase === "retention") return "Retention Window";
  if (state.live_match) return "Live Match Hub";
  if (state.phase === "league_complete") return "League Stage Complete";
  if (state.phase === "playoffs") return "Playoffs";
  if (state.phase === "season_end") return "Season Review";
  return `Season ${state.season}`;
}

function renderSummary() {
  const t = myTeam();
  const teamMvp = t?.roster?.length ? sortedPlayers(t.roster, { key: "mvp", dir: -1 })[0] : null;
  const recordOrSquad = state.phase === "draft" ? `${t.roster.length}/${state.squad_size}` : `${t.wins}-${t.losses}`;
  const metrics = [
    ["Phase", state.phase.replace("_", " ").toUpperCase()],
    ["Season", state.season],
    ["My Team", t.abbr],
    [state.phase === "draft" ? "Squad" : "Record", recordOrSquad],
    ["Team MVP", teamMvp ? `${teamMvp.name} (${teamMvp.mvp || 0})` : "-"],
  ];
  $("summary").innerHTML = metrics.map(([k, v]) => `<div class="metric"><span>${k}</span><b>${esc(v)}</b></div>`).join("");
}

async function draftPlayer(name) {
  state = await api("/api/draft", { player: name });
  if (state.phase === "season") selectedFixtureWeek = null;
  resetDraftTimer();
  render();
}

async function startDraft() {
  state = await api("/api/start-draft", {});
  resetDraftTimer();
  render();
}

async function autodraft(mode) {
  state = await api("/api/autodraft", { mode });
  if (state.phase === "season") selectedFixtureWeek = null;
  resetDraftTimer();
  render();
}

function resetDraftTimer() {
  draftTimer.seconds = 60;
  draftTimer.key = "";
}

function toggleDraftTimer() {
  draftTimer.paused = !draftTimer.paused;
  renderDraft();
}

function renderDraft() {
  if (!state.teams.length) return;
  const draftStarted = state.draft.started !== false;
  if (state.phase === "draft" && draftStarted) startDraftTimer();
  const timerKey = `${state.draft.round}:${state.draft.pick}:${state.draft.current_team}`;
  if (draftTimer.key !== timerKey) {
    draftTimer.key = timerKey;
    draftTimer.seconds = 60;
  }
  const q = ($("draftSearch")?.value || "").toLowerCase();
  const role = $("draftRole")?.value || "All Roles";
  const nation = $("draftNation")?.value || "All";
  const batType = $("draftBatType")?.value || "All";
  const bowlType = $("draftBowlType")?.value || "All";
  const slot = $("draftSlot")?.value || "All Slots";
  const players = sortedPlayers(state.draft.available.filter(p =>
    (!q || `${p.name} ${p.team} ${p.role} ${p.batting_archetype} ${p.bowling_phase} ${p.bowling_type}`.toLowerCase().includes(q)) &&
    (role === "All Roles" || p.role === role) &&
    (nation === "All" || (nation === "Overseas" ? p.overseas : !p.overseas)) &&
    (batType === "All" || p.batting_archetype === batType) &&
    (bowlType === "All" || p.bowling_phase === bowlType || p.bowling_type === bowlType) &&
    (slot === "All Slots" || slotZoneLabel(p.preferred_position) === slot)
  ), draftSort);
  $("draftTable").innerHTML = table(
    [["Player","name"], ["Role","role"], ["Age","age"], ["OVR","ovr"], ["Bat","bat"], ["Bowl","bowl"], ["Bat Type","batting_archetype"], ["Bowl Type","bowling_type"], ["Natural Slot","preferred_position"], ["Origin","overseas"], ""],
    players.slice(0, 160).map(p => [
      `${playerLink(p.name)}<br><small>${esc(p.batting_hand)} bat · ${esc(p.bowling_hand)} bowl</small>`,
      `${p.role}${p.allrounder_style ? `<br><small>${esc(p.allrounder_style)}</small>` : ""}`, p.age, p.ovr, p.bat, p.bowl, esc(p.batting_archetype), esc(p.bowling_type),
      slotZoneChip(p.preferred_position),
      p.overseas ? "OS" : "IND",
      state.phase === "draft" && draftStarted && state.draft.current_team === state.user_team ? `<button class="good" onclick='draftPlayer(${JSON.stringify(p.name)})'>Pick</button>` : "",
    ]), "draft:"
  );
  const user = myTeam();
  const overseas = user.roster.filter(p => p.overseas).length;
  const indian = user.roster.length - overseas;
  $("draftStatus").innerHTML = state.phase === "draft" && !draftStarted
    ? `<b>Mega Draft Setup</b><p>You selected ${esc(state.user_team)}. The draft order is set, and you are drafting ${ordinalText(state.draft.user_pick_position || 0)} in a snake draft with premier cricket players.</p><button class="primary" onclick="startDraft()">Start Draft</button><small>Nothing has been picked yet. Once you start, CPU teams will draft until your first pick.</small>`
    : state.phase === "draft"
    ? `<b>${state.draft_type === "mega" ? "Mega Snake Draft" : "Reverse-Standings Draft"}</b><br>Round ${state.draft.round}, Pick ${state.draft.pick}<br>On the clock: ${esc(state.draft.current_team)}<div class="draft-clock ${draftTimer.paused ? "paused" : ""}"><span>${draftTimer.paused ? "Timer Paused" : formatClock(draftTimer.seconds)}</span><button onclick="toggleDraftTimer()">${draftTimer.paused ? "Start Timer" : "Pause Timer"}</button></div><div class="toolbar"><button onclick="autodraft('one')">Autodraft Pick</button><button class="danger" onclick="autodraft('all')">Autodraft Draft</button></div><small>Mode: ${(state.difficulty || "hard").toUpperCase()} · Roster: ${indian} Indian · ${overseas} Overseas. XI targets: batting XI minimum 7 batting options, bowling XI minimum 6 bowling options.</small>`
    : esc(state.status);
  $("draftNeeds").innerHTML = Object.entries(state.draft.needs || {}).map(([k, v]) => `<div class="card"><span class="pill">${k.toUpperCase()}</span><h2>${v}</h2></div>`).join("");
  $("draftHistory").innerHTML = table(["Pick", "Rnd", "Type", "Team", "Player", "OVR"], state.draft.history.slice().reverse().map(h => [h.pick, h.round, h.type, h.team, h.player, h.ovr]));
  const draftXi = draftStartingXi(user.roster);
  $("draftExtra")?.remove();
  $("draftNeeds").insertAdjacentHTML("afterend", `<div id="draftExtra"><h2 class="gap-top">Drafted XI Preview</h2><div class="notice">A planning preview only — players are slotted by where they naturally bat (e.g. a #4/#5 type lands in the middle order automatically), grouped into openers/middle/death/tail zones. Reorder it to visualize combinations; final match XIs are set on My Squad.</div>${draggableList("draftXiPreview", draftXi, 11, true, { showZones: true, showNaturalSlot: true })}<h2 class="gap-top">My Drafted Squad</h2><div class="table-wrap short"><table>${table(["Player","Role","OVR","Bat","Bowl","Type","Natural Slot","Origin"], user.roster.map(p => [playerLink(p.name), p.role, p.ovr, p.bat, p.bowl, esc(p.batting_archetype), slotZoneChip(p.preferred_position), p.overseas ? "OS" : "IND"]))}</table></div></div>`);
  enableDragLists();
}

function startDraftTimer() {
  if (draftTimer.id) return;
  draftTimer.id = setInterval(async () => {
    if (!state || state.phase !== "draft" || draftTimer.paused) return;
    draftTimer.seconds -= 1;
    if (draftTimer.seconds <= 0 && state.draft.current_team === state.user_team) {
      draftTimer.paused = true;
      await autodraft("one");
      return;
    }
    const node = document.querySelector(".draft-clock span");
    if (node) node.textContent = formatClock(draftTimer.seconds);
  }, 1000);
}

function formatClock(seconds) {
  return `0:${String(Math.max(0, seconds)).padStart(2, "0")}`;
}

function ordinalText(number) {
  if (!number) return "-";
  const suffix = 10 <= number % 100 && number % 100 <= 20 ? "th" : ({1:"st",2:"nd",3:"rd"}[number % 10] || "th");
  return `${number}${suffix}`;
}

async function submitRetention() {
  const players = [...document.querySelectorAll(".retainPick:checked")].map(x => x.value);
  state = await api("/api/retention", { players });
  viewedScorecard = null;
  activeView = "draft";
  render();
}

function renderRetention() {
  if (!state.teams.length) return;
  $("retentionNotice").innerHTML = `Choose exactly <b>${state.retention_limit}</b> players to retain. Every second off-season is a mini-reset where teams keep only 5.`;
  $("retentionGrid").innerHTML = state.retention.players.map((p, i) => `
    <label class="player-card">
      <input class="retainPick" type="checkbox" value="${esc(p.name)}" ${i < state.retention_limit ? "checked" : ""}>
      <b>${playerLink(p.name)}</b>
      <small>${p.role} · OVR ${p.ovr} · Age ${p.age} · MVP ${p.mvp}</small>
    </label>`).join("");
}

async function beginMatch() {
  state = await api("/api/begin-match", {});
  activeView = state.live_match ? "match" : activeView;
  render();
}

async function simulateRound() {
  state = await api("/api/simulate-round", {});
  selectedFixtureWeek = null;
  if (state.phase === "playoffs" || state.phase === "season_end") {
    // Playoff quick-sim doesn't update match_log — don't show a stale league scorecard.
    viewedScorecard = null;
    activeView = defaultView();
  } else {
    viewedScorecard = [...(state.match_log || [])].reverse().find(c => state.user_team && (c.team1 === state.user_team || c.team2 === state.user_team)) || state.match_log?.at(-1) || null;
    activeView = viewedScorecard ? "match" : defaultView();
  }
  render();
}

async function startPlayoffs() {
  state = await api("/api/start-playoffs", {});
  selectedFixtureWeek = null;
  viewedScorecard = null;
  activeView = "season";
  render();
}

function setFixtureWeek(value) {
  selectedFixtureWeek = Number(value);
  renderSeason();
}

function currentPlayoffMatch() {
  return state.playoffs?.[state.playoff_index] || null;
}

function renderSeason() {
  if (!state.teams.length) return;
  $("seasonNotice").innerHTML = state.phase === "season_end"
    ? `${esc(state.status)} <button class="primary" onclick="openRetention()">Open Retention Window</button>`
    : state.phase === "league_complete"
    ? `${esc(state.status)} <button class="primary" onclick="startPlayoffs()">Start Playoffs</button>`
    : esc(state.status);
  const playoff = currentPlayoffMatch();
  const userInPlayoff = state.phase !== "playoffs" || (playoff && [playoff.team1, playoff.team2].includes(state.user_team));
  $("beginMatchBtn").disabled = !["season", "playoffs"].includes(state.phase) || !!state.live_match || !userInPlayoff;
  $("simulateRoundBtn").disabled = !["season", "playoffs"].includes(state.phase);
  $("beginMatchBtn").textContent = state.phase === "playoffs" ? "Enter Playoff Match Hub" : "Enter Match Hub";
  $("simulateRoundBtn").textContent = state.phase === "playoffs" ? "Quick Sim Next Playoff" : "Quick Sim Current Match Day";
  if (state.phase === "season") {
    const selectedWeek = Number(selectedFixtureWeek || state.round || 1);
    const selectedTeam = $("fixtureTeam")?.value || "All Teams";
    const fixtureRows = selectedTeam === "All Teams"
      ? (state.schedule[selectedWeek - 1] || []).map(f => ({ week: selectedWeek, pair: f }))
      : state.schedule.flatMap((week, idx) => week.filter(f => f.includes(selectedTeam)).map(f => ({ week: idx + 1, pair: f })));
    $("fixturePanel").innerHTML = `
      <div class="toolbar gap-top">
        <select id="fixtureWeek" onchange="setFixtureWeek(this.value)">${state.schedule.map((_, i) => `<option value="${i + 1}" ${selectedWeek === i + 1 ? "selected" : ""}>Week ${i + 1}</option>`).join("")}</select>
        <select id="fixtureTeam" onchange="renderSeason()"><option>All Teams</option>${state.teams.map(t => `<option value="${esc(t.name)}" ${selectedTeam === t.name ? "selected" : ""}>${esc(t.name)}</option>`).join("")}</select>
      </div>
      <div class="cards">${fixtureRows.map(({week, pair}) => fixtureCard(week, pair[0], pair[1])).join("")}</div>`;
  } else if (state.phase === "league_complete") {
    $("fixturePanel").innerHTML = `<div class="notice">Regular season is complete. The table and stats are frozen until you start playoffs.</div><div class="cards">${state.standings.slice(0, 4).map((t, i) => `<div class="card"><span class="pill">Seed ${i + 1}</span><h2>${teamLabel(t)}</h2><p>${t.wins}-${t.losses} · ${t.points} pts · NRR ${Number(t.nrr).toFixed(3)}</p></div>`).join("")}</div>`;
  } else {
    $("fixturePanel").innerHTML = `<div class="cards">${state.playoffs.map(p => `<div class="card"><span class="pill">${p.status}</span><h2>${p.name}</h2><p>${esc(p.team1 || "TBD")} vs ${esc(p.team2 || "TBD")}</p><b>${p.winner ? esc(p.winner) + " advanced" : ""}</b></div>`).join("")}</div>`;
  }
  $("recentMatches").innerHTML = state.match_log.slice().reverse().map((card, i) => `
    <button class="card scorecard-link" onclick='viewScorecard(${JSON.stringify(card)})'>
      <span class="pill">${esc(card.stage)}</span>
      <h2>${esc(card.winner)} ${esc(card.margin)}</h2>
      <small>${esc(card.venue)} · Toss: ${esc(card.toss)} · 🏆 MOTM: ${esc(card.motm)}</small>
      <div class="recent-scorecard-grid">${card.innings.map(recentInningsBox).join("")}</div>
    </button>`).join("") || `<div class="notice">No matches played yet.</div>`;
}

function viewScorecard(card) {
  viewedScorecard = card;
  activeView = "match";
  render();
}

function recentInningsBox(i) {
  const batters = (i.batting || []).slice(0, 4).map(b => `<div><span>${shortName(b.name)}</span><b>${b.runs} (${b.balls})</b></div>`).join("");
  const bowlers = (i.bowling || []).slice(0, 4).map(b => `<div><span>${shortName(b.name)}</span><b>${b.wickets}/${b.runs}</b></div>`).join("");
  return `
    <div class="recent-innings">
      <h3>${esc(i.team)} <strong>${esc(i.score)}</strong></h3>
      <div class="recent-columns">
        <section><span class="pill">Batters</span>${batters}</section>
        <section><span class="pill">Bowlers</span>${bowlers}</section>
      </div>
    </div>`;
}

function fixtureCard(week, a, b) {
  const result = (state.fixture_results || []).find(c => c.round === week && ((c.team1 === a && c.team2 === b) || (c.team1 === b && c.team2 === a)));
  const ta = team(a), tb = team(b);
  const record = `${ta?.abbr || a} ${ta?.wins || 0}-${ta?.losses || 0} vs ${tb?.abbr || b} ${tb?.wins || 0}-${tb?.losses || 0}`;
  if (result) {
    return `<button class="card scorecard-link" onclick='viewScorecard(${JSON.stringify(result)})'><span class="pill">Week ${week}</span><h2>${esc(a)} vs ${esc(b)}</h2><small>${esc(record)}</small><p>${result.innings.map(i => `${esc(i.team)} ${esc(i.score)}`).join(" · ")}</p><small>🏆 ${esc(result.motm)} · ${esc(result.winner)} ${esc(result.margin)}</small></button>`;
  }
  return `<div class="card"><span class="pill">Week ${week}</span><h2>${esc(a)} vs ${esc(b)}</h2><small>${esc(record)} · ${esc(team(a)?.home || "home venue")}</small></div>`;
}

async function openRetention() {
  state = await api("/api/open-retention", {});
  viewedScorecard = null;
  activeView = "retention";
  render();
}

async function chooseToss(decision) {
  state = await api("/api/toss", { decision });
  render();
}

async function submitLineup() {
  const isBowling = state.live_match.lineup_context === "bowling";
  const xi = isBowling ? dragListNames("matchBowlXI") : dragListNames("matchBatXI");
  const order = isBowling ? [] : xi;
  const bowlingOrder = isBowling ? dragListNames("matchBowlPlan") : [];
  const xiError = xiValidationError(xi, isBowling ? "Bowling First XI" : "Batting First XI");
  const planError = isBowling ? bowlingPlanError(bowlingOrder, "Live bowling plan") : "";
  if (xiError || planError) {
    alert(xiError || planError);
    return;
  }
  state = await api("/api/lineup", { xi, batting_order: order, bowling_order: bowlingOrder, intents: {}, save: false, context: state.live_match.lineup_context, wicketkeeper: state.live_match.saved_wicketkeeper || "" });
  render();
}

async function playOver(bowler) {
  await applyAggression(false);
  state = await api("/api/play-over", { bowler, stop_on_wicket: true });
  render();
}

async function playBall(bowler = "") {
  await applyAggression(false);
  state = await api("/api/play-ball", { bowler });
  render();
}

async function skipBalls(balls) {
  await applyAggression(false);
  state = await api("/api/play-until", { balls, stop_on_wicket: false });
  render();
}

async function applyAggression(shouldRender = true) {
  const score = state.live_match?.score;
  if (!score) return;
  const batting = {};
  if ($("strikerAgg")) batting[score.striker] = $("strikerAgg").value;
  if ($("nonStrikerAgg")) batting[score.non_striker] = $("nonStrikerAgg").value;
  const bowling = {};
  if ($("bowlerAgg") && score.active_bowler) bowling[score.active_bowler] = $("bowlerAgg").value;
  state = await api("/api/aggression", { batting, bowling });
  if (shouldRender) render();
}

async function chooseNextBatter(name) {
  state = await api("/api/next-batter", { name });
  render();
}

async function submitSuperOver() {
  const batters = [...document.querySelectorAll(".superBatter:checked")].map(x => x.value);
  const bowler = $("superBowler")?.value || "";
  state = await api("/api/super-over-lineup", { batters, bowler });
  render();
}

async function impactSub() {
  state = await api("/api/impact-sub", { out: $("subOut")?.value || "", in: $("subIn")?.value || "" });
  render();
}

async function completeLiveMatch() {
  state = await api("/api/complete-live-match", {});
  viewedScorecard = null;
  activeView = defaultView();
  render();
}

function renderMatch() {
  const match = state.live_match;
  if (!match) {
    if (viewedScorecard) applyThemeColors(team(viewedScorecard.winner) || myTeam());
    $("matchHub").innerHTML = viewedScorecard ? renderFinalScorecard({ card: viewedScorecard }, false) : `<div class="notice">No live match active.</div>`;
    return;
  }
  applyMatchTheme(match);
  if (match.status === "toss") {
    $("matchHub").innerHTML = `<div class="match-stage"><div class="scoreboard"><small>${esc(match.team1)} vs ${esc(match.team2)}</small><div class="scoreline">Toss</div><p>${esc(match.message)}</p></div><div class="panel"><h2>Choose Decision</h2><div class="notice">Your Starting XI plays innings 1. If you bowl first, your Impact Sub starts in place of a batter (and that batter returns at the break) — your saved 20-over bowling plan applies too.</div><div class="toolbar"><button class="primary" onclick="chooseToss('bat')">Bat First</button><button class="primary" onclick="chooseToss('bowl')">Bowl First</button></div></div></div>`;
    return;
  }
  if (match.status === "lineup" || match.status === "batting_order") {
    renderLineupHub(match);
    return;
  }
  if (match.status === "impact") {
    renderImpactHub(match);
    return;
  }
  if (match.status === "super_over_setup") {
    renderSuperOverHub(match);
    return;
  }
  if (match.status === "complete") {
    $("matchHub").innerHTML = renderFinalScorecard(match);
    return;
  }
  if (match.status === "next_batter") {
    renderNextBatterHub(match);
    return;
  }
  renderOverHub(match);
}

function renderLineupHub(match) {
  const isBowling = match.lineup_context === "bowling";
  const context = "Starting XI";
  const preset = uniqueXi(match.lineup_xi, match.suggested);
  const bench = benchNames(match.suggested, preset);
  const savedBowl = isBowling ? (match.saved_bowling_order || []) : [];
  const bowlPool = bowlingOptions(preset);
  const swapNotice = match.swap_notice ? `<div class="notice">${esc(match.swap_notice)}</div>` : "";
  $("matchHub").innerHTML = `
    <div class="panel">
      <div class="section-head"><h2>${context}</h2><button class="primary" onclick="submitLineup()">Confirm XI</button></div>
      <div class="notice">${esc(match.message)} The list below is grouped by where each player naturally bats — openers, middle order, death overs, tail. Drag within the XI to reorder, or drag a player to the bench pool to free a slot, then drag a bench player in.</div>
      ${swapNotice}
      ${draggableList(isBowling ? "matchBowlXI" : "matchBatXI", preset, 11, true, { group: isBowling ? "matchBowl" : "matchBat", showZones: true, showNaturalSlot: true })}
      <h2 class="gap-top">Bench</h2>
      ${draggableList(isBowling ? "matchBowlBenchPool" : "matchBatBenchPool", bench, bench.length, true, { group: isBowling ? "matchBowl" : "matchBat", pool: true, showNaturalSlot: true })}
    </div>
    ${isBowling ? `<div class="panel gap-top"><h2>20-Over Bowling Plan</h2><p class="notice">Grouped by phase — Powerplay (1-6), Middle (7-15), Death (16-20). Drag eligible bowlers into blank over slots; blank means smart auto-pick. Max 4 overs each, never in consecutive overs.</p>${draggableList("matchBowlPlan", savedBowl, 20, true, { group: "matchPlan", allowDuplicates: true, showZones: true, zones: OVER_PHASE_ZONES })}<h2 class="gap-top">Eligible Bowlers</h2>${draggableList("matchBowlPlanPool", bowlPool, bowlPool.length, true, { group: "matchPlan", pool: true, copySource: true, showMeta: true })}</div>` : ""}`;
  enableDragLists();
}

function renderImpactHub(match) {
  const impact = match.impact;
  const first = match.innings?.[0];
  const inningsSummary = first ? `
    <div class="panel">
      <h2>${esc(first.team)} ${esc(first.score)}</h2>
      <p class="notice">Chase target: ${Number(first.score.split("/")[0]) + 1}</p>
      <div class="grid">
        <div class="table-wrap short"><table>${battingCardTable(first.full_batting || first.batting)}</table></div>
        <div class="table-wrap short"><table>${bowlingCardTable(first.full_bowling || first.bowling)}</table></div>
      </div>
    </div>` : "";
  $("matchHub").innerHTML = `
    ${inningsSummary}
    <div class="match-stage">
      <div class="scoreboard"><small>Innings Break</small><div class="scoreline">Impact Sub</div><p>${esc(match.message)}</p></div>
      <div class="panel">
        <h2>Substitution Desk</h2>
        <div class="notice">Pick one player from the current XI to remove and one bench player to bring in for the second innings. The usual approach: defending, bring on an extra specialist bowler for your weakest batting option in the XI; chasing, bring on an extra hitter (often a finisher around #5-8) for your most expendable bowler. Your saved impact preset is preselected when available.</div>
        <div class="toolbar">
          <label>Out <select id="subOut">${impact.xi.map(p => `<option value="${esc(p.name)}">${esc(p.name)} · ${esc(p.role)} · ${slotZoneLabel(p.preferred_position)} · Bat ${p.bat}/Bowl ${p.bowl}</option>`).join("")}</select></label>
          <label>In <select id="subIn">${impact.bench.map(p => `<option value="${esc(p.name)}">${esc(p.name)} · ${esc(p.role)} · ${slotZoneLabel(p.preferred_position)} · Bat ${p.bat}/Bowl ${p.bowl}</option>`).join("")}</select></label>
          <button class="primary" onclick="impactSub()">Use Impact Sub</button>
          <button onclick="api('/api/impact-sub',{}).then(s=>{state=s;render();})">Skip</button>
        </div>
      </div>
    </div>`;
  if ($("subOut") && impact.default_out) $("subOut").value = impact.default_out;
  if ($("subIn") && impact.default_in) $("subIn").value = impact.default_in;
}

function renderSuperOverHub(match) {
  const so = match.super_over;
  const topBatters = (so.batters || []).slice(0, 8).map((p, i) => `
    <label class="choice">
      <input class="superBatter" type="checkbox" value="${esc(p.name)}" ${i < 3 ? "checked" : ""}>
      <b>${esc(p.name)}</b><small>Bat ${p.bat} · ${esc(p.batting_archetype)} · Form ${p.form}</small>
    </label>`).join("");
  const bowlers = (so.bowlers || []);
  $("matchHub").innerHTML = `
    <div class="match-stage">
      <div class="scoreboard"><small>Tied Match</small><div class="scoreline">Super Over</div><p>${esc(so.message || match.message)}</p><small>${esc(so.batting_first)} bat first. ${esc(so.batting_second)} chase.</small></div>
      <div class="panel">
        <div class="section-head"><h2>Pick Super Over Unit</h2><button class="primary" onclick="submitSuperOver()">Play Super Over</button></div>
        <div class="notice">Choose exactly 3 batters. First two start at the crease; the over ends after six balls or two wickets.</div>
        <div class="choice-list">${topBatters}</div>
        <h2>Bowler</h2>
        <select id="superBowler">${bowlers.map((p, i) => `<option value="${esc(p.name)}" ${i === 0 ? "selected" : ""}>${esc(p.name)} · Bowl ${p.bowl} · ${esc(p.bowling_phase)}</option>`).join("")}</select>
      </div>
    </div>`;
}

function renderOverHub(match) {
  const score = match.score;
  const bowlerButtons = match.available_bowlers.map(p => `<button onclick='playBall(${JSON.stringify(p.name)})' ${score.user_bowling && (!score.active_bowler || score.active_bowler === p.name) ? "" : "disabled"}><b>${esc(p.name)}</b><br><small>Bowl ${p.bowl} · Match ${p.match_overs}-${p.match_wickets}, Econ ${p.match_econ} · ${esc(p.bowling_phase)}</small></button>`).join("");
  $("matchHub").innerHTML = `
    ${broadcastStrip(score)}
    <div class="live-control-row gap-top">
      <div class="panel">
        <h2>Ball Controls</h2>
        <div class="notice">${score.user_batting ? "Set aggression for both batters, then play one ball, one over, or simulate a longer stretch." : "Set bowling aggression and choose a bowler when needed. If no bowler is active, pick one from the list below."}</div>
        <div class="control-grid">
          ${score.user_batting ? `<label>${esc(score.striker)} aggression <input id="strikerAgg" type="range" min="1" max="5" value="${score.striker_aggression}" onchange="applyAggression()"><small>1 defend · 5 attack</small></label><label>${esc(score.non_striker)} aggression <input id="nonStrikerAgg" type="range" min="1" max="5" value="${score.non_striker_aggression}" onchange="applyAggression()"><small>1 defend · 5 attack</small></label>` : ""}
          ${score.user_bowling ? `<label>Bowling aggression <input id="bowlerAgg" type="range" min="1" max="5" value="${score.bowler_aggression}" onchange="applyAggression()" ${score.active_bowler ? "" : "disabled"}><small>1 contain · 5 attack</small></label>` : ""}
        </div>
        <div class="toolbar">
          <button class="primary" onclick="playBall('')">Next Ball</button>
          <button onclick="playOver('')">Next Over</button>
          <button onclick="skipBalls(30)">Skip 5 Overs</button>
          <button onclick="skipBalls(60)">Skip 10 Overs</button>
          <button onclick="skipBalls(120)">End Innings</button>
        </div>
      </div>
      <div class="panel bowler-queue-panel">
        <h2>${score.user_bowling ? "Choose Bowler" : "Bowler Queue"}</h2>
        <div class="choice-list compact-choice-list">${bowlerButtons}</div>
      </div>
    </div>
    <div class="grid gap-top">
      <div class="panel"><h2>Batting Card</h2><div class="table-wrap short"><table>${battingCardTable(score.bat_stats, score)}</table></div></div>
      <div class="panel"><h2>Bowling Card</h2><div class="table-wrap short"><table>${bowlingCardTable(score.bowl_stats)}</table></div></div>
    </div>
    <div class="panel gap-top"><h2>Recent Overs</h2>${score.over_log.map(o => `<div><b>Over ${o.over}: ${esc(o.bowler)}</b> <span class="over-log">${o.events.map(e => `<span class="ball ${e.kind === "wicket" ? "wicket-ball" : ""}" title="${esc(e.description || "")}">${esc(e.label)}</span>`).join("")}</span>${o.events.filter(e => e.kind === "wicket").map(e => `<small class="wicket-note">${esc(e.description)}</small>`).join("")}</div>`).join("")}</div>`;
}

function renderNextBatterHub(match) {
  const score = match.score;
  const wicket = score.last_wicket || {};
  const batter = wicket.batter || "";
  const howOut = shortDismissal(wicket.description || "", batter);
  $("matchHub").innerHTML = `
    ${broadcastStrip(score)}
    <div class="grid gap-top">
      <div class="panel"><h2>Batting Card</h2><div class="table-wrap short"><table>${battingCardTable(score.bat_stats, score)}</table></div></div>
      <div class="panel">
        <h2>${esc(batter || "Batter")} is out!</h2>
        <div class="notice">${esc(howOut)}<br>Choose who comes in next.</div>
        <div class="choice-list">${score.next_batter_options.map(p => `<button onclick='chooseNextBatter(${JSON.stringify(p.name)})'><b>${esc(p.name)}</b><br><small>${p.role} · Bat ${p.bat} · ${esc(p.batting_archetype)} · Form ${p.form}</small><br><small>${esc(p.strengths)} / ${esc(p.weaknesses)}</small></button>`).join("")}</div>
      </div>
    </div>`;
}

function renderFinalScorecard(match, canComplete = true) {
  const innings = match.card?.innings || [];
  const innHtml = innings.map(i => `
    <div class="panel scorecard-panel">
      <div class="scorecard-title"><h2>${esc(i.team)} ${esc(i.score)}</h2><small>vs ${esc(i.against)}${i.impact_sub ? ` · Impact: ${esc(i.impact_sub)}` : ""}</small></div>
      <div class="grid">
        <div class="table-wrap short"><table>${battingCardTable(i.full_batting || i.batting)}</table></div>
        <div class="table-wrap short"><table>${bowlingCardTable(i.full_bowling || i.bowling)}</table></div>
      </div>
    </div>`).join("");
  const superOver = match.card?.super_over?.innings?.length ? `<div class="panel"><h2>Super Over</h2><div class="grid">${match.card.super_over.innings.map(i => `<div><b>${esc(i.team)} ${esc(i.score)}</b><br><span class="over-log">${i.events.map(e => `<span class="ball ${e.kind === "wicket" ? "wicket-ball" : ""}">${esc(e.label)}</span>`).join("")}</span><div class="table-wrap short"><table>${table(["Batter","R","B","4s","6s"], i.batting.map(b => [b.name,b.runs,b.balls,b.fours,b.sixes]))}</table></div><div class="table-wrap short"><table>${table(["Bowler","O","R","W","Econ"], i.bowling.map(b => [b.name,b.overs,b.runs,b.wickets,b.econ]))}</table></div></div>`).join("")}</div></div>` : "";
  const impacts = match.card?.impact_subs?.length ? `<div class="panel"><h2>Impact Subs</h2>${match.card.impact_subs.map(x => `<span class="pill">${esc(x)}</span>`).join(" ")}</div>` : "";
  const resultBlock = `<div class="scoreboard gap-top"><small>${esc(match.card?.venue || "")} · Toss: ${esc(match.card?.toss || "")}</small><div class="scoreline">${esc(match.card?.winner || "")} ${esc(match.card?.margin || "")}</div><p>Player of the Match: ${playerLink(match.card?.motm || "")}${esc(motmContribution(match.card))}</p>${canComplete ? `<button class="primary" onclick="completeLiveMatch()">Return to Season</button>` : `<button class="primary" onclick="activeView='season';viewedScorecard=null;render()">Back to Match Centre</button>`}</div>`;
  return `${resultBlock}${impacts}${innHtml}${superOver}`;
}

function renderStandings() {
  if (!state.teams.length) return;
  const headers = [["Pos",""],["Team","name"],["P","played"],["W","wins"],["L","losses"],["Pts","points"],["NRR","nrr"],["Form","wins"]];
  const rows = sortedRows(state.standings, tableSort).map((t, i) => {
    const recent = recentTeamResults(t.name).slice(0, 5).map(r => `<span class="${r.won ? "form-win" : "form-loss"}">${r.won ? "✓" : "×"}</span>`).join("");
    const expanded = expandedTeam === t.name ? `<div class="team-drop">${teamSnapshot(t)}</div>` : "";
    return [i + 1, `<button class="link-btn" onclick='toggleTeam(${JSON.stringify(t.name)})'>${teamLabel(t)}</button>${expanded}`, t.played, t.wins, t.losses, t.points, Number(t.nrr).toFixed(3), recent || "-"];
  });
  $("pointsTable").innerHTML = table(headers, rows, "table:");
  $("playoffCards").innerHTML = state.playoffs.map(p => `<div class="card"><span class="pill">${p.status}</span><h2>${p.name}</h2><p>${esc(p.team1 || "TBD")} vs ${esc(p.team2 || "TBD")}</p><b>${p.winner ? esc(p.winner) + " advanced" : ""}</b></div>`).join("") || `<div class="notice">Playoffs appear after 14 league matches.</div>`;
}

function toggleTeam(name) {
  expandedTeam = expandedTeam === name ? "" : name;
  renderStandings();
  attachSortHandlers();
}

function recentTeamResults(name) {
  return (state.fixture_results || []).filter(c => c.team1 === name || c.team2 === name).slice().reverse().map(c => ({ won: c.winner === name, text: `${c.winner} ${c.margin}` }));
}

function teamSnapshot(t) {
  const topRuns = sortedPlayers(t.roster, {key:"runs", dir:-1}).slice(0,3).map(p => `${esc(p.name)} ${p.runs}`).join(", ") || "-";
  const topWkts = sortedPlayers(t.roster, {key:"wickets", dir:-1}).slice(0,3).map(p => `${esc(p.name)} ${p.wickets}`).join(", ") || "-";
  const mvp = sortedPlayers(t.roster, {key:"mvp", dir:-1})[0];
  return `<small>Captain: ${esc(t.captain || "-")} · MVP: ${esc(mvp?.name || "-")} (${mvp?.mvp || 0})</small><br><small>Top runs: ${topRuns}</small><br><small>Top wickets: ${topWkts}</small><div class="mini-roster">${t.roster.slice(0, 21).map(p => `<span>${esc(p.name)} <b>${p.ovr}</b></span>`).join("")}</div>`;
}

function sortedPlayers(players, sort) {
  return [...players].sort((a, b) => {
    const av = a[sort.key], bv = b[sort.key];
    let result = 0;
    if (typeof av === "string" || typeof bv === "string") result = String(av ?? "").localeCompare(String(bv ?? ""), undefined, { numeric: true, sensitivity: "base" });
    else result = (Number(av) || 0) - (Number(bv) || 0);
    if (result === 0 && sort.key !== "name") result = String(a.name || "").localeCompare(String(b.name || ""), undefined, { sensitivity: "base" });
    return result * sort.dir;
  });
}

function sortedRows(items, sort) {
  return [...items].sort((a, b) => {
    const av = a[sort.key], bv = b[sort.key];
    let result = 0;
    if (typeof av === "string" || typeof bv === "string") result = String(av ?? "").localeCompare(String(bv ?? ""), undefined, { numeric: true, sensitivity: "base" });
    else result = (Number(av) || 0) - (Number(bv) || 0);
    if (result === 0 && sort.key === "points") result = (Number(b.nrr) || 0) - (Number(a.nrr) || 0);
    if (result === 0 && sort.key !== "name") result = String(a.name || "").localeCompare(String(b.name || ""), undefined, { sensitivity: "base" });
    return result * sort.dir;
  });
}

function teamCell(name) {
  const t = team(name);
  return t ? teamLabel(t) : esc(name);
}

function teamName(name) {
  const t = team(name);
  return esc(t ? t.name : name);
}

function renderStats() {
  if (!state.teams.length) return;
  const allPlayers = state.teams.flatMap(t => t.roster);
  const query = ($("statsSearch")?.value || "").toLowerCase();
  const teamFilter = $("statsTeamFilter");
  if (teamFilter && !teamFilter.dataset.filled) {
    teamFilter.innerHTML = `<option value="">All Teams</option>${state.teams.map(t => `<option value="${esc(t.name)}">${esc(t.name)}</option>`).join("")}`;
    teamFilter.dataset.filled = "1";
    teamFilter.onchange = renderStats;
  }
  const teamPick = teamFilter?.value || "";
  const found = query ? allPlayers.find(p => p.name.toLowerCase().includes(query)) : null;
  if (found) {
    const t = team(found.team);
    $("playerProfile").innerHTML = `<div class="profile-card" style="--team-primary:${t?.primary || "#0f172a"};--team-accent:${t?.accent || "#0f172a"}">
      <div class="profile-head">
        ${t ? `<span class="crest lg" style="background:linear-gradient(135deg,${t.primary},${t.accent})">${t.abbr}</span>` : ""}
        <div><h2>${esc(found.name)}</h2><p>${esc(found.team)} · ${esc(found.role)} · Form ${found.form} · OVR ${esc(found.ovr_progression)}</p></div>
      </div>
      <div class="stat-chip-row">
        <span class="stat-chip">Runs<b>${found.runs}</b></span>
        <span class="stat-chip">SR<b>${found.sr}</b></span>
        <span class="stat-chip">Wkts<b>${found.wickets}</b></span>
        <span class="stat-chip">Econ<b>${found.econ}</b></span>
        <span class="stat-chip">Ct/St/RO<b>${found.catches}/${found.stumpings}/${found.runouts}</b></span>
        <span class="stat-chip">MVP<b>${found.mvp}</b></span>
      </div>
      <small>${esc(found.strengths)} · ${esc(found.weaknesses)}</small>
    </div>`;
  } else {
    $("playerProfile").innerHTML = "";
  }
  const batHeaders = [["#",""],["Player","name"],["Team","team"],["Runs","runs"],["Balls","balls"],["Avg","avg"],["SR","sr"],["HS","hs"],["4s","fours"],["6s","sixes"],["Boundaries","boundaries"],["50s","fifties"],["100s","hundreds"],["MOTM","motm"],["MVP","mvp"]];
  const bowlHeaders = [["#",""],["Player","name"],["Team","team"],["Wkts","wickets"],["Balls","balls_bowled"],["Runs","runs_conceded"],["Econ","econ"],["Avg","bowling_avg"],["SR","bowling_sr"],["Best","best_bowling"],["Ct","catches"],["St","stumpings"],["RO","runouts"],["MOTM","motm"],["MVP","mvp"]];
  const batRows = state.tables.batting.filter(p => !teamPick || p.team === teamPick);
  const bowlRows = state.tables.bowling.filter(p => !teamPick || p.team === teamPick);
  $("battingStats").innerHTML = table(batHeaders, sortedPlayers(batRows, batSort).map((p, i) => [i + 1, playerLink(p.name), teamCell(p.team), p.runs, p.balls, p.avg, p.sr, p.hs, p.fours, p.sixes, p.boundaries, p.fifties, p.hundreds, p.motm, p.mvp]), "bat:");
  $("bowlingStats").innerHTML = table(bowlHeaders, sortedPlayers(bowlRows, bowlSort).map((p, i) => [i + 1, playerLink(p.name), teamCell(p.team), p.wickets, p.balls_bowled, p.runs_conceded, p.econ, p.bowling_avg, p.bowling_sr, p.best_bowling, p.catches, p.stumpings, p.runouts, p.motm, p.mvp]), "bowl:");
  const batLeaderDefs = [["Orange Cap","orange_cap","runs","#f97316"],["MVP Race","mvp","mvp","#0f172a"],["Most Sixes","sixes","sixes","#dc2626"],["Most Fours","fours","fours","#2563eb"],["Most Boundaries","boundaries","boundaries","#059669"],["Highest Score","highest_score","hs","#b45309"],["Best SR","strike_rate","sr","#db2777"]];
  const bowlLeaderDefs = [["Purple Cap","purple_cap","wickets","#7c3aed"],["Best Economy","economy","econ","#0891b2"],["Best Bowling","best_figures","best_bowling","#6d28d9"],["Most Catches","catches","catches","#16a34a"],["Most Stumpings","stumpings","stumpings","#0d9488"],["Most Run Outs","runouts","runouts","#ca8a04"]];
  const listHtml = defs => defs.map(([title, listKey, statKey, color]) => {
    const rows = (state.leaderboards[listKey] || []).filter(p => !teamPick || p.team === teamPick).slice(0, 50);
    return `<div class="leader-list tall" style="--award:${color}"><h3>${title}</h3>${rows.map((p, i) => {
      const against = title === "Highest Score" && p.hs_against ? ` vs ${esc(p.hs_against)}` : title === "Best Bowling" && p.best_bowling_against ? ` vs ${esc(p.best_bowling_against)}` : "";
      return `<div class="leader-row"><b>${i + 1}</b><span>${playerLink(p.name)}<small>${teamName(p.team)}${against}</small></span><strong>${esc(p[statKey])}</strong></div>`;
    }).join("") || `<div class="notice compact">No qualifying players for ${esc(team(teamPick)?.name || "this team")}.</div>`}</div>`;
  }).join("");
  $("leaderShowcase").innerHTML = `<section class="award-section"><h3>Batting Awards</h3><div class="award-grid">${listHtml(batLeaderDefs)}</div></section><section class="award-section"><h3>Bowling and Fielding Awards</h3><div class="award-grid">${listHtml(bowlLeaderDefs)}</div></section>`;
  if ($("statsSearch")) $("statsSearch").oninput = renderStats;
}

function attachSortHandlers() {
  document.querySelectorAll("[data-sort]").forEach(th => th.onclick = () => {
    const [type, key] = th.dataset.sort.split(":");
    if (!key) return;
    const sort = type === "bat" ? batSort : type === "bowl" ? bowlSort : type === "squad" ? squadSort : type === "draft" ? draftSort : tableSort;
    if (sort.key === key) sort.dir *= -1; else { sort.key = key; sort.dir = ["name", "team", "role", "batting_archetype", "bowling_phase", "bowling_type"].includes(key) ? 1 : -1; }
    if (type === "bat" || type === "bowl") renderStats();
    else if (type === "draft") renderDraft();
    else if (type === "squad") renderSquadTable();
    else renderStandings();
    attachSortHandlers();
  });
}

async function saveLeadership() {
  const keeperName = $("squadKeeper")?.value || "";
  const keeper = playerByName(keeperName);
  state = await api("/api/leadership", { captain: $("captainSelect").value, vice: $("viceSelect").value, wicketkeeper: keeper?.role === "Wicketkeeper" ? keeperName : "" });
  render();
}

async function savePresets() {
  const bowlingOrder = dragListNames("squadBowlPlan");
  const startingXi = dragListNames("startingXIList");
  const impactSubName = $("impactSubSelect")?.value || "";
  const t = myTeam();
  const xiError = xiValidationError(startingXi, "Starting XI") || impactSubError(impactSubName, startingXi, t.roster) || bowlingPlanError(bowlingOrder, "Default bowling plan");
  if (xiError) {
    alert(xiError);
    return;
  }
  state = await api("/api/presets", {
    batting_order: startingXi,
    bowling_order: bowlingOrder,
    starting_xi: startingXi,
    impact_sub_name: impactSubName,
    wicketkeeper: playerByName($("squadKeeper")?.value || "")?.role === "Wicketkeeper" ? $("squadKeeper").value : "",
  });
  render();
}

function renderSquad() {
  if (!state.teams.length) return;
  const t = myTeam();
  $("captainSelect").innerHTML = t.roster.map(p => `<option value="${esc(p.name)}" ${p.name === t.captain ? "selected" : ""}>Captain: ${esc(p.name)}</option>`).join("");
  $("viceSelect").innerHTML = t.roster.map(p => `<option value="${esc(p.name)}" ${p.name === t.vice_captain ? "selected" : ""}>Vice: ${esc(p.name)}</option>`).join("");
  const startingXi = uniqueXi(t.starting_xi?.length ? t.starting_xi : t.roster.slice(0, 11).map(p => p.name), t.roster);
  const bowlDefault = t.saved_bowling_order?.length ? t.saved_bowling_order : [];
  const keeperOptions = t.roster.filter(p => p.role === "Wicketkeeper").map(p => `<option value="${esc(p.name)}">Keeper: ${esc(p.name)}</option>`).join("") || `<option value="">Draft a wicketkeeper first</option>`;
  const startingBench = benchNames(t.roster, startingXi);
  const planBowlers = bowlingOptions([...startingXi, t.impact_sub_name].filter(Boolean));
  $("squadKeeper").innerHTML = keeperOptions;
  $("squadKeeper").onchange = refreshDragBadges;
  $("battingPreset").innerHTML = "";
  $("bowlingPreset").innerHTML = `
    <p class="notice compact">Overs are grouped by phase — Powerplay (1-6), Middle (7-15), Death (16-20) — so you can see your plan's shape at a glance. Drag bowlers from the pool below into blank slots; max 4 overs each, never in consecutive overs.</p>
    ${draggableList("squadBowlPlan", bowlDefault, 20, true, { group: "squadPlan", allowDuplicates: true, showZones: true, zones: OVER_PHASE_ZONES })}
    <h2 class="gap-top">Eligible Bowlers</h2>
    ${draggableList("squadBowlPlanPool", planBowlers, planBowlers.length, true, { group: "squadPlan", pool: true, copySource: true, showMeta: true })}
  `;
  $("xiPreset").innerHTML = `
    <div class="notice">Your Starting XI plays innings 1. Below it, pick your Impact Sub from the bench — by default it's your best spare bowler. The XI is grouped by where players naturally bat — openers, middle order, death overs, tail — so you can see at a glance whether the order makes sense. Drag players between the XI and its bench pool; Save Match Presets also saves the default keeper.</div>
    <div class="grid">
      <div><h2>Starting XI</h2><p class="notice compact">Slot order here is the actual batting order.</p>${draggableList("startingXIList", startingXi, 11, true, { group: "squadStarting", showZones: true, showNaturalSlot: true })}<h2 class="gap-top">Bench Pool</h2>${draggableList("startingXIBenchPool", startingBench, startingBench.length, true, { group: "squadStarting", pool: true, showNaturalSlot: true })}</div>
    </div>
    <h2 class="gap-top">Impact Sub</h2>
    <div class="notice">If you bat first, your Impact Sub comes on for a batter at the innings break. If you bowl first, your Impact Sub starts the match in place of that batter and the original player returns at the break.</div>
    <div class="toolbar impact-preset-toolbar">
      <label>Impact Sub <select id="impactSubSelect">${impactOptions(t.roster)}</select></label>
    </div>`;
  if ($("squadKeeper")) $("squadKeeper").value = t.saved_wicketkeeper || t.roster.find(p => p.role === "Wicketkeeper")?.name || "";
  if ($("impactSubSelect")) {
    $("impactSubSelect").value = t.impact_sub_name || "";
    $("impactSubSelect").onchange = refreshBowlingPlanPools;
  }
  enableDragLists();
  renderSquadTable();
}

function renderSquadTable() {
  if (!state.teams.length) return;
  const t = myTeam();
  const headers = [["Player","name"],["Runs","runs"],["Avg","avg"],["SR","sr"],["HS","hs"],["Wkts","wickets"],["Econ","econ"],["Best","best_bowling"],["Ct","catches"],["St","stumpings"],["RO","runouts"],["MOTM","motm"],["MVP","mvp"],["Form","form"],["Role","role"],["Age","age"],["OVR","ovr"],["Bat","bat"],["Bowl","bowl"],["Type","batting_archetype"],["Bowl Role","bowling_phase"],["Ball","bowling_type"],["Powerplay","phase_fit_powerplay"],["Middle","phase_fit_middle"],["Death","phase_fit_death"],["Strength","strengths"],["Weakness","weaknesses"]];
  $("squadTable").innerHTML = table(headers, sortedPlayers(t.roster, squadSort).map(p => [playerLink(p.name),p.runs,p.avg,p.sr,p.hs,p.wickets,p.econ,p.best_bowling,p.catches,p.stumpings,p.runouts,p.motm,p.mvp,p.form,p.role,p.age,p.ovr_progression,p.bat_progression,p.bowl_progression,p.batting_archetype,p.bowling_phase,p.bowling_type,p.phase_fit_powerplay,p.phase_fit_middle,p.phase_fit_death,p.strengths,p.weaknesses]), "squad:");
}

function renderHistory() {
  $("historyPanel").innerHTML = state.history.slice().reverse().map(h => `<div class="card"><h2>Season ${h.season}</h2><p><b>Champion:</b> ${esc(h.champion)} · <b>Runner-up:</b> ${esc(h.runner_up)} · <b>MVP:</b> ${esc(h.mvp.name)} (${h.mvp.mvp})</p><div class="table-wrap short"><table>${table(["Pos","Team","Pts","NRR"], h.points_table.map((t,i)=>[i+1,t.name,t.points,Number(t.nrr).toFixed(3)]))}</table></div></div>`).join("") || `<div class="notice">Finish a season to build league history.</div>`;
}

$("newLeagueBtn").onclick = newLeague;
$("saveBtn").onclick = saveLeague;
$("homeBtn").onclick = () => { state.phase = "title"; render(); };
$("draftSearch").oninput = renderDraft;
$("draftRole").onchange = renderDraft;
$("draftNation").onchange = renderDraft;
$("draftBatType").onchange = renderDraft;
$("draftBowlType").onchange = renderDraft;
$("draftSlot").onchange = renderDraft;
$("submitRetentionBtn").onclick = submitRetention;
$("beginMatchBtn").onclick = beginMatch;
$("simulateRoundBtn").onclick = simulateRound;
$("saveLeadershipBtn").onclick = saveLeadership;
$("savePresetsBtn").onclick = savePresets;
$("autoStartingXiBtn").onclick = autofillStartingXi;
$("clearStartingXiBtn").onclick = clearStartingXi;
$("autoBowlPlanBtn").onclick = autofillBowlingPlan;
$("clearBowlPlanBtn").onclick = clearBowlingPlan;

load();
