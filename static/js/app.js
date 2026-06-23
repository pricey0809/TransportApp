'use strict';

const form       = document.getElementById('routeForm');
const btnSearch  = document.getElementById('btnSearch');
const btnText    = document.getElementById('btnText');
const btnSpinner = document.getElementById('btnSpinner');
const errorAlert = document.getElementById('errorAlert');
const errorMsg   = document.getElementById('errorMsg');
const resultsEl  = document.getElementById('results');

// ── Step 1: combination selector ─────────────────────────────────────────────
const combinationSelect = document.getElementById('combinationSelect');
const configStep2       = document.getElementById('configStep2');

// ── Step 2: length + mass scheme ─────────────────────────────────────────────
const lengthRow         = document.getElementById('lengthRow');
const lengthOptions     = document.getElementById('lengthOptions');
const massSchemeRow     = document.getElementById('massSchemeRow');
const massSchemeOptions = document.getElementById('massSchemeOptions');

// ── Step 3: PBS toggle + GVM ──────────────────────────────────────────────────
const pbsToggle  = document.getElementById('pbsToggle');
const pbsGvmRow  = document.getElementById('pbsGvmRow');
const pbsGvm     = document.getElementById('pbsGvm');

// ── Oversize / manual dimension fields ────────────────────────────────────────
const oversizeFields   = document.getElementById('oversizeFields');
const oversizeSubtitle = document.getElementById('oversizeFieldsSubtitle');
const ovWidth  = document.getElementById('ovWidth');
const ovHeight = document.getElementById('ovHeight');
const ovLength = document.getElementById('ovLength');
const ovMass   = document.getElementById('ovMass');

// ── DG field elements ─────────────────────────────────────────────────────────
const dgToggle    = document.getElementById('dgToggle');
const dgFields    = document.getElementById('dgFields');
const dgClassEl   = document.getElementById('dgClass');
const dgQuantity  = document.getElementById('dgQuantity');
const dgUnNumber  = document.getElementById('dgUnNumber');
const pgRow       = document.getElementById('pgRow');
const dgQuantUnit = document.getElementById('dgQuantityUnit');
const PG_CLASSES  = new Set(['3', '5.1']);
const DG_UNIT_MAP = { '2.1': 'L', '2.2': 'L', '2.3': 'L', '3': 'L', default: 'kg' };

// ── Combination data (embedded by Jinja) ──────────────────────────────────────
// window.COMBINATION_GROUPS is set in index.html

/** Return the combination entry for a given code, or null. */
function findCombo(code) {
  for (const group of window.COMBINATION_GROUPS) {
    for (const c of group.combinations) {
      if (c.code === code) return c;
    }
  }
  return null;
}

// ── Combination select → render Step 2 ────────────────────────────────────────
combinationSelect.addEventListener('change', () => {
  const combo = findCombo(combinationSelect.value);
  if (!combo) return;

  const isManual   = combo.requires_manual_dimensions;
  const isOversize = combo.requires_oversize_form;

  // Reset step 2 state
  pbsToggle.checked = false;
  pbsGvmRow.classList.add('d-none');
  pbsGvm.required = false;
  pbsGvm.value = '';

  // Manual dims (SPV / Oversize)
  const needsDims = isManual || isOversize;
  oversizeFields.classList.toggle('d-none', !needsDims);
  [ovWidth, ovHeight, ovLength, ovMass].forEach(el => { el.required = needsDims; });
  oversizeSubtitle.textContent = isManual ? '— enter your vehicle\'s actual dimensions' : '';

  configStep2.classList.toggle('d-none', needsDims);

  if (needsDims) return;

  // ── Length picker ──────────────────────────────────────────────────────────
  const lengths = combo.lengths || [];
  if (lengths.length > 1) {
    lengthOptions.innerHTML = lengths.map((l, i) =>
      `<div class="form-check form-check-inline me-2">
        <input class="form-check-input" type="radio" name="lengthRadio"
               id="len_${i}" value="${l.length_m}"
               ${i === 0 ? 'checked' : ''} />
        <label class="form-check-label" for="len_${i}">${escHtml(l.label)}</label>
      </div>`
    ).join('');
    lengthRow.classList.remove('d-none');
  } else {
    // Single length — hidden, always selected
    lengthOptions.innerHTML =
      `<input type="radio" name="lengthRadio" value="${lengths[0].length_m}" checked class="d-none" />`;
    lengthRow.classList.add('d-none');
  }

  // ── Mass scheme picker ─────────────────────────────────────────────────────
  renderMassSchemes(combo, lengths[0]?.length_m);

  // Re-render when length changes (scheme availability may differ)
  lengthOptions.addEventListener('change', () => {
    const selectedLen = parseFloat(
      lengthOptions.querySelector('input[name="lengthRadio"]:checked')?.value
    );
    renderMassSchemes(combo, selectedLen);
  }, { once: false });
});

function renderMassSchemes(combo, /* float */ _lengthM) {
  const schemes = combo.mass_schemes || {};
  const keys    = Object.keys(schemes);

  massSchemeOptions.innerHTML = keys.map((key, i) => {
    const s = schemes[key];
    return `<div class="form-check form-check-inline me-2">
      <input class="form-check-input" type="radio" name="massSchemeRadio"
             id="ms_${key}" value="${key}" ${i === 0 ? 'checked' : ''} />
      <label class="form-check-label" for="ms_${key}">
        ${escHtml(s.label)}
        <span class="text-muted small">(${s.gvm_t} t)</span>
      </label>
    </div>`;
  }).join('');

  massSchemeRow.classList.toggle('d-none', keys.length === 0);
}

// ── PBS toggle ────────────────────────────────────────────────────────────────
pbsToggle.addEventListener('change', () => {
  const on = pbsToggle.checked;
  pbsGvmRow.classList.toggle('d-none', !on);
  pbsGvm.required = on;
  if (!on) pbsGvm.value = '';
});

// ── DG toggle ─────────────────────────────────────────────────────────────────
dgToggle.addEventListener('change', () => {
  const on = dgToggle.checked;
  dgFields.classList.toggle('d-none', !on);
  dgClassEl.required = on;
  dgQuantity.required = on;
});

dgClassEl.addEventListener('change', () => {
  const cls = dgClassEl.value;
  pgRow.classList.toggle('d-none', !PG_CLASSES.has(cls));
  dgQuantUnit.textContent = `(${DG_UNIT_MAP[cls] || DG_UNIT_MAP.default})`;
});

// ── Geolocation button ────────────────────────────────────────────────────────
document.getElementById('btnGeolocate').addEventListener('click', () => {
  if (!navigator.geolocation) {
    showError('Geolocation is not supported by your browser.');
    return;
  }
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const { latitude, longitude } = pos.coords;
      document.getElementById('origin').value = `${latitude}, ${longitude}`;
    },
    () => showError('Could not retrieve your location.')
  );
});

// ── Form submit ───────────────────────────────────────────────────────────────
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!form.checkValidity()) {
    form.classList.add('was-validated');
    return;
  }

  setLoading(true);
  hideError();
  resultsEl.classList.add('d-none');
  document.getElementById('dgBlock').classList.add('d-none');
  hideMapPanel();

  const origin      = document.getElementById('origin').value.trim();
  const destination = document.getElementById('destination').value.trim();
  const combo       = findCombo(combinationSelect.value);

  try {
    const routePromise = combo?.requires_oversize_form
      ? handleOversizeQuery(origin, destination)
      : handleRouteQuery(origin, destination, combo);

    const dgPromise = dgToggle.checked
      ? handleDGQuery()
      : Promise.resolve(null);

    // Route geometry runs in parallel — silently skipped if Valhalla is offline
    const geometryPromise = handleRouteGeometry(origin, destination, combo)
      .catch(err => {
        console.warn('Route geometry unavailable:', err.message);
      });

    await Promise.all([routePromise, dgPromise, geometryPromise]);
  } catch (err) {
    showError('Network error — please check your connection and try again.');
  } finally {
    setLoading(false);
  }
});

