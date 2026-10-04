import { loadData, responseCount, esc, paragraphs, raceUrl } from './data.js';

const data = await loadData();
const raceId = new URLSearchParams(location.search).get('id');
const race = data.races.get(raceId);
const $ = (id) => document.getElementById(id);

if (!race) {
  // e.g. a ward on the map with no candidates in the sheet yet, or an old link.
  $('race-title').textContent = 'No responses for this race yet';
  document.querySelector('.mode-toggle').hidden = true;
  $('panel').innerHTML = '<p>We haven\'t published any candidate responses for this race yet. Please check back soon.</p><p><a href="./">Back to all races</a></p>';
} else {
  const candidates = data.byRace.get(race.id) || [];
  const responders = candidates.filter((c) => c.responded);
  const nonResponders = candidates.filter((c) => !c.responded);
  const muni = data.municipalities.get(race.municipality);
  // Some questions only apply to certain municipalities (Cambridge wayfinding) or offices (Regional budget).
  const applies = (q) => (!q.municipalities || q.municipalities.includes(race.municipality))
    && (!q.offices || q.offices.includes(race.office));
  const topics = data.survey.topics
    .map((t) => ({ ...t, questions: t.questions.filter(applies) }))
    .filter((t) => t.questions.length);

  // ---- Header ----
  document.title = `${race.name} · CycleWR 2026 Candidate Survey`;
  $('race-title').textContent = race.name;
  $('breadcrumb').innerHTML = `<a href="./">All wards</a> <span aria-hidden="true">›</span> ${esc(muni.name)} <span aria-hidden="true">›</span> <span aria-current="page">${esc(race.office)}</span>`;
  const { total, responded } = responseCount(data, race.id);
  $('race-summary').textContent = total
    ? `${responded} of ${total} candidates responded to the survey.`
    : 'No candidates are registered for this race yet.';

  // Other races a voter in this ward also sees on their ballot.
  const related = race.municipality === 'region'
    ? []
    : [`${race.municipality}-mayor`, `${race.municipality}-regional-councillor`, 'region-chair'];
  const relatedRaces = related.map((id) => data.races.get(id)).filter((r) => r && r.id !== race.id);
  if (relatedRaces.length) {
    $('ballot').innerHTML = `<span class="ballot-label">Also on your ballot:</span>
      ${relatedRaces.map((r) => `<a class="pill" href="${raceUrl(r.id)}">${esc(r.name)}</a>`).join('')}`;
  }

  // ---- Topic tabs (shown in "by topic" mode) ----
  // Plus an "All topics" tab that shows every question on one page.
  $('tabs').innerHTML = topics.map((t) =>
    `<a role="tab" class="tab" href="#topic=${t.id}" data-key="topic=${t.id}">${esc(t.title)}</a>`).join('')
    + '<a role="tab" class="tab tab-all" href="#topic=all" data-key="topic=all">All topics</a>';

  // Colour answers by their first word, so "Yes, with conditions" still reads as a yes.
  const choiceClass = (c) => {
    const word = String(c).toLowerCase().match(/[a-z]+/)?.[0];
    const tone = { yes: 'yes', no: 'no', unsure: 'unsure', undecided: 'unsure', maybe: 'unsure', not: 'unsure' }[word];
    return `chip${tone ? ` chip-${tone}` : ''}`;
  };

  function answerBody(q, a) {
    if (!a || (!a.choice && !a.comment)) return '<p class="muted">No answer given.</p>';
    return `${a.choice ? `<span class="${choiceClass(a.choice)}">${esc(a.choice)}</span>` : ''}
      ${a.comment ? `<div class="comment">${paragraphs(a.comment)}</div>` : ''}`;
  }

  function nonResponderNote() {
    if (!nonResponders.length) return '';
    return `<aside class="nonresponders"><strong>Did not respond:</strong> ${nonResponders.map((c) => esc(c.name)).join(', ')}</aside>`;
  }

  function renderTopic(topic, withNote = true) {
    const note = withNote ? nonResponderNote() : '';
    if (!responders.length) return `<h2>${esc(topic.title)}</h2><p>No candidates in this race have responded yet.</p>${note}`;
    return `<h2>${esc(topic.title)}</h2>
      ${topic.description ? `<p class="topic-desc">${esc(topic.description)}</p>` : ''}
      ${topic.questions.map((q) => `
        <article class="question">
          <h3>${esc(q.text)}</h3>
          ${q.type === 'choice' ? summaryBar(q) : ''}
          <ul class="answers">
            ${responders.map((c) => `<li class="answer">
              <a class="cand-name" href="#candidate=${encodeURIComponent(c.id)}">${esc(c.name)}</a>
              ${answerBody(q, c.answers[q.id])}
            </li>`).join('')}
          </ul>
        </article>`).join('')}
      ${note}`;
  }

  function renderAllTopics() {
    if (!responders.length) return `<p>No candidates in this race have responded yet.</p>${nonResponderNote()}`;
    return topics.map((t) => `<section class="all-topic">${renderTopic(t, false)}</section>`).join('') + nonResponderNote();
  }

  // Quick "3 Yes · 1 Unsure" tally for multiple-choice questions.
  function summaryBar(q) {
    const counts = {};
    for (const c of responders) {
      const ch = c.answers[q.id]?.choice;
      if (ch) counts[ch] = (counts[ch] || 0) + 1;
    }
    const order = [...(q.choices || []), ...Object.keys(counts).filter((ch) => !(q.choices || []).includes(ch))];
    const parts = order.filter((ch) => counts[ch]).map((ch) => `<span class="${choiceClass(ch)}">${counts[ch]} ${esc(ch)}</span>`);
    return parts.length ? `<p class="tally">${parts.join(' ')}</p>` : '';
  }

  function renderCandidates(selectedId) {
    if (!candidates.length) return '<p>No candidates are registered for this race yet.</p>';
    // Non-responders are shown greyed out and can't be selected: they have no answers to show.
    const selected = responders.find((c) => c.id === selectedId) || responders[0];
    const picker = `<div class="cand-picker" role="list">${candidates.map((c) => (c.responded
      ? `<a role="listitem" class="cand-pick ${c === selected ? 'is-selected' : ''}"
           href="#candidate=${encodeURIComponent(c.id)}" ${c === selected ? 'aria-current="true"' : ''}>${esc(c.name)}</a>`
      : `<span role="listitem" class="cand-pick no-response" title="Did not respond to the survey">
           ${esc(c.name)} <small>(no response)</small></span>`)).join('')}</div>`;
    if (!selected) return `${picker}<p>No candidates in this race have responded yet.</p>`;

    return `<h2 class="visually-hidden">All responses by candidate</h2>${picker}
      <div class="cand-card">
        <h2>${esc(selected.name)}</h2>
        ${/^https?:\/\//i.test(selected.website) ? `<p><a href="${esc(selected.website)}" rel="noopener" target="_blank">Campaign website</a></p>` : ''}
        ${topics.map((t) => `
        <section class="cand-topic">
          <h3>${esc(t.title)}</h3>
          ${t.questions.map((q) => `<div class="qa">
            <p class="q">${esc(q.text)}</p>
            ${answerBody(q, selected.answers[q.id])}
          </div>`).join('')}
        </section>`).join('')}
      </div>`;
  }

  // Hash drives the view so every topic and candidate has a shareable link.
  function route() {
    const hash = decodeURIComponent(location.hash.slice(1));
    let key = null;
    let html;
    const byCandidate = hash.startsWith('candidate');
    if (byCandidate) {
      html = renderCandidates(hash.split('=')[1]);
    } else if (hash === 'topic=all') {
      key = hash;
      html = renderAllTopics();
    } else {
      const topic = topics.find((t) => `topic=${t.id}` === hash) || topics[0];
      key = `topic=${topic.id}`;
      html = renderTopic(topic);
    }
    $('mode-topic').classList.toggle('is-active', !byCandidate);
    $('mode-candidate').classList.toggle('is-active', byCandidate);
    $('tabs').hidden = byCandidate;
    for (const a of $('tabs').children) {
      const on = a.dataset.key === key;
      a.classList.toggle('is-active', on);
      a.setAttribute('aria-selected', on);
      if (on) a.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    }
    $('panel').innerHTML = html;
  }

  window.addEventListener('hashchange', () => { route(); $('panel').focus({ preventScroll: true }); });
  route();
}
