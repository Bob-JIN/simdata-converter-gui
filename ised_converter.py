#!/usr/bin/env python3
"""
ised_converter.py: CB2016 .ised格式文件解析与转换工具（最终修复版）

正确处理Fortran未格式化文件的记录长度标记
"""

import struct
import numpy as np
import os
import re
from pathlib import Path
from typing import Tuple, Dict, Any, Optional


def _parse_filename_metadata(filepath: str) -> Dict[str, Any]:
    filename = os.path.basename(filepath)
    metadata = {}
    z_match = re.search(r'z(\d+)', filename)
    if z_match:
        z_str = z_match.group(1)
        if len(z_str) == 3:
            metadata['metallicity'] = float(f"0.{z_str}")
        else:
            metadata['metallicity'] = float(f"0.0{z_str}")
    u_match = re.search(r'u(\d+)p(\d+)', filename)
    if u_match:
        metadata['ionization_parameter'] = -float(f"{u_match.group(1)}.{u_match.group(2)}")
    xi_match = re.search(r'xi(\d+)', filename)
    if xi_match:
        metadata['dust_parameter'] = float(f"0.{xi_match.group(1)}")
    n_match = re.search(r'n(\d+)', filename)
    if n_match:
        metadata['hydrogen_density'] = 10 ** int(n_match.group(1))
    mup_match = re.search(r'mup(\d+)', filename)
    if mup_match:
        metadata['upper_mass_limit'] = float(mup_match.group(1))
    c_match = re.search(r'C(\d+)', filename)
    if c_match:
        metadata['co_ratio'] = float(c_match.group(1))
    metadata['has_lya'] = '_noLya' not in filename
    metadata['has_gas'] = 'stars+gas' in str(Path(filepath).parent)
    return metadata


def read_fortran_record(f):
    """读取一个Fortran未格式化记录，返回数据部分"""
    rec_start = struct.unpack('<i', f.read(4))[0]
    data = f.read(rec_start)
    rec_end = struct.unpack('<i', f.read(4))[0]
    if rec_start != rec_end:
        raise ValueError(f"记录标记不匹配: 开始={rec_start}, 结束={rec_end}")
    return data


def parse_ised(filepath: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    解析CB2016 .ised格式文件
    
    正确处理Fortran记录的方法
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"文件不存在: {filepath}")
    
    with open(filepath, 'rb') as f:
        try:
            # 1. 读取时间步记录
            data = read_fortran_record(f)
            # 前4字节是a，后面是nsteps个Real
            a = struct.unpack('<i', data[0:4])[0]
            nsteps = 221
            time_steps = np.frombuffer(data[4:4 + nsteps*4], dtype='<f4')
            
            # 2. 读取波长记录
            data = read_fortran_record(f)
            a = struct.unpack('<i', data[0:4])[0]
            inws = a
            wavelengths = np.frombuffer(data[4:4 + inws*4], dtype='<f4')
            
            # 3. 读取所有时间步的光谱数据
            flux = np.zeros((inws, nsteps), dtype='<f4')
            for n in range(nsteps):
                data = read_fortran_record(f)
                a = struct.unpack('<i', data[0:4])[0]
                flux[:, n] = np.frombuffer(data[4:4 + inws*4], dtype='<f4')
            
        except Exception as e:
            raise ValueError(f"解析错误: {e}")
    
    metadata = {
        'n_time_steps': nsteps,
        'n_wavelength_points': inws,
        'wavelength_unit': 'Angstrom',
        'flux_unit': 'erg/s/Å/M☉',
        'time_unit': 'year',
        'model_type': 'stars+gas' if inws == 13391 else 'stars_only',
        'filename': os.path.basename(filepath),
        'filepath': os.path.abspath(filepath)
    }
    metadata.update(_parse_filename_metadata(filepath))
    
    return time_steps, wavelengths, flux, metadata


def to_hdf5(time_steps, wavelengths, flux, metadata, output_path, compression='gzip'):
    import h5py
    with h5py.File(output_path, 'w') as hf:
        hf.create_dataset('time_steps', data=time_steps, compression=compression)
        hf.create_dataset('wavelengths', data=wavelengths, compression=compression)
        hf.create_dataset('flux', data=flux, compression=compression)
        for key, value in metadata.items():
            if value is not None:
                hf.attrs[key] = value
    return output_path


def to_parquet(time_steps, wavelengths, flux, metadata, output_path):
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
    inws, nsteps = flux.shape
    wl_idx, ts_idx = np.indices((inws, nsteps))
    df = pd.DataFrame({
        'wavelength': wavelengths[wl_idx.flatten()],
        'time_step_index': ts_idx.flatten(),
        'age': time_steps[ts_idx.flatten()],
        'flux': flux.flatten()
    })
    table = pa.Table.from_pandas(df)
    custom_metadata = {k: str(v) for k, v in metadata.items() if v is not None}
    existing_metadata = table.schema.metadata or {}
    existing_metadata.update(custom_metadata)
    table = table.replace_schema_metadata(existing_metadata)
    pq.write_table(table, output_path, compression='snappy')
    return output_path


