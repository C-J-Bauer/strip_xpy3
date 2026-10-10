import numpy as np
from bruker.api.topspin import Topspin
from bruker.data.nmr  import *
import nmrglue as ng
import strip_defaults
import argparse
import time
from scipy.fft import set_workers
from pathlib import Path
import math
import sys

VERSION = '1.0.2'
REFERENCE = 'C. J. Bauer, "STRIP: A processing method to improve peakshapes in spectra acquired from multidimensional phase-modulated NMR experiments," Journal of Magnetic Resonance, vol. 390, Art. no. 108112, 2026, doi: 10.1016/j.jmr.2026.108112.'

try:
    # throw an exception if CuPy is not available or if FORCE_GPU is set
    if strip_defaults.FORCE_CPU:
        raise ImportError("CuPy is disabled by FORCE_CPU default.")
    import cupy as cp
    from strip_algo_cupy import STRIP, STRIP_quick_and_dirty, PROC_INFO
except ImportError:
    from strip_algo import STRIP, STRIP_quick_and_dirty, PROC_INFO
    
class StripError(Exception):
    pass


def shear_data(spectrum, args, shear_ratio):
    """
    Shear the spectrum to remove the 45 degree tilt

    Parameters:
        spectrum: The output from STRIP. A real numpy data array that is modified in place.
        args: The command-line arguments.
        shear_ratio: The shear ratio calculated from the dataset parameters.
    """
    do_clockwise = args.phase_twist_reflected
    if args.reverse_shear:
        do_clockwise = not do_clockwise
    f1Size = spectrum.shape[0]
    middle = f1Size // 2
    
    for i in range(f1Size):
        distance_from_middle = i - middle
        if do_clockwise:
            shift_amount = distance_from_middle * shear_ratio
        else:
            shift_amount = -distance_from_middle * shear_ratio
        integer_part = math.floor(shift_amount)
        remainder = shift_amount - integer_part
        next_integer = integer_part + 1
     
        lower_spectrum = np.roll(spectrum[i,:], integer_part)
        upper_spectrum = np.roll(spectrum[i,:], next_integer)
        spectrum[i,:] = (1.0 - remainder) * lower_spectrum + remainder * upper_spectrum        
    
                
def strip_process(complex_spectrum, args, shear_ratio):
    """
    Process the complex data using the STRIP algorithm to remove phase-twist from the data.
    
    Parameters:
        complex_spectrum: The complex input numpy data array.
        args: The command-line arguments.
        
    Returns:
        numpy.ndarray: The processed spectrum of the input data.
    """
    print("Starting processing...")
    start = time.time()
    with set_workers(args.scipy_workers):
        msg = PROC_INFO()
        print(msg)
        if args.phase_twist_reflected:
            twist_type_factor = 1.0
        else:
            twist_type_factor = -1.0
        if args.absolute_value:
            processed = np.abs(complex_spectrum)
            method = "absolute value (magnitude) calculation"
        elif args.quick_and_dirty:
            processed = STRIP_quick_and_dirty(complex_spectrum, args.iterations, twist_type_factor)
            method = "quick and dirty STRIP processing"
        else:
            processed = STRIP(complex_spectrum, args.iterations, twist_type_factor)
            method = "STRIP processing"
    print("Finished " + method + " in " + str(time.time() - start) + " seconds.")
    if args.shear_data:
        print("Shearing data...")
        shear_data(processed, args, shear_ratio)
    return processed
        

