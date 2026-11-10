# PR #3 修订的独立实现与回归验收

验收结论：**三个P2问题在所列实现与测试范围内均已修复。** 本次只检查本仓库审计工具的下载工作流、公开导出及复核状态，不提高原论文复现等级。没有重新下载科学数据、运行模型、重算论文、修改上游或更改原实验日志；本审查没有Git写操作或外发。

审查权威树为当前仓库；先读根`AGENTS.md`，再只读原版脚本并保存SHA基线。用户明确要求在同一PR修订，另建`20261110T094927Z-pr3-reviewfix`归档本次修复；不把它当作原研究重新开始。独立源码基线记录时间为2026-11-10T09:52:35Z。具体当前SHA、实际命令/退出状态及保全结果见本报告同名JSON与日志。

## 验收计划与结果

| P2 | 核查重点 | 实现复核 | 实际回归 |
|---|---|---|---|
| 干净目录与selected→full下载 | metadata可自行bootstrap；部分目录不因非空rename失败；已有文件必须验SHA；失败不覆盖证据 | 两CLI共用`pinned_release_download.py`；LFS SHA256、非LFS Git blob SHA1、table/manifest绑定；valid payload用hardlink复用；file no-clobber、manifest最后 | owner最终12项，独立重跑12/12；另独立2项通过 |
| 批量scan拒绝后public不变 | 晚出现的secret/path/type/size/UTF8问题，不能让早期文件、旧manifest或空目录先落public | 全批读取/路径校验→内存sanitize→内容与文件名扫描→目标预检；全部通过后才stage；FD/O_NOFOLLOW和逐文件replace；public manifest最后、source receipt随后 | owner最终17项，独立重跑并加2项，共19/19 |
| 失败review不能Verified/exit0 | 保存Failed与失败细节，非零退出；保留全部可完成检查；Unknown与Partial不能假装成功 | `build_report`保留原科学检查；main从checks/optional review汇总状态；输入错误写Failed；只有Verified返回0 | owner公开默认11项，独立重跑11/11；另5个独立状态/序列化probe全部通过 |

测试数按最终不同测试集合列示，不将重复运行相加。本独审当前重跑的pytest集合合计44项（12+2+17+2+11），另有5项单独main执行的probe；后者没有冒充pytest collected项。全部使用临时夹具或已公开聚合，不是新科学复现。

## 下载工作流的覆盖与边界

已经覆盖：clean selected和clean full的固定revision metadata获取；selected→full完成与幂等重复；既有requests保持inode且仅第一次传输；staging有效payload复用；complete缓存重新验证；错revision、manifest绑定不一致、已有/暂存损坏、同长度非LFS metadata损坏、错误HTTP内容和不足5GiB余量均拒绝。

独立增加的两个场景直接检查SHA而非存在/大小：完整缓存的requests只翻转一个byte、长度不变，必须SHA256拒绝，且不发HTTP、不覆盖损坏证据；selected目标与partial staging同时各有一个有效大文件时，二者inode保持、不重复传输，最终全部fixture字节一致。[独立测试](../scripts/test_independent_download_cache.py)、[日志](../logs/independent_download_cache_probes.log)

fixture通过loopback HTTP提供惰性bytes，urllib的外部目标被拦截映射至本地；没有访问真实HF对象或重新下载8.37GB。生产helper实现按文件no-clobber发布、manifest最后，不再错误宣称能把staging原子替换非空目录。失败可能留下私有`.partial`或已验证的部分文件，以便诊断/续跑；这不是全周目录事务。已有不匹配文件需要人工决定清理或换私有目标，不会静默“修好”它来改变证据。

## 导出安全的覆盖与边界

晚secret、晚missing、traversal、大文件、NUL/binary、非UTF8、错误allowlist类型、source/destination祖先和叶symlink、run path逃逸、把manifest列作输入等拒绝场景都检查了**整个临时source/public树的目录与bytes hash**，而非只检查返回值。包括target本来不存在的情况，拒绝后不能创建target。正常导出检查manifest实际hash与内容一致，sanitize只修改公开副本，原证据不变；成功后只允许回写再生source receipt。