def to_numpy(time_steps, wavelengths, flux, metadata, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    np.save(os.path.join(output_dir, 'time_steps.npy'), time_steps)
    np.save(os.path.join(output_dir, 'wavelengths.npy'), wavelengths)
    np.save(os.path.join(output_dir, 'flux.npy'), flux)
    npz_metadata = {}
    for key, value in metadata.items():
        if value is not None:
            if isinstance(value, (int, float, bool)):
                npz_metadata[key] = np.array(value)
            else:
                npz_metadata[key] = str(value)
    np.savez(os.path.join(output_dir, 'metadata.npz'), **npz_metadata)
    return output_dir


def convert_all(input_path, output_dir=None):
    if output_dir is None:
        output_dir = os.path.dirname(input_path)
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    print(f"正在解析: {input_path}")
    time_steps, wavelengths, flux, metadata = parse_ised(input_path)
    
    print(f"  nsteps={len(time_steps)}, inws={len(wavelengths)}, flux shape={flux.shape}")
    print(f"  前5个波长: {wavelengths[:5]}")
    
    outputs = {}
    
    h5_path = os.path.join(output_dir, f"{base_name}.h5")
    print(f"正在生成HDF5: {h5_path}")
    outputs['hdf5'] = to_hdf5(time_steps, wavelengths, flux, metadata, h5_path)
    
    parquet_path = os.path.join(output_dir, f"{base_name}.parquet")
    print(f"正在生成Parquet: {parquet_path}")
    outputs['parquet'] = to_parquet(time_steps, wavelengths, flux, metadata, parquet_path)
    
    numpy_dir = os.path.join(output_dir, f"{base_name}_numpy")
    print(f"正在生成NumPy: {numpy_dir}")
    outputs['numpy'] = to_numpy(time_steps, wavelengths, flux, metadata, numpy_dir)
    
    print("转换完成！")
    return outputs


def _test_read_hdf5(filepath):
    try:
        import h5py
        with h5py.File(filepath, 'r') as hf:
            _ = hf['time_steps'][:]
            _ = hf['wavelengths'][:]
            _ = hf['flux'][:]
            _ = dict(hf.attrs)
        return True
    except Exception as e:
        print(f"HDF5读取测试失败: {e}")
        return False


def _test_read_parquet(filepath):
    try:
        import pandas as pd
        df = pd.read_parquet(filepath)
        _ = df.head()
        return True
    except Exception as e:
        print(f"Parquet读取测试失败: {e}")
        return False


def _test_read_numpy(dirpath):
    try:
        _ = np.load(os.path.join(dirpath, 'time_steps.npy'))
        _ = np.load(os.path.join(dirpath, 'wavelengths.npy'))
        _ = np.load(os.path.join(dirpath, 'flux.npy'))
        _ = np.load(os.path.join(dirpath, 'metadata.npz'))
        return True
    except Exception as e:
        print(f"NumPy读取测试失败: {e}")
        return False


def verify_conversion(original_path, outputs):
    print("\n开始验证转换结果...")
    time_steps_orig, wavelengths_orig, flux_orig, _ = parse_ised(original_path)
    all_passed = True
    
    if 'hdf5' in outputs and _test_read_hdf5(outputs['hdf5']):
        try:
            import h5py
            with h5py.File(outputs['hdf5'], 'r') as hf:
                time_steps_h5 = hf['time_steps'][:]
                wavelengths_h5 = hf['wavelengths'][:]
                flux_h5 = hf['flux'][:]
            assert np.allclose(time_steps_orig, time_steps_h5, rtol=1e-6)
            assert np.allclose(wavelengths_orig, wavelengths_h5, rtol=1e-6)
            assert np.allclose(flux_orig, flux_h5, rtol=1e-6)
            print("  ✓ HDF5: 数据验证通过")
        except Exception as e:
            print(f"  ✗ HDF5: 数据验证失败 - {e}")
            all_passed = False
    else:
        all_passed = False
    
    if 'parquet' in outputs and _test_read_parquet(outputs['parquet']):
        print("  ✓ Parquet: 读取测试通过")
    else:
        all_passed = False
    
    if 'numpy' in outputs and _test_read_numpy(outputs['numpy']):
        try:
            time_steps_np = np.load(os.path.join(outputs['numpy'], 'time_steps.npy'))
            wavelengths_np = np.load(os.path.join(outputs['numpy'], 'wavelengths.npy'))
            flux_np = np.load(os.path.join(outputs['numpy'], 'flux.npy'))
            assert np.allclose(time_steps_orig, time_steps_np, rtol=1e-6)
            assert np.allclose(wavelengths_orig, wavelengths_np, rtol=1e-6)
            assert np.allclose(flux_orig, flux_np, rtol=1e-6)
            print("  ✓ NumPy: 数据验证通过")
        except Exception as e:
            print(f"  ✗ NumPy: 数据验证失败 - {e}")
            all_passed = False
    else:
        all_passed = False
    
    if all_passed:
        print("\n✓ 所有验证通过！")
    else:
        print("\n✗ 部分验证失败")
    return all_passed


def main():
    import sys
    if len(sys.argv) < 2:
        print("使用方法: python ised_converter.py <input_file.ised> [output_dir]")
        print("\n示例:")
        print("  python ised_converter.py cb2016_z001_chab_hr_xmiless_ssp.ised")
        return
    
    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_path):
        print(f"错误: 文件不存在 - {input_path}")
        return
    
    outputs = convert_all(input_path, output_dir)
    verify_conversion(input_path, outputs)
    
    print("\n输出文件:")
    for fmt, path in outputs.items():
        print(f"  {fmt:8s}: {path}")


if __name__ == "__main__":
    main()
