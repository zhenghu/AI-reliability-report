"""Render a self-contained Chinese research report from frozen local evidence (stdlib)."""
import sys,json,csv,hashlib,html,re,collections,zipfile
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[2]
sys.path.insert(0,str(REPO/'.agents/skills/incident-research/scripts'))
from core import read_csv,utc,union_seconds,write_json
S=json.loads((ROOT/'snapshot.json').read_text());V=json.loads((ROOT/'incidents.validation.json').read_text());T=json.loads((ROOT/'trend_data.json').read_text());D=json.loads((ROOT/'summary-data.json').read_text());R=read_csv(ROOT/'incidents.csv');REF=json.loads((ROOT/'reference-intervals.json').read_text());RI={r['id']:r for r in REF};BY={r['incident_id']:r for r in R}
STEM='Anthropic_Claude_Availability_Report_2026-09-27_v1.0'
LABEL={'Overall':'核心服务并集','Claude.ai':'Claude.ai','API':'第一方 API','Console':'Console','Claude Code':'Claude Code','Cowork':'Cowork','Government':'Government'}
def table(head,rows):return '\n'.join(['| '+' | '.join(head)+' |','| '+' | '.join(['---']*len(head))+' |']+['| '+' | '.join(str(v).replace('|','／').replace('\n',' ') for v in r)+' |' for r in rows])
def pct(v):return f'{v*100:.4f}%'
def number(v):return f'{v:,.2f}'
def link(i):return f"[{BY[i]['incident_title']}](https://status.claude.com/incidents/{i})"
now2026=[r for r in T['annual'] if r['year']==2026]
count_by_year=V['by_publication_year_utc']
all_matched=[]
end=utc(S['cutoff_utc'])
for y in [2024,2025,2026]:
 a=datetime(y,1,1,tzinfo=timezone.utc);b=end.replace(year=y)
 count=sum(r['record_type']=='incident' and a<=utc(r['published_at_utc'])<b for r in R)
 all_matched.append((y,count))
