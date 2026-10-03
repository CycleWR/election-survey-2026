// Shared data loading and helpers. All content lives in /data as static JSON.
let cache;

export async function loadData() {
  if (cache) return cache;
  // 'no-cache' makes the browser check for newer data on every visit (GitHub Pages
  // otherwise lets it reuse a stale copy for up to 10 minutes after an update).
  const get = (f) => fetch(`data/${f}`, { cache: 'no-cache' }).then((r) => {
    if (!r.ok) throw new Error(`Failed to load ${f}`);
    return r.json();
  });
  const [survey, racesFile, candidates] = await Promise.all([
    get('survey.json'), get('races.json'), get('candidates.json'),
  ]);
  const races = new Map(racesFile.races.map((r) => [r.id, r]));
  const municipalities = new Map(racesFile.municipalities.map((m) => [m.id, m]));
  const byRace = new Map();
  for (const c of candidates) {
    if (!byRace.has(c.race)) byRace.set(c.race, []);
    byRace.get(c.race).push(c);
  }
  // Alphabetical by surname so no candidate gets preferential placement.
  for (const list of byRace.values()) list.sort((a, b) => sortName(a).localeCompare(sortName(b)));
  cache = { survey, races, municipalities, racesList: racesFile.races, candidates, byRace };
  return cache;
}

const sortName = (c) => {
  const parts = c.name.trim().split(/\s+/);
  return `${parts.at(-1)} ${parts.slice(0, -1).join(' ')}`;
};

export function responseCount(data, raceId) {
  const list = data.byRace.get(raceId) || [];
  return { total: list.length, responded: list.filter((c) => c.responded).length };
}

export function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (ch) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[ch]);
}

// Keeps line breaks from candidates' written answers.
export const paragraphs = (s) =>
  esc(s).split(/\n{2,}/).map((p) => `<p>${p.replace(/\n/g, '<br>')}</p>`).join('');

export const raceUrl = (id, hash = '') => `race.html?id=${encodeURIComponent(id)}${hash ? `#${hash}` : ''}`;
