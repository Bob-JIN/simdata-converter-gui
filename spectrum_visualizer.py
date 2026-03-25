#!/usr/bin/env python3
"""
spectrum_visualizer.py: CB2016 光谱数据可视化模块

提供独立的光谱数据可视化功能：
- 自动加载并展示前100个时间步的频谱
- 对数x轴刻度
- 自适应y轴缩放
"""

import numpy as np
from typing import Optional, Dict, Any

try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class SpectrumVisualizer(FigureCanvas):
    """
    光谱数据可视化器
    
    功能特性：
    - 绘制前100个时间步的频谱
    - 对数x轴刻度
    - 自适应y轴缩放
    """
    
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(10, 7))
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        
        self._current_data: Optional[Dict[str, Any]] = None
        self._colors = plt.cm.viridis(np.linspace(0, 1, 100)) if MATPLOTLIB_AVAILABLE else []
    
    def load_data(self, time_steps: np.ndarray, wavelengths: np.ndarray, 
                  flux: np.ndarray, metadata: Optional[Dict[str, Any]] = None):
        """
        加载光谱数据
        
        Args:
            time_steps: 时间步数组
            wavelengths: 波长数组
            flux: 流量数据 (形状: [n_time_steps, n_wavelengths])
            metadata: 元数据字典（可选）
        """
        self._current_data = {
            'time_steps': time_steps,
            'wavelengths': wavelengths,
            'flux': flux,
            'metadata': metadata
        }
        self.plot_spectra()
    
    def plot_spectra(self):
        """
        绘制前100个时间步的频谱
        
        - x轴: 波长（对数刻度）
        - y轴: 流量（自适应缩放）
        """
        if not self._current_data:
            return
        
        self.ax.clear()
        
        wavelengths = self._current_data['wavelengths']
        flux = self._current_data['flux']
        time_steps = self._current_data['time_steps']
        
        n_steps = min(100, flux.shape[0])
        
        y_min = np.inf
        y_max = -np.inf
        
        for i in range(n_steps):
            y_data = flux[i, :]
            valid_mask = y_data > 0
            
            if np.any(valid_mask):
                x_plot = wavelengths[valid_mask]
                y_plot = y_data[valid_mask]
                
                self.ax.plot(x_plot, y_plot, 
                            label=f'Step {i}: {time_steps[i]:.2e} yr',
                            color=self._colors[i],
                            linewidth=0.8,
                            alpha=0.8)
                
                y_min = min(y_min, np.min(y_plot))
                y_max = max(y_max, np.max(y_plot))
        
        self.ax.set_xscale('log')
        self.ax.set_xlabel('Wavelength (Å)')
        self.ax.set_ylabel('Flux')
        self.ax.set_title('CB2016 Stellar Population Spectra (First 100 Time Steps)')
        self.ax.grid(True, alpha=0.3, which='both')
        # self.ax.legend(loc='best', fontsize=8, ncol=2)
        
        if y_min < y_max:
            y_pad = (y_max - y_min) * 0.05
            self.ax.set_ylim(y_min - y_pad, y_max + y_pad)
        
        self.fig.tight_layout()
        self.draw()
    
    def autoscale(self):
        """
        自动缩放坐标轴以适应数据范围
        """
        if self._current_data:
            self.plot_spectra()
    
    def clear(self):
        """
        清空绘图
        """
        self.ax.clear()
        self.draw()


if __name__ == '__main__':
    print("Spectrum Visualizer Module")
    print("Import this module in your GUI application.")
