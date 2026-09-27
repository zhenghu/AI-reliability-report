# Early history semantic review

Reviewed frozen docket indices **0–306 inclusive**, 307 records and all **928 updates**, covering 2023-03-14 through 2025-04-29. Read each full title, source component list, update body, update timestamp/status and historical component transition. Initial overlarge output was truncated; reread indices 24–59 and 144–147 in smaller batches. No source bodies remained unread. No new network acquisition or change to frozen v1.0 was made.

Serialization in `early_build.py` uses explicit index-based judgments made after reading. It does not classify by text keywords. Most P cases explicitly name a model, user cohort, or feature; generic elevated errors remain U. Source labels were not used as sufficient semantic evidence. Every quote is verified against its original title/update ID.

- F: 16; P: 217; D: 31; U: 43. F includes the auxiliary website and explicitly scoped Vertex model deployment; these are outside core product availability.
- 73 records have individually supplied intervals, including mixed phases and uncertainty intervals. 35 records have `time_mode=none`, including maintenance and vendor-confirmed no-impact records. Other records use explicitly labeled historical-component/announcement proxies.
- 3 maintenance records (78, 184, 214) remain in audit but excluded from non-planned incidents.
- 3 vendor-confirmed no Anthropic-service/user-request impact records (218, 225, 303) exclude all affected intervals.

Important interpretation decisions:

- n19 has F only on Claude.ai; API/Console receive D. n26 and n59 have distinct grade phases. Early generic error stage in n43 remains U.
- n129 has recovery then recurrence; disabled free usage/model substitution does not mean whole-product F. n145, n147, n163, n171, n180 and n275 retain separate phases. n165 and n180 retain free-tier model limitation after other products recover.
- n138 and n268 first disclose an already repaired quality problem; announcement-to-closure spans are not downtime. n158 and n183 supply known error envelopes but cannot fully time the continuing free-tier model limitation.
- n182 tool calls missing arguments are output/structure quality D; its complete retrospective UTC range supersedes the later notice.
- n167 is Console billing visibility D; API success rates explicitly unaffected.
- n186 and n191 are Message Batches API and map to API even though the obsolete component may be Unmapped in current component metadata.
- n269 contains an emergency offline maintenance phase within an incident; that phase is explicitly separated from preceding unquantified errors. Its historical state lists API as well as Claude.ai/Console; phase scope is preserved in intervals.
- n69, n126, n168, n175, n198, n199, n221, n280, n284 have unresolved chronology/timezone/recovery contradictions. They do not receive invented exact times. n297 only identifies a start date, n0/n1/n86/n257 only duration, and several early resolved-only notices lack positioned intervals.
- Model-only notices without an identifiable product platform retain Unmapped instead of spreading the impact across API/Claude.ai/Console.

Verification: indices 0–306 covered exactly once; 307 IDs match the frozen docket; all exact quotes match their original source fields; all supplied intervals have positive UTC duration. `time_complete` is false for announcement proxies, approximate or partial timelines. Unknown evidence does not mean no outage.
