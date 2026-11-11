> 本文保留已验证案例的目录用法。独立安装本仓库后，`scripts/` 指本仓库目录下的脚本；在你自己的项目中创建 `examples/<单期>/`，或把命令中的案例路径换成实际路径。原始认可成品保存在维护者的制作项目中，不随技能分发。首次新建单期先读 [runtime.md](runtime.md)。

# 项目结构与构建

Git 仓库以单期案例为单位。当前案例结构如下。

    examples/todd-li/
      episode.json        视频信息、章节、输出页数和截图标准
      baseline.json       已认可文件的 SHA-256
      source/             两份 LaTeX 正文
      assets/             原始截图
      raw/                ASR JSON 和显式校正规则
      accepted/           已认可 PDF 与 Markdown
      output/             本次重建的 PDF、逐页图片和检查结果

## 环境

本机已有通用 Conda 环境 latex-pdf 和 asr-mlx。使用 conda run 或激活环境。仓库根目录 environments/ 保存环境规格，新机器可据此创建。

PDF 环境需要 Python、Tectonic、PyMuPDF 和 Pillow。语音环境使用 Apple Silicon 的 MLX Whisper 与 FFmpeg。字体优先保持本机 Songti/Heiti；其他机器准备 Noto CJK 或思源宋体/黑体。跨系统字体变化后重新看分页。

## 获取材料

先检查能否获得平台字幕与发布者时间轴。需要转写时可以获取音频，再定点取截图。

    conda run -n asr-mlx python scripts/bilibili_media.py \
      BV1S9u16KETq --output examples/todd-li/work/media --audio --frames 58 825 3670

脚本只使用公开 API 返回的流，输出音频和所选静帧。失败时保留错误并确认可用材料。已有平台字幕和截图时直接复用。

    conda run -n asr-mlx mlx_whisper examples/todd-li/work/media/audio.m4a \
      --model mlx-community/whisper-large-v3-turbo-q4 --language zh \
      --output-dir examples/todd-li/work --output-name asr \
      --output-format json --verbose False

模型首次使用需要下载。初始提示可以包含本期人名和专名。观察开头、结尾、长静默和重复片段，并披露实际校对程度。

## 输出时间稿

    conda run -n asr-mlx python scripts/transcript.py \
      examples/todd-li/raw/asr.json examples/todd-li/work/李正韬｜全片字幕.md \
      --title '李正韬访谈｜全片字幕' --duration 3904 \
      --corrections examples/todd-li/raw/corrections.json

校正规则采用 JSON 数组，每项有 pattern、replacement、ignore_case。只填写经过确认的修正，原始识别结果保留在 raw/。脚本检查时间单调、时长边界和非空发言。

## 排版与构建

编辑每期的 source/ 正文和 episode.json。从当前示例复制新一期时，先调整视频标识、来源链接、章节和预期页面，再编辑正文。共用样式通过构建脚本放入临时编译目录，截图路径统一为 assets/。

    conda run -n latex-pdf python scripts/build.py examples/todd-li

可以用 --tectonic /path/to/tectonic 指定编译器，用 --output /path/to/output 指定工作输出。每份文档先在临时目录编译；本批所有文档通过结构检查后发布到输出目录。已认可文件在 accepted/ 原样保留。

episode.json 的 source_links 控制正文末尾的来源栏。documents 中的 source 指向正文，expected_pages 是该次编辑完成后的预期值，photo_pages 是含原片截图的页码，index_page 是含完整章节时间的页码。详细稿可用 check_chapter_destinations 核对章节页码。

构建完成后看 output/review/validation.json 和所有逐页 PNG。脚本检查 A4、预期页数、章节落点、同片时间链接、图片宽度和文本边界。留白标记、原片细小字幕和内容准确性需要人工复核。

## 版本留存

源码、配置、原始证据、当前认可产物进入 Git。本地大音频、模型缓存和重建预览留在忽略目录。接受新版后更新 accepted/ 与 baseline.json，再提交对应版本。远端发布范围按用户当次要求处理。

## 多期制作中新增的入口

新一期可以把编辑内容存成 notes.json，再生成两份 LaTeX 正文：

    conda run -n latex-pdf python scripts/render_notes.py examples/chen-ran
    conda run -n latex-pdf python scripts/build.py examples/chen-ran

notes.json 保存封面、按主题组织的 chapters，以及人工选出的 short 内容。块类型为 topic（时间、标题、正文）、para、box、compare（两项）、photo（原图文件、时间、图注）。各期现有 notes.json 是可运行例子。渲染只负责排版，内容和精简稿仍由编辑判断；一章一页是本批案例的安排，内容变化后检查实际分页。

长音频实测出现过跨窗口重复字、整段标点和空片段。转写可使用 --condition-on-previous-text False 减少续写循环。完成后检查：

    conda run -n latex-pdf python scripts/audit_transcript.py examples/jiang-junchen

需要局部重转时，在 asr-mlx 环境执行明确的时间范围：

    conda run -n asr-mlx python scripts/repair_asr.py examples/jiang-junchen --ranges 6090:6600

脚本以原段落边界扩展窗口、关闭前文续写，再合回全片，保留修复记录；音频仍位于 work/media/audio.m4a。检查报告里的 gap、重复、纯标点和时长越界，不把“无异常标记”当成逐句听校。导出时保留原始 JSON，把纯标点丢弃、尾段结束时间裁到原片等操作记入 raw/export-adjustments.json。

transcript.py 新增 --source-note 与 --source-url，分别标明平台字幕或本地音频转写来源，不向发言中混入注释。


## 日期与命名

原片发布日期从 B站公开 view API 的 pubdate 获取，按 Asia/Shanghai 转为 YYYY-MM-DD；保存原始时间戳与完整 title 到 raw/metadata.json，同时在 episode.json 保留 publication_date、publication_timezone 和 video_title。不要把文件创建日、制作日或下载日当成发布日期。

成品目录按 `YYYY-MM-DD 嘉宾` 组织；其中三个阅读文件均为 `YYYY-MM-DD B站原标题｜类型.扩展名`，类型为全片字幕、图文伴读、精简笔记。英文冒号等跨平台不兼容的文件名字符转为全角对应符号，原始标题仍完整保留在元数据与索引。

本仓库的 scripts/assemble_collection.py 负责按这套规则汇总、核对原文件散列、更新索引和交付记录，并重打阅读压缩包；不改写 PDF 内容，也不改动已认可基线。只清理旧交付记录列出且散列吻合的旧副本。