// ── Route query (NHVR network check) ─────────────────────────────────────────
async function handleRouteQuery(origin, destination, combo) {
  if (!combo) {
    showError('Please select a vehicle combination.');
    return;
  }

  const payload = buildVehiclePayload(origin, destination, combo);

  const resp = await fetch('/api/route', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(payload),
  });

  const data = await resp.json();
  if (!resp.ok) {
    showError(data.error || `Server error (${resp.status})`);
    return;
  }

  document.getElementById('oversizeBlock').classList.add('d-none');
  document.getElementById('summaryDimsRow').classList.add('d-none');
  document.getElementById('statusBanner').classList.remove('d-none');

  renderResults(payload, data);
}

// ── Oversize query ────────────────────────────────────────────────────────────
async function handleOversizeQuery(origin, destination) {
  const payload = {
    width_m:  parseFloat(ovWidth.value),
    height_m: parseFloat(ovHeight.value),
    length_m: parseFloat(ovLength.value),
    mass_t:   parseFloat(ovMass.value),
  };

  const resp = await fetch('/api/oversize', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(payload),
  });

  const data = await resp.json();
  if (!resp.ok) {
    showError(data.error || `Server error (${resp.status})`);
    return;
  }

  renderOversizeResults({ origin, destination, ...payload }, data);
}

// ── DG query ──────────────────────────────────────────────────────────────────
async function handleDGQuery() {
  const cls = dgClassEl.value;
  const qty = parseFloat(dgQuantity.value);
  const un  = dgUnNumber.value.trim();
  const pg  = document.querySelector('input[name="dgPG"]:checked')?.value || null;

  const payload = {
    dg_class:      cls,
    quantity:      qty,
    un_number:     un,
    packing_group: PG_CLASSES.has(cls) ? pg : null,
  };

  const resp = await fetch('/api/dangerous-goods', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(payload),
  });

  const data = await resp.json();
  if (!resp.ok) {
    showError(data.error || `DG check error (${resp.status})`);
    return;
  }

  renderDGResults(data);
}

// ── Valhalla polyline decoder ─────────────────────────────────────────────────
// Valhalla uses a 6-decimal-precision (1e6) variant of Google Encoded Polyline.
// Output: [[lon, lat], ...] in GeoJSON coordinate order.
function _decodeShape(encoded) {
  let index = 0, lat = 0, lng = 0;
  const coords = [];
  while (index < encoded.length) {
    let b, shift = 0, result = 0;
    do {
      b = encoded.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);
    lat += (result & 1) ? ~(result >> 1) : (result >> 1);

    shift = 0; result = 0;
    do {
      b = encoded.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);
    lng += (result & 1) ? ~(result >> 1) : (result >> 1);

    coords.push([lng / 1e6, lat / 1e6]); // GeoJSON: [lon, lat]
  }
  return coords;
}

// Build a Google Maps directions URL from Valhalla shape coordinates.
// shapeCoords: [[lon, lat], ...]  origin/destination: { lat, lon }
function _buildMapsUrl(shapeCoords, origin, destination) {
  const params = new URLSearchParams({
    api:         '1',
    origin:      `${origin.lat.toFixed(6)},${origin.lon.toFixed(6)}`,
    destination: `${destination.lat.toFixed(6)},${destination.lon.toFixed(6)}`,
    travelmode:  'driving',
  });
  if (shapeCoords.length > 2) {
    const interior = shapeCoords.slice(1, -1);
    const step     = Math.max(1, Math.floor(interior.length / 6));
    const sampled  = interior.filter((_, i) => i % step === 0).slice(0, 6);
    if (sampled.length > 0) {
      // shapeCoords are [lon, lat]; Google Maps needs "lat,lon"
      params.set('waypoints', sampled.map(([lon, lat]) => `${lat.toFixed(6)},${lon.toFixed(6)}`).join('|'));
    }
  }
  return 'https://www.google.com/maps/dir/?' + params.toString();
}

// ── Route geometry (Valhalla) ─────────────────────────────────────────────────
// Two-step approach: server computes geocoding + costing params (/api/valhalla-params),
// then browser POSTs directly to Valhalla. This bypasses server-to-server blocks
// on public Valhalla (405) while keeping geocoding + costing logic server-side.
async function handleRouteGeometry(origin, destination, combo) {
  if (!combo) return;

  const payload = buildVehiclePayload(origin, destination, combo);

  // Attach DG params so the backend can apply tunnel avoidance
  if (dgToggle.checked) {
    const cls = dgClassEl.value;
    const qty = parseFloat(dgQuantity.value);
    if (cls && !isNaN(qty) && qty > 0) {
      payload.dg_class    = cls;
      payload.dg_quantity = qty;
      const un = dgUnNumber.value.trim();
      if (un) payload.dg_un_number = un;
      if (PG_CLASSES.has(cls)) {
        payload.dg_packing_group =
          document.querySelector('input[name="dgPG"]:checked')?.value || null;
      }
    }
  }

  // ── Step 1: Server computes geocoding + Valhalla request params ─────────────
  const paramsResp = await fetch('/api/valhalla-params', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(payload),
  });

  const paramsData = await paramsResp.json();
  if (!paramsResp.ok) {
    if (paramsData.error_type === 'height_restricted') {
      document.getElementById('heightRestrictedAlert').classList.remove('d-none');
      return;
    }
    document.getElementById('valhallaOfflineNote').classList.remove('d-none');
    document.getElementById('valhallaOfflineNoteText').textContent =
      paramsData.error || 'Route map unavailable.';
    return;
  }

  // ── Step 2: Browser calls Valhalla directly ────────────────────────────────
  let vr;
  try {
    const vResp = await fetch(`${paramsData.valhalla_url}/route`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(paramsData.valhalla_request),
    });
    vr = await vResp.json();
    if (!vResp.ok || vr.error) {
      if (vr.error_code === 442) {
        document.getElementById('heightRestrictedAlert').classList.remove('d-none');
        return;
      }
      throw new Error(vr.error || `HTTP ${vResp.status}`);
    }
  } catch (err) {
    document.getElementById('valhallaOfflineNote').classList.remove('d-none');
    document.getElementById('valhallaOfflineNoteText').textContent =
      'Route map unavailable — ' + err.message;
    return;
  }

  // ── Step 3: Decode shape and extract maneuvers ─────────────────────────────
  const shapeCoords  = [];
  const allManeuvers = [];
  let shapeOffset = 0;

  for (const leg of vr.trip?.legs ?? []) {
    const legCoords = _decodeShape(leg.shape);
    for (const m of leg.maneuvers ?? []) {
      allManeuvers.push({
        type:              m.type              ?? 0,
        instruction:       m.instruction       ?? '',
        verbal_pre:        m.verbal_pre_transition_instruction   ?? '',
        verbal_alert:      m.verbal_transition_alert_instruction ?? '',
        street_names:      m.street_names      ?? [],
        length:            Math.round((m.length ?? 0) * 1000) / 1000,
        time:              Math.round(m.time   ?? 0),
        begin_shape_index: (m.begin_shape_index ?? 0) + shapeOffset,
        end_shape_index:   (m.end_shape_index   ?? 0) + shapeOffset,
      });
    }
    shapeCoords.push(...legCoords);
    shapeOffset += legCoords.length;
  }

  const distanceKm  = Math.round((vr.trip?.summary?.length ?? 0) * 10) / 10;
  const durationMin = Math.round((vr.trip?.summary?.time   ?? 0) / 60);
  const mapsUrl     = _buildMapsUrl(shapeCoords, paramsData.origin, paramsData.destination);

  const data = {
    route: {
      type: 'FeatureCollection',
      features: [{
        type: 'Feature',
        geometry: { type: 'LineString', coordinates: shapeCoords },
        properties: {
          distance_km:           distanceKm,
          duration_min:          durationMin,
          vehicle_label:         paramsData.vehicle_label,
          is_placard_load:       paramsData.is_placard_load,
          permit_class:          paramsData.permit_class,
          tunnels_avoided_count: paramsData.tunnels_avoided.length,
        },
      }],
    },
    summary: {
      distance_km:  distanceKm,
      duration_min: durationMin,
      origin:       paramsData.origin,
      destination:  paramsData.destination,
      vehicle_label: paramsData.vehicle_label,
    },
    tunnels_avoided: paramsData.tunnels_avoided,
    maneuvers:       allManeuvers,
    maps_url:        mapsUrl,
  };

  NAV.lastPayload = payload;  // stored for off-route recalculate
  renderRouteMap(data);

  // Update the Google Maps button with actual computed waypoints
  document.getElementById('btnGoogleMaps').href = mapsUrl;
}