first=min(r['published_at_utc'] for r in R);last=max(r['published_at_utc'] for r in R)
allcore=next(r for r in now2026 if r['group']=='Overall');excore=next(r for r in D['sensitivity_2026_excluding_suspension'] if r['group']=='Overall')
susp=RI['s9w82lp9dcn9'];susph=union_seconds(susp['intervals'])/3600
raw_unknown=sum(r['official_severity']=='unknown' and r['record_type']=='incident' for r in R)
maint=table(['年份（公告 UTC）','事故','维护'],[(y,x['incidents'],x['maintenance']) for y,x in count_by_year.items()])
y2026=table(['服务','观察起点','事件数¹','F 参考','F∪P 参考','F∪P∪D 参考'],[(LABEL[r['group']],r['window_start'][:10],r['incident_count'],pct(r['availability_full']),pct(r['availability_full_partial']),pct(r['availability_all'])) for r in now2026])
hours=table(['服务','F 小时','F∪P 小时','F∪P∪D 小时'],[(LABEL[r['group']],number(r['full_hours']),number(r['full_partial_hours']),number(r['all_hours'])) for r in now2026])
sensitivity=table(['服务','含暂停 F∪P','排除暂停 F∪P','含暂停全部等级','排除暂停全部等级'],[(LABEL[a['group']],pct(a['availability_full_partial']),pct(b['availability_full_partial']),pct(a['availability_all']),pct(b['availability_all'])) for a,b in zip(now2026,D['sensitivity_2026_excluding_suspension'])])
annual=table(['年份','服务','观察天数','公告数¹','F 小时','F∪P 小时','全部等级小时','全部等级参考率'],[(r['year'],LABEL[r['group']],number(r['denominator_seconds']/86400),r['incident_count'],number(r['full_hours']),number(r['full_partial_hours']),number(r['all_hours']),pct(r['availability_all'])) for r in T['annual']])
matched=table(['同期年份','全站事故公告数','核心服务事故公告数','核心服务全部等级参考率'],[(y,c,next(r['incident_count'] for r in T['matched_windows'] if r['year']==y and r['group']=='Overall'),pct(next(r['availability_all'] for r in T['matched_windows'] if r['year']==y and r['group']=='Overall'))) for y,c in all_matched])
windowtable=table(['服务','观察起点 UTC','选择理由'],[(LABEL[g],v['start'],'官方组件 start_date' if g in ['Overall','Claude.ai','API','Console'] else '官方组件 created_at 后首个完整 UTC 日') for g,v in json.loads((ROOT/'service_windows.json').read_text())['service_windows'].items()])
unknown_reference=[r for r in R if r['record_type']=='incident' and not RI[r['incident_id']]['intervals']]
unknown_table=table(['公告日期','事故','官方等级'],[(r['published_at_utc'][:10],f"[{r['incident_title']}](https://status.claude.com/incidents/{r['incident_id']})",r['official_severity']) for r in unknown_reference])
md=f'''# Claude 可用性与历史事故报告

**Anthropic · 2026-09-27 · v1.0 状态记录参考估计版**

冻结截止：**2026-09-27 16:10:43 UTC**（德国时间 18:10:43）。来源：[Claude 官方状态站](https://status.claude.com)、[History](https://status.claude.com/history)、逐事故公开 JSON。

> 本报告已完成公开历史采集与结构校验，但未完成全部事故的逐阶段语义复核。百分比是“已取得并可定位的状态异常区间之外的时间比例”，不是实际请求成功率、官方 uptime 或合同 SLA。请先看口径和质量表，再使用数字。

## 一、可以确认的结论

- 取得 **920 条唯一记录：916 起事故、4 条维护、2,919 条更新**。按公告时间，2023 年 30 起、2024 年 188 起、2025 年 334 起、2026 年截至本次冻结 364 起事故。枚举范围覆盖官方 History 可得历史，不能证明厂商披露了所有真实故障。
- 当前不能负责任地用一个数字宣称“Claude 的真实可用率”。同一条公告可能只影响登录、某个模型、免费用户或某个工具；按“任一功能出现问题”计算，与按“所有请求失败”计算差别很大。
- 2026 年核心服务并集的 **F 参考率为 {pct(allcore['availability_full'])}、F∪P 为 {pct(allcore['availability_full_partial'])}、全部等级为 {pct(allcore['availability_all'])}**。这些 F/P/D 主要沿用官方历史组件状态，只有重点记录做了正文校正；F 并不等于整家公司完全停机。
- 一条指定模型访问暂停公告的生命周期约 **{susph:.2f} 小时**。排除此项后，2026 年核心服务并集的 F∪P 参考率为 **{pct(excore['availability_full_partial'])}**、全部等级为 **{pct(excore['availability_all'])}**。差值来自重新取时间并集，不是直接减掉 {susph:.2f} 小时。
- 缺失时间、未完成分级、不同组件历史起点和披露习惯都会影响结果。**本版适合用于定位风险与选择复核重点，不适合作为供应商 SLA 排名或与 OpenAI 报告直接横向排序。**

## 二、历史范围、覆盖与年度数量

{maint}

实际取得最早公告：**{first}**；最新公告：**{last}**。2026-09-22 后到冻结时刻之间没有取得新的事故公告，不等于这段时间不存在任何真实故障。

History 以连续 3 个月为一页，共保存 **16 页**，从 2026 年第三季度读到 2022 年第四季度。最后一页为空，且早于页面创建时间 **2023-01-25T06:38:50.038Z**。页面没有提供明确的“全部历史可得起点”声明，因此不把页面创建日或第一起事故当作产品上线日。

事故列表 API 的 `page=2` 与第一页重复；维护列表也重复。因此这两个列表接口不作为全量覆盖依据。History 的 920 个 ID 与最终 920 条对象一一对应；其中两个维护 ID 在事故详情接口返回 404，改用公开维护详情接口后取得。最近列表的 50 个 ID 全部包含在 History 枚举中。

**覆盖状态：enumerated（对实际可访问的 History 边界完成枚举）。**交叉检查是 History HTML 内嵌数据与公开详情 JSON 的 ID 对照；未把两个同源接口称为独立信源，也未宣称已执行浏览器逐页视觉核对。每页原始 HTTP 响应体及 SHA-256 已保存在本地证据目录。

## 三、观察窗口与统计定义

{windowtable}

较新组件的官方 `start_date` 有早于组件创建日期的情况，Claude Code 尤为明显。本版保守采用组件创建后的首个完整 UTC 日，不回填组件出现前的“零故障”历史。Cowork 在 2026 年 4 月之前的相关公告仍保留于 CSV，但不用于 Cowork 本版可用性分母。所有窗口截止均为本轮冻结时间。

核心服务并集纳入 Claude.ai、第一方 API、Console、Claude Code、Cowork 和 Government，且每个组件只在自身观察窗口内参与。Vertex/Bedrock、营销网站、文档站、社交账号单独归 External/Other，不计入核心服务并集。未能归属核心组件的公告仍留在 CSV，不能悄悄当成无影响。

- **F**：参考序列中的 `major_outage`，或已核验范围内的 Full。它可能只是组件/功能失效，不能解释成全公司停机。
- **F∪P**：上述区间与 `partial_outage` 的时间并集。
- **F∪P∪D**：再加入 `degraded_performance`，涵盖延迟、质量或功能退化。
- 事故级 `critical / major / minor` 仅在没有可用历史组件阶段时作为候选映射，分别对应 F/P/D，并标为公告代理。`none` 不是正常状态证据。

计算式：**参考率 = 1 − 相应异常时间并集 ÷ 明确观察窗口秒数**。维护排除；跨年裁切；同一事故、组件间和事故间的重叠均去重。Overall 重新对全部纳入阶段取并集，不加总产品小时数。没有精确区间的数据不进入时长，因而剩余时间不能解释成已确认正常。

¹ 各表事故数按公告时间归年、按对应服务归属计数。一个事故可同时计入多个服务，所以各服务次数不能相加。数量表与时间表采用不同的合理边界：迟报事件按公告日计数，但明确影响窗口按真实日期计时。

## 四、2026 年截至冻结时刻的参考结果

{y2026}

为便于复算，对应的异常并集时长如下：

{hours}

API 的统计范围是第一方 API 公告所涉组件，既可能包含核心推理，也可能包含工具、批处理或其他功能。Claude Code 的登录故障可能影响新登录用户，却不阻断已登录会话。Cowork 和 Government 观察窗口短于 2026 年全段；不能把它们的百分比与长窗口产品当成同等实验条件。

## 五、主动暂停对结果的影响

{link('s9w82lp9dcn9')} 于 2026-06-13 公告暂停指定模型访问，7 月 1 日关闭。官方说明指出暂停针对 Fable 5 与 Mythos 5，其他模型不受影响；因此本研究将其视为产品范围的 Partial，而非所有 Claude 服务 Full。它的公告关闭时间并不能独立证明各平台、各用户在同一秒恢复。

来源：[官方暂停说明](https://www.anthropic.com/news/fable-mythos-access)、[官方重新开放说明](https://www.anthropic.com/news/redeploying-fable-5)。本版只分析其服务范围与统计影响，不对政策合法性或背景作判断。

{sensitivity}

主表保留这条事件，因为用户确实可能失去指定模型的访问；对照表排除它，帮助观察技术运行事件。**“排除暂停”仍不是完整技术故障真值**：其他访问政策、未知时间和功能性事件未因此全部消除。

## 六、年度与同期变化

截至相同的 9 月 27 日 16:10:43 UTC，事故公告数量如下。2026 年数字不与 2025 全年直接比较：

{matched}

公告增加可能同时反映产品范围扩大、组件细分和披露方式变化，不能单凭次数推断底层系统同幅度恶化。2026 年的范围又增加 Cowork 和 Government，Overall 的服务集合也发生变化。

完整年度/部分年度服务表：

{annual}

2023 年仅覆盖核心三组件 7 月 11 日后的窗口；2025 年 Claude Code、2026 年 Cowork/Government 均为部分年度。本版不连接不存在的早期产品数据，也不把缺失年份补成 100%。

## 七、重点事件：哪些细节改变结论

### 1. 部分请求失败，不等于红色标签所暗示的全停

{link('d8v3zr02my00')} 的官方严重度是 critical，但正文说明受影响请求比例较小，明确影响窗口为 **2026-02-03 17:52–17:56 UTC**。本次将其按 API 范围的 Partial 处理。仅根据 critical→Full 映射会夸大故障范围。

### 2. 一次长公告中只有部分时段是入口完全不可访问

{link('7542z654hwl8')} 横跨约一天。正文明确 Claude.ai 与 Console 在 **2025-07-09 21:36–21:52 UTC** 无法访问；其他时段涉及少量错误和 Artifacts 发布不可用。CSV 为这一事件保留分段，不能把全天都算作 Full。API 明确未受影响。

### 3. 依赖故障有不同影响路径

{link('kn7mvrgb0c8m')} 将异常归因于 GCP 依赖。图像/文件上传不可用时，部分文本请求仍可成功。它支持“依赖故障会跨入口传播”的结论，但不支持“全部文本推理持续失败”的结论。恢复过程按记录分层，不能把监控状态自动当作完全恢复。

### 4. 输出质量也是可靠性，但没有秒级时间就不能编造

{link('4q9qw2g0nlcb')} 明确给出 **2025-07-08 08:45 至 7 月 10 日 02:00 UTC** 的输出质量退化，与推理栈发布有关，计入 Degraded。

{link('72f99lh1cj2c')} 则引用了多个早于公告的质量问题。官方[技术复盘](https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues)讨论路由、输出损坏和采样计算问题，说明错误率/延迟监测不足以覆盖回答质量。其阶段多以日期表述，本版没有擅自补成 UTC 午夜；也没有把后发复盘的发表时间延长为故障时间。

### 5. 客户端功能失效与核心模型推理分开

{link('r1pqn1kb4hvk')} 描述 Windows 更新导致 Cowork 本地命令失效，而多数用户仍能聊天和读写文件，因此按 Cowork 产品范围 Partial 处理。更新发布日期只精确到日，公告生命周期约 99 小时只是代理，不证明真实影响从公告时才开始。

{link('pqpgkf52p3tg')} 的官方更新说明夏令时跳过的小时引发定时任务定位循环，限定于相应时区和配置的用户。这类事件说明客户端、认证和任务调度需要独立的可靠性指标。

## 八、质量缺口与可信度

{table(['检查项','本轮结果'],[
('历史枚举','920 个 History ID 全部取得；16 个连续季度窗口；最后窗口早于页面创建'),
('原始记录','916 事故 + 4 维护；2,919 更新；同名不同 ID 未合并'),
('官方严重度缺失/none',f'{raw_unknown} 起事故；不视为零影响'),
('重点语义复核',f"{V['review_counts']['assessed']} 条；其余 {V['review_counts']['needs_review']} 条标 needs_review"),
('语义严重度仍 unknown',f"{V['unknown_severity_records']} 起事故，包括未完成分级及证据不足"),
('完整核验的精确时间线',f"{V['assessed_exact_timeline_count']} 条；不能把其余都有起止字段等同于已核验"),
('语义分析区间未建立',f"{V['unknown_time_records']} 起事故；含未完成语义复核，并不等于原始公告没有时间"),
('参考序列无法定位/不采用区间',f"{V['reference_unknown_time_count']} 起事故；其他参考区间仍包含官方状态边界与公告代理"),
('当前未结案记录',str(sum(r['incident_status'] not in ['resolved','postmortem','completed'] for r in R))),
('结构校验','UTF-8 BOM、48 列、唯一 ID、JSON、原始对象 SHA-256、时区、正长度、时长并集、转义复读均通过'),
('非结构验收','未完成所有事件的逐阶段语义验收；未核验未公开故障、实际请求成功率及用户/地区权重')])}

CSV 的 **impact_intervals_json** 仅存已做重点判断的分析区间；**evidence_json.reference_intervals** 存本报告参考序列。两者不能混用。`trend_data.json` 明确标记为 `official_state_reference_with_focused_corrections`，不会将待复核的官方映射包装为已分析结果。

需优先复核的时间冲突包括：2024-04-18 公告正文却写 Feb 18；2025-09-12 同时给出的 PT 与 UTC 时长不同；2026-04-15 API 恢复描述的 PT/UTC 换算与发布时间互相不一致。相应 CSV 质量标志已保留，未无声修正成貌似精确的数字。

最早两起事件只披露 1 小时和 30 分钟，不能据此定位时间段。官方组件阶段也是“发布状态变化”的时间，未必等于真实影响时间；代理既可能漏掉公告前影响，也可能包含恢复后的监控。故本报告百分比没有可声称的统计置信区间。

额外技术复盘已通过网页读取工具查看；直接 HTTP 下载该页面返回 403，已停止该下载路径。本地只保留明确标注的摘录/研究笔记，不声称取得其完整原始 HTTP 文件。没有使用登录凭证或绕过访问限制。

## 九、如何使用本报告

可用于：建立公开事故基线；定位功能性和依赖风险；选择需要进一步复核的长事故；设计按调用路径区分的监测目标。

要用于生产选型或承诺 SLO，还需要补齐请求量、成功率、延迟分位数、模型/地域分布、客户端失败、重试后的任务成功率与质量评测。对于应用本身，分别观察“能连接”“能生成”“结果可用”“任务完成”比复用一个供应商状态页百分比更有意义。

本版不提供跨供应商优劣排名。与仓库中的 OpenAI 报告比较前，应先统一观察窗口、服务范围、分类定义、代理时间处理及语义复核程度。

## 十、交付物与复算入口

- [单一事故 CSV](incidents.csv)：UTF-8 BOM、48 列；完整原始对象、更新、证据、未知项均在同一文件。
- [CSV 校验结果](incidents.validation.json)、[历史快照](snapshot.json)、[枚举轨迹](history-index.json)。
- [重点分析](analysis.json)、[服务观察窗口](service_windows.json)、[年度及同期数据](trend_data.json)、[暂停敏感性数据](summary-data.json)。
- [参考区间](reference-intervals.json)、[本地复算脚本](tools/analyze.py)、[报告生成脚本](tools/build_report.py)。

CSV SHA-256：`{V['csv_sha256']}`。

原始 HTTP 响应体哈希与规范化事故对象哈希分开记录。后者使用键排序、UTF-8、无多余空白 JSON，不冒充网络原始字节。产物只保存在本地工作目录，未提交或推送 GitHub。

## 附录：参考序列无可用时间区间的 {len(unknown_reference)} 起事故

下表包括只有事后结案、缺官方严重度、仅有持续时长、时间冲突或实际阶段早于公告而不能定位的记录。缺失不计为零；完整原文可从 CSV 或 HTML 事故索引查看。

{unknown_table}
'''
(ROOT/(STEM+'.md')).write_text(md)
def inline(s):
 s=html.escape(s)
 s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
 s=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',s)
 s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',lambda m:f'<a href="{m[2]}">{m[1]}</a>',s)
 return s
