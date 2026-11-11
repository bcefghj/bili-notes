#!/usr/bin/env python3
"""Retranscribe explicit defective windows without previous-text conditioning."""
import argparse,json,math,shutil
from pathlib import Path
import mlx_whisper

def main():
 p=argparse.ArgumentParser();p.add_argument('episode',type=Path);p.add_argument('--ranges',nargs='+',required=True,help='start:end seconds');a=p.parse_args();ep=a.episode
 raw=ep/'raw/asr.json';data=json.loads(raw.read_text());backup=ep/'work/asr-before-repair.json'
 if not backup.exists():shutil.copy2(raw,backup)
 changes=[]
 for item in a.ranges:
  start,end=map(float,item.split(':'));old=data['segments'];overlap=[s for s in old if s['start']<end and s['end']>start]
  # Use existing segment boundaries so speech at either edge is not silently lost.
  start=min([start]+[s['start'] for s in overlap]);end=max([end]+[s['end'] for s in overlap])
  result=mlx_whisper.transcribe(str(ep/'work/media/audio.m4a'),path_or_hf_repo='mlx-community/whisper-large-v3-turbo-q4',language='zh',condition_on_previous_text=False,clip_timestamps=f'{start},{end}',verbose=False)
  new=[s for s in result['segments'] if s['start']<end and s['end']>start]
  if not new:raise RuntimeError('Repair produced no speech')
  data['segments']=sorted([s for s in old if s['end']<=start or s['start']>=end]+new,key=lambda s:s['start'])
  changes.append(dict(start=start,end=end,old_segments=len(overlap),new_segments=len(new)))
 data['text']=''.join(s['text'] for s in data['segments']);raw.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');history=ep/'raw/asr-repairs.json';previous=json.loads(history.read_text()) if history.exists() else [];history.write_text(json.dumps(previous+changes,ensure_ascii=False,indent=2)+'\n');print(changes)
if __name__=='__main__':main()
