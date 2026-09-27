# incident-research v1.0.3 · 纯文档安装包

[下载安装包](incident-research.skill?raw=true) · [SHA-256](incident-research.skill.sha256) · [文件清单与核验记录](incident-research.skill.manifest.json)

本版新增规则：**用户要求生成或更新最终可用性报告时，在正文开头用同一张汇总表和同一张趋势折线图，展示整体及各应用的年度可用性。**

- 默认采用统一 F∪P∪D 口径，用户指定其他口径时遵从并注明；颜色区分应用，明确整体是任一纳入应用受影响的区间并集。
- 标明观察起点、部分年度及冻结截止时间；缺失不填零或100%，单年数据只显示一个点，不跨缺失年份连线。
- 总结同时说明整体和应用差异、可比性限制及显著影响结论的长事件；表、图、源数据保持一致。
- 仅要求事故 CSV 时不扩展为报告任务；保留 v1.0.2 的分析优先、官方颜色兜底规则及48列CSV契约。
- 当前本地技能已同步更新；冻结研究数据保留原方法版本，不随展示规则升级改写。

| 项目 | 内容 |
| --- | --- |
| 版本 | 1.0.3（纯文档版） |
| 文件大小 | 21,712 字节 |
| 包内文件数 | 4 |
| SHA-256 | `90ee9e91f9f545246367544d9d938617f9b840b16e5208c60a1d701117c41f95` |

```text
incident-research/
├── SKILL.md
└── reference/
    ├── ADAPTERS.md
    ├── CSV_CONTRACT.md
    └── METHODOLOGY.md
```

`.skill` 使用ZIP格式。支持该格式的客户端可导入；目录式技能客户端可解压后加载完整的 `incident-research/` 目录。包内是当前技能的四份文档，不含脚本、缓存或macOS元数据。

已验证ZIP完整性、逐文件哈希、与当前本地技能逐字节一致、文档相对链接，并对本地及解压后的技能运行结构校验。未进行特定客户端安装验收。

下载后校验：

```sh
sha256sum -c incident-research.skill.sha256
# macOS：
shasum -a 256 -c incident-research.skill.sha256
```

[v1.0.2 历史安装包](../v1.0.2/README.md) 保留供对照。仓库 `.agents/` 是独立研发源码，本次分发包来自已更新的本地纯文档技能。
