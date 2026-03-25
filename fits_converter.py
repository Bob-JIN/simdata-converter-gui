#!/usr/bin/env python3
"""
fits_converter.py: .fits格式文件解析与转换工具

参考ised_converter.py的架构，正确解析CB16的fits数据格式
完整提取所有83个参数字段
"""

import numpy as np
import os
import re
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List

try:
    from astropy.io import fits
    ASTROPY_AVAILABLE = True
except ImportError:
    ASTROPY_AVAILABLE = False


def _extract_all_parameters_from_hdu(hdul, hdu_name: str, spectrum_index: Optional[int] = None) -> Dict[str, Any]:
    """
    从指定HDU中提取所有参数字段
    """
    params = {}
    if hdu_name in hdul:
        hdu = hdul[hdu_name]
        if hasattr(hdu, 'data') and hdu.data is not None and hasattr(hdu.data, 'names'):
            for field in hdu.data.names:
                data = hdu.data[field]
                if spectrum_index is not None:
                    if spectrum_index < len(data):
                        try:
                            params[field] = float(data[spectrum_index])
                        except (ValueError, TypeError):
                            params[field] = data[spectrum_index]
                else:
                    params[field] = data
    return params


def parse_fits(filepath: str, spectrum_index: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    解析.fits格式文件
    
    参数:
        filepath: fits文件路径
        spectrum_index: 选择第几个光谱（None表示返回所有光谱）
    
    返回:
        time_steps: 时间步数组（这里模拟为光谱索引）
        wavelengths: 波长数组
        flux: 流量数据 (时间步数 x 波长数)
        metadata: 元数据字典，包含所有83个参数字段
    """
    if not ASTROPY_AVAILABLE:
        raise ImportError("astropy库未安装，请运行: pip install astropy")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"文件不存在: {filepath}")
    
    with fits.open(filepath) as hdul:
        hdu_names = [hdu.name for hdu in hdul]
        
        if 'FULL SED WL' not in hdu_names or 'FULL SED' not in hdu_names:
            raise ValueError("FITS文件不包含必需的HDU: 'FULL SED WL' 和 'FULL SED'")
        
        wl_hdu = hdul['FULL SED WL']
        sed_hdu = hdul['FULL SED']
        
        wavelengths = wl_hdu.data['wl'][0]
        flux_data = sed_hdu.data
        
        num_spectra = flux_data.shape[0]
        num_wavelengths = flux_data.shape[1]
        
        if spectrum_index is not None:
            if spectrum_index < 0 or spectrum_index >= num_spectra:
                raise ValueError(f"光谱索引超出范围: {spectrum_index}, 有效范围 0-{num_spectra-1}")
            flux = flux_data[spectrum_index, :].reshape(1, -1)
            time_steps = np.array([spectrum_index], dtype=np.float32)
        else:
            flux = flux_data
            time_steps = np.arange(num_spectra, dtype=np.float32)
        
        metadata = {
            'n_time_steps': len(time_steps),
            'n_wavelength_points': num_wavelengths,
            'n_total_spectra': num_spectra,
            'wavelength_unit': 'Angstrom',
            'flux_unit': 'erg/s/A/cm2',
            'time_unit': 'spectrum_index',
            'model_type': 'CB16_star_forming',
            'filename': os.path.basename(filepath),
            'filepath': os.path.abspath(filepath)
        }
        
        param_count = 0
        
        hii_params = _extract_all_parameters_from_hdu(hdul, 'HII EMISSION', spectrum_index)
        metadata.update(hii_params)
        param_count += len(hii_params)
        
        gal_params = _extract_all_parameters_from_hdu(hdul, 'GALAXY PROPERTIES', spectrum_index)
        metadata.update(gal_params)
        param_count += len(gal_params)
        
        sf_params = _extract_all_parameters_from_hdu(hdul, 'STAR FORMATION', spectrum_index)
        metadata.update(sf_params)
        param_count += len(sf_params)
        
        sfb_params = _extract_all_parameters_from_hdu(hdul, 'STAR FORMATION BINS', spectrum_index)
        metadata.update(sfb_params)
        param_count += len(sfb_params)
        
        dust_params = _extract_all_parameters_from_hdu(hdul, 'DUST ATTENUATION', spectrum_index)
        metadata.update(dust_params)
        param_count += len(dust_params)
        
        lick_params = _extract_all_parameters_from_hdu(hdul, 'LICK SPECTRAL INDICES', spectrum_index)
        metadata.update(lick_params)
        param_count += len(lick_params)
        
        si_params = _extract_all_parameters_from_hdu(hdul, 'SPECTRAL INDICES', spectrum_index)
        metadata.update(si_params)
        param_count += len(si_params)
        
        metadata['_param_extraction_summary'] = {
            'total_parameters_extracted': param_count,
            'hdu_sources': {
                'HII EMISSION': len(hii_params),
                'GALAXY PROPERTIES': len(gal_params),
                'STAR FORMATION': len(sf_params),
                'STAR FORMATION BINS': len(sfb_params),
                'DUST ATTENUATION': len(dust_params),
                'LICK SPECTRAL INDICES': len(lick_params),
                'SPECTRAL INDICES': len(si_params)
            }
        }
    
    return time_steps, wavelengths, flux, metadata


def to_hdf5(time_steps, wavelengths, flux, metadata, output_path, compression='gzip'):
    import h5py
    with h5py.File(output_path, 'w') as hf:
        hf.create_dataset('time_steps', data=time_steps, compression=compression)
        hf.create_dataset('wavelengths', data=wavelengths, compression=compression)
        hf.create_dataset('flux', data=flux, compression=compression)
        
        for key, value in metadata.items():
            if value is not None:
                if key == '_param_extraction_summary':
                    hf.attrs[key] = str(value)
                elif isinstance(value, np.ndarray):
                    hf.create_dataset(key, data=value, compression=compression)
                elif isinstance(value, (int, float, bool, str)):
                    hf.attrs[key] = value
                else:
                    hf.attrs[key] = str(value)
    return output_path


def to_parquet(time_steps, wavelengths, flux, metadata, output_path):
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
    nsteps, inws = flux.shape
    ts_idx, wl_idx = np.indices((nsteps, inws))
    df = pd.DataFrame({
        'wavelength': wavelengths[wl_idx.flatten()],
        'time_step_index': ts_idx.flatten(),
        'age': time_steps[ts_idx.flatten()],
        'flux': flux.flatten()
    })
    table = pa.Table.from_pandas(df)
    custom_metadata = {}
    for k, v in metadata.items():
        if v is not None:
            if k == '_param_extraction_summary':
                custom_metadata[k] = str(v)
            elif isinstance(v, (int, float, bool, str)):
                custom_metadata[k] = str(v)
            elif isinstance(v, np.ndarray):
                custom_metadata[k] = f"array_shape_{v.shape}"
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
    array_params = []
    
    for key, value in metadata.items():
        if value is not None:
            if key == '_param_extraction_summary':
                npz_metadata[key] = str(value)
            elif isinstance(value, np.ndarray):
                np.save(os.path.join(output_dir, f'{key}.npy'), value)
                array_params.append(key)
            elif isinstance(value, (int, float, bool)):
                npz_metadata[key] = np.array(value)
            else:
                npz_metadata[key] = str(value)
    
    if array_params:
        npz_metadata['_array_parameters'] = np.array(array_params, dtype=str)
    
    np.savez(os.path.join(output_dir, 'metadata.npz'), **npz_metadata)
    return output_dir


def convert_all(input_path, output_dir=None, spectrum_index: Optional[int] = None):
    if output_dir is None:
        output_dir = os.path.dirname(input_path)
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    if spectrum_index is not None:
        base_name = f"{base_name}_spec{spectrum_index}"
    
    print(f"正在解析: {input_path}")
    time_steps, wavelengths, flux, metadata = parse_fits(input_path, spectrum_index)
    
    print(f"  nsteps={len(time_steps)}, inws={len(wavelengths)}, flux shape={flux.shape}")
    print(f"  前5个波长: {wavelengths[:5]}")
    
    if '_param_extraction_summary' in metadata:
        summary = metadata['_param_extraction_summary']
        print(f"\n  参数提取摘要:")
        print(f"    总参数数量: {summary['total_parameters_extracted']}")
        for hdu, count in summary['hdu_sources'].items():
            if count > 0:
                print(f"    {hdu}: {count} 个参数")
    
    outputs = {}
    
    h5_path = os.path.join(output_dir, f"{base_name}.h5")
    print(f"\n正在生成HDF5: {h5_path}")
    outputs['hdf5'] = to_hdf5(time_steps, wavelengths, flux, metadata, h5_path)
    
    parquet_path = os.path.join(output_dir, f"{base_name}.parquet")
    print(f"正在生成Parquet: {parquet_path}")
    outputs['parquet'] = to_parquet(time_steps, wavelengths, flux, metadata, parquet_path)
    
    numpy_dir = os.path.join(output_dir, f"{base_name}_numpy")
    print(f"正在生成NumPy: {numpy_dir}")
    outputs['numpy'] = to_numpy(time_steps, wavelengths, flux, metadata, numpy_dir)
    
    print("\n转换完成！")
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


def verify_conversion(original_path, outputs, spectrum_index: Optional[int] = None):
    print("\n开始验证转换结果...")
    time_steps_orig, wavelengths_orig, flux_orig, metadata_orig = parse_fits(original_path, spectrum_index)
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
        print("使用方法: python fits_converter.py <input_file.fits> [output_dir] [spectrum_index]")
        print("\n示例:")
        print("  python fits_converter.py CB16_mup100_ssp_CO1p0.fits")
        print("  python fits_converter.py CB16_mup100_ssp_CO1p0.fits output_dir")
        print("  python fits_converter.py CB16_mup100_ssp_CO1p0.fits output_dir 0")
        print("\n说明:")
        print("  - 不指定spectrum_index时，将转换所有2016条光谱数据")
        print("  - 指定spectrum_index时，仅转换指定的单条光谱")
        return
    
    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    spectrum_index = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    if not os.path.exists(input_path):
        print(f"错误: 文件不存在 - {input_path}")
        return
    
    outputs = convert_all(input_path, output_dir, spectrum_index)
    verify_conversion(input_path, outputs, spectrum_index)
    
    print("\n输出文件:")
    for fmt, path in outputs.items():
        print(f"  {fmt:8s}: {path}")


if __name__ == "__main__":
    main()
