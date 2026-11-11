# 执行环境与单期数据

## 宿主适配

本技能的方法和模板可由兼容 Agent Skills 的宿主读取。普通聊天网页能否执行附带 Python、访问 B站音频、写文件和编译 LaTeX，取决于该产品与账号实际开放的工具；本仓库尚未完成豆包网页版端到端验证。

开始处理时确认：完整发言材料是否可得；能否取原片静帧；能否执行脚本和保存文件；能否编译 PDF 并看到逐页预览。按实际能力推进。已有完整字幕时可跳过 ASR；用户已提供截图时可复用。只有简介时不能补写访谈。

本机验证环境是 macOS Apple Silicon，Conda 环境为 `latex-pdf` 与 `asr-mlx`。MLX 转写需要兼容的 Apple Silicon，不能假设云端或 Linux 有同样能力。其他宿主可使用已有字幕或其他 ASR 生成下面的时间段格式，再复用导出、编辑与编译流程。替代 ASR 需要单独验证。

PDF 脚本需要 Python 3.11、Tectonic、PyMuPDF 和 Pillow；媒体获取需要 FFmpeg。依赖规格在 `environments/`。macOS 用宋体与黑体；其他环境准备 Noto Serif CJK SC + Noto Sans CJK SC，或思源宋体 + 思源黑体。字体变化后重看分页。首次编译可能需联网获取 TeX 依赖。

## 新建单期

在自己的项目中创建以下结构，技能目录和材料目录可以分开：

```text
episode/
  raw/metadata.json
  raw/asr.json
  raw/corrections.json
  assets/0100.jpg
  notes.json
  source/
  deliverables/
  work/media/audio.m4a
```

`raw/metadata.json` 至少包含以下字段（值仅为示意，实际值取原片元数据）：

```json
{
  "title": "完整B站原标题",
  "bvid": "原片BV号",
  "cid": 0,
  "pubdate": 0,
  "publication_date": "YYYY-MM-DD",
  "publication_timezone": "Asia/Shanghai",
  "duration": 3600,
  "series": "系列名称"
}
```

`bilibili_media.py` 的 `media.json` 只包含标题、BV、CID 和时长，需补存 pubdate、北京时间日期与来源。`source/` 和 `assets/` 在渲染前创建。

ASR 输入最小结构为 `{"segments": [{"start": 0.0, "end": 2.0, "text": "原始发言"}]}`。保留原始文件，转换字幕格式时记录来源。时间单位为秒，单调递增且在原片时长内。没有校正规则时使用空数组 `[]`。局部重转脚本使用 `work/media/audio.m4a`。

## notes.json

这是经过编辑的内容，不是从简介自动填满的空表。结构如下，示意信息量不足以成为可验收笔记：

```json
{
  "name": "嘉宾名",
  "series": "系列名称",
  "subtitle": "本期具体议题",
  "intro": "人物与本期内容的简短介绍",
  "cover": {"type": "photo", "seconds": 100, "file": "0100.jpg", "caption": "实际场景"},
  "chapters": [
    {
      "seconds": 120,
      "index": "具体话题 · 核心范围",
      "title": "能让读者找回案例的问题",
      "blocks": [
        {"type": "topic", "seconds": 120, "title": "具体问题", "text": "依据发言整理的回答、条件与例子"},
        {"type": "box", "color": "gold", "title": "案例", "text": "案例经过"}
      ]
    }
  ],
  "short": {
    "intro": "精简版独立介绍",
    "picks": [{"type": "box", "seconds": 120, "color": "jade", "title": "选看片段", "text": "这段具体讲什么"}],
    "recap_title": "具体案例回顾",
    "recap": [{"type": "topic", "seconds": 120, "title": "案例", "text": "经过与取舍"}],
    "closing_title": "关键区别与全片选段",
    "closing": [{"type": "para", "text": "仍有必要保留的区别和条件"}]
  }
}
```

支持块：`topic`、`para`、`box`、`compare`（`items` 中两个 box）、`photo`。框颜色使用 `gold`、`jade` 等已定义颜色。可选 `time_note` 标明章节依据，可选 `source_links` 为 `[{"label": "来源名称", "url": "https://..."}]`。

编辑完成后，以技能实际安装路径代替 `<技能目录>`：

```sh
python <技能目录>/scripts/render_notes.py /实际路径/episode
python <技能目录>/scripts/build.py /实际路径/episode --tectonic /实际路径/tectonic
```

生成器当前以一章一页、精简版三页为起点；`source/*.tex` 与 `episode.json` 可继续人工调整。不要为了固定页数删掉必要案例，或用空泛建议填满页面。检查通过后仍需逐页看 `output/review/` 的 PNG。
