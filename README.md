# bili-notes · B站笔记

把一期 B站访谈整理成带时间的原味 Markdown、详细图文 LaTeX PDF、几页精简 PDF，服务于选看、伴读和回顾。

本仓库保存技能、编辑标准、脚本和 LaTeX 模板。大音频、账号凭据、私人工作记录和各期完整材料留在制作项目中。

## 使用

支持 Agent Skills 的工具可读取根目录 [SKILL.md](SKILL.md)，按宿主支持的方式导入整个目录；脚本、参考资料与模板需一同保留。只粘贴 SKILL.md 不会自动安装依赖。

给豆包等网页助手可先发 [WEB.md](WEB.md) 的链接和视频链接：

> 请先读取 https://raw.githubusercontent.com/bcefghj/bili-notes/main/WEB.md ，按其中标准处理这个 B站访谈：〈视频链接〉。读取相关模板与运行说明，依据你实际能获取的材料和工具推进。

如果网页打不开 GitHub，可上传说明文档或技能 ZIP。附件读取、解压、执行脚本、提取视频与编译 PDF 需分别核实。**豆包网页版完整流程尚未实测，原生一键安装兼容性尚未确认。**

独立运行先读 [环境与数据格式](references/runtime.md)，再读 [工作流](references/workflow.md)。环境规格在 [environments/](environments/)。内容编辑由使用技能的助手完成，`render_notes.py` 负责将已经编辑好的内容排成 LaTeX。

## 当前验证范围

- 来源流程已在维护者 macOS Apple Silicon 的月球大叔八期访谈项目中使用，文字稿和两类 PDF 各自独立。
- 本分发包已通过目录、脚本、文字稿导出和版式重建检查；重建的八页伴读、三页精简稿共 11 页，与原认可成品渲染结果逐页像素一致。见 [VALIDATION.md](VALIDATION.md)。跨机器字体、字幕权限与不同 ASR 仍需单独验证。
- MLX Whisper 需要兼容的 Apple Silicon；其他环境可接已有字幕或其他 ASR 的时间段 JSON。
- 生成器默认一章一页、精简版三页；可以修改 LaTeX 和预期页数，页数服从内容。

## 文件

```text
SKILL.md        技能入口
WEB.md          网页助手可直接阅读的任务说明
references/     编辑标准、运行条件、字段说明
scripts/        媒体获取、时间稿导出、异常检查、渲染与构建
assets/latex/   ElegantNote、共用样式、字体与许可
environments/   通用环境规格
```

PDF 构建会生成逐页预览，并检查时间链接、章节落点、截图尺寸和页面边界。结构检查不能代替视觉复核或逐句听校。

## 版本与许可

Git 提交和标签固定技能、脚本与模板。使用时记录版本，先在单期材料上验证再升级常用版本。

ElegantNote 类文件保留原始 LPPL 许可，见 [ElegantNote-License.txt](assets/latex/ElegantNote-License.txt)。其余内容暂未另行声明再分发许可。访谈截图与发言材料需保留原片来源。

格式参考：[Agent Skills](https://agentskills.io/home)。本仓库是技能来源；是否被目录服务收录、是否可在某个网页助手内安装，以对应平台实际支持为准。