def str_to_bool(value):
    if isinstance(value, bool):
        return value
    if value.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif value.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError(f"Boolean value expected. Got '{value}'.")    

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--iterations', type=int, default=strip_defaults.NUMBER_OF_ITERATIONS,
                        help='Number of iterations for the STRIP algorithm')
    parser.add_argument('-q', '--quick_and_dirty', type=str_to_bool, default=strip_defaults.QUICK_AND_DIRTY,
                        help='Set to True to use the quick and dirty version of the STRIP algorithm, False to use the full version')
    parser.add_argument('-a', '--absolute_value', type=str_to_bool, default=strip_defaults.ABSOLUTE_VALUE,
                        help='If true perform an absolute value (magnitude) calculation instead of STRIP processing')
    parser.add_argument('-p', '--phase_twist_reflected', type=str_to_bool, default=strip_defaults.PHASE_TWIST_REFLECTED,
                        help='Set to True if the phase twist is reflected, False otherwise')
    parser.add_argument('-s', '--shear_data', type=str_to_bool, default=strip_defaults.SHEAR_DATA,
                        help='Set to True to shear the data to remove the 45 degree tilt, False otherwise')
    parser.add_argument('-r', '--reverse_shear', type=str_to_bool, default=strip_defaults.REVERSE_SHEAR,
                        help='Set to True to reverse the shear, False otherwise')
    parser.add_argument('-o', '--overwrite_existing_data', type=str_to_bool, default=strip_defaults.OVERWRITE_EXISTING_DATA,
                        help='Set to True to overwrite existing data, False otherwise')
    parser.add_argument('-w', '--scipy_workers', type=int, default=strip_defaults.SCIPY_WORKERS,
                        help='Number of workers for parallel processing in SciPy (irrelevant if using GPU)')
    parser.add_argument('-v', '--version',  action='version', version=f'%(prog)s {VERSION} ({REFERENCE})')
    args = parser.parse_args()

    try:
        top = Topspin()
        dp = top.getDataProvider()
    except Exception as e:
        raise StripError("Failure to connect to TopSpin : " + str(e))

    current_dataset = dp.getCurrentDatasetIdentifier()
    if not current_dataset:
        raise StripError("No dataset is currently open in TopSpin.")
    
    current_procno = Path(current_dataset).name
    if not current_procno or not current_procno.isdigit():
        raise StripError("No processing number (procno) is currently selected in TopSpin.")
    current_procno = int(current_procno)

    source = dp.getNMRData(current_dataset)
    if not source:
        raise StripError(f"The dataset {current_dataset} does not exist.")

    num_dims = source.getDimension()
    if num_dims != 2:
        raise StripError(f"The dataset is not 2D. It has {num_dims} dimensions.")
    
    pdata_dir = str(current_dataset)
    # check if 2rr exists in the pdata directory
    rr_file_path = Path(pdata_dir) / '2rr'
    if not rr_file_path.exists():
        raise StripError(f"The '2rr' file does not exist. Either it is a 1d view or the 2rr file is missing. Please check the dataset.")
    
    print(REFERENCE)
    print()
    print('Dataset: {}'.format(current_dataset)  )
    # Transform the data so that we have spectrum with phase-twist peaks
    print('Transforming this dataset to create a spectrum with phase-twist peaks ...')
    source.launch('xfb')
        
    size_f2 = int(source.getPar("2s SI")) # Matrix width (e.g., 32768)
    size_f1 = int(source.getPar("1s SI")) # Matrix height (e.g., 2048)
    sw_f2 = float(source.getPar("2s SW")) # Spectral width in Hz (e.g., 10000.0)
    sw_f1 = float(source.getPar("1s SW")) # Spectral width in Hz (e.g., 10000.0)
    shear_ratio = (size_f2 / sw_f2) / (size_f1 / sw_f1) # Shear ratio for 45 degree tilt correction (assuming quadrature detection in both dimensions)

    print(f"Dataset dimensions: {size_f1} x {size_f2}")
    
    print("Reading spectrum data ...")
    # Sadly TopSpin API fails with large data matrices, so we use nmrglue instead
    dic, data = ng.bruker.read_pdata(pdata_dir, all_components=True)

    # 'data' is a 2D NumPy array containing the real-real spectrum matrix
    if len(data) != 2:
        raise StripError("Expected both an rr and an ii matrix. Instead found {} matrices.".format(len(data)))

    if data[0].shape != (size_f1, size_f2) or data[1].shape != (size_f1, size_f2):
        raise StripError("Data shape does not match expected dimensions.")


    source_complex = data[0] + 1j * data[1]
    processed = strip_process(source_complex, args, shear_ratio)
    
    
    if args.overwrite_existing_data:
        ng.bruker.write_pdata(pdata_dir, dic, processed, scale_data=True, overwrite=True)
        save_procno = current_procno
        print(f"Processed data written to existing procno: {save_procno}")
    else:
        existing_procnos = []
        parent = Path(pdata_dir).parent
        for path in parent.iterdir():
            if path.is_dir() and path.name.isdigit():
                existing_procnos.append(int(path.name))
        
        # Find first unused procno after the current procno
        procno_set = set(existing_procnos)
        save_procno = current_procno
        while save_procno in procno_set:
            save_procno = save_procno + 1
            
        source.launch('wrp ' + str(save_procno))  # Launch the new procno in TopSpin

        # make sure it works on windows and linux by using pathlib to create the new directory
        pdata_dir = parent / str(save_procno)
        ng.bruker.write_pdata(pdata_dir, dic, processed, scale_data=True, overwrite=True)
        print(f"Processed data written to new procno: {save_procno}")
        
    # Remove the 2ii from the procno directory to avoid confusion.
    # If it were posible in nmr_glue to write the 2ii file, we would save the B-Transform of the 2rr file,
    # but nmr_glue does not appear to support writing the 2ii file. So we just remove it.
    # It is likely of no interest anyway.
    ii_file_path = Path(pdata_dir) / '2ii'
    if ii_file_path.exists():
        ii_file_path.unlink()
        print(f"Removed 2ii file from procno: {save_procno}")

    
if __name__ == "__main__":
     try:
        main()
        print("Processing complete.")
     except StripError as e:
        print(f"Error: {e}")
        print("Processing failed.")
        sys.exit(1)