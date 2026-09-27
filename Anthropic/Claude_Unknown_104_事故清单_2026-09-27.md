# Claude：104 条研究等级 unknown 记录清单

本清单从已完成复核的 v1.1 CSV 直接筛选，不重新抓取状态页，也不修改既有分类或可用性计算。

筛选条件：`record_type = incident` 且 `assessed_severity = unknown`。全部 104 条的 `review_status` 均为 `assessed`。日期按公告 UTC 日期，不是实际影响开始日期。冻结截止为 **2026-09-27 16:10:43 UTC**。

**准确拆分：101 条无法依据已取得文本判定 F/P/D 的事件 + 3 条厂商确认无服务或用户请求影响的记录。** 后三条没有进入故障时长；它们在现有三等级数据契约中保留 unknown，并另有 `no_user_impact` 标记。因此不能把104条全部称为“已证实故障但严重性未知”。

unknown 是本研究的影响范围分类，不代表厂商没有官方标签，也不代表记录未复核。官方映射中，12条为Full、44条为Partial、36条为Degraded、12条为unknown；这些标签不能直接证明整个命名产品的全量/部分不可用。

其中93条保留了可定位的未知等级候选时间（含公告/组件状态代理），仅用于敏感性计算；未进入主序列已分级影响时长。其余11条包括3条明确无影响和8条没有可用候选时间。**等级未知与时间未知是两种不同问题。**

| 公告年份 | unknown记录 | 其中明确无影响 | 其余等级不足以判定 |
| --- | ---: | ---: | ---: |
| 2023 | 4 | 0 | 4 |
| 2024 | 24 | 1 | 23 |
| 2025 | 39 | 2 | 37 |
| 2026 | 37 | 0 | 37 |

## 厂商确认无影响的3条记录

