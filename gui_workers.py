#!/usr/bin/env python3
"""
gui_workers.py: 后台工作线程类
"""

import os
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

from ised_converter import to_hdf5 as ised_to_hdf5
from ised_converter import to_parquet as ised_to_parquet
from ised_converter import to_numpy as ised_to_numpy
from fits_converter import to_hdf5 as fits_to_hdf5
from fits_converter import to_parquet as fits_to_parquet
from fits_converter import to_numpy as fits_to_numpy
from ised_converter import parse_ised
from fits_converter import parse_fits


class ConversionWorker(QThread):
    """后台转换工作线程"""
    progress_updated = pyqtSignal(int, str)
    file_finished = pyqtSignal(str, bool, str)
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, files, output_dir, formats):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.formats = formats
        self._should_stop = False

    def run(self):
        try:
            total = len(self.files)
            for i, filepath in enumerate(self.files):
                if self._should_stop:
                    break

                filename = os.path.basename(filepath)
                self.progress_updated.emit(int((i / total) * 100), f'Converting: {filename} ({i+1}/{total})')

                try:
                    is_ised = filepath.lower().endswith('.ised')
                    is_fits = filepath.lower().endswith('.fits')
                    
                    if is_ised:
                        time_steps, wavelengths, flux, metadata = parse_ised(filepath)
                    elif is_fits:
                        time_steps, wavelengths, flux, metadata = parse_fits(filepath)
                    else:
                        raise ValueError(f'不支持的文件格式: {filename}')
                    
                    base_name = os.path.splitext(filename)[0]

                    if 'hdf5' in self.formats:
                        h5_path = os.path.join(self.output_dir, f'{base_name}.h5')
                        if is_ised:
                            ised_to_hdf5(time_steps, wavelengths, flux, metadata, h5_path)
                        else:
                            fits_to_hdf5(time_steps, wavelengths, flux, metadata, h5_path)

                    if 'parquet' in self.formats:
                        parquet_path = os.path.join(self.output_dir, f'{base_name}.parquet')
                        if is_ised:
                            ised_to_parquet(time_steps, wavelengths, flux, metadata, parquet_path)
                        else:
                            fits_to_parquet(time_steps, wavelengths, flux, metadata, parquet_path)

                    if 'numpy' in self.formats:
                        numpy_dir = os.path.join(self.output_dir, f'{base_name}_numpy')
                        if is_ised:
                            ised_to_numpy(time_steps, wavelengths, flux, metadata, numpy_dir)
                        else:
                            fits_to_numpy(time_steps, wavelengths, flux, metadata, numpy_dir)

                    self.file_finished.emit(filepath, True, '')
                except Exception as e:
                    self.file_finished.emit(filepath, False, str(e))

            self.progress_updated.emit(100, '')
            self.finished.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def stop(self):
        self._should_stop = True


class DataSplitWorker(QThread):
    """后台数据拆分工作线程 - 按HDF5文件内样本拆分"""
    progress_updated = pyqtSignal(int, str)
    file_finished = pyqtSignal(str, bool, str)
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, files, output_dir, 
                 train_ratio, test_ratio, valid_ratio,
                 shuffle_num):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.train_ratio = train_ratio
        self.test_ratio = test_ratio
        self.valid_ratio = valid_ratio
        self.shuffle_num = shuffle_num
        self._should_stop = False

    def _check_hdf5_structure(self, filepath):
        """检查HDF5文件结构，返回样本数和有效键列表"""
        import h5py
        with h5py.File(filepath, 'r') as f:
            first_dims = {}
            for key in f.keys():
                if key == 'wavelengths':
                    continue
                dataset = f[key]
                if len(dataset.shape) > 0:
                    first_dims[key] = dataset.shape[0]
            
            if not first_dims:
                raise ValueError(f'HDF5文件中没有有效的数据集: {os.path.basename(filepath)}')
            
            dim_values = list(first_dims.values())
            sample_count = max(set(dim_values), key=dim_values.count)
            
            valid_keys = [key for key, dim in first_dims.items() if dim == sample_count]
            scalar_keys = [key for key in f.keys() if len(f[key].shape) == 0 or key == 'wavelengths']
            
            return sample_count, valid_keys, scalar_keys

    def run(self):
        try:
            import h5py
            
            if self.shuffle_num is not None:
                np.random.seed(self.shuffle_num)
            
            total_files = len(self.files)
            for file_idx, filepath in enumerate(self.files):
                if self._should_stop:
                    break
                
                filename = os.path.basename(filepath)
                base_name = os.path.splitext(filename)[0]
                
                self.progress_updated.emit(
                    int((file_idx / total_files) * 50), 
                    f'Processing: {filename} ({file_idx+1}/{total_files})'
                )
                
                try:
                    is_hdf5 = filepath.lower().endswith('.h5') or filepath.lower().endswith('.hdf5')
                    if not is_hdf5:
                        raise ValueError(f'只支持HDF5格式文件: {filename}')
                    
                    sample_count, valid_keys, scalar_keys = self._check_hdf5_structure(filepath)
                    
                    indices = np.arange(sample_count)
                    np.random.shuffle(indices)
                    
                    n_train = int(np.round(sample_count * self.train_ratio))
                    n_test = int(np.round(sample_count * self.test_ratio))
                    
                    if n_train + n_test > sample_count:
                        if n_train > n_test:
                            n_train -= 1
                        else:
                            n_test -= 1
                    
                    n_valid = sample_count - n_train - n_test
                    
                    if n_valid < 0:
                        n_valid = 0
                        if n_train + n_test > sample_count:
                            if n_test > 0:
                                n_test -= 1
                            else:
                                n_train -= 1
                    
                    train_indices = indices[:n_train]
                    test_indices = indices[n_train:n_train + n_test]
                    valid_indices = indices[n_train + n_test:]
                    
                    splits = {
                        'train': train_indices,
                        'test': test_indices,
                        'valid': valid_indices
                    }
                    
                    with h5py.File(filepath, 'r') as src_f:
                        for split_name, split_indices in splits.items():
                            if self._should_stop:
                                break
                            
                            if len(split_indices) == 0:
                                continue
                            
                            new_filename = f'{base_name}_{split_name}.hdf5'
                            new_path = os.path.join(self.output_dir, new_filename)
                            
                            with h5py.File(new_path, 'w') as dst_f:
                                for key in valid_keys:
                                    src_data = src_f[key][:]
                                    dst_f.create_dataset(key, data=src_data[split_indices])
                                
                                for key in scalar_keys:
                                    src_f.copy(key, dst_f)
                            
                            progress = 50 + int((file_idx + 1) / total_files * 50)
                            self.progress_updated.emit(progress, f'Created: {new_filename}')
                    
                    self.file_finished.emit(filepath, True, 'success')
                    
                except Exception as e:
                    self.file_finished.emit(filepath, False, str(e))
            
            self.progress_updated.emit(100, '')
            self.finished.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def stop(self):
        self._should_stop = True
