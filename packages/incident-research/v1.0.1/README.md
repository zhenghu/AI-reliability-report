# incident-research v1.0.1 · 纯文档安装包

[下载安装包](incident-research.skill?raw=true) · [SHA-256](incident-research.skill.sha256) · [文件清单与核验记录](incident-research.skill.manifest.json)

本版本替代已删除的 v1.0.0 分发包；不恢复旧安装包。上传文件与对话提供的 `incident-research-v1.0.1.skill` 逐字节一致，仅在仓库中使用统一文件名 `incident-research.skill`。

| 项目 | 内容 |
| --- | --- |
| 版本 | 1.0.1（纯文档版） |
| 文件大小 | 17,732 字节，约 17.3 KiB |
| 包内文件数 | 4 |
| SHA-256 | `4604f79f247f628d9f8569fc8deda5d24221d017daf6849f49b5f5a40337a024` |

```text
incident-research/
├── SKILL.md
└── reference/
    ├── ADAPTERS.md
    ├── CSV_CONTRACT.md
    └── METHODOLOGY.md
```

包内不含 Python 脚本、`agents/` 配置、独立示例文件或旧测试记录。事故采集、证据核验、等级与时间分析以及 CSV 交付由执行 Skill 的智能体使用当前可用且获授权的工具完成；不依赖原包中的脚本。

`.skill` 使用 ZIP 格式。支持该格式的客户端可导入；使用目录式技能的客户端可解压后加载完整的 `incident-research/` 目录。ZIP 完整性和四个文件的哈希已经核对，但不将此检查等同于客户端安装验收。

下载后校验：

```sh
sha256sum -c incident-research.skill.sha256
# macOS：
shasum -a 256 -c incident-research.skill.sha256
```

本次仅提交安装包及配套说明、校验文件；仓库 `.agents/` 中的研发源码、采集脚本、工作流和已发表报告未修改。这个纯文档安装包不是研发源码目录的完整镜像。