// ── Shared vehicle payload builder ────────────────────────────────────────────
function buildVehiclePayload(origin, destination, combo) {
  const isManual   = combo.requires_manual_dimensions;
  const isOversize = combo.requires_oversize_form;
  const needsDims  = isManual || isOversize;

  const lengthInput = lengthOptions.querySelector('input[name="lengthRadio"]:checked');
  const length_m    = needsDims ? null : (lengthInput ? parseFloat(lengthInput.value) : null);

  const schemeInput = massSchemeOptions.querySelector('input[name="massSchemeRadio"]:checked');
  const mass_scheme = needsDims ? null : (schemeInput ? schemeInput.value : null);

  const is_pbs       = pbsToggle.checked;
  const manual_gvm_t = is_pbs ? parseFloat(pbsGvm.value) || null : null;

  let manual_dimensions = null;
  if (needsDims) {
    manual_dimensions = {
      width_m:  parseFloat(ovWidth.value),
      height_m: parseFloat(ovHeight.value),
      length_m: parseFloat(ovLength.value),
      gvm_t:    parseFloat(ovMass.value),
    };
  }

  return {
    origin,
    destination,
    combination_code: combo.code,
    length_m,
    mass_scheme,
    is_pbs,
    ...(manual_gvm_t       !== null ? { manual_gvm_t }     : {}),
    ...(manual_dimensions          ? { manual_dimensions } : {}),
  };
}

// ── Leaflet map ───────────────────────────────────────────────────────────────
let _map         = null;
let _routeLayer  = null;
let _markerGroup = null;
let _tunnelGroup = null;

function ensureMap() {
  if (_map) return;
  _map = L.map('routeMap', { zoomControl: true });
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18,
  }).addTo(_map);
}

function renderRouteMap(data) {
  const panel = document.getElementById('routeMapPanel');
  panel.classList.remove('d-none');
  document.getElementById('valhallaOfflineNote').classList.add('d-none');

  ensureMap();

  // Clear previous layers
  if (_routeLayer)  { _map.removeLayer(_routeLayer);  _routeLayer  = null; }
  if (_markerGroup) { _map.removeLayer(_markerGroup); _markerGroup = null; }
  if (_tunnelGroup) { _map.removeLayer(_tunnelGroup); _tunnelGroup = null; }

  const { route, summary, tunnels_avoided } = data;
  const feature = route.features[0];
  const props   = feature.properties;

  // ── Route line ──────────────────────────────────────────────────────────────
  // GeoJSON coordinates are [lon, lat]; Leaflet wants [lat, lon]
  const leafletCoords = feature.geometry.coordinates.map(([lon, lat]) => [lat, lon]);
  _routeLayer = L.polyline(leafletCoords, { color: '#0d6efd', weight: 5, opacity: 0.85 });
  _routeLayer.addTo(_map);

  // ── Origin / destination markers ────────────────────────────────────────────
  _markerGroup = L.layerGroup();

  const greenDot = { radius: 9, color: '#198754', fillColor: '#198754', fillOpacity: 1, weight: 2 };
  const redDot   = { radius: 9, color: '#dc3545', fillColor: '#dc3545', fillOpacity: 1, weight: 2 };

  L.circleMarker([summary.origin.lat, summary.origin.lon], greenDot)
    .bindTooltip(`<strong>Origin:</strong> ${escHtml(summary.origin.label)}`, { sticky: true })
    .addTo(_markerGroup);

  L.circleMarker([summary.destination.lat, summary.destination.lon], redDot)
    .bindTooltip(`<strong>Destination:</strong> ${escHtml(summary.destination.label)}`, { sticky: true })
    .addTo(_markerGroup);

  _markerGroup.addTo(_map);

  // ── Avoided tunnel polygons ──────────────────────────────────────────────────
  if (tunnels_avoided && tunnels_avoided.length > 0) {
    _tunnelGroup = L.layerGroup();

    tunnels_avoided.forEach(tunnel => {
      // GeoJSON polygon coordinates: [[[lon, lat], ...]]
      const rings = tunnel.polygon.coordinates.map(ring =>
        ring.map(([lon, lat]) => [lat, lon])
      );
      const colour = tunnel.restriction_level === 'restricted' ? '#dc3545' : '#fd7e14';
      L.polygon(rings, {
        color:       colour,
        weight:      2,
        fillColor:   colour,
        fillOpacity: 0.18,
        dashArray:   '4 4',
      })
        .bindTooltip(
          `<strong>${escHtml(tunnel.name)}</strong><br>` +
          `<span class="text-muted">${tunnel.state} — ${tunnel.restriction_level}</span>`,
          { sticky: true }
        )
        .addTo(_tunnelGroup);
    });

    _tunnelGroup.addTo(_map);
  }

  // ── Fit map to route ─────────────────────────────────────────────────────────
  // Two-path fit strategy handles the race between Valhalla (fast, local) and
  // NHVR (slower, external) — either can win:
  //
  // Valhalla wins (common): renderRouteMap fires while #results is still d-none.
  //   The rAF here is a no-op (guards against 0×0 container corrupting Leaflet
  //   state). renderResults reveals #results, then fires its own rAF which does
  //   the actual invalidateSize + fitBounds against the now-visible container.
  //
  // NHVR wins: renderResults fires first, reveals #results, but _routeLayer is
  //   null so its rAF guard skips. renderRouteMap fires later with #results
  //   already visible — the rAF here runs normally and fits correctly.
  requestAnimationFrame(() => {
    if (resultsEl.classList.contains('d-none')) return;
    _map.invalidateSize();
    _map.fitBounds(_routeLayer.getBounds(), { padding: [30, 30] });
  });

  // ── Footer summary ───────────────────────────────────────────────────────────
  document.getElementById('routeMapDistance').textContent = `${props.distance_km} km`;
  document.getElementById('routeMapDuration').textContent = formatDuration(props.duration_min);

  const tunnelBadge = document.getElementById('tunnelAvoidanceBadge');
  const tunnelCount = document.getElementById('tunnelAvoidanceCount');
  const tunnelNames = document.getElementById('tunnelAvoidanceNames');

  if (tunnels_avoided && tunnels_avoided.length > 0) {
    tunnelCount.textContent = tunnels_avoided.length;
    tunnelBadge.classList.remove('d-none');
    const names = tunnels_avoided.map(t => escHtml(t.name)).join(', ');
    tunnelNames.innerHTML = `<i class="bi bi-sign-stop-fill text-danger me-1"></i>Avoided: ${names}`;
    tunnelNames.classList.remove('d-none');
  } else {
    tunnelBadge.classList.add('d-none');
    tunnelNames.classList.add('d-none');
  }

  const permitBadge = document.getElementById('permitClassBadge');
  if (props.permit_class && props.permit_class !== 'none') {
    const permitLabels = { class1: 'Class 1 Permit', special: 'Special Permit' };
    permitBadge.textContent = permitLabels[props.permit_class] || props.permit_class;
    permitBadge.className   = `badge ${props.permit_class === 'special' ? 'bg-danger' : 'bg-warning text-dark'}`;
    permitBadge.classList.remove('d-none');
  } else {
    permitBadge.classList.add('d-none');
  }

  // ── Populate navigation engine ───────────────────────────────────────────────
  // Convert GeoJSON [lon,lat] to Leaflet [lat,lon] for geometry math
  NAV.shapeLatlng   = feature.geometry.coordinates.map(([lon, lat]) => [lat, lon]);
  NAV.maneuvers     = data.maneuvers || [];
  NAV.maneuverIdx   = 0;
  NAV.spokenFlags   = {};
  NAV.offRouteCount = 0;

  if (NAV.maneuvers.length > 0) {
    document.getElementById('btnStartNav').classList.remove('d-none');
    renderStepList(NAV.maneuvers);
    document.getElementById('stepListPanel').classList.remove('d-none');
  }
}

