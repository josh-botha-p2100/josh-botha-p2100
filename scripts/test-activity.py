"""Exercise real counting hazards with synthetic events, never private logs."""
import importlib.util
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

spec = importlib.util.spec_from_file_location('activity', Path(__file__).with_name('export-ai-activity.py'))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
now = datetime(2026, 10, 14, 5, tzinfo=timezone.utc)

with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    def save(path, rows):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('\n'.join(json.dumps(r) for r in rows)+'\n',encoding='utf-8')
    human = {'padding':'x'*800,'type':'user','timestamp':'2026-10-13T14:30:00Z','message':{'content':'Synthetic prompt, not private data'}}
    save('.claude/projects/test/root.jsonl', [human, human,
         {**human,'isSidechain':True,'timestamp':'2026-10-12T14:30:00Z'},
         {**human,'message':{'content':[{'type':'tool_result','content':'Not human'}]}},
         {**human,'message':{'content':'<system-reminder>Ignore this event'}}])
    save('.claude/projects/test/agent-child.jsonl', [{**human,'message':{'content':'Subagent'}}])
    save('.claude/history.jsonl', [
         {'timestamp':datetime(2026,10,1,1,tzinfo=timezone.utc).timestamp()*1000,'display':'Older history prompt'},
         {'timestamp':datetime(2026,10,13,15,tzinfo=timezone.utc).timestamp()*1000,'display':'History day already covered by transcript'}])
    meta={'type':'session_meta','payload':{'id':'root','source':'cli'}}
    event={'type':'event_msg','timestamp':'2026-10-13T14:30:00Z','payload':{'type':'item_completed','turn_id':'one','item':{'type':'UserMessage','content':[{'type':'text','text':'Synthetic Codex prompt'}]}}}
    save('.codex/sessions/2026/10/14/rollout-root.jsonl',[meta,event,event])
    save('.codex/sessions/2026/10/14/rollout-fork.jsonl',[meta,event])
    save('.codex/sessions/2026/10/14/rollout-subagent.jsonl',[{'type':'session_meta','payload':{'source':{'subagent':{}}}},event])
    save('.codex/sessions/2026/10/14/rollout-import.jsonl',[{'type':'session_meta','payload':{'id':'imported'}},event])
    (root/'.codex/external_agent_session_imports.json').write_text(json.dumps({'records':[{'imported_thread_id':'imported'}]}))
    out, malformed = mod.collect(root,now,root/'cache.json')
    assert out['sources']['claude']['total']==2, out['sources']
    assert out['sources']['codex']['total']==1, out['sources']
    rows={d['date']:d for d in out['days']}
    assert rows['2026-10-14']['claude']==1 and rows['2026-10-14']['codex']==1
    assert rows['2026-10-13']['codex'] is None
    serialized=json.dumps(out)
    assert 'Synthetic' not in serialized and 'test/root' not in serialized and 'imported_thread_id' not in serialized
    second,_=mod.collect(root,now,root/'cache.json')
    assert second==out, 'Cached export differs'
    with (root/'.claude/history.jsonl').open('a') as fh:
        fh.write(json.dumps({'timestamp':datetime(2026,10,1,2,tzinfo=timezone.utc).timestamp()*1000,'display':'Another historical prompt'})+'\n')
    third,_=mod.collect(root,now,root/'cache.json')
    assert third['sources']['claude']['total']==3, 'New history on a cached day was missed'
    assert all(set(d)=={'date','claude','codex'} for d in out['days'])
    print('PASS: deduplication, long metadata, source exclusions, history fallback, Sydney day boundary, cache parity and public schema')
