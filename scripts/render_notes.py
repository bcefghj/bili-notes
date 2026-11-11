#!/usr/bin/env python3
"""Render an editorial notes.json into the established per-episode LaTeX layout."""
import json
from pathlib import Path
import argparse
from build import tex_text as esc

def clock(s):
 h,r=divmod(int(s),3600); m,s=divmod(r,60)
 return f'{h}:{m:02}:{s:02}' if h else f'{m:02}:{s:02}'
def watch(s):return rf'\watch{{{s}}}{{{clock(s)}}}'
def box(b):
 title=esc(b['title'])
 if 'seconds' in b:title += r'\hfill '+watch(b['seconds'])
 return r'\begin{casebox}{'+b.get('color','jade')+'}{'+title+'}\n'+esc(b['text'])+'\n'+r'\end{casebox}'
def blocks(items):
 out=[]
 for b in items:
  k=b['type']
  if k=='topic':out.append(rf'\topic{{{b["seconds"]}}}{{{clock(b["seconds"])}}}{{{esc(b["title"])}}}'+'\n'+esc(b['text']))
  elif k=='para':out.append(esc(b['text']))
  elif k=='box':out.append(box(b))
  elif k=='compare':out.append(r'\duo{'+box(b['items'][0])+'}{'+box(b['items'][1])+'}')
  elif k=='photo':out.append(rf'\def\frametime{{{clock(b["seconds"])}}}'+'\n'+rf'\framephoto{{155mm}}{{{b["file"]}}}{{{esc(b["caption"])}}}{{{b["seconds"]}}}')
  else:raise ValueError(k)
 return '\n\n'.join(out)+'\n'
def table(chapters,short=False):
 # Long interviews need a longer index; keep the large original screenshot.
 opening=(r'{\small\renewcommand{\arraystretch}{1.10}\noindent' if len(chapters)>10 else r'{\renewcommand{\arraystretch}{1.25}\noindent')
 out=[opening,r'\begin{tabularx}{\linewidth}{@{}p{19mm}X@{}}',r'\toprule']
 for i,c in enumerate(chapters):
  title=esc(f'{i+1:02}  '+c['index'])
  out.append((rf'\shortrow{{{c["seconds"]}}}{{{clock(c["seconds"])}}}{{{title}}}' if short else rf'\indexrow{{{c["seconds"]}}}{{{clock(c["seconds"])}}}{{c{i+1:02}}}{{{title}}}'))
 out.extend([r'\bottomrule',r'\end{tabularx}\par}'])
 return '\n'.join(out)+'\n'
def head(title,edition):return '\\input{访谈样式}\n'+rf'\newcommand{{\edition}}{{{edition}}}'+'\n'+rf'\hypersetup{{pdftitle={{{esc(title)}访谈 · {edition}}}}}'+'\n\\begin{document}\n\\color{ink}\n'
def main():
 p=argparse.ArgumentParser();p.add_argument('episode',type=Path);a=p.parse_args();ep=a.episode
 n=json.loads((ep/'notes.json').read_text());meta=json.loads((ep/'raw/metadata.json').read_text());chap=n['chapters'];name=n['name'];dur=meta['duration'];doc=[]
 title=f'{name}｜图文伴读';out=head(name,'图文伴读');out+=r'\markpage{home}{全片索引}'+'\n'+rf'\hero{{原片 {clock(dur)} \hfill 图文伴读}}{{{name}}}{{{esc(n["subtitle"])}}}'+'\n';out+=blocks([n['cover']]);out+=esc(n['intro'])+'\n\n'+table(chap)
 out+=r'\smallnote{'+esc(n.get('time_note','章序按原片话题与发布者时间轴整理。'))+'}\n'
 photos=[1]
 for i,c in enumerate(chap):
  end=chap[i+1]['seconds'] if i+1<len(chap) else dur
  out+='\n\\newpage\n'+rf'\markpage{{c{i+1:02}}}{{{i+1:02} {esc(c["index"])}}}'+'\n'+rf'\pagehead{{{i+1:02} \enspace {esc(c["index"].split(" · ")[0])} \hfill {clock(c["seconds"])}–{clock(end)}}}{{{esc(c["title"])}}}'+'\n'+blocks(c['blocks'])
  if any(b['type']=='photo' for b in c['blocks']):photos.append(i+2)
  if i+1<len(chap):out+=rf'\nextroute{{{end}}}{{{clock(end)}}}{{c{i+2:02}}}'+'\n'
  else:out+=r'\sourcebar'+'\n'
 out+=r'\end{document}'+'\n';(ep/'source'/f'{title}.tex').write_text(out)
 doc.append(dict(source=f'source/{title}.tex',expected_pages=len(chap)+1,photo_pages=photos,index_page=1,check_chapter_destinations=True))
 s=n['short'];title=f'{name}｜三页速览';out=head(name,'三页速览')+r'\markpage{home}{看前与选段}'+'\n'+rf'\hero{{原片 {clock(dur)} \hfill 三页速览}}{{{name}}}{{{esc(n["subtitle"])}}}'+'\n'+blocks([n['cover']])+esc(s['intro'])+'\n\n'+blocks(s['picks'])+r'\smallnote{\hyperlink{recap}{案例回顾}\hfill\hyperlink{chapters}{全片时间表}}'+'\n\\newpage\n'+r'\markpage{recap}{案例回顾}'+'\n'+rf'\pagehead{{案例回顾}}{{{esc(s["recap_title"])}}}'+'\n'+blocks(s['recap'])+'\n\\newpage\n'+r'\markpage{chapters}{回顾与全片时间表}'+'\n'+rf'\pagehead{{复习与选段}}{{{esc(s["closing_title"])}}}'+'\n'+blocks(s['closing'])+r'{\sffamily\bfseries\color{jade}全片时间表}\par'+'\n'+table(chap,True)+r'\sourcebar'+'\n'+r'\end{document}'+'\n';(ep/'source'/f'{title}.tex').write_text(out)
 doc.append(dict(source=f'source/{title}.tex',expected_pages=3,photo_pages=[1],index_page=3,check_chapter_destinations=False))
 config=dict(title=name,video_title=meta['title'],publication_date=meta['publication_date'],publication_timezone=meta.get('publication_timezone','Asia/Shanghai'),series=n.get('series',meta.get('series','月球大叔的硅谷播客')),bvid=meta['bvid'],duration_seconds=dur,minimum_screenshot_width_mm=150,transcript=f'deliverables/{name}｜全片字幕.md',sources={'video':f'https://www.bilibili.com/video/{meta["bvid"]}/'},chapters=[dict(seconds=c['seconds'],anchor=f'c{i+1:02}',title=c['index'],page=i+2) for i,c in enumerate(chap)],documents=doc,source_links=n.get('source_links',[dict(label='Bilibili 原片与发布者时间轴',url=f'https://www.bilibili.com/video/{meta["bvid"]}/')]),asr={'model':'mlx-community/whisper-large-v3-turbo-q4','manually_proofread':False})
 origin_file=ep/'raw/transcript-origin.json'
 if origin_file.exists():
  origin=json.loads(origin_file.read_text());config['asr']={'model':origin.get('model'),'source':origin['kind'],'manually_proofread':False}
 (ep/'episode.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
 print(ep,len(chap)+1,3)
if __name__=='__main__':main()