function hideMapPanel() {
  stopNavigation(false);
  document.getElementById('routeMapPanel').classList.add('d-none');
  document.getElementById('valhallaOfflineNote').classList.add('d-none');
  document.getElementById('heightRestrictedAlert').classList.add('d-none');
  document.getElementById('offRouteAlert').classList.add('d-none');
  document.getElementById('stepListPanel').classList.add('d-none');
  document.getElementById('btnStartNav').classList.add('d-none');
}

// ── Render DG results ─────────────────────────────────────────────────────────
function renderDGResults(data) {
  const dgBlock = document.getElementById('dgBlock');

  const banner = document.getElementById('dgPlacarBanner');
  const icon   = document.getElementById('dgPlacarIcon');
  const title  = document.getElementById('dgPlacarTitle');
  const desc   = document.getElementById('dgPlacarDesc');

  banner.className = 'alert mb-3';

  if (data.is_placard_load === true) {
    banner.classList.add('dg-placard');
    icon.className    = 'bi bi-exclamation-diamond-fill fs-5';
    title.textContent = 'Placard Load';
  } else if (data.is_placard_load === false) {
    banner.classList.add('dg-no-placard');
    icon.className    = 'bi bi-check-circle-fill fs-5';
    title.textContent = 'Not a Placard Load';
  } else {
    banner.classList.add('dg-indeterminate');
    icon.className    = 'bi bi-question-circle-fill fs-5';
    title.textContent = 'Placard Status — Verify';
  }
  desc.textContent = data.placard_description || '';

  const dl = document.getElementById('dgSummaryDl');
  dl.innerHTML = '';
  const summaryItems = [
    ['DG Class',  data.dg_class_label ? `Class ${escHtml(data.dg_class_label)}` : escHtml(data.dg_class)],
    data.un_number ? ['UN Number', `UN ${escHtml(data.un_number)}`] : null,
    ['Quantity',  `${data.quantity} ${(DG_UNIT_MAP[data.dg_class] || DG_UNIT_MAP.default)}`],
    data.packing_group ? ['Packing Group', `PG ${escHtml(data.packing_group)}`] : null,
  ].filter(Boolean);

  summaryItems.forEach(([label, value]) => {
    dl.innerHTML +=
      `<dt class="col-sm-4 text-muted">${label}</dt><dd class="col-sm-8 fw-semibold">${value}</dd>`;
  });

  const threshCard = document.getElementById('dgThresholdCard');
  const threshNote = document.getElementById('dgThresholdNote');
  if (data.threshold_note) {
    threshNote.textContent = data.threshold_note;
    threshCard.classList.remove('d-none');
  } else {
    threshCard.classList.add('d-none');
  }

  const tunnelCard  = document.getElementById('dgTunnelCard');
  const tunnelTitle = document.getElementById('dgTunnelTitle');
  const tunnelNote  = document.getElementById('dgTunnelNote');

  if (data.tunnel_flag && data.tunnel_flag !== 'none' && data.tunnel_note) {
    const isRestricted = data.tunnel_flag === 'restricted';
    tunnelCard.classList.remove('d-none');
    tunnelTitle.innerHTML = isRestricted
      ? '<i class="bi bi-sign-stop-fill text-danger me-1"></i>Tunnel Restrictions'
      : '<i class="bi bi-sign-stop text-warning me-1"></i>Tunnel Restrictions (Check Required)';
    tunnelNote.textContent = data.tunnel_note;

    // Show policy-conflict badge when the restriction comes from operator policy
    // rather than the strict legislative text of NSW Road Rule 300-2
    const existingBadge = tunnelCard.querySelector('.tunnel-policy-conflict-badge');
    if (existingBadge) existingBadge.remove();

    if (data.tunnel_policy_conflict) {
      const badge = document.createElement('div');
      badge.className = 'tunnel-policy-conflict-badge alert alert-warning py-1 px-2 mt-2 mb-0 small';
      badge.innerHTML =
        '<i class="bi bi-exclamation-triangle-fill me-1"></i>' +
        '<strong>Policy conflict:</strong> NSW Road Rule 300-2 does not explicitly prohibit ' +
        `this class from tunnels for a single-class placard load. Toll road operators ` +
        '(Linkt, Transurban) apply a blanket ban regardless of class. ' +
        'Confirm with NHVR / EPA and the relevant tunnel operator before travel — ' +
        'this has not been resolved by current published guidance.';
      tunnelCard.querySelector('.card-body').appendChild(badge);
    }
  } else if (data.tunnel_flag === 'none' && data.tunnel_note) {
    // "none" flag but a note was provided — show a soft informational card
    tunnelCard.classList.remove('d-none');
    tunnelTitle.innerHTML = '<i class="bi bi-info-circle text-secondary me-1"></i>Tunnel Access';
    tunnelNote.textContent = data.tunnel_note;
    const existingBadge = tunnelCard.querySelector('.tunnel-policy-conflict-badge');
    if (existingBadge) existingBadge.remove();
  } else {
    tunnelCard.classList.add('d-none');
  }

  const segCard = document.getElementById('dgSegCard');
  const segNote = document.getElementById('dgSegNote');
  const segs    = data.segregation_classes || [];

  if (segs.length > 0 || data.segregation_note) {
    segCard.classList.remove('d-none');
    let html = '';
    if (data.segregation_note) {
      html += escHtml(data.segregation_note);
    } else if (segs.length > 0) {
      html += `Must not be carried together with: <strong>${escHtml(segs.join(', '))}</strong>`;
    }
    segNote.innerHTML = html;
  } else {
    segCard.classList.add('d-none');
  }

  const warnCard = document.getElementById('dgWarningsCard');
  const warnList = document.getElementById('dgWarningsList');
  const warnings = data.warnings || [];

  if (warnings.length > 0) {
    warnList.innerHTML = warnings.map(w => `<li class="mb-1">${escHtml(w)}</li>`).join('');
    warnCard.classList.remove('d-none');
  } else {
    warnCard.classList.add('d-none');
  }

  dgBlock.classList.remove('d-none');
}

