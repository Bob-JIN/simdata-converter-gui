# SimData Converter GUI / 数据预处理工具

[English](#english) | [中文](#中文)

---

## English

### Overview
A graphical user interface (GUI) tool for preprocessing CB2016 stellar population synthesis model data. This tool supports converting .ised and .fits files to HDF5, Parquet, and NumPy formats, visualizing spectral data, and splitting HDF5 datasets into training/test/validation sets.

### Features
- **File Conversion**: Convert .ised and .fits files to HDF5 (.h5), Parquet, and NumPy formats
- **Data Visualization**: Visualize spectral data with interactive plotting
- **Data Splitting**: Split HDF5 files by samples into train/test/valid sets (70%/20%/10% default)
- **Multi-language Support**: Chinese, English, and French user interfaces
- **Batch Processing**: Process multiple files or entire folders at once

### Installation

#### Prerequisites
- Python 3.7+
- Git (optional, for cloning the repository)

#### Steps
1. Clone or download the repository
```bash
git clone https://github.com/Bob-JIN/simdata-converter-gui.git
cd simdata-converter-gui
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

### Usage

#### Running the Application
```bash
python main.py
```

#### Tabs / 标签页

1. **Input / 输入**
   - Select .ised or .fits files or folders
   - Choose output directory
   - Select output formats (HDF5, Parquet, NumPy)
   - Click "Convert" to start conversion

2. **Visualization / 可视化**
   - Load spectral data files
   - Interactive plotting with zoom and pan
   - Switch between wavelength and time step axes

3. **Data Split / 数据拆分**
   - Select HDF5 files or folders
   - Set random seed for reproducibility
   - Adjust train/test/valid ratios (in percentage)
   - Click "Split" to split datasets by samples
   - Output format: `{filename}_{train/test/valid}.hdf5`

### Data Formats

#### Input Formats
- **.ised**: CB2016 binary unformatted format (see [doc/README_ised_en.md](doc/README_ised_en.md))
- **.fits**: FITS format with multiple HDUs (see [doc/README_fits_en.md](doc/README_fits_en.md))

#### Output Formats
- **HDF5 (.h5)**: Hierarchical Data Format, efficient for large datasets
- **Parquet**: Columnar storage format, good for dataframes
- **NumPy**: Numpy array directory, easy for Python processing

### Project Structure
```
simdata-converter-gui/
├── main.py                  # Main entry point
├── gui.py                   # Main GUI class
├── gui_workers.py           # Background worker threads
├── ised_converter.py        # .ised file parser and converter
├── fits_converter.py        # .fits file parser and converter
├── spectrum_visualizer.py   # Spectral visualization component
├── translations.py          # Multi-language translations
├── requirements.txt         # Dependencies
├── doc/                     # Documentation
│   ├── README_ised_en.md
│   ├── README_ised_zh.md
│   ├── README_fits_en.md
│   └── README_fits_zh.md
└── .gitignore
```

### Dependencies
- numpy >= 1.20.0
- PyQt5 >= 5.15.0
- matplotlib >= 3.4.0 (optional, for visualization)
- h5py >= 3.0.0
- pandas >= 1.3.0
- pyarrow >= 5.0.0
- astropy >= 5.0.0

### License
This project is provided for educational and research purposes.

---

## 中文

### 概述
一个用于预处理 CB2016 恒星种群合成模型数据的图形界面（GUI）工具。该工具支持将 .ised 和 .fits 文件转换为 HDF5、Parquet 和 NumPy 格式，可视化光谱数据，以及将 HDF5 数据集拆分为训练/测试/验证集。

### 功能特性
- **文件转换**：将 .ised 和 .fits 文件转换为 HDF5 (.h5)、Parquet 和 NumPy 格式
- **数据可视化**：通过交互式绘图可视化光谱数据
- **数据拆分**：按样本将 HDF5 文件拆分为训练/测试/验证集（默认 70%/20%/10%）
- **多语言支持**：中文、英文和法语用户界面
- **批量处理**：一次处理多个文件或整个文件夹

### 安装

#### 前置要求
- Python 3.7+
- Git（可选，用于克隆仓库）

#### 安装步骤
1. 克隆或下载仓库
```bash
git clone https://github.com/Bob-JIN/simdata-converter-gui.git
cd simdata-converter-gui
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

### 使用方法

#### 运行应用
```bash
python main.py
```

#### 标签页

1. **输入**
   - 选择 .ised 或 .fits 文件或文件夹
   - 选择输出目录
   - 选择输出格式（HDF5、Parquet、NumPy）
   - 点击"转换"开始转换

2. **可视化**
   - 加载光谱数据文件
   - 支持缩放和平移的交互式绘图
   - 在波长轴和时间步轴之间切换

3. **数据拆分**
   - 选择 HDF5 文件或文件夹
   - 设置随机种子以确保可复现性
   - 调整训练/测试/验证比例（百分比）
   - 点击"拆分"按样本拆分数据集
   - 输出格式：`{文件名}_{train/test/valid}.hdf5`

### 数据格式

#### 输入格式
- **.ised**：CB2016 二进制未格式化格式（参见 [doc/README_ised_zh.md](doc/README_ised_zh.md)）
- **.fits**：包含多个 HDU 的 FITS 格式（参见 [doc/README_fits_zh.md](doc/README_fits_zh.md)）

#### 输出格式
- **HDF5 (.h5)**：分层数据格式，适用于大型数据集
- **Parquet**：列式存储格式，适合数据框
- **NumPy**：NumPy 数组目录，便于 Python 处理

### 项目结构
```
simdata-converter-gui/
├── main.py                  # 主程序入口
├── gui.py                   # 主 GUI 类
├── gui_workers.py           # 后台工作线程
├── ised_converter.py        # .ised 文件解析器和转换器
├── fits_converter.py        # .fits 文件解析器和转换器
├── spectrum_visualizer.py   # 光谱可视化组件
├── translations.py          # 多语言翻译
├── requirements.txt         # 依赖库
├── doc/                     # 文档
│   ├── README_ised_en.md
│   ├── README_ised_zh.md
│   ├── README_fits_en.md
│   └── README_fits_zh.md
└── .gitignore
```

### 依赖库
- numpy >= 1.20.0
- PyQt5 >= 5.15.0
- matplotlib >= 3.4.0（可选，用于可视化）
- h5py >= 3.0.0
- pandas >= 1.3.0
- pyarrow >= 5.0.0
- astropy >= 5.0.0

### 许可证
本项目仅供教学和研究目的使用。
