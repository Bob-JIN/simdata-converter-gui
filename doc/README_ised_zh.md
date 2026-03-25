# .ised 格式文件数据结构与解析说明文档

## 1. 文件格式概述
.ised是CB2016恒星种群合成模型使用的二进制未格式化文件格式，存储不同年龄、不同金属丰度下的恒星光谱数据，支持两种模型类型：
- 仅恒星光谱模型（isedfiles_stars/目录）
- 恒星+气体发射线模型（isedfiles_stars+gas/目录）

文件采用Fortran未格式化二进制存储，每个读写操作前包含记录长度标记，便于顺序读取。

## 2. 字节序说明
- 字节序：与生成文件的系统原生字节序一致，通常为小端序（x86/x64架构）
- 数据类型：Fortran默认数据类型，Integer为4字节，Real为4字节单精度浮点数

## 3. 详细数据结构说明

### 通用文件头结构
| 偏移量 | 字段名称 | 数据类型 | 长度 | 说明 |
|--------|----------|----------|------|------|
| 0x00   | 记录长度标记 | Integer | 4字节 | 时间步数组记录总长度 = (1 + nsteps) * 4 字节 |
| 0x04   | nsteps | Integer | 4字节 | 时间步数量，固定为221 |
| 0x08   | tb数组 | Real[nsteps] | nsteps*4字节 | 各时间步对应的年龄值（单位：年） |
| 0x08 + nsteps*4 | 记录结束标记 | Integer | 4字节 | 同记录长度标记 |
| | | | |
| 下一记录开始 | 记录长度标记 | Integer | 4字节 | 波长数组记录总长度 = (1 + inws) * 4 字节 |
| +0x04 | inws | Integer | 4字节 | 波长点数量：<br>- 纯恒星模型：13216<br>- 恒星+气体模型：13391 |
| +0x08 | ws数组 | Real[inws] | inws*4字节 | 波长数组，单位：埃（Å） |
| +0x08 + inws*4 | 记录结束标记 | Integer | 4字节 | 同记录长度标记 |

### 光谱数据块结构
文件头后连续存储nsteps个时间步的光谱数据，每个时间步结构如下：
| 偏移量 | 字段名称 | 数据类型 | 长度 | 说明 |
|--------|----------|----------|------|------|
| 0x00 | 记录长度标记 | Integer | 4字节 | 当前时间步光谱记录总长度 = (1 + inws) * 4 字节 |
| 0x04 | 预留字段 | Integer | 4字节 | 未使用，通常等于inws |
| 0x08 | fs数组 | Real[inws] | inws*4字节 | 当前时间步的光谱通量数据 |
| 0x08 + inws*4 | 记录结束标记 | Integer | 4字节 | 同记录长度标记 |

## 4. 关键字段解释
- **tb(n)**：第n个时间步对应的恒星种群年龄，范围从0年到140亿年
- **ws(i)**：第i个波长点的波长值，单位为埃（Å）
- **fs(i,n)**：第n个时间步、第i个波长点的光谱通量，单位：erg/s/Å/M☉
- **nsteps**：时间步总数，所有模型统一为221个
- **inws**：波长点数量，根据模型类型不同为13216或13391

## 5. 数据块组织方式
```
+-------------------+
| 时间步数组记录     |
+-------------------+
| 波长数组记录       |
+-------------------+
| 时间步1光谱数据    |
+-------------------+
| 时间步2光谱数据    |
+-------------------+
| ...               |
+-------------------+
| 时间步221光谱数据  |
+-------------------+
```

## 6. 解析注意事项和潜在问题
1. **Fortran记录标记处理**：每个读写记录前后都有4字节的记录长度标记，读取时需要跳过这些标记，否则会导致数据偏移
2. **模型类型识别**：需要通过第一次读取的inws值判断模型类型，进而确定后续数据块的大小
3. **字节序兼容性**：如果文件在不同字节序的系统间迁移，需要进行字节序转换
4. **数据精度**：原始数据为单精度浮点数，转换为HDF5时建议保留为单精度以节省空间
5. **时间步索引对应关系**：
   - 索引1：0年
   - 索引35：1 Myr
   - 索引55：3 Myr
   - 索引90：10 Myr
   - 索引136：100 Myr
   - 索引150：500 Myr

## 7. 推荐的解析方法或工具

### Python解析方案
```python
import struct
import numpy as np

def read_ised_file(filepath):
    with open(filepath, 'rb') as f:
        # 读取时间步数组
        rec_len = struct.unpack('<i', f.read(4))[0]
        nsteps = struct.unpack('<i', f.read(4))[0]
        tb = np.frombuffer(f.read(nsteps * 4), dtype='<f4')
        struct.unpack('<i', f.read(4))  # 跳过结束标记
        
        # 读取波长数组
        rec_len = struct.unpack('<i', f.read(4))[0]
        inws = struct.unpack('<i', f.read(4))[0]
        ws = np.frombuffer(f.read(inws * 4), dtype='<f4')
        struct.unpack('<i', f.read(4))  # 跳过结束标记
        
        # 读取所有时间步的光谱数据
        fs = np.zeros((inws, nsteps), dtype='<f4')
        for n in range(nsteps):
            rec_len = struct.unpack('<i', f.read(4))[0]
            struct.unpack('<i', f.read(4))  # 跳过预留字段
            fs[:, n] = np.frombuffer(f.read(inws * 4), dtype='<f4')
            struct.unpack('<i', f.read(4))  # 跳过结束标记
    
    return tb, ws, fs
```

### 转换为HDF5方案
使用h5py库将解析后的数据写入HDF5文件：
```python
import h5py

def convert_to_hdf5(input_path, output_path):
    tb, ws, fs = read_ised_file(input_path)
    
    with h5py.File(output_path, 'w') as hf:
        hf.create_dataset('time_steps', data=tb, compression='gzip')
        hf.create_dataset('wavelengths', data=ws, compression='gzip')
        hf.create_dataset('flux', data=fs, compression='gzip')
        
        # 添加属性
        hf.attrs['model_type'] = 'stars_only' if len(ws) == 13216 else 'stars+gas'
        hf.attrs['n_time_steps'] = len(tb)
        hf.attrs['n_wavelength_points'] = len(ws)
        hf.attrs['wavelength_unit'] = 'Angstrom'
        hf.attrs['flux_unit'] = 'erg/s/Å/M☉'
        hf.attrs['time_unit'] = 'year'
```

## 8. 模型参数说明
从文件名可以提取模型参数：
- zXXX：金属丰度，例如z004表示Z=0.004
- uXpX：电离参数log Us，例如u3p5表示log Us=-3.5
- xiX：尘埃参数xi_d
- nX：氢原子数密度n_H，单位：cm⁻³
- mupXXX：上限质量，单位：M☉
- CXXX：C/O相对太阳丰度比，单位：%
- _noLya：不包含Lyman-alpha发射线的版本
