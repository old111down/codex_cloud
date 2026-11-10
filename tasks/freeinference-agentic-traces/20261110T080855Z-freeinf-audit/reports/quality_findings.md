# 数据质量结论



全部16周schema一致；实际3表38个顶层字段，展开role_tokens另5个子字段。无重复候选主键、无孤儿Request/Tool/子代理、无子代理环、step/call_index均从0连续，ID格式符合公开定义；实际请求时长与TTFT没有负值、没有TTFT大于衍生请求时长的行。所有行的工具latency与官方邻接公式一致。只意味着所列检查未观察到例外，不能据此证明重建关系是真实因果关联。

空值具有条件语义：顶层的父/出生键为null；每个Session第一步link_reason/waited_for/transition为null；非mutation的cause为null；非Shell工具parse_status为null；没有匹配result的outcome/result_tokens可为null；cache计数/TTFT也可能缺失。**缺失缓存计数不等于零**，应遵循 [tokens.py](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/paper/metrics/tokens.py#L19) 的cache-reporting选择。已修正字典中的用户清单：Session start/end、Request turn_index、provider_tokens/mutation、Tool arguments/subagent 属于JSONL派生/嵌套表示，不是同名Parquet列。

`end_ms`来自原日志timestamp；`start_ms=end_ms-(latency_ms or 0)`是 [转换算式](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/log_records/fields.py#L174)，并非独立客户端发包时间测量。物理采集事件、历史部署时钟和队列延迟在这份数据里仍Unknown。Completion落在周内而start跨到前一天正常：例如Aug30周4条衍生start在Aug29，不能误报超界损坏。Session自己的JSONL起止为主链request min/max；本审计分别记录主链span和包含descendant的span，不混用。

## 需解释的值观测，而非自动判定损坏

1. **4条负工具gap**：Jun21周两个request batch分别−437/−180ms；Aug30周一个batch含2条call，各−1497ms。工具latency实际为next_request.start−current.end、同batch共享，完全符合源码公式。真实工具执行起止并未采集在此字段；重建/日志时钟/并发等原因Unknown。源码在time_breakdown中把负gap截为0，tool overview单call统计等路径口径需单独识别，不能把四行解释为“真实工具耗时为负”。
2. **4条cache_read_tokens>prompt_tokens**：均在Aug9周、匿名Provider C、minimax-m3，四条总prompt835,640、cache835,703，差63。源字段来自Provider/log usage；供应商计费/报告或归一化语义不可由匿名字母还原，因此不单凭该不等式断言损坏。[anomaly_and_confounding_aggregates.json](anomaly_and_confounding_aggregates.json) 保留无ID聚合证据。官方uncached_tokens截为0、cache ratio部分路径截为1，而token_growth明确保留负uncached，复算须保留该区别。
3. **Provider tokens与role_tokens不同口径**：前三种usage优先日志、fallback response.usage；role_tokens来自o200k_base digest。二者差异不是质量失败。`schema.py`的TOKENIZER注释泛称token counts，但实际 [fields.py](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/log_records/fields.py#L154) 与 [paper tokens.py](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/paper/metrics/tokens.py#L1) 明确区分。
4. **Harness方法次序**：论文§3说有UA时使用UA，否则system prompt；当前 [harness.py](https://github.com/HarvardMadSys/freeinference_agentic_trace/blob/2b795dbf5eac490a7c081906fdce6cc7a184b7ef/export/log_records/harness.py#L64) 先匹配前6条system/user消息、最多20K字符的intro phrase，再UA fallback。差异已源码确认；由于公开数据无原文本和UA，影响Unknown。



完整范围、Table1对比和命令见 [data_validation_report.md](../data_validation_report.md)。