parts=[];lines=md.splitlines();idx=0;sec=0;nav=[]
while idx<len(lines):
 l=lines[idx]
 if l.startswith('| '):
  batch=[]
  while idx<len(lines) and lines[idx].startswith('| '):batch.append(lines[idx]);idx+=1
  cells=lambda x:[inline(c.strip()) for c in x.strip('|').split('|')]
  heads=cells(batch[0]);body=['<tr>'+''.join('<td>'+c+'</td>' for c in cells(x))+'</tr>' for x in batch[2:]]
  parts.append('<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+x+'</th>' for x in heads)+'</tr></thead><tbody>'+''.join(body)+'</tbody></table></div>');continue
 if l.startswith('### '):parts.append('<h3>'+inline(l[4:])+'</h3>')
 elif l.startswith('## '):
  sec+=1;title=l[3:];nav.append((sec,title));parts.append(f'<h2 id="s{sec}">{inline(title)}</h2>')
 elif l.startswith('# '):parts.append('<h1>'+inline(l[2:])+'</h1>')
 elif l.startswith('> '):parts.append('<aside class="callout">'+inline(l[2:])+'</aside>')
 elif l.startswith('- '):parts.append('<p class="bullet">'+inline(l[2:])+'</p>')
 elif l:parts.append('<p>'+inline(l)+'</p>')
 idx+=1
# The interactive appendix is fully local; all labels/body text HTML-escaped.
records=[]
for r in R:
 ref=RI[r['incident_id']];us=r['updates_json'];body=''.join('<div class="update"><small>'+html.escape(u['at']+' · '+u['status'])+'</small><p>'+html.escape(u['body']).replace('\n','<br>')+'</p></div>' for u in us)
 flags=' · '.join(r['quality_flags_json']);groups=', '.join(r['service_groups_json']);content=f"<p>{html.escape(r['analysis_summary'])}</p><p><b>语义等级：</b>{html.escape(r['assessed_severity'])} · <b>官方等级：</b>{html.escape(r['official_severity'])} · <b>服务：</b>{html.escape(groups)}</p><p><b>原始对象 SHA-256：</b><code>{r['raw_sha256']}</code></p><p><b>质量标志：</b>{html.escape(flags)}</p>"+body
 records.append(f'<details class="incident" data-year="{r["published_at_utc"][:4]}" data-review="{r["review_status"]}" data-search="{html.escape((r["incident_title"]+" "+groups+" "+r["incident_id"]).lower(),quote=True)}"><summary><span class="date">{r["published_at_utc"][:10]}</span><span>{html.escape(r["incident_title"])}</span><span class="tag">{html.escape(r["record_type"])} · {r["review_status"]}</span></summary><div class="incident-body"><a href="https://status.claude.com/incidents/{r["incident_id"]}">官方公告 ↗</a>{content}</div></details>')
css='''*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:90px}body{margin:0;color:#232d36;background:#f5f3ed;font:16px/1.8 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}header{background:#183d3e;color:#fff;position:sticky;top:0;z-index:10;display:flex;justify-content:space-between;align-items:center;padding:14px 4vw;gap:20px}header a{color:#fff}header button{padding:7px 16px;border:1px solid #9cbab5;color:white;background:transparent;border-radius:6px}.layout{max-width:1550px;display:grid;grid-template-columns:230px minmax(0,1fr);gap:30px;margin:auto;padding:30px 3vw}nav{position:sticky;top:90px;align-self:start;max-height:85vh;overflow:auto}nav a{display:block;padding:8px 10px;font-size:13px;color:#47615d;text-decoration:none;border-left:2px solid transparent}nav a:hover{border-color:#b85a35;background:#eee8df}main{min-width:0;background:#fffefa;border:1px solid #dcded5;border-radius:12px;padding:40px 4vw;box-shadow:0 6px 30px #19333105}h1{font-size:clamp(28px,3.5vw,44px);line-height:1.35;letter-spacing:-.025em;margin:0 0 20px;color:#183d3e}h2{font-size:26px;margin:48px 0 20px;padding-top:20px;border-top:1px solid #d8dfd7;color:#183d3e}h3{font-size:19px;margin-top:28px}a{color:#146e68;text-underline-offset:3px}p{margin:14px 0}strong{font-weight:650}.callout{padding:20px 24px;background:#fff2da;border-left:4px solid #bc7530;border-radius:0 7px 7px 0;margin:25px 0}.bullet{padding-left:16px;border-left:3px solid #c3d6ce;margin:18px 0}.table-wrap{overflow-x:auto;margin:22px 0;border:1px solid #d9e2db;border-radius:7px}table{border-collapse:collapse;min-width:100%;font-size:13px;font-variant-numeric:tabular-nums}th{background:#254f4b;color:white;text-align:left;padding:12px;white-space:nowrap}td{padding:11px;border-top:1px solid #dce4df;min-width:85px}tr:nth-child(even){background:#f2f6f1}tbody tr:hover{background:#e9f0e9}code{font-family:ui-monospace,monospace;font-size:12px;overflow-wrap:anywhere}.controls{display:flex;gap:10px;flex-wrap:wrap;background:#eef3ed;padding:14px;border-radius:8px;position:sticky;top:72px;z-index:5}input,select{font:inherit;border:1px solid #bfd1c7;border-radius:5px;padding:8px;background:white}input{flex:1;min-width:180px}.incident{border-bottom:1px solid #dbe1d7;padding:12px 0}.incident summary{cursor:pointer;display:grid;grid-template-columns:90px 1fr;gap:6px 15px;font-size:14px}.date{color:#667871;font-size:12px}.tag{grid-column:2;font-size:11px;color:#728076}.incident-body{padding:10px 20px;border-left:3px solid #c9d7ce;margin:15px 0}.update{padding:12px 0;border-top:1px dashed #d4dcd3}.update small{color:#748076}.update p{font-size:13px}.muted{color:#7a847d;font-size:13px}.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:24px 0}.kpi{border:1px solid #d4dfd5;border-radius:8px;padding:18px;background:#f2f6f0}.kpi b{font-size:30px;display:block;color:#254f4b}.kpi span{font-size:12px;color:#596e61}[hidden]{display:none!important}@media(max-width:900px){.layout{display:block;padding:15px}nav{display:none}main{padding:26px 20px}h2{font-size:22px}.controls{position:static}.kpi{padding:12px}.kpi b{font-size:24px}}@media print{header,nav,.controls,#incident-index,.incident,.muted{display:none}.layout{display:block;padding:0}main{border:0;padding:0;box-shadow:none}body{background:white;font-size:10pt}h2{break-after:avoid}table{font-size:8pt}.table-wrap{overflow:visible}th{color:#183d3e;background:#e7eee6}tr{break-inside:avoid}a{color:inherit;text-decoration:none}}'''
script='''const q=document.querySelector('#q'),y=document.querySelector('#year'),v=document.querySelector('#review'),items=[...document.querySelectorAll('.incident')];function filter(){let n=0;for(const e of items){let ok=(!y.value||e.dataset.year===y.value)&&(!v.value||e.dataset.review===v.value)&&e.dataset.search.includes(q.value.toLowerCase());e.hidden=!ok;if(ok)n++}document.querySelector('#shown').textContent=n+' / '+items.length+' 条'}[q,y,v].forEach(e=>e.addEventListener('input',filter));filter();'''
htmltext='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Claude 可用性报告 · 2026-09-27</title><style>'+css+'</style></head><body><header><span>ANTHROPIC / RELIABILITY RESEARCH</span><a href="#incident-index">920 条事故与维护索引</a><button onclick="window.print()">打印报告</button></header><div class="layout"><nav>'+''.join(f'<a href="#s{i}">{html.escape(title)}</a>' for i,title in nav)+'<a href="#incident-index">交互事故索引</a></nav><main><div class="kpis"><div class="kpi"><b>916</b><span>公开事故 · 全历史</span></div><div class="kpi"><b>4</b><span>维护 · 时长统计排除</span></div><div class="kpi"><b>'+str(V['review_counts']['assessed'])+' / 920</b><span>已完成重点语义复核 · 非全部</span></div></div>'+''.join(parts)+'<h2 id="incident-index">交互事故索引</h2><p>所有内容来自冻结快照，可离线筛选。展开查看完整公告更新、评估状态与原始对象校验值。</p><div class="controls"><input id="q" type="search" placeholder="搜索标题、服务或 ID" aria-label="搜索事故"><select id="year" aria-label="年份"><option value="">全部年份</option>'+''.join(f'<option>{y}</option>' for y in [2023,2024,2025,2026])+'</select><select id="review" aria-label="复核状态"><option value="">全部复核状态</option><option value="assessed">已做重点复核</option><option value="needs_review">仍待语义复核</option></select><span id="shown"></span></div>'+''.join(reversed(records))+'<p class="muted">Frozen public evidence · local artifact · no analytics or remote scripts.</p></main></div><script>'+script+'</script></body></html>'
(ROOT/(STEM+'.html')).write_text(htmltext)
# Snapshot metadata and named export files for quick independent calculations.
for name,data in [('annual-results.csv',T['annual']),('matched-window-results.csv',T['matched_windows']),('suspension-sensitivity.csv',D['sensitivity_2026_excluding_suspension'])]:
 with (ROOT/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
readme=f'''# Anthropic / Claude 可用性研究 · 2026-09-27

先打开 `{STEM}.html`。本版为公开状态参考估计，不是全量语义核验定稿或 SLA。

主交付 `incidents.csv` 为 48 列 UTF-8 BOM，920 条；精确冻结范围与缺口见报告。

`trend_data.json` 来自 CSV 的 `evidence_json.reference_intervals`，不是未完成的分析区间。不要误用通用聚合器把后者当完整时长。

在仓库根目录，用已有 Python 3 运行：

```sh
python3 Anthropic/2026-09-27/v1.0/tools/analyze.py
python3 Anthropic/2026-09-27/v1.0/tools/build_report.py
python3 Anthropic/2026-09-27/v1.0/tools/verify.py
```

复算脚本只读本轮快照；会重建本轮派生文件，不访问网络。新的采集应新建版本目录，不能对本轮改变 cutoff。

`evidence/` 为原始 HTTP 响应体与单独元数据，`snapshot.json` 为整合后的规范化快照。失败路径保存在 coverage 元数据中。

未安装软件，未使用凭证，未提交或推送 GitHub。
'''
(ROOT/'README.md').write_text(readme)
print('report',ROOT/(STEM+'.html'));print('bytes',len(htmltext.encode()),'markdown',len(md.encode()))
