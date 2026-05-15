# Windows + 非 ASCII 路径(中文目录名)—— 用 `--config` 模式

主 SKILL.md 简单 case 直通车里有钩子:Windows + 中文路径报错时打开本文件。

## Contents

- [为什么需要 `--config`](#为什么需要-config)
- [`--config` JSON 写法](#config-json-写法)
- [何时切到 --config 模式](#何时切到-config-模式)
- [Mac / Linux 也可以用,完全等价](#mac--linux-也可以用完全等价)

## 为什么需要 `--config`

Windows 默认代码页是 cp936/GBK,不是 UTF-8。当你 spawn 子进程把中文路径作为命令行参数传给 Python 时,中间这一层经常会把中文字静默替换成 `?`,Python 收到的就是坏路径(`C:\TR\????\??\X.xlsx`),开文件会报 `OSError: [Errno 22] Invalid argument`。这是 Windows + 非 ASCII argv 的经典坑,Python 里面没法挽回。

**正确做法:用 `--config FILE` 模式,把所有参数(包括路径)写在 UTF-8 JSON 文件里,绕开 argv 编码**。

## `--config` JSON 写法

四个脚本(inspect / patch_xlsx / diff / validate_refs)都支持 `--config`。**规则**:

1. 在一个 **纯 ASCII 路径**(如 `C:\Temp\`、skill 自身目录、系统 temp 目录)下写一个 UTF-8 JSON,key 用 argparse 的 dest 名(下划线、不带 `--`):

   ```json
   {
     "root": "C:\\TR\\配置表\\装备",
     "field_row": 2,
     "meta_rows": [1, 3, 4],
     "output": "C:\\TR\\配置表\\装备\\inventory.md",
     "patch_template": "C:\\Temp\\patch.json",
     "format": "md"
   }
   ```

2. 用纯 ASCII 路径调用脚本,其他参数全在 JSON 里:

   ```bash
   python3 scripts/inspect_config_tables.py --config C:\Temp\inspect_config.json
   ```

3. patch_xlsx / diff / validate_refs 同理。

## 何时切到 --config 模式

- 用户的配置路径里含中文、日文、韩文等任何非 ASCII 字符
- 你在 Windows 上,不确定终端是 cp936 还是 UTF-8
- 脚本报 `路径里检测到 '?' 字符` 错误时

脚本会 **自动检测路径里有 `?` 字符**(典型的 cp936 替换痕迹),直接报清晰错误告诉你切到 `--config`。

## Mac / Linux 也可以用,完全等价

Mac / Linux 默认 UTF-8,中文路径直接走 argv 也没问题,不强制用 `--config` 模式 —— 但用了也行,完全等价。
