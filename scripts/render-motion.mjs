// Usage: node scripts/render-motion.mjs /path/to/ffmpeg
// Six-second GIF loops from original generated artwork, plus typing SVGs.
import { execFileSync } from 'node:child_process';
import { writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
const root = fileURLToPath(new URL('../', import.meta.url));
const ffmpeg = process.argv[2] || 'ffmpeg';
function render(input, output, filter) {
  execFileSync(ffmpeg, ['-hide_banner', '-loglevel', 'error', '-y', '-loop', '1', '-i', `${root}assets/${input}`, '-filter_complex', `${filter},trim=duration=6,split[a][b];[a]palettegen=max_colors=96:stats_mode=full[p];[b][p]paletteuse=dither=bayer:bayer_scale=3`, '-t', '6', '-loop', '0', `${root}assets/${output}`], { stdio: 'inherit', timeout: 180000 });
}
render('reaching-hands.png', 'reaching-hands.gif', "zoompan=z='1.022+0.012*sin(2*PI*on/48)':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=840x280:fps=8");
render('astronaut.png', 'astronaut.gif', "scale=280:280,pad=320:320:20:20:color=0x0d1117,crop=300:300:10:'10+6*sin(2*PI*t/6)',fps=8");
for (const [theme, ink] of [['dark', '#c9d1d9'], ['light', '#424a53']]) {
  writeFileSync(`${root}assets/typing-${theme}.svg`, `<svg xmlns="http://www.w3.org/2000/svg" width="650" height="62" viewBox="0 0 650 62" role="img"><title>Software. Data. AI. Building things that make work better.</title><style>.reveal{animation:type 7s steps(19,end) infinite}.cursor{animation:blink 1s step-end infinite}@keyframes type{0%,8%{width:0}45%,82%{width:310px}97%,100%{width:0}}@keyframes blink{50%{opacity:0}}@media(prefers-reduced-motion:reduce){.reveal{animation:none;width:310px}.cursor{animation:none;opacity:0}}</style><defs><clipPath id="type"><rect class="reveal" x="172" y="0" width="310" height="38"/></clipPath></defs><g clip-path="url(#type)"><text x="325" y="27" text-anchor="middle" font-family="Consolas,monospace" font-size="24" fill="${ink}">Software. Data. AI.</text></g><text class="cursor" x="470" y="27" font-family="Consolas,monospace" font-size="24" fill="${ink}">_</text><text x="325" y="53" text-anchor="middle" font-family="Segoe UI,Arial,sans-serif" font-size="13" fill="${ink}">Building things that make work better.</text></svg>`);
}
console.log('Rendered two looping GIFs and theme-aware typing SVGs.');
