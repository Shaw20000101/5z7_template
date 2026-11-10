# 脚本入口索引

| 脚本 | 用途 | 输入 | 输出与限制 |
|---|---|---|---|
| [validate_records.py](validate_records.py) | 维护结构、链接、登记和Git排除自检 | 项目目录；默认本脚本所在项目根目录 | JSON检查结果到标准输出；退出0为通过，1为失败；只读，不运行实验 |

```bash
python3 scripts/validate_records.py
python3 scripts/validate_records.py --root /path/to/project
```

仅要求Python 3.9+标准库。与Git有关的检查需要已安装Git；Git不可用时明确显示未执行，不把它报成通过。项目本身无需先初始化Git。

新增脚本时在本页登记：用途、实际输入、输出位置、最小命令、依赖、资源需求、是否修改已有数据、验证级别和限制。示例命令不当作已经执行的证据。

不要创建没有实际功能的运行/评测占位脚本。真正可运行的入口放在此目录，设计与结论放入 [文档](../docs/README.md)，运行产物留在本地。
