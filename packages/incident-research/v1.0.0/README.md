# incident-research v1.0.0 安装包

[下载安装包](incident-research.skill?raw=true) · [SHA-256 校验文件](incident-research.skill.sha256) · [原始打包与离线核验记录](incident-research.skill.manifest.json)

| 项目 | 值 |
| --- | --- |
| 安装包 | `incident-research.skill` |
| 版本 | `1.0.0` |
| 大小 | 34,559 字节 |
| 文件数 | 13 |
| 源码提交 | `d3d4aa794de117fff4406a20dfb7e48881fa52e0` |
| SHA-256 | `0272e2116742a550117cc7f3e81d7b9afc405ce892530164d96c1942659d9e67` |

该包与对话提供的 `.skill` 下载文件逐字节一致。`.skill` 文件采用 ZIP 格式，包含顶层 `incident-research/` 目录、`SKILL.md`、界面配置、Python 脚本、参考资料和合成示例，不包含整个代码仓。

核对下载文件：

```sh
sha256sum -c incident-research.skill.sha256
# macOS 也可使用：shasum -a 256 -c incident-research.skill.sha256
```

支持 `.skill` 导入的客户端可导入该文件；使用目录式技能加载的客户端可将其作为 ZIP 解压并安装包内的 `incident-research/` 文件夹。详见[源码中的 Skill 定义](../../../.agents/skills/incident-research/SKILL.md)及[使用说明](../../../docs/INCIDENT_RESEARCH.md)。

校验记录保留最初打包时的测试信息，不表示已安装到任何客户端，也不声明完成任意状态网站的联网端到端采集验收。版本内容未修改；后续版本应另建目录，不覆盖本包。
