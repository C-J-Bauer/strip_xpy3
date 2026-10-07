
# These defaults can be overriden by command line arguments
NUMBER_OF_ITERATIONS     = 15      # Number of iterations for the STRIP algorithm
QUICK_AND_DIRTY          = False   # Set to True to use the quick and dirty version of the STRIP algorithm, False to use the full version
PHASE_TWIST_REFLECTED    = True    # Set to True if the phase twist is reflected, False otherwise
SHEAR_DATA               = True    # Set to True to shear the data to remove the 45 degree tilt, False otherwise
REVERSE_SHEAR            = False   # Set to True to reverse the shear, False otherwise
OVERWRITE_EXISTING_DATA  = False   # Set to True to overwrite existing data, False to create new proc number
SCIPY_WORKERS            = 6       # Number of workers for parallel processing in SciPy (irrelevent if using GPU)
ABSOLUTE_VALUE           = False   # If true perform an absolute value (magnitude) calculation instead of STRIP processing

# This default cannot be overriden by command line arguments. It is for testing purposes only.
# It forces the use of the CPU even if a GPU is available. This is useful for testing the CPU implementation of the STRIP algorithm. 
FORCE_CPU                = False   # Set to True to force the use of CPU even if GPU is available