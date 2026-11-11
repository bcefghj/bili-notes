#!/usr/bin/env python3
"""Flag suspicious ASR loops, long segments and timeline gaps for review."""
import argparse,json,re,zlib
from pathlib import Path

def audit(data,duration):
 issues=[];last=0
 for i,s in enumerate(data['segments']):
  t=s['text'].strip();start=float(s['start']);end=float(s['end']);why=[]
  if re.search(r'(.)\1{11,}',t) or re.search(r'(.{2,20})\1{7,}',t):why.append('repetition')
  if t and not re.search(r'[\w\u4e00-\u9fff]',t):why.append('punctuation_only')
  if len(t)>150 and len(t.encode())/len(zlib.compress(t.encode()))>8:why.append('compression')
  if end-start>30:why.append('long_segment')
  if start-last>30:issues.append(dict(segment=i,start=last,end=start,reasons=['gap']))
  if end>duration+1:why.append('outside_duration')
  if why:issues.append(dict(segment=i,start=start,end=end,reasons=why,text=t[:100]))
  last=max(last,end)
 if duration-last>10:issues.append(dict(start=last,end=duration,reasons=['missing_tail']))
 return dict(segments=len(data['segments']),first=data['segments'][0]['start'],last=last,issues=issues)
def main():
 p=argparse.ArgumentParser();p.add_argument('episode',type=Path);a=p.parse_args();ep=a.episode
 meta=json.loads((ep/'raw/metadata.json').read_text());r=audit(json.loads((ep/'raw/asr.json').read_text()),meta['duration']);(ep/'work').mkdir(exist_ok=True);(ep/'work/transcript-audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(ep.name,r['segments'],len(r['issues']))
if __name__=='__main__':main()
