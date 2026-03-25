# FITS File Data Structure

## 1. FITS File Structure Analysis

### 1.1 Basic Information
- **Filename**: CB16_mup100_ssp_CO1p0.fits
- **Total HDU Count**: 10
- **Spectral Data Records**: **2016**
- **Wavelength Points**: 12619

### 1.2 HDU Composition
| HDU Name | Type | Field Count | Description |
|----------|------|-------------|-------------|
| PRIMARY | PrimaryHDU | - | Primary HDU |
| GALAXY PROPERTIES | BinTableHDU | 22 | Galaxy properties |
| STAR FORMATION | BinTableHDU | 8 | Star formation parameters |
| STAR FORMATION BINS | BinTableHDU | 8 | Star formation bin parameters |
| DUST ATTENUATION | BinTableHDU | 15 | Dust attenuation parameters |
| LICK SPECTRAL INDICES | BinTableHDU | 70 | Lick spectral indices |
| HII EMISSION | BinTableHDU | 30 | HII region emission parameters |
| SPECTRAL INDICES | BinTableHDU | 3 | Spectral indices |
| FULL SED WL | BinTableHDU | 1 | Full SED wavelength |
| FULL SED | ImageHDU | - | Full SED flux data |

### 1.3 Data Shape
- **FULL SED Data Shape**: (2016, 12619) → (spectra count, wavelength count)

---

## 2. Identified Simulation Parameters List

### 2.1 Total Extracted Parameters
- **Total Parameter Count**: 156

### 2.2 Parameters by HDU
| HDU Name | Parameter Count |
|----------|-----------------|
| HII EMISSION | 30 |
| GALAXY PROPERTIES | 22 |
| STAR FORMATION | 8 |
| STAR FORMATION BINS | 8 |
| DUST ATTENUATION | 15 |
| LICK SPECTRAL INDICES | 70 |
| SPECTRAL INDICES | 3 |

### 2.3 Key Physical Parameters

#### Metallicity-related
- **Z_ISM**: ISM metallicity (range: 0.0002 - 0.03)
- **logOH**: Logarithmic oxygen abundance (range: 6.83 - 9.03)
- **mass_w_Z**: Mass-weighted metallicity
- **lumin_w_Z**: Luminosity-weighted metallicity

#### Ionization Parameters
- **logU**: Ionization parameter (range: -4.0 - -1.0)
- **N_ion**: Logarithm of ionizing photon count (range: 50.05 - 52.80)
- **N_ion_HeI**: HeI ionizing photon count
- **N_ion_HeII**: HeII ionizing photon count
- **xi_ion**: Ionization efficiency
- **xi_ion_unatt**: Unattenuated ionization efficiency
- **xi_ion_unatt_stellar**: Unattenuated stellar ionization efficiency

#### Dust Parameters
- **xi_d**: Dust-to-metal mass ratio (fixed: 0.3)
- **tauV_eff**: Effective V-band optical depth
- **tauV_HII_max**: Maximum V-band optical depth of HII region
- **tauV_HII_accounting**: V-band optical depth accounting for HII region
- **tauB_perp**: Perpendicular B-band optical depth
- **tauV_eff_ang_aver**: Angle-averaged effective V-band optical depth
- **A_1500**: 1500Å extinction
- **A_1500_stellar**: Stellar 1500Å extinction
- **A_B**: B-band extinction
- **A_B_stellar**: Stellar B-band extinction
- **A_V**: V-band extinction
- **A_V_stellar**: Stellar V-band extinction
- **mu**: Geometric factor
- **attenuation_type**: Attenuation type
- **t_birth_clouds**: Birth cloud time
- **inclination**: Inclination angle

#### Mass-related
- **M_tot**: Total mass (fixed: 1e6 Msun)
- **M_star**: Stellar mass (range: 890240 - 1000000)
- **M_liv**: Living stellar mass
- **M_remnants**: Remnant mass
- **mass_w_age**: Mass-weighted age
- **lumin_w_age**: Luminosity-weighted age

#### Age-related
- **bin_ssp_age**: Simple stellar population age (range: 1 - 10000000 yr)
- **max_stellar_age**: Maximum stellar age
- **bin_start_age**: Bin start age
- **bin_end_age**: Bin end age
- **bin_max_stellar_age**: Bin maximum stellar age

#### Star Formation-related
- **SFR**: Star formation rate (fixed: 0.1 Msun/yr)
- **sSFR**: Specific star formation rate (fixed: -7.0)
- **SFR_10**: 10Myr averaged SFR
- **SFR_100**: 100Myr averaged SFR
- **current_sfr_timescale**: Current SFR timescale
- **bin_sfh_type**: Star formation history type
- **bin_mass**: Bin mass
- **bin_tau**: Bin tau value
- **bin_chem_abund_1**: Chemical abundance 1

#### C/O Ratio-related
- **bin_chem_abund_1**: Chemical abundance (can be used for C/O ratio) (range: 0.0002 - 0.03)

#### Luminosity-related
- **L_UV**: Logarithmic UV luminosity (range: 24.64 - 27.22)
- **L_UV_unatt**: Unattenuated UV luminosity
- **L_UV_unatt_stellar**: Unattenuated stellar UV luminosity
- **UV_slope**: UV slope

#### Emission Line Luminosities
Contains observed and intrinsic luminosities for 24 emission lines:
- C4d_1549, HeBaA_1640, O3d_1665, C3d_1909
- O2d_3727, He2_4686, HBaB_4861, O3_5007
- O1_6300, HBaA_6563, N2_6584, S2d_6720
- etc.

#### Lick Spectral Indices
70 Lick spectral indices, including:
- CN_1, CN_2, Ca4227, G4300, Fe4383, Ca4455, Fe4531, Fe4668
- H_beta, Fe5015, Mg_1, Mg_2, Mg_b, Fe5270, Fe5335, Fe5406
- Fe5709, Fe5782, Na_D, TiO_1, TiO_2, H_delta_A, H_gamma_A
- H_delta_F, H_gamma_F, D_4000, B4_VN, CaII8498, CaII8542, CaII8662
- MgI8807, H8_3889, H9_3835, H10_3798, BH_HK
- and corresponding _Lick versions

#### Other Spectral Indices
- **CIV1549_EW**: CIV 1549Å equivalent width
- **CIII1909_EW**: CIII 1909Å equivalent width
- **HeII1640_EW**: HeII 1640Å equivalent width

#### Other Parameters
- **redshift**: Redshift (fixed: 0)
- **luminosity_distance**: Luminosity distance
- **sigma**: Velocity dispersion
- **Half_light_R**: Half-light radius
- **formation_redshift**: Formation redshift
- **sf_present**: Star formation presence flag
