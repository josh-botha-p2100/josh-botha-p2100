// Uses GitHub's contribution calendar. No dependencies or estimated data.
import { execFileSync } from 'node:child_process';
import { renderHeatmap } from './render-heatmap.mjs';
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
  response = JSON.parse(execFileSync('gh', ['api', 'graphql', '-f', `query=${query}`], { encoding: 'utf8', timeout: 120000 }));
}
if (response.errors) throw new Error(JSON.stringify(response.errors));
const calendar = response.data?.user?.contributionsCollection?.contributionCalendar;
if (!calendar?.weeks?.length) throw new Error('No contribution calendar returned. Existing assets preserved.');
renderHeatmap(calendar);
