#!/usr/bin/env python3
"""
ised_gui.py: CB2016 .ised格式文件转换工具的图形用户界面

功能特性:
- 文件选择和批量处理
- 多语言支持 (中文/英文/法文)
- 光谱数据可视化
- 进度显示和错误处理
- 详细的操作日志
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

from ised_converter import parse_ised, to_hdf5, to_parquet, to_numpy

try:
    from spectrum_visualizer import SpectrumVisualizer
    VISUALIZER_AVAILABLE = True
except ImportError:
    VISUALIZER_AVAILABLE = False


TRANSLATIONS = {
    'zh': {
        'app_title': 'CB2016 .ised文件转换工具',
        'file_menu': '文件',
        'exit': '退出',
        'help_menu': '帮助',
        'about': '关于',
        'language': '语言',
        'input': '输入',
        'select_file': '选择文件',
        'select_folder': '选择文件夹',
        'input_files': '输入文件',
        'output': '输出',
        'select_output_dir': '选择输出目录',
        'output_dir': '输出目录',
        'formats': '输出格式',
        'hdf5': 'HDF5 (.h5)',
        'parquet': 'Parquet',
        'numpy': 'NumPy',
        'convert': '转换',
        'stop': '停止',
        'progress': '进度',
        'log': '日志',
        'visualization': '可视化',
        'spectrum_viewer': '光谱查看器',
        'load_file': '加载文件',
        'time_step': '时间步',
        'wavelength': '波长',
        'flux': '流量',
        'zoom': '缩放',
        'x_axis_type': '横轴类型',
        'wavelength_axis': '波长',
        'time_step_axis': '时间步',
        'x_scale': 'X轴刻度',
        'y_scale': 'Y轴刻度',
        'linear': '线性',
        'log': '对数',
        'autoscale': '自动缩放',
        'pan': '平移',
        'error': '错误',
        'warning': '警告',
        'info': '信息',
        'success': '成功',
        'conversion_started': '转换开始',
        'conversion_completed': '转换完成',
        'conversion_failed': '转换失败',
        'file_not_found': '文件未找到',
        'invalid_file': '无效文件',
        'no_files_selected': '未选择文件',
        'select_output_first': '请先选择输出目录',
        'about_text': 'CB2016 .ised文件转换工具\n\n版本: 1.0.0\n\n这是一个用于转换CB2016恒星种群合成模型.ised格式文件的图形界面工具。',
        'no_data_loaded': '请先加载数据文件',
        'ready': '就绪',
        'processing': '处理中...',
        'files_found': '找到 {} 个文件',
        'converting_file': '正在转换: {} ({}/{})',
        'all_done': '全部完成！',
    },
    'en': {
        'app_title': 'CB2016 .ised File Converter',
        'file_menu': 'File',
        'exit': 'Exit',
        'help_menu': 'Help',
        'about': 'About',
        'language': 'Language',
        'input': 'Input',
        'select_file': 'Select File',
        'select_folder': 'Select Folder',
        'input_files': 'Input Files',
        'output': 'Output',
        'select_output_dir': 'Select Output Directory',
        'output_dir': 'Output Directory',
        'formats': 'Output Formats',
        'hdf5': 'HDF5 (.h5)',
        'parquet': 'Parquet',
        'numpy': 'NumPy',
        'convert': 'Convert',
        'stop': 'Stop',
        'progress': 'Progress',
        'log': 'Log',
        'visualization': 'Visualization',
        'spectrum_viewer': 'Spectrum Viewer',
        'load_file': 'Load File',
        'time_step': 'Time Step',
        'wavelength': 'Wavelength',
        'flux': 'Flux',
        'zoom': 'Zoom',
        'x_axis_type': 'X-axis Type',
        'wavelength_axis': 'Wavelength',
        'time_step_axis': 'Time Step',
        'x_scale': 'X Scale',
        'y_scale': 'Y Scale',
        'linear': 'Linear',
        'log': 'Logarithmic',
        'autoscale': 'Autoscale',
        'pan': 'Pan',
        'error': 'Error',
        'warning': 'Warning',
        'info': 'Info',
        'success': 'Success',
        'conversion_started': 'Conversion started',
        'conversion_completed': 'Conversion completed',
        'conversion_failed': 'Conversion failed',
        'file_not_found': 'File not found',
        'invalid_file': 'Invalid file',
        'no_files_selected': 'No files selected',
        'select_output_first': 'Please select output directory first',
        'about_text': 'CB2016 .ised File Converter\n\nVersion: 1.0.0\n\nThis is a GUI tool for converting CB2016 stellar population synthesis model .ised files.',
        'no_data_loaded': 'Please load a data file first',
        'ready': 'Ready',
        'processing': 'Processing...',
        'files_found': '{} files found',
        'converting_file': 'Converting: {} ({}/{})',
        'all_done': 'All done!',
    },
    'fr': {
        'app_title': 'Convertisseur de fichiers .ised CB2016',
        'file_menu': 'Fichier',
        'exit': 'Quitter',
        'help_menu': 'Aide',
        'about': 'À propos',
        'language': 'Langue',
        'input': 'Entrée',
        'select_file': 'Sélectionner un fichier',
        'select_folder': 'Sélectionner un dossier',
        'input_files': 'Fichiers d\'entrée',
        'output': 'Sortie',
        'select_output_dir': 'Sélectionner le répertoire de sortie',
        'output_dir': 'Répertoire de sortie',
        'formats': 'Formats de sortie',
        'hdf5': 'HDF5 (.h5)',
        'parquet': 'Parquet',
        'numpy': 'NumPy',
        'convert': 'Convertir',
        'stop': 'Arrêter',
        'progress': 'Progression',
        'log': 'Journal',
        'visualization': 'Visualisation',
        'spectrum_viewer': 'Visualiseur de spectre',
        'load_file': 'Charger un fichier',
        'time_step': 'Pas de temps',
        'wavelength': 'Longueur d\'onde',
        'flux': 'Flux',
        'zoom': 'Zoom',
        'x_axis_type': 'Type d\'axe X',
        'wavelength_axis': 'Longueur d\'onde',
        'time_step_axis': 'Pas de temps',
        'x_scale': 'Échelle X',
        'y_scale': 'Échelle Y',
        'linear': 'Linéaire',
        'log': 'Logarithmique',
        'autoscale': 'Ajustement automatique',
        'pan': 'Panning',
        'error': 'Erreur',
        'warning': 'Avertissement',
        'info': 'Info',
        'success': 'Succès',
        'conversion_started': 'Conversion démarrée',
        'conversion_completed': 'Conversion terminée',
        'conversion_failed': 'Échec de la conversion',
        'file_not_found': 'Fichier non trouvé',
        'invalid_file': 'Fichier invalide',
        'no_files_selected': 'Aucun fichier sélectionné',
        'select_output_first': 'Veuillez d\'abord sélectionner le répertoire de sortie',
        'about_text': 'Convertisseur de fichiers .ised CB2016\n\nVersion: 1.0.0\n\nC\'est un outil GUI pour convertir les fichiers .ised des modèles de synthèse de populations stellaires CB2016.',
        'no_data_loaded': 'Veuillez d\'abord charger un fichier de données',
        'ready': 'Prêt',
        'processing': 'Traitement en cours...',
        'files_found': '{} fichiers trouvés',
        'converting_file': 'Conversion: {} ({}/{})',
        'all_done': 'Tout terminé!',
    }
}


class ConversionWorker(QThread):
    """后台转换工作线程"""
    progress_updated = pyqtSignal(int, str)
    file_finished = pyqtSignal(str, bool, str)
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, files: List[str], output_dir: str, formats: List[str]):
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
                    time_steps, wavelengths, flux, metadata = parse_ised(filepath)
                    base_name = os.path.splitext(filename)[0]

                    if 'hdf5' in self.formats:
                        h5_path = os.path.join(self.output_dir, f'{base_name}.h5')
                        to_hdf5(time_steps, wavelengths, flux, metadata, h5_path)

                    if 'parquet' in self.formats:
                        parquet_path = os.path.join(self.output_dir, f'{base_name}.parquet')
                        to_parquet(time_steps, wavelengths, flux, metadata, parquet_path)

                    if 'numpy' in self.formats:
                        numpy_dir = os.path.join(self.output_dir, f'{base_name}_numpy')
                        to_numpy(time_steps, wavelengths, flux, metadata, numpy_dir)

                    self.file_finished.emit(filepath, True, '')
                except Exception as e:
                    self.file_finished.emit(filepath, False, str(e))

            self.progress_updated.emit(100, '')
            self.finished.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def stop(self):
        self._should_stop = True


class ISEDConverterGUI(QMainWindow):
    """主界面"""
    def __init__(self):
        super().__init__()
        self.current_lang = 'zh'
        self.input_files: List[str] = []
        self.output_dir: str = ''
        self.current_data: Optional[Dict[str, Any]] = None
        self.worker: Optional[ConversionWorker] = None

        self._setup_logging()
        self._init_ui()
        self._retranslate_ui()

    def _setup_logging(self):
        self.logger = logging.getLogger('ISEDConverter')
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers = []

        log_file = Path.home() / '.ised_converter' / f'log_{datetime.now().strftime("%Y%m%d")}.log'
        log_file.parent.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def _init_ui(self):
        self.setWindowTitle('CB2016 .ised文件转换工具')
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
        input_layout.addLayout(btn_layout)

        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
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

        self.input_group.setTitle(tr['input'])
        self.btn_select_file.setText(tr['select_file'])
        self.btn_select_folder.setText(tr['select_folder'])
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

    def _change_language(self, lang_code: str):
        for code, action in self.lang_actions.items():
            action.setChecked(code == lang_code)
        self.current_lang = lang_code
        self._retranslate_ui()

    def _select_file(self):
        tr = TRANSLATIONS[self.current_lang]
        files, _ = QFileDialog.getOpenFileNames(
            self, tr['select_file'], '', 'ISED Files (*.ised);;All Files (*)'
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
            self.input_files.extend([str(f) for f in ised_files])
            self._update_file_list()
            self._log(tr['info'], tr['files_found'].format(len(ised_files)))

    def _update_file_list(self):
        self.file_list.clear()
        for filepath in self.input_files:
            item = QListWidgetItem(os.path.basename(filepath))
            item.setData(Qt.UserRole, filepath)
            self.file_list.addItem(item)

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

        if not self.input_files:
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

        self.worker = ConversionWorker(self.input_files, self.output_dir, formats)
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
            self, tr['load_file'], '', 'ISED Files (*.ised);;All Files (*)'
        )
        if filepath:
            try:
                time_steps, wavelengths, flux, metadata = parse_ised(filepath)
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


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = ISEDConverterGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
