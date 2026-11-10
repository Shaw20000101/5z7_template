# 项目维护模板

面向人与AI协作的通用项目骨架：规定如何找入口、接续任务、维护文档、记录运行、验证结果和保存Git版本。适用于开发和实验项目，不包含特定算法、数据或业务代码。

## 开始使用

将本目录的**内容**复制到一个新建的空项目目录，或把本目录作为GitHub仓库根目录上传。保留隐藏文件 `.gitignore`；不要把上层项目、实验目录或 `.git/` 一起上传。

1. 先读 [AGENTS.md](AGENTS.md)，这是每次工作的默认约定。
2. 填写 [TASKMEMORY.md](TASKMEMORY.md) 中的目标、范围与下一步。
3. 在 [项目导航](docs/PROJECT_MAP.md) 补充实际代码、运行和结果入口；源码沿用自己的目录，不强制重排。
4. 在 [复现说明](docs/REPRODUCTION.md) 填写真实环境和已验证命令。
5. 运行 `python3 scripts/validate_records.py`，检查文档链接、登记关联和Git排除规则。脚本仅使用Python标准库，不运行实验，不初始化Git。

模板里的“未配置”“未验证”和空登记表都是待填写状态，不能当作实际完成记录。

## 目录

```text
project/
├── README.md
├── AGENTS.md
├── TASKMEMORY.md
├── .gitignore
├── scripts/
│   ├── README.md
│   └── validate_records.py
├── docs/
│   ├── README.md
│   ├── PROJECT_MAP.md
│   ├── PROJECT_MEMORY.md
│   ├── REPRODUCTION.md
│   ├── RECORD_SPEC.md
│   ├── GIT_WORKFLOW.md
│   ├── RESPONSE_STYLE.md
│   ├── design/README.md
│   ├── reports/README.md
│   ├── provenance/README.md
│   ├── archive/README.md
│   ├── templates/
│   │   ├── REPORT.md
│   │   ├── PLAN.json
│   │   ├── EXECUTION.json
│   │   └── RECEIPT.json
│   └── registry/
│       ├── README.md
│       ├── datasets.json
│       ├── runs.json
│       ├── evaluations.json
│       └── sites.json
└── generated_artifacts/
    └── README.md
```

## 维护原则

- README提供入口，AGENTS规定工作方式；TASKMEMORY记录当前任务，PROJECT_MEMORY只记录跨任务有效的决定。
- docs/README按类别索引，PROJECT_MAP按问题导航，scripts/README按可执行入口导航；详细过程放专题报告，以链接关联。
- 完成代码、运行或实验后，主动维护对应索引、记忆和必要证据；失败和中断也要记录，不能只保存成功。
- Git保存代码、文档、可公开的配置示例与轻量来源记录。实验数据、权重、逐样本输出和运行产物不进入Git。
- 功能完成、检查通过且达到预期后，主动询问用户是否保存本地Git版本。提交与推送分别授权，已有明确授权不重复询问。
- 回答先给简短结论，再将详细解释放在可展开的说明中；客户端不支持折叠时，提供简答和详情文档链接。

具体约定见 [Git工作流](docs/GIT_WORKFLOW.md)、[回复样式](docs/RESPONSE_STYLE.md) 和 [记录规范](docs/RECORD_SPEC.md)。
