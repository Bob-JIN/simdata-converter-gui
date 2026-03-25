# FITS文件数据结构

## 一、FITS文件结构分析

### 1.1 基本信息
- **文件名**: CB16_mup100_ssp_CO1p0.fits
- **总HDU数量**: 10个
- **光谱数据记录数**: **2016条**
- **波长点数**: 12619个

### 1.2 HDU组成
| HDU名称 | 类型 | 字段数 | 说明 |
|---------|------|--------|------|
| PRIMARY | PrimaryHDU | - | 主HDU |
| GALAXY PROPERTIES | BinTableHDU | 22 | 星系属性 |
| STAR FORMATION | BinTableHDU | 8 | 恒星形成参数 |
| STAR FORMATION BINS | BinTableHDU | 8 | 恒星形成箱参数 |
| DUST ATTENUATION | BinTableHDU | 15 | 尘埃衰减参数 |
| LICK SPECTRAL INDICES | BinTableHDU | 70 | Lick光谱指数 |
| HII EMISSION | BinTableHDU | 30 | HII区发射参数 |
| SPECTRAL INDICES | BinTableHDU | 3 | 光谱指数 |
| FULL SED WL | BinTableHDU | 1 | 完整SED波长 |
| FULL SED | ImageHDU | - | 完整SED流量数据 |

### 1.3 数据形状
- **FULL SED数据形状**: (2016, 12619) → (光谱数, 波长数)

---

## 二、识别到的仿真参数列表

### 2.1 总计提取参数
- **总参数数量**: 156个

### 2.2 按HDU分类的参数
| HDU名称 | 参数数量 |
|---------|----------|
| HII EMISSION | 30 |
| GALAXY PROPERTIES | 22 |
| STAR FORMATION | 8 |
| STAR FORMATION BINS | 8 |
| DUST ATTENUATION | 15 |
| LICK SPECTRAL INDICES | 70 |
| SPECTRAL INDICES | 3 |

### 2.3 关键物理参数

#### 金属丰度相关
- **Z_ISM**: 星际介质金属丰度 (范围: 0.0002 - 0.03)
- **logOH**: 对数氧丰度 (范围: 6.83 - 9.03)
- **mass_w_Z**: 质量加权金属丰度
- **lumin_w_Z**: 光度加权金属丰度

#### 电离参数
- **logU**: 电离参数 (范围: -4.0 - -1.0)
- **N_ion**: 电离光子数对数 (范围: 50.05 - 52.80)
- **N_ion_HeI**: HeI电离光子数
- **N_ion_HeII**: HeII电离光子数
- **xi_ion**: 电离效率
- **xi_ion_unatt**: 无衰减电离效率
- **xi_ion_unatt_stellar**: 无衰减恒星电离效率

#### 尘埃参数
- **xi_d**: 尘埃-金属质量比 (固定: 0.3)
- **tauV_eff**: 有效V波段光学深度
- **tauV_HII_max**: HII区最大V波段光学深度
- **tauV_HII_accounting**: HII区V波段光学深度核算
- **tauB_perp**: 垂直方向B波段光学深度
- **tauV_eff_ang_aver**: 角平均有效V波段光学深度
- **A_1500**: 1500Å消光
- **A_1500_stellar**: 恒星1500Å消光
- **A_B**: B波段消光
- **A_B_stellar**: 恒星B波段消光
- **A_V**: V波段消光
- **A_V_stellar**: 恒星V波段消光
- **mu**: 几何因子
- **attenuation_type**: 衰减类型
- **t_birth_clouds**: 出生云时间
- **inclination**: 倾角

#### 质量相关
- **M_tot**: 总质量 (固定: 1e6 Msun)
- **M_star**: 恒星质量 (范围: 890240 - 1000000)
- **M_liv**: 存活恒星质量
- **M_remnants**: 遗迹质量
- **mass_w_age**: 质量加权年龄
- **lumin_w_age**: 光度加权年龄

#### 年龄相关
- **bin_ssp_age**: 简单恒星族年龄 (范围: 1 - 10000000 yr)
- **max_stellar_age**: 最大恒星年龄
- **bin_start_age**: 箱起始年龄
- **bin_end_age**: 箱结束年龄
- **bin_max_stellar_age**: 箱最大恒星年龄

#### 恒星形成相关
- **SFR**: 恒星形成率 (固定: 0.1 Msun/yr)
- **sSFR**: 比恒星形成率 (固定: -7.0)
- **SFR_10**: 10Myr平均SFR
- **SFR_100**: 100Myr平均SFR
- **current_sfr_timescale**: 当前SFR时标
- **bin_sfh_type**: 恒星形成历史类型
- **bin_mass**: 箱质量
- **bin_tau**: 箱τ值
- **bin_chem_abund_1**: 化学丰度1

#### C/O比相关
- **bin_chem_abund_1**: 化学丰度(可用于C/O比) (范围: 0.0002 - 0.03)

#### 光度相关
- **L_UV**: UV光度对数 (范围: 24.64 - 27.22)
- **L_UV_unatt**: 无衰减UV光度
- **L_UV_unatt_stellar**: 无衰减恒星UV光度
- **UV_slope**: UV斜率

#### 发射线光度
包含24条发射线的观测和本征光度:
- C4d_1549, HeBaA_1640, O3d_1665, C3d_1909
- O2d_3727, He2_4686, HBaB_4861, O3_5007
- O1_6300, HBaA_6563, N2_6584, S2d_6720
- 等等...

#### Lick光谱指数
70个Lick光谱指数，包括:
- CN_1, CN_2, Ca4227, G4300, Fe4383, Ca4455, Fe4531, Fe4668
- H_beta, Fe5015, Mg_1, Mg_2, Mg_b, Fe5270, Fe5335, Fe5406
- Fe5709, Fe5782, Na_D, TiO_1, TiO_2, H_delta_A, H_gamma_A
- H_delta_F, H_gamma_F, D_4000, B4_VN, CaII8498, CaII8542, CaII8662
- MgI8807, H8_3889, H9_3835, H10_3798, BH_HK
- 以及对应的_Lick版本

#### 其他光谱指数
- **CIV1549_EW**: CIV 1549Å等值宽度
- **CIII1909_EW**: CIII 1909Å等值宽度
- **HeII1640_EW**: HeII 1640Å等值宽度

#### 其他参数
- **redshift**: 红移 (固定: 0)
- **luminosity_distance**: 光度距离
- **sigma**: 速度弥散
- **Half_light_R**: 半光半径
- **formation_redshift**: 形成红移
- **sf_present**: 恒星形成存在标志
