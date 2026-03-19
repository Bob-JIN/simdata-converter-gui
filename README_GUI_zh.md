# ISED Converter GUI 使用说明

## 概述

ISED Converter GUI 是一个用于转换 CB2016 恒星种群合成模型 .ised 格式文件的图形界面工具。

## 功能特性

- 文件选择和批量处理
- 支持转换为 HDF5、Parquet 和 NumPy 格式
- 多语言支持（中文/英文/法文）
- 光谱数据可视化
- 实时进度显示
- 详细的操作日志
- 完善的错误处理

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行程序

```bash
python ised_gui.py
```

## 使用说明

### 转换功能

1. **选择输入文件**
   - 点击"选择文件"按钮选择单个或多个 .ised 文件
   - 或点击"选择文件夹"按钮选择包含多个 .ised 文件的文件夹

2. **选择输出目录**
   - 点击"选择输出目录"按钮指定输出文件保存位置

3. **选择输出格式**
   - 勾选需要的输出格式（HDF5、Parquet、NumPy）

4. **开始转换**
   - 点击"转换"按钮开始转换
   - 进度条显示转换进度
   - 日志区域显示详细操作信息

### 可视化功能

1. **加载文件**
   - 切换到"可视化"标签页
   - 点击"加载文件"按钮选择 .ised 文件

2. **查看光谱**
   - 使用时间步选择器查看不同演化阶段的光谱
   - 使用工具栏进行缩放、平移等操作

### 语言切换

- 在菜单栏选择"语言"，然后选择所需语言（中文/English/Français）

## 文件结构

```
d:\260318_Michaela\
├── ised_gui.py              # 主程序文件
├── requirements.txt          # 依赖库列表
├── README_GUI.md            # 本文件
├── Michaela_files/
│   └── cb2016_models/
│       ├── ised_converter.py   # 转换核心模块
│       └── isedfiles_stars/    # 示例数据文件
└── back/                   # 备份文件
```

## 日志文件

程序运行日志保存在：`~/.ised_converter/log_YYYYMMDD.log`

## 故障排除

### 问题：缺少依赖库

**解决方案：**
```bash
pip install -r requirements.txt
```

### 问题：Matplotlib 不可用

**解决方案：**
```bash
pip install matplotlib
```

### 问题：转换失败

**解决方案：**
- 检查输入文件是否为有效的 .ised 格式
- 检查输出目录是否有写入权限
- 查看日志窗口的详细错误信息

## 技术支持

如有问题，请查看日志文件获取详细错误信息。

## 许可证

本工具仅供学术研究使用。