| 日期 UTC | 官方公告 | 厂商结论 |
| --- | --- | --- |
| 2024-12-17 | [Unauthorized post from @AnthropicAI X.com account](https://status.claude.com/incidents/mzyhcbn140fg) | 厂商明确所有系统和服务不受影响；社交账号事件，排除核心可用性。 |
| 2025-01-09 | [Elevated errors on the API](https://status.claude.com/incidents/fwj5yn2lmbrc) | 最终调查明确未影响用户请求；撤销初始错误告警的影响判断。 |
| 2025-04-25 | [Elevated errors on request to models](https://status.claude.com/incidents/h4bygm7vgqkj) | 厂商最终确认错误未影响用户请求，排除影响时长。 |

## 全部104条，按公告时间排列

每条标题链接到官方公告；“判断理由”直接保留现有复核结论。服务映射及完整原文、时间阶段、原始哈希见主 CSV。

### 2023 年：4 条

| 序号 | 公告日期 UTC | 官方标题及链接 | ID | 研究分类说明 | 判断理由 |
| ---: | --- | --- | --- | --- | --- |
| 1 | 2023-06-07 | [Outage causing 500s across multiple models](https://status.claude.com/incidents/5dcd2h34gbcg) | `5dcd2h34gbcg` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 2 | 2023-06-24 | [Elevated 503 and 504 errors](https://status.claude.com/incidents/w0mfznzqgnbc) | `w0mfznzqgnbc` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 3 | 2023-11-15 | [Elevated API error rate](https://status.claude.com/incidents/llqq0177mckq) | `llqq0177mckq` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 4 | 2023-12-12 | [API Outage](https://status.claude.com/incidents/z3v941z3z11b) | `z3v941z3z11b` | 影响等级不足以判定 | API请求报错没有失败比例；3:55–4:00 PST 缺少AM/PM且公告接近前一日16:00PST，时间保留歧义。 |

### 2024 年：24 条

| 序号 | 公告日期 UTC | 官方标题及链接 | ID | 研究分类说明 | 判断理由 |
| ---: | --- | --- | --- | --- | --- |
| 5 | 2024-01-29 | [Elevated API error rate across all models](https://status.claude.com/incidents/qxdvjb4njp6q) | `qxdvjb4njp6q` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 6 | 2024-02-03 | [Elevated error rate on claude.ai](https://status.claude.com/incidents/h1lxbyszyxrq) | `h1lxbyszyxrq` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 7 | 2024-02-16 | [Elevated error rate on claude.ai](https://status.claude.com/incidents/tmsczhzhjd63) | `tmsczhzhjd63` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 8 | 2024-03-04 | [Elevated Error Rate](https://status.claude.com/incidents/cj4jxvqhtyq1) | `cj4jxvqhtyq1` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 9 | 2024-03-11 | [Elevated error rate](https://status.claude.com/incidents/gy2g64fmqwjb) | `gy2g64fmqwjb` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 10 | 2024-03-23 | [Elevated API Error Rates](https://status.claude.com/incidents/czwvmc36gjgq) | `czwvmc36gjgq` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 11 | 2024-06-21 | [Elevated error rates in the API](https://status.claude.com/incidents/ttsdth94gxz9) | `ttsdth94gxz9` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 12 | 2024-07-01 | [Elevated errors on Claude.ai](https://status.claude.com/incidents/059swcjlk587) | `059swcjlk587` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 13 | 2024-07-02 | [Elevated error rates in the API](https://status.claude.com/incidents/zcqbpk14kylw) | `zcqbpk14kylw` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 14 | 2024-07-03 | [Elevated errors on Claude.ai and Console](https://status.claude.com/incidents/jsp92d37pvs0) | `jsp92d37pvs0` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 15 | 2024-07-11 | [Elevated errors on Claude.ai and Console](https://status.claude.com/incidents/j8t7dz18qf1y) | `j8t7dz18qf1y` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 16 | 2024-07-19 | [API errors elevated](https://status.claude.com/incidents/8mlvgc29rvxg) | `8mlvgc29rvxg` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 17 | 2024-08-06 | [High error rates affecting inference](https://status.claude.com/incidents/qn4crqd8ym36) | `qn4crqd8ym36` | 影响等级不足以判定 | 后端服务中断为已披露原因，但错误比例未知；8:27PST与夏令时/公告时间不一致。 |
| 18 | 2024-08-06 | [Elevated error rates on API, Claude, and Console](https://status.claude.com/incidents/xndqxrj1mnnb) | `xndqxrj1mnnb` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 19 | 2024-09-05 | [High number of errors for API and Claude.ai](https://status.claude.com/incidents/j3mqn3h171rq) | `j3mqn3h171rq` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 20 | 2024-09-11 | [Elevated errors across Claude models](https://status.claude.com/incidents/sn3y911gkt0r) | `sn3y911gkt0r` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 21 | 2024-09-12 | [Elevated errors on Claude.ai, Console, and the Anthropic API](https://status.claude.com/incidents/x6kvdyjgzxb2) | `x6kvdyjgzxb2` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 22 | 2024-11-01 | [Elevated errors on Anthropic API](https://status.claude.com/incidents/hbnr2ffn9b9p) | `hbnr2ffn9b9p` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 23 | 2024-11-13 | [Elevated error rate on Haiku, Sonnet, and Opus](https://status.claude.com/incidents/tw3w5ddv028j) | `tw3w5ddv028j` | 影响等级不足以判定 | 列举Haiku、Sonnet、Opus覆盖模型家族但无子集限定或错误比例，不能确认P/F。 |
| 24 | 2024-11-14 | [Elevated errors on the API](https://status.claude.com/incidents/7svmbgb2b28x) | `7svmbgb2b28x` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 25 | 2024-11-20 | [Elevated error rate on anthropic.com](https://status.claude.com/incidents/7qwmbhnk74bz) | `7qwmbhnk74bz` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 26 | 2024-11-28 | [Elevated errors for requests to Anthropic API](https://status.claude.com/incidents/ff02srsfxr0d) | `ff02srsfxr0d` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 27 | 2024-12-13 | [Elevated errors on the Anthropic API](https://status.claude.com/incidents/nh9j7wwgn40f) | `nh9j7wwgn40f` | 影响等级不足以判定 | 实际UTC窗口已给，但通用错误缺失败比例，等级U。 |
| 28 | 2024-12-17 | [Unauthorized post from @AnthropicAI X.com account](https://status.claude.com/incidents/mzyhcbn140fg) | `mzyhcbn140fg` | 厂商确认无服务/用户请求影响 | 厂商明确所有系统和服务不受影响；社交账号事件，排除核心可用性。 |

### 2025 年：39 条

| 序号 | 公告日期 UTC | 官方标题及链接 | ID | 研究分类说明 | 判断理由 |
| ---: | --- | --- | --- | --- | --- |
| 29 | 2025-01-09 | [Elevated errors on the API](https://status.claude.com/incidents/fwj5yn2lmbrc) | `fwj5yn2lmbrc` | 厂商确认无服务/用户请求影响 | 最终调查明确未影响用户请求；撤销初始错误告警的影响判断。 |
| 30 | 2025-02-04 | [Elevated Error Rates on Claude.ai](https://status.claude.com/incidents/wz8k6v47yx6h) | `wz8k6v47yx6h` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 31 | 2025-03-04 | [Elevated errors on on requests](https://status.claude.com/incidents/yk3jn3bl942r) | `yk3jn3bl942r` | 影响等级不足以判定 | 官方标major但正文只说错误率与most models恢复，无完整失败范围证据，U。 |
| 32 | 2025-03-13 | [Errors when accessing anthropic.com](https://status.claude.com/incidents/bybj2w3097hm) | `bybj2w3097hm` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 33 | 2025-03-26 | [Elevated errors on requests to models](https://status.claude.com/incidents/bttrz8tknckh) | `bttrz8tknckh` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 34 | 2025-03-29 | [Errors loading Claude.ai and Console](https://status.claude.com/incidents/r20t009skp4b) | `r20t009skp4b` | 影响等级不足以判定 | 访问错误率显著升高但未称全部无法访问，等级U；实际时间窗明确。 |
| 35 | 2025-03-31 | [Elevated errors on Claude.ai and the Anthropic Console](https://status.claude.com/incidents/rv4qtngkcdny) | `rv4qtngkcdny` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 36 | 2025-04-03 | [Elevated Errors on API](https://status.claude.com/incidents/mbg5kmfdf9f3) | `mbg5kmfdf9f3` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 37 | 2025-04-03 | [Elevated Errors On API And Claude.ai](https://status.claude.com/incidents/s0c6w5gmlcq3) | `s0c6w5gmlcq3` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 38 | 2025-04-25 | [Elevated errors on request to models](https://status.claude.com/incidents/h4bygm7vgqkj) | `h4bygm7vgqkj` | 厂商确认无服务/用户请求影响 | 厂商最终确认错误未影响用户请求，排除影响时长。 |
| 39 | 2025-04-25 | [Elevated errors on request to models](https://status.claude.com/incidents/qnjg0bnpvzyy) | `qnjg0bnpvzyy` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 40 | 2025-04-26 | [Elevated errors on request to models](https://status.claude.com/incidents/hbmhhjc2d558) | `hbmhhjc2d558` | 影响等级不足以判定 | 已核阅完整公告；仅报告错误升高或笼统异常，没有可判全量或部分失败的对象边界，等级保留未知。 |
| 41 | 2025-05-10 | [Elevated errors in the API](https://status.claude.com/incidents/j080x9g1v5pw) | `j080x9g1v5pw` | 影响等级不足以判定 | Elevated errors in the API：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 42 | 2025-05-12 | [Elevated 500 Internal Server Errors for API and Claude.ai](https://status.claude.com/incidents/rw3gjsvcny0l) | `rw3gjsvcny0l` | 影响等级不足以判定 | Elevated 500 Internal Server Errors for API and Claude.ai：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 43 | 2025-05-21 | [Elevated errors across many models](https://status.claude.com/incidents/mmk2nx0mc4ph) | `mmk2nx0mc4ph` | 影响等级不足以判定 | Elevated errors across many models：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 44 | 2025-05-21 | [Elevated errors on requests to some models](https://status.claude.com/incidents/zbjx86j1mg7s) | `zbjx86j1mg7s` | 影响等级不足以判定 | Elevated errors on requests to some models：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 45 | 2025-06-06 | [High rate of errors across models](https://status.claude.com/incidents/hs97xp476w3t) | `hs97xp476w3t` | 影响等级不足以判定 | High rate of errors across models：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 46 | 2025-06-17 | [Elevated errors across many models](https://status.claude.com/incidents/jnrthmjgg0f9) | `jnrthmjgg0f9` | 影响等级不足以判定 | Elevated errors across many models：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 47 | 2025-06-18 | [Elevated errors on Claude.ai](https://status.claude.com/incidents/h9466w330vb5) | `h9466w330vb5` | 影响等级不足以判定 | Elevated errors on Claude.ai：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 48 | 2025-07-01 | [Elevated errors across models](https://status.claude.com/incidents/gnv6tpy1kq7v) | `gnv6tpy1kq7v` | 影响等级不足以判定 | Elevated errors across models：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 49 | 2025-07-10 | [Issues with accessing claude.ai](https://status.claude.com/incidents/49p2r17qb7k9) | `49p2r17qb7k9` | 影响等级不足以判定 | Issues with accessing claude.ai：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 50 | 2025-07-22 | [Elevated errors on claude.ai](https://status.claude.com/incidents/s8t7ls5t5j61) | `s8t7ls5t5j61` | 影响等级不足以判定 | Elevated errors on claude.ai：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 51 | 2025-08-07 | [Potential Errors with Claude.ai Connectors](https://status.claude.com/incidents/bh62vm741g0w) | `bh62vm741g0w` | 影响等级不足以判定 | Potential Errors with Claude.ai Connectors：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 52 | 2025-08-14 | [Elevated errors across models](https://status.claude.com/incidents/mpwx6wbxy02h) | `mpwx6wbxy02h` | 影响等级不足以判定 | Elevated errors across models：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 53 | 2025-09-03 | [Elevated error rates on API and claude.ai](https://status.claude.com/incidents/072fdwqt08ps) | `072fdwqt08ps` | 影响等级不足以判定 | Elevated error rates on API and claude.ai：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 54 | 2025-09-10 | [Claude.ai services impacted](https://status.claude.com/incidents/p8pczg3gxg2k) | `p8pczg3gxg2k` | 影响等级不足以判定 | 仅称 Claude.ai services impacted 后直接结案，无法判断具体影响方式和程度。 |
| 55 | 2025-09-22 | [Elevated error rates on API and claude.ai](https://status.claude.com/incidents/35ff8rq8c6lr) | `35ff8rq8c6lr` | 影响等级不足以判定 | Elevated error rates on API and claude.ai：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 56 | 2025-09-22 | [Claude App and API connectivity errors](https://status.claude.com/incidents/xg2v4m4nc40n) | `xg2v4m4nc40n` | 影响等级不足以判定 | 连接错误公告与组件红色状态不足以确认全量失败；后续明确部分端点恢复，保留未知严重度候选窗口。 |
| 57 | 2025-09-24 | [Elevated error rates on API and claude.ai](https://status.claude.com/incidents/mf6sw0fbyvvf) | `mf6sw0fbyvvf` | 影响等级不足以判定 | Elevated error rates on API and claude.ai：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 58 | 2025-09-30 | [Elevated errors](https://status.claude.com/incidents/3fq7j7zbfrkm) | `3fq7j7zbfrkm` | 影响等级不足以判定 | Elevated errors：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 59 | 2025-10-09 | [Elevated errors on claude.ai](https://status.claude.com/incidents/6xlfx3mrb8ct) | `6xlfx3mrb8ct` | 影响等级不足以判定 | Elevated errors on claude.ai：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 60 | 2025-10-31 | [Elevated errors on claude.ai](https://status.claude.com/incidents/s5f75jhwjs6g) | `s5f75jhwjs6g` | 影响等级不足以判定 | Elevated errors on claude.ai：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 61 | 2025-11-11 | [Elevated errors on Claude.ai](https://status.claude.com/incidents/4kv6xfjg5cz2) | `4kv6xfjg5cz2` | 影响等级不足以判定 | Elevated errors on Claude.ai：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 62 | 2025-11-11 | [Elevated errors on Claude.ai](https://status.claude.com/incidents/h46s65s799ch) | `h46s65s799ch` | 影响等级不足以判定 | Elevated errors on Claude.ai：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 63 | 2025-11-17 | [Issues with Claude.ai Research](https://status.claude.com/incidents/9gm98llzp382) | `9gm98llzp382` | 影响等级不足以判定 | Issues with Claude.ai Research：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 64 | 2025-11-18 | [Elevated errors on claude.ai](https://status.claude.com/incidents/p0svq4j6sk04) | `p0svq4j6sk04` | 影响等级不足以判定 | Elevated errors on claude.ai：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 65 | 2025-11-23 | [Elevated error rates on the API](https://status.claude.com/incidents/538r2y9cjmhk) | `538r2y9cjmhk` | 影响等级不足以判定 | Elevated error rates on the API：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 66 | 2025-11-25 | [Elevated Error Rates on the API](https://status.claude.com/incidents/1y63m9yzpjn2) | `1y63m9yzpjn2` | 影响等级不足以判定 | Elevated Error Rates on the API：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 67 | 2025-12-02 | [Elevated errors on claude.ai](https://status.claude.com/incidents/qj71q3gqvvlk) | `qj71q3gqvvlk` | 影响等级不足以判定 | Elevated errors on claude.ai：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |

### 2026 年：37 条

| 序号 | 公告日期 UTC | 官方标题及链接 | ID | 研究分类说明 | 判断理由 |
| ---: | --- | --- | --- | --- | --- |
| 68 | 2026-01-12 | [Elevated rate of errors for multiple models](https://status.claude.com/incidents/zt2q0ltqcvbx) | `zt2q0ltqcvbx` | 影响等级不足以判定 | Elevated rate of errors for multiple models：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 69 | 2026-01-15 | [Compaction is having issues](https://status.claude.com/incidents/6ykk5hyrg95v) | `6ykk5hyrg95v` | 影响等级不足以判定 | 仅称 compaction having issues，未说明失败还是质量/速度退化；不凭组件标签判 P/D。 |
| 70 | 2026-01-22 | [Elevated errors on claude.ai](https://status.claude.com/incidents/ct82mw4kc0kt) | `ct82mw4kc0kt` | 影响等级不足以判定 | Elevated errors on claude.ai：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 71 | 2026-01-22 | [Elevated error rates on claude.ai and API](https://status.claude.com/incidents/713v1h3z2j5k) | `713v1h3z2j5k` | 影响等级不足以判定 | Elevated error rates on claude.ai and API：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 72 | 2026-02-03 | [Elevated error rate on API across all Claude models](https://status.claude.com/incidents/pr6yx3bfr172) | `pr6yx3bfr172` | 影响等级不足以判定 | Elevated error rate on API across all Claude models：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 73 | 2026-02-04 | [Elevated errors on Claude models](https://status.claude.com/incidents/pvbysfjjrf8m) | `pvbysfjjrf8m` | 影响等级不足以判定 | Elevated errors on Claude models：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 74 | 2026-02-06 | [Elevated error rates on claude.ai](https://status.claude.com/incidents/2gjynbb7ydph) | `2gjynbb7ydph` | 影响等级不足以判定 | Claude.ai 错误率上升缺用户/请求边界，且仅已恢复记录。 |
| 75 | 2026-02-07 | [Elevated errors on Claude models](https://status.claude.com/incidents/mm4pj02mp4gq) | `mm4pj02mp4gq` | 影响等级不足以判定 | Elevated errors on Claude models：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 76 | 2026-02-14 | [Elevated errors on Claude models](https://status.claude.com/incidents/bybkm0xccbm6) | `bybkm0xccbm6` | 影响等级不足以判定 | Elevated errors on Claude models：已读完全部更新；公告未提供足以区分全量/部分失败或性能退化的影响边界，保留未知。 |
| 77 | 2026-02-18 | [Elevated error rates across multiple models](https://status.claude.com/incidents/kqxx66h5qsy2) | `kqxx66h5qsy2` | 影响等级不足以判定 | 标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。 |
| 78 | 2026-02-25 | [Elevated error rates across multiple models](https://status.claude.com/incidents/bdxgsy48hp00) | `bdxgsy48hp00` | 影响等级不足以判定 | 标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。 |
| 79 | 2026-02-27 | [Elevated errors on claude.ai](https://status.claude.com/incidents/6rw4nd44bqqh) | `6rw4nd44bqqh` | 影响等级不足以判定 | 标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。 |
| 80 | 2026-02-27 | [Elevated errors on claude.ai](https://status.claude.com/incidents/zp9x05pcbwxq) | `zp9x05pcbwxq` | 影响等级不足以判定 | 标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。 |
| 81 | 2026-02-28 | [Elevated errors on claude.ai](https://status.claude.com/incidents/ddyyz34c24vt) | `ddyyz34c24vt` | 影响等级不足以判定 | 标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。 |
| 82 | 2026-03-02 | [Elevated errors in claude.ai](https://status.claude.com/incidents/63943gpfb97z) | `63943gpfb97z` | 影响等级不足以判定 | 标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。 |
| 83 | 2026-03-03 | [Elevated errors in claude.ai, cowork, platform, claude code](https://status.claude.com/incidents/yf48hzysrvl5) | `yf48hzysrvl5` | 影响等级不足以判定 | 多个产品仅报错误增加，无失败比例或明确受影响子集，U；Cowork 从标题补入。 |
| 84 | 2026-03-16 | [Elevated errors on Claude.ai](https://status.claude.com/incidents/t2m389x6k1tq) | `t2m389x6k1tq` | 影响等级不足以判定 | 标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。 |
| 85 | 2026-03-16 | [Elevated errors on Claude.ai](https://status.claude.com/incidents/81m3f5p97qkk) | `81m3f5p97qkk` | 影响等级不足以判定 | 标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。 |
| 86 | 2026-03-23 | [Elevated errors on Claude.ai [retroactive]](https://status.claude.com/incidents/0kxm85c9w7rw) | `0kxm85c9w7rw` | 影响等级不足以判定 | 实际窗口明确，但只说明 Claude.ai 错误率上升，无影响比例，U。 |
| 87 | 2026-03-25 | [Elevated Errors on claude.ai](https://status.claude.com/incidents/9rt6y2y4gkh1) | `9rt6y2y4gkh1` | 影响等级不足以判定 | 错误率无比例或范围，U；resolved 同时标 major_outage 是状态冲突，不能延长。 |
| 88 | 2026-05-06 | [Elevated errors across multiple models](https://status.claude.com/incidents/437swp24nrf4) | `437swp24nrf4` | 影响等级不足以判定 | 标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。 |
| 89 | 2026-05-13 | [Claude.ai is experiencing elevated error rates](https://status.claude.com/incidents/sb7byp4h7yp8) | `sb7byp4h7yp8` | 影响等级不足以判定 | 标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。 |
| 90 | 2026-05-13 | [Claude.ai is experiencing elevated error rates](https://status.claude.com/incidents/yn24rtdnf77b) | `yn24rtdnf77b` | 影响等级不足以判定 | 标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。 |
| 91 | 2026-05-16 | [Elevated error rates on requests to multiple models](https://status.claude.com/incidents/v9s6d0jt84hj) | `v9s6d0jt84hj` | 影响等级不足以判定 | 标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。 |
| 92 | 2026-05-21 | [Elevated errors on Claude.ai](https://status.claude.com/incidents/zvlgr3k8lny0) | `zvlgr3k8lny0` | 影响等级不足以判定 | 标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。 |
| 93 | 2026-06-02 | [Elevated errors on multiple models](https://status.claude.com/incidents/zkr25thltwc9) | `zkr25thltwc9` | 影响等级不足以判定 | 标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。 |
| 94 | 2026-06-11 | [Elevated errors across models](https://status.claude.com/incidents/j8ghp7dk6lym) | `j8ghp7dk6lym` | 影响等级不足以判定 | 标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。 |
| 95 | 2026-06-18 | [Service disruption on Claude services](https://status.claude.com/incidents/jlbvcpfwwq8z) | `jlbvcpfwwq8z` | 影响等级不足以判定 | 仅 service disruption，未说明用户失败比例或具体功能，U；实际窗口可定位。 |
| 96 | 2026-06-19 | [Elevated error rates on the Claude API](https://status.claude.com/incidents/1p98mj17s1z2) | `1p98mj17s1z2` | 影响等级不足以判定 | 标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。 |
| 97 | 2026-06-22 | [Elevated errors across many models](https://status.claude.com/incidents/bbcpk0t2cj4p) | `bbcpk0t2cj4p` | 影响等级不足以判定 | 标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。 |
| 98 | 2026-06-23 | [Elevated error rate across multiple models](https://status.claude.com/incidents/jbhf20wjmzrf) | `jbhf20wjmzrf` | 影响等级不足以判定 | 标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。 |
| 99 | 2026-07-03 | [Elevated errors across many models](https://status.claude.com/incidents/c0052w6jxl47) | `c0052w6jxl47` | 影响等级不足以判定 | 标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。 |
| 100 | 2026-07-15 | [Elevated errors on multiple models](https://status.claude.com/incidents/09g0fh2l7qbb) | `09g0fh2l7qbb` | 影响等级不足以判定 | 标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。 |
| 101 | 2026-07-21 | [Elevated errors on several models](https://status.claude.com/incidents/vcynh9cf33xp) | `vcynh9cf33xp` | 影响等级不足以判定 | 标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。 |
| 102 | 2026-07-29 | [Elevated errors across all models](https://status.claude.com/incidents/q2kg8n613kr3) | `q2kg8n613kr3` | 影响等级不足以判定 | 标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。 |
| 103 | 2026-08-03 | [Error rates across multiple models](https://status.claude.com/incidents/ch7k4vh9fr1y) | `ch7k4vh9fr1y` | 影响等级不足以判定 | 标题仅说明跨产品/多个模型错误率，没有失败比例或明确受影响子集，复核后等级未知。 |
| 104 | 2026-08-31 | [Degraded performance on claude.ai](https://status.claude.com/incidents/9jrp5rtyzrf6) | `9jrp5rtyzrf6` | 影响等级不足以判定 | 仅聊天错误上升，无用户/请求比例，不能证明整产品或明确子集不可用，U。 |

## 核验及数据入口

- [完整事故 CSV](2026-09-27/v1.1/incidents.csv)
- [主报告及完整原文索引](2026-09-27/v1.1/Anthropic_Claude_Availability_Report_2026-09-27_v1.1.html)：底部等级筛选选择 unknown 时还会显示4条维护；本清单已排除维护，只列104条 incident。
- [事故等级定义](2026-09-27/v1.1/事故等级定义.md)
- [既有全量复核验证记录](2026-09-27/v1.1/verification.json)

CSV SHA-256：`22d69c1d5a8cb39343f62a5b9b8af0766f5fa1943f365d26f553054bf8c12eee`。

清单核验：104个唯一ID；年份合计4+24+39+37=104；明确无影响3条；既有CSV与研究判断未更改。
