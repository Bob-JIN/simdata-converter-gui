# .ised File Format Data Structure and Parsing Documentation

## 1. File Format Overview
.ised is a binary unformatted file format used by the CB2016 stellar population synthesis models, storing stellar spectral data for different ages and metallicities. Two model types are supported:
- Stars-only spectral models (in `isedfiles_stars/` directory)
- Stars + gas emission line models (in `isedfiles_stars+gas/` directory)

Files are stored as Fortran unformatted binary, with record length markers before each read/write operation to facilitate sequential reading.

## 2. Byte Order Specifications
- **Byte order**: Native byte order of the system that generated the file, typically little-endian (x86/x64 architectures)
- **Data types**: Fortran default data types: Integer is 4 bytes, Real is 4-byte single-precision floating point

## 3. Detailed Data Structure

### General File Header Structure
| Offset | Field Name | Data Type | Length | Description |
|--------|------------|-----------|--------|-------------|
| 0x00   | Record length marker | Integer | 4 bytes | Total length of time step array record = (1 + nsteps) * 4 bytes |
| 0x04   | nsteps | Integer | 4 bytes | Number of time steps, fixed at 221 |
| 0x08   | tb array | Real[nsteps] | nsteps*4 bytes | Age values corresponding to each time step (unit: years) |
| 0x08 + nsteps*4 | Record end marker | Integer | 4 bytes | Same as record length marker |
| | | | | |
| Next record start | Record length marker | Integer | 4 bytes | Total length of wavelength array record = (1 + inws) * 4 bytes |
| +0x04 | inws | Integer | 4 bytes | Number of wavelength points:<br>- Stars-only models: 13216<br>- Stars + gas models: 13391 |
| +0x08 | ws array | Real[inws] | inws*4 bytes | Wavelength array, unit: Angstrom (Å) |
| +0x08 + inws*4 | Record end marker | Integer | 4 bytes | Same as record length marker |

### Spectral Data Block Structure
After the file header, spectral data for nsteps time steps are stored consecutively. Each time step has the following structure:
| Offset | Field Name | Data Type | Length | Description |
|--------|------------|-----------|--------|-------------|
| 0x00 | Record length marker | Integer | 4 bytes | Total length of current time step spectral record = (1 + inws) * 4 bytes |
| 0x04 | Reserved field | Integer | 4 bytes | Not used, typically equal to inws |
| 0x08 | fs array | Real[inws] | inws*4 bytes | Spectral flux data for current time step |
| 0x08 + inws*4 | Record end marker | Integer | 4 bytes | Same as record length marker |

## 4. Key Field Explanations
- **tb(n)**: Age of the stellar population at time step n, ranging from 0 years to 14 billion years
- **ws(i)**: Wavelength value at wavelength point i, unit: Angstrom (Å)
- **fs(i,n)**: Spectral flux at wavelength point i, time step n, unit: erg/s/Å/M☉
- **nsteps**: Total number of time steps, uniformly 221 for all models
- **inws**: Number of wavelength points, 13216 or 13391 depending on model type

## 5. Data Block Organization
```
+-------------------+
| Time step array   |
+-------------------+
| Wavelength array  |
+-------------------+
| Time step 1 data  |
+-------------------+
| Time step 2 data  |
+-------------------+
| ...               |
+-------------------+
| Time step 221 data|
+-------------------+
```

## 6. Parsing Notes and Potential Issues
1. **Fortran record marker handling**: Each read/write record has 4-byte length markers before and after. These markers must be skipped during reading to avoid data offset.
2. **Model type identification**: The inws value from the first read determines the model type, which in turn determines the size of subsequent data blocks.
3. **Byte order compatibility**: Byte order conversion is required if files are migrated between systems with different byte orders.
4. **Data precision**: Original data is single-precision floating point. It is recommended to retain single precision when converting to HDF5 to save space.
5. **Time step index correspondence**:
   - Index 1: 0 years
   - Index 35: 1 Myr
   - Index 55: 3 Myr
   - Index 90: 10 Myr
   - Index 136: 100 Myr
   - Index 150: 500 Myr

## 7. Recommended Parsing Methods and Tools

### Python Parsing Solution
```python
import struct
import numpy as np

def read_ised_file(filepath):
    with open(filepath, 'rb') as f:
        # Read time step array
        rec_len = struct.unpack('<i', f.read(4))[0]
        nsteps = struct.unpack('<i', f.read(4))[0]
        tb = np.frombuffer(f.read(nsteps * 4), dtype='<f4')
        struct.unpack('<i', f.read(4))  # Skip end marker
        
        # Read wavelength array
        rec_len = struct.unpack('<i', f.read(4))[0]
        inws = struct.unpack('<i', f.read(4))[0]
        ws = np.frombuffer(f.read(inws * 4), dtype='<f4')
        struct.unpack('<i', f.read(4))  # Skip end marker
        
        # Read spectral data for all time steps
        fs = np.zeros((inws, nsteps), dtype='<f4')
        for n in range(nsteps):
            rec_len = struct.unpack('<i', f.read(4))[0]
            struct.unpack('<i', f.read(4))  # Skip reserved field
            fs[:, n] = np.frombuffer(f.read(inws * 4), dtype='<f4')
            struct.unpack('<i', f.read(4))  # Skip end marker
    
    return tb, ws, fs
```

### HDF5 Conversion Solution
Use the h5py library to write parsed data to HDF5 files:
```python
import h5py

def convert_to_hdf5(input_path, output_path):
    tb, ws, fs = read_ised_file(input_path)
    
    with h5py.File(output_path, 'w') as hf:
        hf.create_dataset('time_steps', data=tb, compression='gzip')
        hf.create_dataset('wavelengths', data=ws, compression='gzip')
        hf.create_dataset('flux', data=fs, compression='gzip')
        
        # Add attributes
        hf.attrs['model_type'] = 'stars_only' if len(ws) == 13216 else 'stars+gas'
        hf.attrs['n_time_steps'] = len(tb)
        hf.attrs['n_wavelength_points'] = len(ws)
        hf.attrs['wavelength_unit'] = 'Angstrom'
        hf.attrs['flux_unit'] = 'erg/s/Å/M☉'
        hf.attrs['time_unit'] = 'year'
```

## 8. Model Parameter Descriptions
Model parameters can be extracted from filenames:
- **zXXX**: Metallicity, e.g., z004 indicates Z=0.004
- **uXpX**: Ionization parameter log Us, e.g., u3p5 indicates log Us=-3.5
- **xiX**: Dust parameter xi_d
- **nX**: Hydrogen number density n_H, unit: cm⁻³
- **mupXXX**: Upper mass limit, unit: M☉
- **CXXX**: C/O abundance ratio relative to solar, unit: %
- **_noLya**: Version without Lyman-alpha emission line
