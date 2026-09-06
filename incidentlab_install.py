"""Explicit, non-destructive skill installation for Hermes and OpenClaw."""
import argparse
import json
import os
from pathlib import Path
import shlex
import sys


def install(host, home=None):
    if host not in ('hermes', 'openclaw'):
        raise ValueError('host must be hermes or openclaw')
    root=Path(home).expanduser() if home is not None else Path(os.environ.get('HERMES_HOME', str(Path.home()/'.hermes'))) if host=='hermes' else Path.home()/'.openclaw'
    root=root.resolve()
    target=root/'skills'/'incidentlab'/'SKILL.md'
    command=shlex.join([sys.executable,'-m','incidentlab','--db',str(root/'incidentlab'/'incidents.db')])
    content=f'''---
name: incidentlab
description: Record an agent mistake and track recovery evidence.
---
# Incident Lab — explicit workflow, not an enforcement hook

Run the installed local CLI with this prefix:
`{command}`

1. When the user corrects a mistake or you detect one, record an incident with
   `record --scope SCOPE --task TASK --failure FAILURE_CLASS --evidence REF`.
   SCOPE must identify the real profile/account/chat/thread. Never guess or merge rooms.
   Use stable task IDs. Keep credentials and private transcript content out of REF.
2. Finish the original authorized task first. Report failure honestly; a timeout is not success.
3. Investigate root cause. Preserve uncertainty; do not invent a provider outage.
4. Within existing authorization, reproduce the failure, make a narrow prevention fix,
   test it, and independently read back actual deployment if deployment is required.
5. Register each attestation using `attest ID GATE --evidence REF`, with gates
   original, red, green, deployment. This records a CLAIM, not independent verification.
   Never fabricate evidence to satisfy a gate. If a gate is inapplicable or blocked,
   leave the incident open and explain why; this version has no waiver command.
6. Use `show ID` to inspect the record and `close ID` only after honest evidence exists.
   Report original-task and prevention completion separately.

This skill does not automatically observe all turns, execute repairs, validate evidence,
or enforce host completion. Do not modify permissions, auto-approve settings, or
restart the host to satisfy an incident. It grants no new authorization.
Use the CLI only on a trusted local machine; the database is not tamper-proof.
'''
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if target.read_text()==content: return target
        raise FileExistsError('existing skill differs; refusing overwrite: '+str(target))
    with target.open('x',encoding='utf-8') as f: f.write(content)
    return target


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('host',choices=['hermes','openclaw'])
    p.add_argument('--home',help='Explicit host home; never updates sibling profiles automatically')
    a=p.parse_args()
    try: print(json.dumps({'skill':str(install(a.host,a.home)),'activation':'start a new host session and load incidentlab'}))
    except (ValueError,OSError) as e:
        print(json.dumps({'error':str(e)})); return 2
    return 0

if __name__=='__main__': raise SystemExit(main())