// ── Render route results ──────────────────────────────────────────────────────
function renderResults(payload, data) {
  document.getElementById('summaryOrigin').textContent      = payload.origin;
  document.getElementById('summaryDestination').textContent = payload.destination;
  document.getElementById('summaryVehicle').textContent     = data.vehicle_label || payload.combination_code;

  const banner       = document.getElementById('statusBanner');
  const statusIcon   = document.getElementById('statusIcon');
  const statusTitle  = document.getElementById('statusTitle');
  const statusDetail = document.getElementById('statusDetail');

  banner.className = 'alert d-flex align-items-center mb-3';

  const status = (data.status || 'unknown').toLowerCase();
  const statusMap = {
    approved:    { cls: 'status-approved',    icon: 'bi-check-circle-fill',       title: 'Approved',               detail: 'This route is approved for your vehicle type.' },
    conditional: { cls: 'status-conditional', icon: 'bi-exclamation-circle-fill', title: 'Conditionally Approved', detail: 'This route is accessible subject to conditions.' },
    restricted:  { cls: 'status-restricted',  icon: 'bi-x-circle-fill',           title: 'Restricted',             detail: 'This vehicle type is restricted on this route.' },
    unknown:     { cls: 'status-unknown',     icon: 'bi-question-circle-fill',    title: 'Status Unknown',         detail: 'Route status could not be determined. Check NHVR Route Planner.' },
  };

  const s = statusMap[status] || statusMap.unknown;
  banner.classList.add(s.cls);
  statusIcon.className     = `bi ${s.icon} me-3 fs-4`;
  statusTitle.textContent  = s.title;
  statusDetail.textContent = data.status_detail || s.detail;

  const condBlock = document.getElementById('conditionsBlock');
  const condList  = document.getElementById('conditionsList');
  if (data.conditions && data.conditions.length > 0) {
    condList.innerHTML = data.conditions.map(c => `<li>${escHtml(c)}</li>`).join('');
    condBlock.classList.remove('d-none');
  } else {
    condBlock.classList.add('d-none');
  }

  const restBlock = document.getElementById('restrictionsBlock');
  const restList  = document.getElementById('restrictionsList');
  if (data.restrictions && data.restrictions.length > 0) {
    restList.innerHTML = data.restrictions.map(r => `<li>${escHtml(r)}</li>`).join('');
    restBlock.classList.remove('d-none');
  } else {
    restBlock.classList.add('d-none');
  }

  // Google Maps fallback link (text-based) — will be replaced by actual route URL
  // once route-geometry completes, but set the fallback now so the button works
  // even while geometry is still loading.
  document.getElementById('btnGoogleMaps').href =
    buildFallbackMapsUrl(payload.origin, payload.destination);

  document.getElementById('rawDataContent').textContent =
    JSON.stringify(data.raw || data, null, 2);

  resultsEl.classList.remove('d-none');

  // If Valhalla geometry arrived before NHVR (race condition), the Leaflet map
  // initialised against a 0×0 container while #results was still d-none.
  // Re-fit now that the container is visible.
  if (_map && _routeLayer) {
    requestAnimationFrame(() => {
      _map.invalidateSize();
      _map.fitBounds(_routeLayer.getBounds(), { padding: [30, 30] });
    });
  }

  resultsEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── Render oversize results ───────────────────────────────────────────────────
function renderOversizeResults(payload, data) {
  document.getElementById('summaryOrigin').textContent      = payload.origin || '—';
  document.getElementById('summaryDestination').textContent = payload.destination || '—';
  document.getElementById('summaryVehicle').textContent     = 'Oversize / Overmass (Class 1)';

  const dimsRow = document.getElementById('summaryDimsRow');
  document.getElementById('summaryDims').textContent =
    `${payload.width_m} m wide × ${payload.height_m} m high × ${payload.length_m} m long, ${payload.mass_t} t GCM`;
  dimsRow.classList.remove('d-none');

  document.getElementById('statusBanner').classList.add('d-none');
  document.getElementById('conditionsBlock').classList.add('d-none');
  document.getElementById('restrictionsBlock').classList.add('d-none');

  const permitBanner = document.getElementById('permitBanner');
  const permitIcon   = document.getElementById('permitIcon');
  const permitTitle  = document.getElementById('permitTitle');
  const permitDesc   = document.getElementById('permitDescription');

  permitBanner.className = 'alert mb-3';

  const permitMap = {
    none:    { cls: 'permit-none',    icon: 'bi-check-circle-fill',       title: 'No Permit Required' },
    class1:  { cls: 'permit-class1',  icon: 'bi-exclamation-circle-fill', title: 'NHVR Class 1 Permit Required' },
    special: { cls: 'permit-special', icon: 'bi-x-octagon-fill',          title: 'Special Permit / Assessment Required' },
  };

  const pm = permitMap[data.permit_class] || permitMap.class1;
  permitBanner.classList.add(pm.cls);
  permitIcon.className    = `bi ${pm.icon} me-1`;
  permitTitle.textContent = pm.title;
  permitDesc.textContent  = data.permit_description;

  const excBlock = document.getElementById('exceedancesBlock');
  const excList  = document.getElementById('exceedancesList');
  if (data.exceedances && data.exceedances.length > 0) {
    excList.innerHTML = data.exceedances.map(e => `<li>${escHtml(e)}</li>`).join('');
    excBlock.classList.remove('d-none');
  } else {
    excBlock.classList.add('d-none');
  }

  const peBlock  = document.getElementById('pilotEscortBlock');
  const peDetail = document.getElementById('pilotEscortDetail');
  const pilotStates  = data.requires_pilot  || [];
  const escortStates = data.requires_escort || [];

  if (pilotStates.length > 0 || escortStates.length > 0) {
    let html = '';
    if (escortStates.length > 0) {
      html += `<p class="mb-1"><strong>Police/traffic escort required:</strong> ${escHtml(escortStates.join(', '))}</p>`;
    }
    if (pilotStates.length > 0) {
      html += `<p class="mb-0"><strong>Pilot vehicle required:</strong> ${escHtml(pilotStates.join(', '))}</p>`;
    }
    peDetail.innerHTML = html;
    peBlock.classList.remove('d-none');
  } else {
    peBlock.classList.add('d-none');
  }

  const accordion = document.getElementById('stateAccordion');
  accordion.innerHTML = '';

  const stateFlags = data.state_flags || {};
  const states = Object.keys(stateFlags);

  if (states.length === 0) {
    accordion.innerHTML = '<p class="small text-muted mb-0">No state-specific restrictions flagged.</p>';
  } else {
    states.forEach((state, i) => {
      const flags   = stateFlags[state] || [];
      const id      = `state-${state}`;
      const headId  = `head-${id}`;
      const bodyId  = `body-${id}`;
      const isAlert = (data.requires_escort || []).includes(state);
      const isPilot = (data.requires_pilot  || []).includes(state);
      const badgeCls = isAlert ? 'bg-danger' : isPilot ? 'bg-warning text-dark' : 'bg-secondary';
      const badge    = isAlert ? 'Escort' : isPilot ? 'Pilot' : '';

      accordion.innerHTML += `
        <div class="accordion-item">
          <h2 class="accordion-header" id="${headId}">
            <button
              class="accordion-button collapsed py-2"
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#${bodyId}"
              aria-expanded="false"
              aria-controls="${bodyId}"
            >
              <span class="fw-semibold me-2">${escHtml(state)}</span>
              ${badge ? `<span class="badge ${badgeCls} me-1" style="font-size:0.7rem">${badge}</span>` : ''}
            </button>
          </h2>
          <div id="${bodyId}" class="accordion-collapse collapse" aria-labelledby="${headId}">
            <div class="accordion-body py-2">
              <ul class="mb-0 ps-3 small">
                ${flags.map(f => `<li class="mb-1">${escHtml(f)}</li>`).join('')}
              </ul>
            </div>
          </div>
        </div>`;
    });
  }

  if (payload.origin && payload.destination) {
    document.getElementById('btnGoogleMaps').href =
      buildFallbackMapsUrl(payload.origin, payload.destination);
    document.getElementById('btnGoogleMaps').classList.remove('d-none');
  } else {
    document.getElementById('btnGoogleMaps').classList.add('d-none');
  }

  document.getElementById('rawDataContent').textContent = JSON.stringify(data, null, 2);

  document.getElementById('oversizeBlock').classList.remove('d-none');
  resultsEl.classList.remove('d-none');

  if (_map && _routeLayer) {
    requestAnimationFrame(() => {
      _map.invalidateSize();
      _map.fitBounds(_routeLayer.getBounds(), { padding: [30, 30] });
    });
  }

  resultsEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Fallback Google Maps URL from plain text strings (used before Valhalla route arrives). */
function buildFallbackMapsUrl(origin, destination) {
  const base = 'https://www.google.com/maps/dir/?api=1';
  return `${base}&origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}&travelmode=driving`;
}

function formatDuration(totalMinutes) {
  if (totalMinutes < 60) return `${totalMinutes} min`;
  const h = Math.floor(totalMinutes / 60);
  const m = totalMinutes % 60;
  return m > 0 ? `${h} h ${m} min` : `${h} h`;
}

function setLoading(loading) {
  btnSearch.disabled = loading;
  btnText.classList.toggle('d-none', loading);
  btnSpinner.classList.toggle('d-none', !loading);
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorAlert.classList.remove('d-none');
  errorAlert.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideError() {
  errorAlert.classList.add('d-none');
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Navigation Engine ─────────────────────────────────────────────────────────

// Valhalla maneuver type integer → Bootstrap Icon class
const MANEUVER_ICON = {
  0:  'bi-arrow-up-circle',
  1:  'bi-geo-alt',               // Start
  2:  'bi-geo-alt',               // Start right
  3:  'bi-geo-alt',               // Start left
  4:  'bi-geo-alt-fill',          // Destination
  5:  'bi-geo-alt-fill',          // Destination right
  6:  'bi-geo-alt-fill',          // Destination left
  7:  'bi-arrow-up-circle',       // Becomes (road name change)
  8:  'bi-arrow-up-circle',       // Continue straight
  9:  'bi-arrow-up-right-circle', // Slight right
  10: 'bi-arrow-right-circle',    // Right
  11: 'bi-arrow-right-circle',    // Sharp right
  12: 'bi-arrow-repeat',          // U-turn right
  13: 'bi-arrow-repeat',          // U-turn left
  14: 'bi-arrow-left-circle',     // Sharp left
  15: 'bi-arrow-left-circle',     // Left
  16: 'bi-arrow-up-left-circle',  // Slight left
  17: 'bi-arrow-up-circle',       // Ramp straight
  18: 'bi-arrow-up-right-circle', // Ramp right
  19: 'bi-arrow-up-left-circle',  // Ramp left
  20: 'bi-sign-turn-right',       // Exit right
  21: 'bi-sign-turn-left',        // Exit left
  22: 'bi-arrow-up-circle',       // Stay straight
  23: 'bi-arrow-up-right-circle', // Stay right
  24: 'bi-arrow-up-left-circle',  // Stay left
  25: 'bi-arrow-up-circle',       // Merge
  26: 'bi-arrow-clockwise',       // Roundabout enter
  27: 'bi-arrow-clockwise',       // Roundabout exit
  28: 'bi-water',                 // Ferry enter
  29: 'bi-water',                 // Ferry exit
  37: 'bi-arrow-up-right-circle', // Merge right
  38: 'bi-arrow-up-left-circle',  // Merge left
};

function maneuverIcon(type) {
  return MANEUVER_ICON[type] || 'bi-arrow-up-circle';
}

// ── Nav state object ──────────────────────────────────────────────────────────
const NAV = {
  phase:         'idle',   // 'idle' | 'navigating' | 'off_route' | 'arrived'
  maneuvers:     [],       // from Valhalla response
  shapeLatlng:   [],       // [[lat, lon], ...] — Leaflet/geometry order
  maneuverIdx:   0,        // current maneuver
  watchId:       null,     // geolocation.watchPosition handle
  wakeLock:      null,     // Wake Lock API handle
  offRouteCount: 0,        // consecutive off-route readings
  spokenFlags:   {},       // { maneuverIdx: { dist300, dist80 } }
  lastPayload:   null,     // request payload (for recalculate)
  posMarker:     null,     // Leaflet driver position marker
  turnMarker:    null,     // Leaflet upcoming-turn marker
  muted:         localStorage.getItem('navMuted') === 'true',
};

// Thresholds
const TTS_DIST_FAR  = 300;  // metres — announce upcoming turn
const TTS_DIST_NEAR =  80;  // metres — announce turn now
const OFF_ROUTE_M   =  75;  // metres off-route before flagging
const OFF_ROUTE_N   =   3;  // consecutive readings before warning
const ADVANCE_M     =  40;  // metres to turn point before auto-advancing

// Destination maneuver types
const DEST_TYPES = new Set([4, 5, 6]);

// ── Geometry helpers ──────────────────────────────────────────────────────────

function haversineM(a, b) {
  // a, b: [lat, lon] degrees → distance in metres
  const R = 6371000;
  const dLat = (b[0] - a[0]) * Math.PI / 180;
  const dLon = (b[1] - a[1]) * Math.PI / 180;
  const lat1 = a[0] * Math.PI / 180;
  const lat2 = b[0] * Math.PI / 180;
  const sinDLat = Math.sin(dLat / 2);
  const sinDLon = Math.sin(dLon / 2);
  const x = sinDLat * sinDLat + Math.cos(lat1) * Math.cos(lat2) * sinDLon * sinDLon;
  return R * 2 * Math.atan2(Math.sqrt(x), Math.sqrt(1 - x));
}

function ptSegDistM(p, a, b) {
  // Distance in metres from point p to segment a–b (all [lat, lon]).
  // Uses flat-earth approximation — accurate enough for short nav segments.
  const cosLat = Math.cos(a[0] * Math.PI / 180);
  const px = (p[1] - a[1]) * cosLat, py = p[0] - a[0];
  const bx = (b[1] - a[1]) * cosLat, by = b[0] - a[0];
  const lenSq = bx * bx + by * by;
  let t = lenSq > 0 ? (px * bx + py * by) / lenSq : 0;
  t = Math.max(0, Math.min(1, t));
  const dx = (px - t * bx) / cosLat;
  const dy = py - t * by;
  return 6371000 * (Math.PI / 180) * Math.sqrt(dx * dx + dy * dy);
}

function closestSegment(pt, shape) {
  // Returns { idx, dist } — closest shape-segment index + distance in metres.
  let best = Infinity, idx = 0;
  for (let i = 0; i < shape.length - 1; i++) {
    const d = ptSegDistM(pt, shape[i], shape[i + 1]);
    if (d < best) { best = d; idx = i; }
  }
  return { idx, dist: best };
}

// ── Maneuver resolution ───────────────────────────────────────────────────────

function maneuverAtSegment(segIdx) {
  // Highest maneuver index whose begin_shape_index <= segIdx.
  let result = 0;
  for (let i = 0; i < NAV.maneuvers.length; i++) {
    if (segIdx >= NAV.maneuvers[i].begin_shape_index) result = i;
    else break;
  }
  return result;
}

function distToNextTurn(currentLatlng, segIdx) {
  // Distance in metres from current GPS position to the start of the NEXT maneuver.
  const nextIdx = NAV.maneuverIdx + 1;
  if (nextIdx >= NAV.maneuvers.length) return 0;

  const turnShapeIdx = NAV.maneuvers[nextIdx].begin_shape_index;
  if (segIdx >= turnShapeIdx) return 0;

  const shape = NAV.shapeLatlng;
  const segEnd = shape[segIdx + 1];
  if (!segEnd) return 0;

  // current position → end of current segment → along shape → turn point
  let d = haversineM(currentLatlng, segEnd);
  for (let i = segIdx + 1; i < turnShapeIdx && i < shape.length - 1; i++) {
    d += haversineM(shape[i], shape[i + 1]);
  }
  return d;
}

// ── GPS update handler (core nav loop) ───────────────────────────────────────

function onGpsUpdate(pos) {
  const latlng = [pos.coords.latitude, pos.coords.longitude];

  // Update live position marker
  if (!NAV.posMarker) {
    NAV.posMarker = L.circleMarker(latlng, {
      radius: 10, color: '#fff', fillColor: '#0d6efd',
      fillOpacity: 1, weight: 3, zIndexOffset: 1000,
    }).bindTooltip('Your position', { permanent: false }).addTo(_map);
  } else {
    NAV.posMarker.setLatLng(latlng);
  }

  if (NAV.phase !== 'navigating' && NAV.phase !== 'off_route') return;

  const { idx: segIdx, dist: offDist } = closestSegment(latlng, NAV.shapeLatlng);

  // ── Off-route detection ──────────────────────────────────────────────────────
  if (offDist > OFF_ROUTE_M) {
    NAV.offRouteCount = Math.min(NAV.offRouteCount + 1, OFF_ROUTE_N + 1);
    if (NAV.offRouteCount >= OFF_ROUTE_N && NAV.phase !== 'off_route') {
      NAV.phase = 'off_route';
      document.getElementById('offRouteAlert').classList.remove('d-none');
    }
    if (NAV.phase === 'off_route') {
      // Still pan to keep driver visible
      if (_map) _map.panTo(latlng, { animate: true, duration: 0.5 });
      return;
    }
  } else {
    if (NAV.offRouteCount > 0) NAV.offRouteCount = 0;
    if (NAV.phase === 'off_route') {
      NAV.phase = 'navigating';
      document.getElementById('offRouteAlert').classList.add('d-none');
    }
  }

  // ── Advance maneuver via segment detection ───────────────────────────────────
  const candidateIdx = maneuverAtSegment(segIdx);
  if (candidateIdx > NAV.maneuverIdx) {
    NAV.maneuverIdx = candidateIdx;
    NAV.spokenFlags[NAV.maneuverIdx] = {};
    if (DEST_TYPES.has(NAV.maneuvers[NAV.maneuverIdx]?.type)) {
      onArrived(); return;
    }
  }

  const dist = distToNextTurn(latlng, segIdx);

  // ── Advance maneuver via proximity to turn point ─────────────────────────────
  const nextIdx = NAV.maneuverIdx + 1;
  if (nextIdx < NAV.maneuvers.length && dist <= ADVANCE_M) {
    NAV.maneuverIdx = nextIdx;
    NAV.spokenFlags[NAV.maneuverIdx] = {};
    if (DEST_TYPES.has(NAV.maneuvers[NAV.maneuverIdx]?.type)) {
      onArrived(); return;
    }
  }

  checkTTSTriggers(dist);
  updateNavDisplay(dist);

  // Auto-pan map
  if (_map) _map.panTo(latlng, { animate: true, duration: 0.5 });
}

// ── Nav display ───────────────────────────────────────────────────────────────

function updateNavDisplay(distToTurn) {
  const m = NAV.maneuvers[NAV.maneuverIdx];
  if (!m) return;

  document.getElementById('navBarIcon').className = `bi ${maneuverIcon(m.type)}`;
  document.getElementById('navBarInstruction').textContent = m.instruction;

  const next = NAV.maneuvers[NAV.maneuverIdx + 1];
  document.getElementById('navBarNext').textContent =
    next ? `Then: ${next.instruction}` : '';

  const isLastManeuver = NAV.maneuverIdx >= NAV.maneuvers.length - 1;
  document.getElementById('navBarDistance').textContent =
    isLastManeuver ? '' : formatDistNav(distToTurn);

  updateTurnMarker();
  highlightCurrentStep();
}

function formatDistNav(metres) {
  if (metres >= 1000) return `${(metres / 1000).toFixed(1)}\u00a0km`;
  if (metres >= 100)  return `${Math.round(metres / 10) * 10}\u00a0m`;
  return `${Math.round(metres)}\u00a0m`;
}

function updateTurnMarker() {
  const nextManIdx = NAV.maneuverIdx + 1;
  if (nextManIdx >= NAV.maneuvers.length) {
    if (NAV.turnMarker) { _map.removeLayer(NAV.turnMarker); NAV.turnMarker = null; }
    return;
  }
  const shapeIdx  = NAV.maneuvers[nextManIdx].begin_shape_index;
  const turnLatlng = NAV.shapeLatlng[shapeIdx];
  if (!turnLatlng) return;

  if (!NAV.turnMarker) {
    NAV.turnMarker = L.circleMarker(turnLatlng, {
      radius: 8, color: '#ffc107', fillColor: '#ffc107',
      fillOpacity: 1, weight: 2, zIndexOffset: 900,
    }).bindTooltip('Upcoming turn', { permanent: false }).addTo(_map);
  } else {
    NAV.turnMarker.setLatLng(turnLatlng);
  }
}

function highlightCurrentStep() {
  const items = document.querySelectorAll('.nav-step-item');
  items.forEach((el, i) => {
    const active = i === NAV.maneuverIdx;
    el.classList.toggle('nav-step-active', active);
    if (active) el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  });
}

// ── TTS ───────────────────────────────────────────────────────────────────────

function speak(text) {
  if (NAV.muted || !window.speechSynthesis || !text) return;
  window.speechSynthesis.cancel();
  const utt = new SpeechSynthesisUtterance(text);
  utt.rate = 0.95;
  window.speechSynthesis.speak(utt);
}

function checkTTSTriggers(dist) {
  const nextIdx = NAV.maneuverIdx + 1;
  if (nextIdx >= NAV.maneuvers.length) return;

  const nextM = NAV.maneuvers[nextIdx];
  const flags = NAV.spokenFlags[NAV.maneuverIdx] || {};

  if (!flags.dist300 && dist <= TTS_DIST_FAR) {
    flags.dist300 = true;
    speak(nextM.verbal_pre || nextM.instruction);
  } else if (!flags.dist80 && dist <= TTS_DIST_NEAR) {
    flags.dist80 = true;
    speak(nextM.instruction);
  }

  NAV.spokenFlags[NAV.maneuverIdx] = flags;
}

// ── Arrival ───────────────────────────────────────────────────────────────────

function onArrived() {
  NAV.phase = 'arrived';
  speak('You have arrived at your destination.');
  stopNavigation(false);
  // Keep nav bar visible with arrival state
  document.getElementById('navBar').classList.remove('d-none');
  document.getElementById('navBarInstruction').textContent = 'Arrived at destination';
  document.getElementById('navBarIcon').className          = 'bi bi-geo-alt-fill text-success';
  document.getElementById('navBarDistance').textContent    = '';
  document.getElementById('navBarNext').textContent        = '';
}

// ── Navigation lifecycle ──────────────────────────────────────────────────────

function startNavigation() {
  if (!navigator.geolocation) {
    alert('Geolocation is not available in this browser.');
    return;
  }
  if (NAV.shapeLatlng.length === 0) return;

  NAV.phase         = 'navigating';
  NAV.maneuverIdx   = 0;
  NAV.offRouteCount = 0;
  NAV.spokenFlags   = {};

  document.getElementById('navBar').classList.remove('d-none');
  document.getElementById('btnStartNav').classList.add('d-none');
  document.getElementById('btnStopNav').classList.remove('d-none');
  document.getElementById('btnMuteNav').classList.remove('d-none');
  document.getElementById('offRouteAlert').classList.add('d-none');

  // iOS screen-lock warning
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) ||
                (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  document.getElementById('navBarIosWarning').classList.toggle('d-none', !isIOS);

  // Wake Lock API (Chrome/Android)
  if (navigator.wakeLock) {
    navigator.wakeLock.request('screen').then(wl => { NAV.wakeLock = wl; }).catch(() => {});
  }

  // Show first maneuver immediately
  updateNavDisplay(Infinity);

  // Speak first instruction
  const first = NAV.maneuvers[0];
  if (first) speak(first.verbal_pre || first.instruction);

  NAV.watchId = navigator.geolocation.watchPosition(
    onGpsUpdate,
    err => console.warn('GPS error:', err.message),
    { enableHighAccuracy: true, maximumAge: 2000, timeout: 10000 }
  );
}

function stopNavigation(showStartButton = true) {
  if (NAV.watchId !== null) {
    navigator.geolocation.clearWatch(NAV.watchId);
    NAV.watchId = null;
  }
  if (NAV.wakeLock) {
    NAV.wakeLock.release().catch(() => {});
    NAV.wakeLock = null;
  }
  if (NAV.posMarker && _map) { _map.removeLayer(NAV.posMarker); NAV.posMarker = null; }
  if (NAV.turnMarker && _map) { _map.removeLayer(NAV.turnMarker); NAV.turnMarker = null; }

  if (NAV.phase !== 'arrived') NAV.phase = 'idle';

  document.getElementById('navBar').classList.add('d-none');
  document.getElementById('btnStopNav').classList.add('d-none');
  document.getElementById('btnMuteNav').classList.add('d-none');
  document.getElementById('navBarIosWarning').classList.add('d-none');

  if (showStartButton && NAV.maneuvers.length > 0) {
    document.getElementById('btnStartNav').classList.remove('d-none');
  }
}

// ── Recalculate route ─────────────────────────────────────────────────────────

async function recalculateRoute() {
  if (!NAV.lastPayload) return;

  // Use current GPS position as new origin if available
  const payload = { ...NAV.lastPayload };
  if (NAV.posMarker) {
    const pos = NAV.posMarker.getLatLng();
    payload.origin = `${pos.lat.toFixed(6)}, ${pos.lng.toFixed(6)}`;
  }

  document.getElementById('offRouteAlert').classList.add('d-none');
  stopNavigation(false);

  const resp = await fetch('/api/route-geometry', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(payload),
  });

  if (resp.status === 503) {
    document.getElementById('valhallaOfflineNote').classList.remove('d-none');
    return;
  }

  const data = await resp.json();
  if (!resp.ok) {
    if (data.error_type === 'height_restricted') {
      document.getElementById('heightRestrictedAlert').classList.remove('d-none');
    } else {
      showError(data.error || 'Could not recalculate route.');
    }
    return;
  }

  NAV.lastPayload = payload;
  renderRouteMap(data);
  document.getElementById('btnGoogleMaps').href = data.maps_url;
}

// ── Mute toggle ───────────────────────────────────────────────────────────────

function updateMuteButton() {
  const btn = document.getElementById('btnMuteNav');
  if (NAV.muted) {
    btn.innerHTML = '<i class="bi bi-volume-mute-fill"></i>';
    btn.title     = 'Voice muted — tap to unmute';
    btn.classList.replace('btn-outline-secondary', 'btn-outline-warning');
  } else {
    btn.innerHTML = '<i class="bi bi-volume-up-fill"></i>';
    btn.title     = 'Voice on — tap to mute';
    btn.classList.replace('btn-outline-warning', 'btn-outline-secondary');
  }
}

document.getElementById('btnMuteNav').addEventListener('click', () => {
  NAV.muted = !NAV.muted;
  localStorage.setItem('navMuted', String(NAV.muted));
  updateMuteButton();
});
updateMuteButton();

// ── Button wiring ─────────────────────────────────────────────────────────────

document.getElementById('btnStartNav').addEventListener('click', () => {
  // Prime TTS engine on user gesture (required by iOS Safari)
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(new SpeechSynthesisUtterance(''));
  }
  startNavigation();
});

document.getElementById('btnStopNav').addEventListener('click', () => stopNavigation(true));
document.getElementById('btnRecalculate').addEventListener('click', recalculateRoute);

// ── Step list ─────────────────────────────────────────────────────────────────

function renderStepList(maneuvers) {
  const container = document.getElementById('stepListContent');
  container.innerHTML = maneuvers.map((m, i) => {
    const distStr = m.length > 0
      ? (m.length < 1 ? `${Math.round(m.length * 1000)}\u00a0m` : `${m.length.toFixed(1)}\u00a0km`)
      : '';
    return `<div class="nav-step-item list-group-item list-group-item-action py-2 px-3 d-flex align-items-start gap-2"
                 data-step="${i}">
      <i class="bi ${maneuverIcon(m.type)} mt-1 flex-shrink-0 text-primary" style="font-size:1.1rem;"></i>
      <div class="flex-grow-1 overflow-hidden">
        <div class="small fw-semibold">${escHtml(m.instruction)}</div>
        ${m.street_names && m.street_names.length
          ? `<div class="text-muted" style="font-size:0.75rem;">${escHtml(m.street_names[0])}</div>`
          : ''}
      </div>
      ${distStr ? `<div class="text-muted flex-shrink-0 small">${distStr}</div>` : ''}
    </div>`;
  }).join('');
}
