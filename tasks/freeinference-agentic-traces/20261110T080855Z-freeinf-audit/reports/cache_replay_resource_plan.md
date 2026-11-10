# Cache replay 资源计划（只读估计）

原版16周完整独立cache不应以30–45分钟可完成为预期。已经实际完成的最小周（Jun7）含42,080,519个block读取，单worker8GiB地址空间guard共110.29秒；按全量block数量粗线性外推约 **9.33小时**。这不是全量实测预测区间，排序/merge与多scope还可能增加工作量。

已只读全部Parquet footer，没有下载或读取block值。16周共130 rowgroups、12,820,652,493个非null block值；纯int64解码102.565GB，Parquet编码解压97.141GB、压缩8.308GB。两者口径不同，不能把1.82GB压缩Aug30当内存需求。

官方每个scope启动64个partition任务，而每个partition都重新扫描完整周所有rowgroup后才做scope/mod64筛选。最低一scope的全量扫描相当于6.217TB编码解码工作，OS页缓存不能消除重复解码和数组操作。

最大rowgroup在Aug30：204,994,546值，仅int64约1.640GB；np.repeat request int32约0.820GB、mod int64约1.640GB，另有Arrow拷贝/masks/保留partition数组/排序和Pandas merge。这些是组件尺寸，**不是已测峰值**。建议仍1 worker、1 week串行，勿同时跑多个大块任务。

当前free9,181,081,600B，保5GiB后scratch上限3,812,372,480B。Aug30整周原始(id64,request32)约30.2GB，因此全周/全量预分区落盘不可行。可研究每pass2–4 partitions、限2.5GB临时spool、校验成功后只删除自建spool：4 partitions均匀估计1.888GB，但热block频率偏斜Unknown，必须动态限盘。该优化尚未实现或运行，须先对已重算小周全52 policy/TTL格及misses/totals做等价验证，且保持顺序、scope、mod64和week起始空cache，独立标注优化执行。

预算内更可靠的动作是追加完整小周（May31/May17/May24等），每周实际比较并保存；不能把若干小周当16周论文总体仿真。完整数字、来源和逐周大小见 [cache_replay_resource_plan.json](cache_replay_resource_plan.json)。
