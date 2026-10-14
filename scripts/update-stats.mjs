// Uses GitHub's contribution calendar. No dependencies or estimated data.
import { execFileSync } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
const root = fileURLToPath(new URL('../', import.meta.url));
const query = `query { user(login: "josh-botha-p2100") { contributionsCollection { contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } } } } }`;
let response;
if (process.env.GITHUB_TOKEN) {
  const res = await fetch('https://api.github.com/graphql', {
    method: 'POST',
    headers: { Authorization: `Bearer ${process.env.GITHUB_TOKEN}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }), signal: AbortSignal.timeout(30000),
  });
  if (!res.ok) throw new Error(`GitHub API returned ${res.status}`);
  response = await res.json();
} else {
  response = JSON.parse(execFileSync('gh', ['api', 'graphql', '-f', `query=${query}`], { encoding: 'utf8', timeout: 30000 }));
}
if (response.errors) throw new Error(JSON.stringify(response.errors));
const calendar = response.data?.user?.contributionsCollection?.contributionCalendar;
if (!calendar?.weeks?.length) throw new Error('No contribution calendar returned. Existing assets preserved.');
const days = calendar.weeks.flatMap(w => w.contributionDays);
const weeks = calendar.weeks.map(w => w.contributionDays.reduce((sum, d) => sum + d.contributionCount, 0));
let streak = 0, longest = 0;
for (const day of days) { streak = day.contributionCount ? streak + 1 : 0; longest = Math.max(longest, streak); }
const active = days.filter(d => d.contributionCount > 0).length;
const updated = new Date().toISOString().slice(0, 10);
const start = days[0].date, end = days.at(-1).date;
const number = n => n.toLocaleString('en-US');
mkdirSync(`${root}assets`, { recursive: true });
const svg = (w, h, body, p, title) => `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img"><title>${title}</title><style>text{font-family:Segoe UI,Arial,sans-serif;fill:${p.ink}}.muted{fill:${p.muted}}.trace{stroke-dasharray:2200;stroke-dashoffset:2200;animation:draw 2s ease-out forwards}@keyframes draw{to{stroke-dashoffset:0}}@media(prefers-reduced-motion:reduce){.trace{animation:none!important;stroke-dashoffset:0}}</style>${body}</svg>`;
for (const [theme, p] of Object.entries({
  dark: { bg: '#0d1117', ink: '#f0f6fc', muted: '#919ba7', grid: '#27313c', accent: '#a9bbcf', fill: '#19232e' },
  light: { bg: '#ffffff', ink: '#1f2328', muted: '#59636e', grid: '#d8dee4', accent: '#536d89', fill: '#edf2f7' },
})) {
  const labels = ['Contributions', 'Active days', 'Longest streak'];
  const values = [number(calendar.totalContributions), number(active), `${longest} days`];
  let body = `<rect width="760" height="164" rx="8" fill="${p.bg}"/><path d="M253 34v79M506 34v79" stroke="${p.grid}"/>`;
  for (let i = 0; i < 3; i++) {
    const x = (i + .5) * 760 / 3;
    body += `<text x="${x}" y="77" text-anchor="middle" font-size="35" font-weight="600">${values[i]}</text><text x="${x}" y="105" text-anchor="middle" font-size="14" class="muted">${labels[i]}</text>`;
  }
  body += `<text x="380" y="144" text-anchor="middle" font-size="11" class="muted">${start} to ${end} · Updated ${updated}</text>`;
  writeFileSync(`${root}assets/stats-${theme}.svg`, svg(760, 164, body, p, `${calendar.totalContributions} contributions, ${active} active days, longest streak ${longest} days. ${start} to ${end}.`));
  const max = Math.max(4, Math.ceil(Math.max(...weeks) / 4) * 4);
  const points = weeks.map((n, i) => [56 + i / (weeks.length - 1) * 754, 215 - n / max * 148]);
  const line = points.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
  body = `<rect width="850" height="278" rx="8" fill="${p.bg}"/><text x="28" y="33" font-size="14" font-weight="600">A year of building</text><text x="822" y="33" text-anchor="end" font-size="11" class="muted">Contributions per week</text>`;
  for (let i = 0; i <= 4; i++) {
    const y = 215 - i / 4 * 148;
    body += `<path d="M56 ${y}H810" stroke="${p.grid}" stroke-dasharray="3 5"/><text x="43" y="${y + 4}" text-anchor="end" font-size="10" class="muted">${max * i / 4}</text>`;
  }
  body += `<polygon points="56,215 ${line} 810,215" fill="${p.fill}"/><polyline class="trace" points="${line}" fill="none" stroke="${p.accent}" stroke-width="2.5" stroke-linejoin="round"/>`;
  for (let i = 0; i < weeks.length; i += 9) {
    const date = calendar.weeks[i].contributionDays[0].date;
    const label = new Date(`${date}T00:00:00Z`).toLocaleDateString('en-US', { month: 'short', year: '2-digit', timeZone: 'UTC' });
    body += `<text x="${points[i][0]}" y="239" text-anchor="middle" font-size="11" class="muted">${label}</text>`;
  }
  body += `<text x="425" y="262" text-anchor="middle" font-size="10" class="muted">GitHub contribution calendar · Updated ${updated}</text>`;
  writeFileSync(`${root}assets/activity-${theme}.svg`, svg(850, 278, body, p, `Weekly GitHub contributions from ${start} to ${end}. Total ${calendar.totalContributions}.`));
}
console.log(JSON.stringify({ total: calendar.totalContributions, activeDays: active, longestStreak: longest, weeks: weeks.length, start, end }));
