"""Export daily human-prompt counts only. Raw local histories never leave this process.

Python 3.10+, tzdata on Windows. Reads Claude Code and Codex local histories.
Use --home to point at a fixture or another explicitly selected local account.
"""
import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

SKIP = ('<command-name>', '<local-command', '<system-reminder>', 'Caveat:',
        '<task-notification>', '<ci-monitor-event>', '[Request interrupted',
        '<command-message>', '<user-prompt-submit-hook>', '<<autonomous-loop',
        '<teammate-message', 'This session is being continued from a previous conversation',
        '<bash-input>', '<bash-stdout>', '<bash-stderr>', 'Tool loaded.',
        'You are running an automated 30-minute briefing')


def text_of(content):
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ''
    if any(b.get('type') == 'tool_result' for b in content if isinstance(b, dict)):
        return ''
    return '\n'.join(b.get('text', '') for b in content if isinstance(b, dict) and b.get('type') in ('text', 'input_text'))


def collect(home, now, cache_path=None):
    zone = ZoneInfo('Australia/Sydney')
    today = now.astimezone(zone).date()
    start = today - timedelta(days=364)
    counts = {'claude': Counter(), 'codex': Counter()}
    seen = {'claude': set(), 'codex': set()}
    malformed = Counter()
    cache = {}
    if cache_path and cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding='utf-8'))
        except ValueError:
            pass
    updated_cache = {}
    captured = []
    import_revision = ''

    def register(source, day, digest):
        if start.isoformat() <= day <= today.isoformat() and digest not in seen[source]:
            seen[source].add(digest)
            counts[source][day] += 1

    def cached(source, path):
        key = hashlib.sha256((source + str(path) + (import_revision if source == 'codex' else '')).encode()).hexdigest()
        stat = path.stat()
        signature = [stat.st_size, stat.st_mtime_ns]
        old = cache.get(key)
        if old and old['signature'] == signature:
            updated_cache[key] = old
            for day, digest in old['events']:
                register(source, day, digest)
            return key, signature, True
        return key, signature, False

    def add(source, stamp, text):
        text = text.lstrip('\ufeff').strip()
        if not stamp or not text or text.startswith(SKIP):
            return
        try:
            dt = datetime.fromisoformat(str(stamp).replace('Z', '+00:00'))
            if dt.tzinfo is None:
                return
            day = dt.astimezone(zone).date()
        except (ValueError, TypeError):
            return
        if not start <= day <= today:
            return
        # Forks and resumed sessions can repeat the same historical user event.
        digest = hashlib.sha256((dt.isoformat() + '\0' + text).encode()).hexdigest()
        captured.append([day.isoformat(), digest])
        register(source, day.isoformat(), digest)

    claude_files = sorted((home / '.claude' / 'projects').glob('*/*.jsonl'))
    for path in claude_files:
        if path.name.startswith('agent-'):
            continue
        key, signature, reused = cached('claude', path)
        if reused:
            continue
        captured = []
        with path.open('rb') as fh:
            for line in fh:
                if b'"user"' not in line or not re.search(rb'"type"\s*:\s*"user"', line):
                    continue
                try:
                    r = json.loads(line)
                except (ValueError, UnicodeError):
                    malformed['claude'] += 1
                    continue
                if r.get('type') != 'user' or any(r.get(k) for k in ('isSidechain', 'isMeta', 'isCompactSummary')) or r.get('toolUseResult') is not None:
                    continue
                add('claude', r.get('timestamp'), text_of((r.get('message') or {}).get('content')))
        updated_cache[key] = {'signature': signature, 'events': captured}

    # CLI input history can cover days whose full transcripts were not retained.
    # Use it only on dates with no transcript prompts, never add both counts.
    captured = []
    transcript_days = set(counts['claude'])
    history = home / '.claude' / 'history.jsonl'
    if history.exists():
        with history.open(encoding='utf-8') as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                    dt = datetime.fromtimestamp(r['timestamp'] / 1000, timezone.utc)
                    if dt.astimezone(zone).date().isoformat() not in transcript_days:
                        add('claude', dt.isoformat(), r.get('display', ''))
                except (ValueError, KeyError, TypeError):
                    malformed['claudeHistory'] += 1

    base = home / '.codex'
    imported = set()
    imports = base / 'external_agent_session_imports.json'
    if imports.exists():
        imported = {r.get('imported_thread_id') for r in json.loads(imports.read_text(encoding='utf-8')).get('records', [])}
        import_revision = '|'.join(sorted(s for s in imported if isinstance(s,str)))
    files = sorted((base / 'sessions').glob('**/rollout-*.jsonl')) + sorted((base / 'archived_sessions').glob('rollout-*.jsonl'))
    for path in files:
        key, signature, reused = cached('codex', path)
        if reused:
            continue
        captured = []
        pending = []
        skip = False
        with path.open('rb') as fh:
            for line in fh:
                if not any(x in line for x in (b'"session_meta"', b'"UserMessage"', b'"user_message"')):
                    continue
                try:
                    r = json.loads(line)
                except (ValueError, UnicodeError):
                    malformed['codex'] += 1
                    continue
                p = r.get('payload') or {}
                if r.get('type') == 'session_meta':
                    src = p.get('source')
                    if p.get('id') in imported or p.get('session_id') in imported or p.get('thread_source') in ('guardian_review', 'subagent') or (isinstance(src, dict) and 'subagent' in src):
                        skip = True
                        break
                if r.get('type') != 'event_msg':
                    continue
                if str(p.get('turn_id', '')).startswith('external-import'):
                    skip = True
                    break
                if p.get('type') == 'item_completed' and (p.get('item') or {}).get('type') == 'UserMessage':
                    pending.append((r.get('timestamp'), text_of(p['item'].get('content'))))
                elif p.get('type') == 'user_message':
                    pending.append((r.get('timestamp'), p.get('message') or ''))
        if not skip:
            for stamp, text in pending:
                add('codex', stamp, text)
        updated_cache[key] = {'signature': signature, 'events': captured}

    sources = {}
    for source in counts:
        dates = sorted(counts[source])
        sources[source] = {'metric': 'recorded human prompts', 'firstRecordedDay': dates[0] if dates else None,
                           'lastRecordedDay': dates[-1] if dates else None, 'total': sum(counts[source].values())}
    rows = []
    for n in range(365):
        day = (start + timedelta(days=n)).isoformat()
        row = {'date': day}
        for source in counts:
            first = sources[source]['firstRecordedDay']
            row[source] = counts[source][day] if first and day >= first else None
        rows.append(row)
    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(updated_cache), encoding='utf-8')
    return {'schemaVersion': 1, 'timezone': 'Australia/Sydney', 'generatedAt': now.isoformat(),
            'coverage': 'Local histories available on this computer; excludes subagents and imported threads. Earlier or missing histories are not reconstructed.',
            'sources': sources, 'days': rows}, malformed


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--home', type=Path, default=Path.home())
    ap.add_argument('--out', type=Path, default=Path(__file__).resolve().parents[1] / 'data' / 'ai-activity.json')
    args = ap.parse_args()
    cache_path = Path(__file__).resolve().parents[1] / 'preview' / 'activity-cache-v2.json'
    result, malformed = collect(args.home, datetime.now(timezone.utc), cache_path)
    if not any(s['total'] for s in result['sources'].values()):
        raise SystemExit('No supported local AI activity found. Existing snapshot preserved.')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'sources': result['sources'], 'skippedMalformedLines': dict(malformed)}))
