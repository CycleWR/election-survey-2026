import { loadData, responseCount, esc, raceUrl } from './data.js';

const data = await loadData();

// ---- Race directory (also the accessible alternative to the map) ----
const officeOrder = ['Regional Chair', 'Mayor', 'Regional Councillor', 'Ward Councillor'];
const countBadge = (id) => {
  const { total, responded } = responseCount(data, id);
  return `<span class="count" title="${responded} of ${total} candidates responded">${responded}/${total}</span>`;
};

let html = '';
for (const m of data.municipalities.values()) {
  const races = data.racesList.filter((r) => r.municipality === m.id)
    .sort((a, b) => officeOrder.indexOf(a.office) - officeOrder.indexOf(b.office) || (a.ward ?? 0) - (b.ward ?? 0));
  const main = races.filter((r) => r.office !== 'Ward Councillor');
  const wards = races.filter((r) => r.office === 'Ward Councillor');
  html += `<article class="muni-card">
    <h3>${esc(m.name)}</h3>
    <ul class="race-links">${main.map((r) => `<li><a href="${raceUrl(r.id)}">${esc(r.office)} ${countBadge(r.id)}</a></li>`).join('')}</ul>
    ${wards.length ? `<p class="ward-label">Ward councillor</p>
    <ul class="ward-grid">${wards.map((r) => `<li><a href="${raceUrl(r.id)}" aria-label="${esc(r.name)}">Ward ${r.ward}</a></li>`).join('')}</ul>` : ''}
  </article>`;
}
document.getElementById('race-directory').innerHTML = html;

// ---- Map ----
const geo = await fetch('data/wards.geojson').then((r) => r.json());
if (geo.placeholder) document.getElementById('placeholder-note').hidden = false;

const colours = { kitchener: '#1f7a4d', waterloo: '#2a6fb0', cambridge: '#b0582a' };
const colour = (f) => colours[f.properties.municipality] || '#6b5ca5';

const map = L.map('map', { scrollWheelZoom: false });
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 18,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
}).addTo(map);

const base = (f) => ({ color: colour(f), weight: 2, fillColor: colour(f), fillOpacity: 0.22 });
const layer = L.geoJSON(geo, {
  style: base,
  onEachFeature(f, l) {
    const { total, responded } = responseCount(data, f.properties.race);
    l.bindTooltip(`<strong>${esc(f.properties.name)}</strong><br>${responded} of ${total} candidates responded`, { sticky: true });
    l.on({
      mouseover: () => { l.setStyle({ weight: 4, fillOpacity: 0.45 }); l.bringToFront(); },
      mouseout: () => layer.resetStyle(l),
      click: () => { location.href = raceUrl(f.properties.race); },
    });
  },
}).addTo(map);
map.fitBounds(layer.getBounds(), { padding: [10, 10] });
