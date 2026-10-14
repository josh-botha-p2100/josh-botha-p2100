import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
const root = fileURLToPath(new URL('../', import.meta.url));
const fmt = n => n.toLocaleString('en-US');
const escape = s => String(s).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
const colors = {github:['#263648','#172637','#536577'], claude:['#0066CC','#0055AA','#318CE7'], codex:['#79B8F3','#4C93D9','#B3D8FC']};

export function renderHeatmap(calendar, mobile = false) {
  const ai = JSON.parse(readFileSync(`${root}data/ai-activity.json`, 'utf8'));
  if (ai.schemaVersion !== 1 || !Array.isArray(ai.days)) throw new Error('Unsupported AI snapshot');
  const records = new Map(ai.days.map(d => [d.date,d]));
  const weeks = calendar.weeks.slice(-(mobile ? 26 : 53));
  const days = weeks.flatMap((week,w) => week.contributionDays.map((day,d) => ({date:day.date, github:day.contributionCount, claude:records.get(day.date)?.claude ?? null, codex:records.get(day.date)?.codex ?? null, w,d})));
  for (const d of days) for (const key of ['github','claude','codex']) {
    if (d[key] !== null && (!Number.isInteger(d[key]) || d[key] < 0)) throw new Error(`Invalid ${key} count`);
  }
  const totals = Object.fromEntries(['github','claude','codex'].map(k => [k, days.reduce((n,d) => n+(d[k]??0),0)]));
  const max = Object.fromEntries(['github','claude','codex'].map(k => [k, Math.max(1,...days.map(d => d[k]??0))]));
  const range = `${days[0].date} to ${days.at(-1).date}`;
  const snapshot = new Date(ai.generatedAt).toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric',timeZone:'Australia/Sydney'});
  const today = new Date().toISOString().slice(0,10);
  const width = mobile ? 480 : 960;
  let body = `<rect width="${width}" height="516" fill="#FAFBFC"/><text x="${mobile?24:38}" y="48" font-size="${mobile?30:34}" font-weight="600" letter-spacing="-1.1">My working rhythm.</text>`;
  body += mobile ? `<text x="24" y="72" font-size="12" fill="#6B7280">Last 26 weeks · ${range}</text>` : `<text x="922" y="46" text-anchor="end" font-size="12" fill="#6B7280">${range}</text>`;
  const names = ['GitHub contributions','Claude prompts','Codex prompts'];
  ['github','claude','codex'].forEach((k,i) => {
    const x = mobile ? 24+i*152 : 38+i*308;
    const y = mobile ? 113 : 96;
    body += `<rect x="${x}" y="${y-9}" width="8" height="8" fill="${colors[k][0]}"/><text x="${x+14}" y="${y}" font-size="${mobile?11:13}" fill="#4B5563">${names[i]}</text><text x="${x}" y="${y+43}" font-size="${mobile?30:36}" font-weight="600" letter-spacing="-1">${fmt(totals[k])}</text>`;
  });
  const poly = (points, fill) => `<path d="M${points.map(p => p.map(n=>n.toFixed(1)).join(',')).join('L')}Z" fill="${fill}"/>`;
  // Project 53 weeks by 7 days into one continuous isometric landscape.
  const ox=mobile?24:55, oy=mobile?344:336, ux=mobile?13.7:14.8, uy=-2.25, vx=mobile?8.6:10.6, vy=7.7;
  let floor = '', columns = '';
  // Back-to-front painter order prevents nearer columns being overpainted.
  for (const day of [...days].sort((a,b)=>(a.d*vy+a.w*uy)-(b.d*vy+b.w*uy))) {
    const x=ox+day.w*ux+day.d*vx, y=oy+day.w*uy+day.d*vy;
    const a=[x,y], b=[x+12.8,y-1.95], c=[x+22,y+4.7], d=[x+9.2,y+6.7];
    floor += poly([a,b,c,d], '#E3EBF2');
    let height=0;
    let pillar='';
    for (const key of ['github','claude','codex']) {
      if (!day[key]) continue;
      const h = 3 + Math.log1p(day[key])/Math.log1p(max[key])*28;
      const at=p=>[p[0],p[1]-height];
      const top=p=>[p[0],p[1]-height-h];
      pillar += poly([at(b),at(c),top(c),top(b)],colors[key][1]);
      pillar += poly([at(c),at(d),top(d),top(c)],colors[key][0]);
      pillar += poly([top(a),top(b),top(c),top(d)],colors[key][2]);
      height += h;
    }
    const detail = `${day.date}: ${day.github} GitHub contributions, ${day.claude===null?'unavailable':day.claude} Claude prompts, ${day.codex===null?'unavailable':day.codex} Codex prompts`;
    const delay=(day.w/(weeks.length-1)*1.6+day.d*.045).toFixed(3);
    columns += `<g class="column" style="animation-delay:${delay}s"><title>${escape(detail)}</title>${pillar}</g>`;
  }
  body += floor + columns;
  for(let w=0;w<weeks.length;w+=mobile?5:9){
    const day=weeks[w].contributionDays[0].date;
    const label=new Date(`${day}T12:00:00Z`).toLocaleDateString('en-GB',{month:'short',timeZone:'UTC'});
    body+=`<text x="${ox+w*ux+82}" y="${oy+w*uy+79}" text-anchor="middle" font-size="11" fill="#6B7280">${label}</text>`;
  }
  body+=`<path d="M${mobile?24:38} 440H${mobile?456:922}" stroke="#DCE5ED"/>`;
  if(mobile){
    body+=`<text x="24" y="463" font-size="12" fill="#4B5563">One column per day · Log scale within each source</text><text x="24" y="484" font-size="11" fill="#6B7280">Local AI snapshot: ${snapshot} · Recorded prompts</text><text x="24" y="503" font-size="11" fill="#6B7280">GitHub updated ${today} · AI dates use Sydney time</text>`;
  } else {
    body+=`<text x="38" y="466" font-size="12" fill="#4B5563">One column per day. Three sources, kept distinct.</text><text x="922" y="466" text-anchor="end" font-size="11" fill="#6B7280">Log scale within each source</text>`;
    body+=`<text x="38" y="491" font-size="11" fill="#6B7280">Local AI snapshot: ${snapshot} · Sydney time · Recorded human prompts only</text><text x="922" y="491" text-anchor="end" font-size="11" fill="#6B7280">GitHub updated ${today}</text>`;
  }
  const title = `Combined 3D activity calendar: ${fmt(totals.github)} GitHub contributions, ${fmt(totals.claude)} recorded Claude prompts, ${fmt(totals.codex)} recorded Codex prompts. ${range}. Local AI snapshot ${snapshot}.`;
  const style = 'text{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif;fill:#0A0A0A;font-variant-numeric:tabular-nums}text[fill]{fill:attr(fill)}.column{animation:rise .8s cubic-bezier(.22,1,.36,1) both}@keyframes rise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}@media(prefers-reduced-motion:reduce){.column{animation:none}}';
  // Presentation attributes must remain effective; do not override their fill in CSS.
  const css=style.replace('fill:#0A0A0A;','').replace('text[fill]{fill:attr(fill)}','');
  const output=`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="516" viewBox="0 0 ${width} 516" role="img"><title>${escape(title)}</title><style>${css}</style>${body}</svg>`;
  const suffix = mobile ? '-mobile' : '';
  writeFileSync(`${root}assets/activity-3d${suffix}.svg`,output);
  writeFileSync(`${root}assets/activity-3d${suffix}-static.svg`,output.replace(/animation:rise[^}]+/g,'animation:none'));
  console.log('Heatmap totals:',JSON.stringify(totals));
  if(!mobile) renderHeatmap(calendar,true);
  return {totals,days:days.length};
}
