# 数据、运行、评测与展示登记

本目录用于需要追溯来源的任务。四张表初始为空，不表示已有运行或验证；普通代码编辑无需创建虚构实验。

| 文件 | 每条记录必需字段 |
|---|---|
| [datasets.json](datasets.json) | id、title、source、evidence、status |
| [runs.json](runs.json) | id、title、dataset_ids、kind、output_uri、code、config、evidence、status |
| [evaluations.json](evaluations.json) | id、title、run_ids、definition、output_uri、evaluator、evidence、status |
| [sites.json](sites.json) | id、title、run_ids、evaluation_ids、output_uri、evidence、status |

每个文件的schema为 `project_maintenance_v1`，records为列表。ID全局唯一，不能使用同一个ID代表不同输入、代码或评测口径。status使用planned/running/completed/failed/interrupted/paused。

- dataset_ids引用数据记录，run_ids引用运行记录，evaluation_ids引用评测记录。
- 可选parent_run_ids说明复用/恢复关系，必须引用运行记录且不能形成循环。
- 展示若引用评测，其run_ids应包含该评测关联的运行；只展示子集时另建子集选择记录，说明复用关系。
- output_uri记录真实的本地输出位置或明确的存储URI；自检不访问该位置，也不证明服务在线。
- evidence为非空列表，每项包含path和sha256。path相对项目根目录，指向可进入Git的实际轻量来源文件；单个证据不超过8 MiB，不能指向本地实验数据或通过上级路径逃出项目。
- external_evidence可记录外部原始数据的URI与哈希，但自检不下载或核验这些数据。
- 可选limitations明确缺失证据、未核验内容或适用范围。缺失与未知不是零。

示例仅解释结构，填写真实来源后才能登记：

```json
{
  "id": "run-example-v1",
  "title": "真实任务名称",
  "dataset_ids": [],
  "kind": "实际运行类型",
  "output_uri": "实际本地路径或存储URI",
  "code": {"commit": null, "dirty": null, "snapshot": "实际来源说明"},
  "config": {"实际有效参数": "实际值"},
  "evidence": [{"path": "docs/provenance/实际任务/manifest.json", "sha256": "替换为实际64位SHA256"}],
  "status": "planned",
  "limitations": []
}
```

修改后运行 `python3 scripts/validate_records.py`。检查覆盖格式、关联、轻量证据和相对文档链接，不验证实验正确性、外部输出、服务在线状态或密钥内容。