独立复核还发现原word-boundary会漏掉underscore分隔的token。owner已改为alnum边界并增加文件名/正文两项，最终17项通过。测试marker仅运行时拼接并保留在TemporaryDirectory，不写入源码常量或日志；错误不回显敏感文件名。

两个独立probe进一步确认：敏感文件名被拒绝时无内容披露且两树不变；成功批次所有普通文件先发布，public manifest是最后一个replace，然后才更新source receipt，二者bytes一致。[独立测试](../scripts/test_independent_export_boundaries.py)、[最终19项日志](../logs/independent_export_final_tests.log)

这些结论只承诺**批量预检/扫描拒绝时不写public**。发布阶段采用每文件原子replace，不是覆盖全部I/O异常、进程中断或并发export的filesystem transaction；代码和说明均保留这个界限。模式扫描也不是所有敏感数据均可识别的证明。没有在权威public tree实际调用导出器做本次验收，所有导出行为均在可删除临时树内。

## 复核器状态的覆盖与边界

公开默认测试复制现有公开聚合/CSV/log；因为完整CLI numbers原本未公开，明确构造仅含`dataset.trace_summary`的最小**synthetic**对象。它只测试状态与退出码，不替代真实figure output或检验论文数值。显式私有evidence override另有owner保存的检查记录，与公开夹具分开。

11项回归覆盖正常28项base checks、request count mismatch、manifest boolean mismatch、多失败累积、optional complete-week在root/week/count层失败、缺失/损坏JSON/错误结构，以及“已确认论文差异不等于内部一致性检查失败”。这种区分保留原科学含义，不会为了让reviewer通过而抹掉Table6等差异。

独立5项再覆盖：nested check实际Failed但保存计数仍零；Unknown与Partially Verified正确非零；NaN常量拒绝后保存Failed；合法JSON的`1e309`数值溢成Inf时也持久化strict JSON Failed并标注无法保留的partial values。5项均符合期望，公开默认日志明确`minimal_synthetic_numbers_fixture=true`。[probe源码](../scripts/independent_review_status_probes.py)、[实际结果](../logs/independent_review_status_public_probes.log)

状态保证只针对所列输入与可写输出位置。若输出本身无法写入，工具会非零并报告persist错误，不能保证在不可写位置生成报告。原始论文数据、历史部署、标签准确率与缓存/网络实验是否成立仍由旧报告限定；本修复没有把它们从Unknown提升。

## 原归档保全

初始旧run有206个文件。用户/根代理允许改4个existing脚本、README、metadata和publication manifest共7项，另新增shared helper。其余**199个文件逐SHA检查一致，包括82个历史log**；唯一旧run新增文件是声明的helper，没有旁生数据或测试缓存。[保全记录](independent_archive_preservation.json)

metadata独立投影比较确认：原有所有key/value未改、未删，仅增加`historical_artifact_hash_scope`、`post_review_revisions`两项。原T0、结束时间、科学状态与artifact记录不变。旧README新增干净**私有副本**工作流、selected不是完整周的说明及本reviewrun链接，并明确不提高复现等级。manifest会按修订脚本刷新，它是当前发布收据，不覆盖历史科学log的hash证据。

## 原版失败与后续归档

原版失败日志已检查：download初始10项为9失败/1通过；export扩展17项为15失败/2通过；公开reviewer11项为9失败/2通过。修复后均通过相应集合，未删除初版/中间日志。源码与日志SHA进入机器可读记录，不把source或fixture变更后的结果指称为更早版本运行。

最后提交、manifest刷新、PR评论回复和远端SHA验证由根代理负责。本独立审查不声称已推送或关闭PR，也不修改其他owner代码。
