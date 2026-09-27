# incident-research v1.0.2 · 纯文档安装包

[下载安装包](incident-research.skill?raw=true) · [SHA-256](incident-research.skill.sha256) · [文件清单与核验记录](incident-research.skill.manifest.json)

本版新增默认规则：**分析可以判断时采用分析等级；分析无法判断时，根据官方给出的颜色或对应状态代码定级。**

- 优先对应服务、对应时段的历史组件等级，其次事故级等级；先核验目标站点图例。
- 红色→Full、橙色→Partial、黄色→Degraded，仅适用于已确认具有相应语义的官方图例/代码。
- 保留原分析结论、官方原值和兜底来源，不覆盖已确定分析阶段，不补造影响时间。
- 厂商确认无服务或用户请求影响的记录单列并排除时长；维护单列。
- 方法说明、验收规则和CSV契约已同步更新，保持48列格式。

| 项目 | 内容 |
| --- | --- |
| 版本 | 1.0.2（纯文档版） |
| 文件大小 | 20,150 字节 |
| 包内文件数 | 4 |
| SHA-256 | `2eec72354bec001ad49e9e64b0095c5967be5f7f27b019f34cc8f97a7b27c745` |

```text
incident-research/
├── SKILL.md
└── reference/
    ├── ADAPTERS.md
    ├── CSV_CONTRACT.md
    └── METHODOLOGY.md
```

`.skill` 使用ZIP格式。支持该格式的客户端可导入；目录式技能客户端可解压后加载完整的 `incident-research/` 目录。包内为当前1.0.2技能的四份文档，不含脚本、缓存或macOS元数据。

已验证ZIP完整性、逐文件哈希、与本地技能源文档逐字节一致，并对解压后的技能运行结构校验。未进行特定客户端安装验收。

下载后校验：

```sh
sha256sum -c incident-research.skill.sha256
# macOS：
shasum -a 256 -c incident-research.skill.sha256
```

[v1.0.1 历史安装包](../v1.0.1/README.md) 保留供对照。仓库 `.agents/` 是独立研发源码，本次分发包来自已更新的本地纯文档技能。
