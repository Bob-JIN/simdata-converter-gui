#!/usr/bin/env python3
"""
gui.py: GUI类定义
"""

import sys
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QComboBox, QCheckBox,
    QProgressBar, QTextEdit, QTabWidget, QSplitter, QListWidget,
    QListWidgetItem, QGroupBox, QSpinBox, QDoubleSpinBox, QMessageBox,
    QStatusBar, QToolBar, QAction, QMenuBar, QMenu
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont, QColor

import numpy as np

try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from ised_converter import parse_ised
from ised_converter import to_hdf5 as ised_to_hdf5
from ised_converter import to_parquet as ised_to_parquet
from ised_converter import to_numpy as ised_to_numpy
from fits_converter import parse_fits
from fits_converter import to_hdf5 as fits_to_hdf5
from fits_converter import to_parquet as fits_to_parquet
from fits_converter import to_numpy as fits_to_numpy

try:
    from spectrum_visualizer import SpectrumVisualizer
    VISUALIZER_AVAILABLE = True
except ImportError:
    VISUALIZER_AVAILABLE = False

from translations import TRANSLATIONS
from gui_workers import ConversionWorker, DataSplitWorker


class ISEDConverterGUI(QMainWindow):
    """主界面"""
    def __init__(self):
        super().__init__()
        self.current_lang = 'zh'
        self.input_files: List[str] = []
        self.output_dir: str = ''
        self.current_data: Optional[Dict[str, Any]] = None
        self.worker: Optional[ConversionWorker] = None
        self.split_input_files: List[str] = []
        self.split_output_dir: str = ''
        self.split_worker: Optional[DataSplitWorker] = None

        self._setup_logging()
        self._init_ui()
        self._retranslate_ui()

    def _setup_logging(self):
        self.logger = logging.getLogger('DataDealer')
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers = []

        log_file = Path.home() / '.data_dealer' / f'log_{datetime.now().strftime("%Y%m%d")}.log'
        log_file.parent.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def _init_ui(self):
        self.setWindowTitle('数据预处理工具')
        self.setMinimumSize(1000, 700)

        self._create_menu_bar()
        self._create_central_widget()
        self._create_status_bar()

    def _create_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu('')
        self.file_menu = file_menu

        exit_action = QAction('', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        self.exit_action = exit_action
        file_menu.addAction(exit_action)

        lang_menu = menubar.addMenu('')
        self.lang_menu = lang_menu

        self.lang_actions = {}
        for lang_code, lang_name in [('zh', '中文'), ('en', 'English'), ('fr', 'Français')]:
            action = QAction(lang_name, self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, l=lang_code: self._change_language(l))
            self.lang_actions[lang_code] = action
            lang_menu.addAction(action)
        self.lang_actions['zh'].setChecked(True)

        help_menu = menubar.addMenu('')
        self.help_menu = help_menu

        about_action = QAction('', self)
        about_action.triggered.connect(self._show_about)
        self.about_action = about_action
        help_menu.addAction(about_action)

    def _create_central_widget(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        self._create_converter_tab()
        self._create_visualization_tab()
        self._create_data_split_tab()

    def _create_converter_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        splitter = QSplitter(Qt.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        input_group = QGroupBox('')
        self.input_group = input_group
        input_layout = QVBoxLayout(input_group)

        btn_layout = QHBoxLayout()
        self.btn_select_file = QPushButton('')
        self.btn_select_file.clicked.connect(self._select_file)
        btn_layout.addWidget(self.btn_select_file)

        self.btn_select_folder = QPushButton('')
        self.btn_select_folder.clicked.connect(self._select_folder)
        btn_layout.addWidget(self.btn_select_folder)
        
        self.btn_clear_list = QPushButton('')
        self.btn_clear_list.clicked.connect(self._clear_file_list)
        btn_layout.addWidget(self.btn_clear_list)
        input_layout.addLayout(btn_layout)

        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self._show_file_list_context_menu)
        input_layout.addWidget(self.file_list)
        left_layout.addWidget(input_group)

        output_group = QGroupBox('')
        self.output_group = output_group
        output_layout = QVBoxLayout(output_group)

        self.btn_output_dir = QPushButton('')
        self.btn_output_dir.clicked.connect(self._select_output_dir)
        output_layout.addWidget(self.btn_output_dir)

        self.label_output_dir = QLabel('')
        output_layout.addWidget(self.label_output_dir)

        formats_group = QGroupBox('')
        self.formats_group = formats_group
        formats_layout = QVBoxLayout(formats_group)

        self.chk_hdf5 = QCheckBox('HDF5')
        self.chk_hdf5.setChecked(True)
        formats_layout.addWidget(self.chk_hdf5)

        self.chk_parquet = QCheckBox('Parquet')
        self.chk_parquet.setChecked(True)
        formats_layout.addWidget(self.chk_parquet)

        self.chk_numpy = QCheckBox('NumPy')
        self.chk_numpy.setChecked(True)
        formats_layout.addWidget(self.chk_numpy)

        output_layout.addWidget(formats_group)
        left_layout.addWidget(output_group)

        btn_convert_layout = QHBoxLayout()
        self.btn_convert = QPushButton('')
        self.btn_convert.clicked.connect(self._start_conversion)
        self.btn_convert.setMinimumHeight(40)
        btn_convert_layout.addWidget(self.btn_convert)

        self.btn_stop = QPushButton('')
        self.btn_stop.clicked.connect(self._stop_conversion)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setMinimumHeight(40)
        btn_convert_layout.addWidget(self.btn_stop)
        left_layout.addLayout(btn_convert_layout)

        left_layout.addStretch()

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        progress_group = QGroupBox('')
        self.progress_group = progress_group
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)

        self.label_progress = QLabel('')
        progress_layout.addWidget(self.label_progress)
        right_layout.addWidget(progress_group)

        log_group = QGroupBox('')
        self.log_group = log_group
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont('Consolas', 9))
        log_layout.addWidget(self.log_text)
        right_layout.addWidget(log_group)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 600])

        layout.addWidget(splitter)
        self.tab_widget.addTab(tab, '')

    def _create_visualization_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        if MATPLOTLIB_AVAILABLE and VISUALIZER_AVAILABLE:
            controls_layout = QHBoxLayout()

            self.btn_viz_load = QPushButton('')
            self.btn_viz_load.clicked.connect(self._load_viz_file)
            controls_layout.addWidget(self.btn_viz_load)

            controls_layout.addStretch()
            layout.addLayout(controls_layout)

            self.visualizer = SpectrumVisualizer(self)
            self.nav_toolbar = NavigationToolbar(self.visualizer, self)
            layout.addWidget(self.nav_toolbar)
            layout.addWidget(self.visualizer)
        else:
            if not MATPLOTLIB_AVAILABLE:
                label = QLabel('Matplotlib not available. Please install matplotlib for visualization.')
            else:
                label = QLabel('Spectrum visualizer module not available.')
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)

        self.tab_widget.addTab(tab, '')

    def _create_data_split_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        splitter = QSplitter(Qt.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        input_group = QGroupBox('')
        self.split_input_group = input_group
        input_layout = QVBoxLayout(input_group)

        btn_layout = QHBoxLayout()
        self.btn_split_select_file = QPushButton('')
        self.btn_split_select_file.clicked.connect(self._split_select_file)
        btn_layout.addWidget(self.btn_split_select_file)

        self.btn_split_select_folder = QPushButton('')
        self.btn_split_select_folder.clicked.connect(self._split_select_folder)
        btn_layout.addWidget(self.btn_split_select_folder)
        
        self.btn_split_clear_list = QPushButton('')
        self.btn_split_clear_list.clicked.connect(self._split_clear_file_list)
        btn_layout.addWidget(self.btn_split_clear_list)
        input_layout.addLayout(btn_layout)

        self.split_file_list = QListWidget()
        self.split_file_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.split_file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.split_file_list.customContextMenuRequested.connect(self._split_show_file_list_context_menu)
        input_layout.addWidget(self.split_file_list)
        left_layout.addWidget(input_group)

        output_group = QGroupBox('')
        self.split_output_group = output_group
        output_layout = QVBoxLayout(output_group)

        self.btn_split_output_dir = QPushButton('')
        self.btn_split_output_dir.clicked.connect(self._split_select_output_dir)
        output_layout.addWidget(self.btn_split_output_dir)

        self.split_label_output_dir = QLabel('')
        output_layout.addWidget(self.split_label_output_dir)

        settings_group = QGroupBox('')
        self.split_settings_group = settings_group
        settings_layout = QVBoxLayout(settings_group)

        shuffle_layout = QHBoxLayout()
        self.lbl_shuffle = QLabel('')
        shuffle_layout.addWidget(self.lbl_shuffle)
        self.spin_shuffle = QSpinBox()
        self.spin_shuffle.setMinimum(0)
        self.spin_shuffle.setMaximum(999999)
        self.spin_shuffle.setValue(42)
        shuffle_layout.addWidget(self.spin_shuffle)
        settings_layout.addLayout(shuffle_layout)

        train_layout = QHBoxLayout()
        self.lbl_train = QLabel('')
        train_layout.addWidget(self.lbl_train)
        self.spin_train = QSpinBox()
        self.spin_train.setMinimum(0)
        self.spin_train.setMaximum(100)
        self.spin_train.setSingleStep(5)
        self.spin_train.setValue(70)
        train_layout.addWidget(self.spin_train)
        settings_layout.addLayout(train_layout)

        test_layout = QHBoxLayout()
        self.lbl_test = QLabel('')
        test_layout.addWidget(self.lbl_test)
        self.spin_test = QSpinBox()
        self.spin_test.setMinimum(0)
        self.spin_test.setMaximum(100)
        self.spin_test.setSingleStep(5)
        self.spin_test.setValue(20)
        test_layout.addWidget(self.spin_test)
        settings_layout.addLayout(test_layout)

        valid_layout = QHBoxLayout()
        self.lbl_valid = QLabel('')
        valid_layout.addWidget(self.lbl_valid)
        self.spin_valid = QSpinBox()
        self.spin_valid.setMinimum(0)
        self.spin_valid.setMaximum(100)
        self.spin_valid.setSingleStep(5)
        self.spin_valid.setValue(10)
        self.spin_valid.setReadOnly(True)
        valid_layout.addWidget(self.spin_valid)
        settings_layout.addLayout(valid_layout)

        output_layout.addWidget(settings_group)
        left_layout.addWidget(output_group)

        btn_split_layout = QHBoxLayout()
        self.btn_split = QPushButton('')
        self.btn_split.clicked.connect(self._start_split)
        self.btn_split.setMinimumHeight(40)
        btn_split_layout.addWidget(self.btn_split)

        self.btn_split_stop = QPushButton('')
        self.btn_split_stop.clicked.connect(self._stop_split)
        self.btn_split_stop.setEnabled(False)
        self.btn_split_stop.setMinimumHeight(40)
        btn_split_layout.addWidget(self.btn_split_stop)
        left_layout.addLayout(btn_split_layout)

        left_layout.addStretch()

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        progress_group = QGroupBox('')
        self.split_progress_group = progress_group
        progress_layout = QVBoxLayout(progress_group)

        self.split_progress_bar = QProgressBar()
        progress_layout.addWidget(self.split_progress_bar)

        self.split_label_progress = QLabel('')
        progress_layout.addWidget(self.split_label_progress)
        right_layout.addWidget(progress_group)

        log_group = QGroupBox('')
        self.split_log_group = log_group
        log_layout = QVBoxLayout(log_group)

        self.split_log_text = QTextEdit()
        self.split_log_text.setReadOnly(True)
        self.split_log_text.setFont(QFont('Consolas', 9))
        log_layout.addWidget(self.split_log_text)
        right_layout.addWidget(log_group)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 600])

        layout.addWidget(splitter)
        self.tab_widget.addTab(tab, '')

        self.spin_train.valueChanged.connect(self._update_valid_ratio)
        self.spin_test.valueChanged.connect(self._update_valid_ratio)

    def _create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.label_status = QLabel('')
        self.status_bar.addWidget(self.label_status)

    def _retranslate_ui(self):
        tr = TRANSLATIONS[self.current_lang]

        self.setWindowTitle(tr['app_title'])
        self.file_menu.setTitle(tr['file_menu'])
        self.exit_action.setText(tr['exit'])
        self.lang_menu.setTitle(tr['language'])
        self.help_menu.setTitle(tr['help_menu'])
        self.about_action.setText(tr['about'])

        self.tab_widget.setTabText(0, tr['input'])
        self.tab_widget.setTabText(1, tr['visualization'])
        self.tab_widget.setTabText(2, tr['data_split'])

        self.input_group.setTitle(tr['input'])
        self.btn_select_file.setText(tr['select_file'])
        self.btn_select_folder.setText(tr['select_folder'])
        self.btn_clear_list.setText(tr['clear_list'])
        self.output_group.setTitle(tr['output'])
        self.btn_output_dir.setText(tr['select_output_dir'])
        self.formats_group.setTitle(tr['formats'])
        self.chk_hdf5.setText(tr['hdf5'])
        self.chk_parquet.setText(tr['parquet'])
        self.chk_numpy.setText(tr['numpy'])
        self.btn_convert.setText(tr['convert'])
        self.btn_stop.setText(tr['stop'])
        self.progress_group.setTitle(tr['progress'])
        self.log_group.setTitle(tr['log'])

        if MATPLOTLIB_AVAILABLE:
            self.btn_viz_load.setText(tr['load_file'])

        self.label_status.setText(tr['ready'])
        self._log(tr['info'], tr['app_title'] + ' started')

        self.split_input_group.setTitle(tr['input'])
        self.btn_split_select_file.setText(tr['select_file'])
        self.btn_split_select_folder.setText(tr['select_folder'])
        self.btn_split_clear_list.setText(tr['clear_list'])
        self.split_output_group.setTitle(tr['output'])
        self.btn_split_output_dir.setText(tr['select_output_dir'])
        self.split_settings_group.setTitle(tr['formats'])
        self.btn_split.setText(tr['split'])
        self.btn_split_stop.setText(tr['stop'])
        self.split_progress_group.setTitle(tr['progress'])
        self.split_log_group.setTitle(tr['log'])
        
        self.lbl_shuffle.setText(tr['shuffle_num'])
        self.lbl_train.setText(tr['train_ratio'])
        self.lbl_test.setText(tr['test_ratio'])
        self.lbl_valid.setText(tr['valid_ratio'])

    def _change_language(self, lang_code: str):
        for code, action in self.lang_actions.items():
            action.setChecked(code == lang_code)
        self.current_lang = lang_code
        self._retranslate_ui()

    def _select_file(self):
        tr = TRANSLATIONS[self.current_lang]
        files, _ = QFileDialog.getOpenFileNames(
            self, tr['select_file'], '', 
            f"{tr['all_files']};;{tr['ised_format']};;{tr['fits_format']}"
        )
        if files:
            self.input_files.extend(files)
            self._update_file_list()
            self._log(tr['info'], tr['files_found'].format(len(files)))

    def _select_folder(self):
        tr = TRANSLATIONS[self.current_lang]
        folder = QFileDialog.getExistingDirectory(self, tr['select_folder'])
        if folder:
            ised_files = list(Path(folder).rglob('*.ised'))
            fits_files = list(Path(folder).rglob('*.fits'))
            all_files = ised_files + fits_files
            self.input_files.extend([str(f) for f in all_files])
            self._update_file_list()
            self._log(tr['info'], tr['files_found'].format(len(all_files)))

    def _update_file_list(self):
        self.file_list.clear()
        for filepath in self.input_files:
            item = QListWidgetItem(os.path.basename(filepath))
            item.setData(Qt.UserRole, filepath)
            self.file_list.addItem(item)
    
    def _clear_file_list(self):
        tr = TRANSLATIONS[self.current_lang]
        self.input_files = []
        self.file_list.clear()
        self._log(tr['info'], '文件列表已清空')
    
    def _show_file_list_context_menu(self, position):
        tr = TRANSLATIONS[self.current_lang]
        menu = QMenu(self)
        
        action_select_all = QAction(tr['select_all'], self)
        action_select_all.triggered.connect(lambda: self.file_list.selectAll())
        menu.addAction(action_select_all)
        
        action_remove_selected = QAction(tr['remove_selected'], self)
        action_remove_selected.triggered.connect(self._remove_selected_files)
        menu.addAction(action_remove_selected)
        
        menu.exec_(self.file_list.mapToGlobal(position))
    
    def _remove_selected_files(self):
        tr = TRANSLATIONS[self.current_lang]
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return
        
        removed_count = 0
        for item in selected_items:
            filepath = item.data(Qt.UserRole)
            if filepath in self.input_files:
                self.input_files.remove(filepath)
                removed_count += 1
        
        self._update_file_list()
        self._log(tr['info'], f'已删除 {removed_count} 个文件')

    def _select_output_dir(self):
        tr = TRANSLATIONS[self.current_lang]
        folder = QFileDialog.getExistingDirectory(self, tr['select_output_dir'])
        if folder:
            self.output_dir = folder
            self.label_output_dir.setText(folder)

    def _get_selected_formats(self) -> List[str]:
        formats = []
        if self.chk_hdf5.isChecked():
            formats.append('hdf5')
        if self.chk_parquet.isChecked():
            formats.append('parquet')
        if self.chk_numpy.isChecked():
            formats.append('numpy')
        return formats

    def _start_conversion(self):
        tr = TRANSLATIONS[self.current_lang]

        display_files = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            filepath = item.data(Qt.UserRole)
            display_files.append(filepath)
        
        if not display_files:
            QMessageBox.warning(self, tr['warning'], tr['no_files_selected'])
            return
        if not self.output_dir:
            QMessageBox.warning(self, tr['warning'], tr['select_output_first'])
            return

        formats = self._get_selected_formats()
        if not formats:
            QMessageBox.warning(self, tr['warning'], '请选择至少一种输出格式')
            return

        self.btn_convert.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setValue(0)

        self.worker = ConversionWorker(display_files, self.output_dir, formats)
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.file_finished.connect(self._on_file_finished)
        self.worker.finished.connect(self._on_conversion_finished)
        self.worker.error_occurred.connect(self._on_conversion_error)
        self.worker.start()

        self._log(tr['info'], tr['conversion_started'])
        self.label_status.setText(tr['processing'])

    def _stop_conversion(self):
        if self.worker:
            self.worker.stop()
            self.btn_stop.setEnabled(False)

    def _on_progress_updated(self, value: int, message: str):
        self.progress_bar.setValue(value)
        if message:
            self.label_progress.setText(message)

    def _on_file_finished(self, filepath: str, success: bool, error_msg: str):
        tr = TRANSLATIONS[self.current_lang]
        filename = os.path.basename(filepath)
        if success:
            self._log(tr['success'], f'{filename}: {tr["conversion_completed"]}')
        else:
            self._log(tr['error'], f'{filename}: {tr["conversion_failed"]} - {error_msg}')

    def _on_conversion_finished(self):
        tr = TRANSLATIONS[self.current_lang]
        self.btn_convert.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.label_status.setText(tr['ready'])
        self._log(tr['success'], tr['all_done'])

    def _on_conversion_error(self, error_msg: str):
        tr = TRANSLATIONS[self.current_lang]
        self._log(tr['error'], error_msg)
        QMessageBox.critical(self, tr['error'], error_msg)

    def _load_viz_file(self):
        tr = TRANSLATIONS[self.current_lang]
        filepath, _ = QFileDialog.getOpenFileName(
            self, tr['load_file'], '', 
            f"{tr['ised_format']};;{tr['fits_format']};;{tr['all_files']}"
        )
        if filepath:
            try:
                if filepath.lower().endswith('.ised'):
                    time_steps, wavelengths, flux, metadata = parse_ised(filepath)
                elif filepath.lower().endswith('.fits'):
                    time_steps, wavelengths, flux, metadata = parse_fits(filepath)
                else:
                    raise ValueError(f'不支持的文件格式')
                
                self.current_data = {
                    'time_steps': time_steps,
                    'wavelengths': wavelengths,
                    'flux': flux,
                    'metadata': metadata
                }
                
                if hasattr(self, 'visualizer'):
                    self.visualizer.load_data(time_steps, wavelengths, flux, metadata)
                
                self._log(tr['success'], f'Loaded: {os.path.basename(filepath)}')
            except Exception as e:
                self._log(tr['error'], str(e))
                QMessageBox.critical(self, tr['error'], str(e))

    def _log(self, level: str, message: str):
        timestamp = datetime.now().strftime('%H:%M:%S')
        color_map = {
            'error': 'red',
            'warning': 'orange',
            'success': 'green',
            'info': 'blue'
        }
        color = color_map.get(level, 'black')
        self.log_text.append(f'<span style="color:{color}">[{timestamp}] {level.upper()}: {message}</span>')
        self.logger.info(f'{level}: {message}')

    def _show_about(self):
        tr = TRANSLATIONS[self.current_lang]
        QMessageBox.about(self, tr['about'], tr['about_text'])

    def _split_select_file(self):
        tr = TRANSLATIONS[self.current_lang]
        files, _ = QFileDialog.getOpenFileNames(
            self, tr['select_file'], '', 
            f"{tr['hdf5_format']};;{tr['all_files']}"
        )
        if files:
            self.split_input_files.extend(files)
            self._split_update_file_list()
            self._split_log(tr['info'], tr['files_found'].format(len(files)))

    def _split_select_folder(self):
        tr = TRANSLATIONS[self.current_lang]
        folder = QFileDialog.getExistingDirectory(self, tr['select_folder'])
        if folder:
            hdf5_files = list(Path(folder).rglob('*.h5'))
            hdf5_files.extend(list(Path(folder).rglob('*.hdf5')))
            self.split_input_files.extend([str(f) for f in hdf5_files])
            self._split_update_file_list()
            self._split_log(tr['info'], tr['files_found'].format(len(hdf5_files)))

    def _split_update_file_list(self):
        self.split_file_list.clear()
        for filepath in self.split_input_files:
            item = QListWidgetItem(os.path.basename(filepath))
            item.setData(Qt.UserRole, filepath)
            self.split_file_list.addItem(item)
    
    def _split_clear_file_list(self):
        tr = TRANSLATIONS[self.current_lang]
        self.split_input_files = []
        self.split_file_list.clear()
        self._split_log(tr['info'], '文件列表已清空')
    
    def _split_show_file_list_context_menu(self, position):
        tr = TRANSLATIONS[self.current_lang]
        menu = QMenu(self)
        
        action_select_all = QAction(tr['select_all'], self)
        action_select_all.triggered.connect(lambda: self.split_file_list.selectAll())
        menu.addAction(action_select_all)
        
        action_remove_selected = QAction(tr['remove_selected'], self)
        action_remove_selected.triggered.connect(self._split_remove_selected_files)
        menu.addAction(action_remove_selected)
        
        menu.exec_(self.split_file_list.mapToGlobal(position))
    
    def _split_remove_selected_files(self):
        tr = TRANSLATIONS[self.current_lang]
        selected_items = self.split_file_list.selectedItems()
        if not selected_items:
            return
        
        removed_count = 0
        for item in selected_items:
            filepath = item.data(Qt.UserRole)
            if filepath in self.split_input_files:
                self.split_input_files.remove(filepath)
                removed_count += 1
        
        self._split_update_file_list()
        self._split_log(tr['info'], f'已删除 {removed_count} 个文件')

    def _split_select_output_dir(self):
        tr = TRANSLATIONS[self.current_lang]
        folder = QFileDialog.getExistingDirectory(self, tr['select_output_dir'])
        if folder:
            self.split_output_dir = folder
            self.split_label_output_dir.setText(folder)

    def _update_valid_ratio(self):
        train = self.spin_train.value()
        test = self.spin_test.value()
        valid = max(0, 100 - train - test)
        self.spin_valid.setValue(valid)

    def _check_hdf5_files(self, files):
        """检查所有HDF5文件的结构一致性"""
        import h5py
        tr = TRANSLATIONS[self.current_lang]
        
        for filepath in files:
            filename = os.path.basename(filepath)
            try:
                with h5py.File(filepath, 'r') as f:
                    first_dims = {}
                    for key in f.keys():
                        if key == 'wavelengths':
                            continue
                        dataset = f[key]
                        if len(dataset.shape) > 0:
                            first_dims[key] = dataset.shape[0]
                    
                    if not first_dims:
                        return False, f'{filename}: HDF5文件中没有有效的数据集'
                    
                    dim_values = list(first_dims.values())
                    sample_count = max(set(dim_values), key=dim_values.count)
                    
                    inconsistent_keys = [key for key, dim in first_dims.items() if dim != sample_count]
                    if inconsistent_keys:
                        return False, f'{filename}: 以下键的第一个维度与样本数({sample_count})不一致: {", ".join(inconsistent_keys)}'
                        
            except Exception as e:
                return False, f'{filename}: {str(e)}'
        
        return True, ''

    def _start_split(self):
        tr = TRANSLATIONS[self.current_lang]

        display_files = []
        for i in range(self.split_file_list.count()):
            item = self.split_file_list.item(i)
            filepath = item.data(Qt.UserRole)
            display_files.append(filepath)
        
        if not display_files:
            QMessageBox.warning(self, tr['warning'], tr['no_files_selected'])
            return
        if not self.split_output_dir:
            QMessageBox.warning(self, tr['warning'], tr['select_output_first'])
            return

        train_percent = self.spin_train.value()
        test_percent = self.spin_test.value()
        valid_percent = self.spin_valid.value()
        shuffle_num = self.spin_shuffle.value()

        if train_percent + test_percent + valid_percent != 100:
            QMessageBox.warning(self, tr['warning'], '百分比总和必须为100')
            return

        ok, error_msg = self._check_hdf5_files(display_files)
        if not ok:
            QMessageBox.warning(self, tr['warning'], error_msg)
            return

        self.btn_split.setEnabled(False)
        self.btn_split_stop.setEnabled(True)
        self.split_progress_bar.setValue(0)

        train_ratio = train_percent / 100.0
        test_ratio = test_percent / 100.0
        valid_ratio = valid_percent / 100.0

        self.split_worker = DataSplitWorker(display_files, self.split_output_dir, 
                                             train_ratio, test_ratio, valid_ratio, shuffle_num)
        self.split_worker.progress_updated.connect(self._split_on_progress_updated)
        self.split_worker.file_finished.connect(self._split_on_file_finished)
        self.split_worker.finished.connect(self._split_on_split_finished)
        self.split_worker.error_occurred.connect(self._split_on_split_error)
        self.split_worker.start()

        self._split_log(tr['info'], tr['split_started'])
        self.label_status.setText(tr['processing'])

    def _stop_split(self):
        if self.split_worker:
            self.split_worker.stop()
            self.btn_split_stop.setEnabled(False)

    def _split_on_progress_updated(self, value: int, message: str):
        self.split_progress_bar.setValue(value)
        if message:
            self.split_label_progress.setText(message)

    def _split_on_file_finished(self, filepath: str, success: bool, split_name: str):
        tr = TRANSLATIONS[self.current_lang]
        filename = os.path.basename(filepath)
        if success:
            self._split_log(tr['success'], f'{filename}: {tr["split_completed"]} -> {split_name}')
        else:
            self._split_log(tr['error'], f'{filename}: {tr["split_failed"]} - {split_name}')

    def _split_on_split_finished(self):
        tr = TRANSLATIONS[self.current_lang]
        self.btn_split.setEnabled(True)
        self.btn_split_stop.setEnabled(False)
        self.label_status.setText(tr['ready'])
        self._split_log(tr['success'], tr['all_done'])

    def _split_on_split_error(self, error_msg: str):
        tr = TRANSLATIONS[self.current_lang]
        self._split_log(tr['error'], error_msg)
        QMessageBox.critical(self, tr['error'], error_msg)

    def _split_log(self, level: str, message: str):
        timestamp = datetime.now().strftime('%H:%M:%S')
        color_map = {
            'error': 'red',
            'warning': 'orange',
            'success': 'green',
            'info': 'blue'
        }
        color = color_map.get(level, 'black')
        self.split_log_text.append(f'<span style="color:{color}">[{timestamp}] {level.upper()}: {message}</span>')
        self.logger.info(f'{level}: {message}')
