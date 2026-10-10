# strip_xpy3

## What is this?

In 2026 the STRIP algorithm was open sourced and published in The Journal of Magnetic Resonance (<https://doi.org/10.1016/j.jmr.2026.108112>). This algorithm can be used to improve peak shapes by removing the double dispersive component from NMR data acquired with phase modulation. Alongside the paper, scripts were put on GitHub (<https://github.com/C-J-Bauer/STRIP>) demonstrating usage of the algorithm and ways to externally process NMR data using this algorithm. The use of that software required a certain level of Python programming knowledge that not all NMR spectroscopists possess. To make the STRIP algorithm more accessible to NMR users, the scripts now provided in strip_xpy3 were written with the intention that they could be used directly from within Bruker TopSpin software by anyone, regardless of their level of Python programming experience.

## How does STRIP work?

Simply. The algorithm takes a guess of the pure absorption spectrum, transforms this into a guess of the dispersion signal and subtracts this from the input spectrum containing phase-twist peaks. This provides an improved guess of the pure absorption spectrum. The algorithm is iterative. The improved guess for the pure absorption spectrum is then transformed into an improved guess for the dispersion signal, which is then subtracted from the input data and so on until convergence. In contrast to other processing methods to remove phase-twist peaks, STRIP does not attempt to model the input data (such as assuming exponentially decaying FID data). The initial guess of the absorption spectrum is the absolute value (magnitude) of the input spectrum. Consequently, the only data input is the spectrum with phase-twist peaks. In practice complete convergence may take many iterations, but good enough spectra can be produced with just a few. The default number of iterations is 15, which should produce good results in most cases. For details on the STRIP algorithm see the paper (<https://doi.org/10.1016/j.jmr.2026.108112>) or the preprint on GitHub (<https://github.com/C-J-Bauer/STRIP>).

## When to use STRIP?

Let us assume that you have acquired data from a phase-twist experiment and you want to remove the phase-twist peaks. Previously there have been 2 different approaches, either model the data (using linear prediction, FDM , CUPID etc) or use the model-free approach of doing a magnitude calculation to create the absolute value spectrum. The advantage of a magnitude calculation is that it is trivial to perform since there are no data-specific parameters that need to be set. The disadvantage is that the peaks have very broad tails. The model-based methods have much better resolution but require more time and effort to set up optimally. Being model-free, STRIP offers the advantages of both approaches. It is trivial to perform and it provides resolution nearly as good as a pure-absorption spectrum (if generating such a spectrum were possible). The only downside is that negative phase-twist peaks are not handled well by this method. However, for experiments such as 2D J-Spectroscopy, the peaks of interest are all positive, whereas negative peaks from strong coupling artefacts are of lower intensity and not common.

It follows that the answer of "When to use STRIP?" is whenever you have spectra containing phase-twist peaks of the same sign. In these cases use it to replace or complement doing a magnitude calculation.

## How to use strip_xpy3 on a 2D J-Spectrum in TopSpin

Best results are achieved if the spectrum has been acquired so that no first-order phase corrections are needed. The first step is to calculate the zero-order phase correction needed in F2 by phasing the first increment of the 2D data. In the PROCPARS display in TopSpin set PHC0 in F2 to the zero order phase correction determined from the first increment. If the acquired data is good PHC0 in F1 and PHC1 in F1 and F2 can be set to 0. Set PH_mod to pk in F1 and F2. FIDs should be zero filled before transformation - so make sure SI is at least twice TD in F1 and F2. Set the window functions in F1 and F2 as you choose, but remember that STRIP does not rely on removing dispersive components by aggressive windowing. Typing 'xfb' should display a spectrum containing phase-twist peaks. If you set up STRIP as described below all that you need to do to run STRIP is type 'strip'. No manual tweaking is needed.

## How fast is STRIP

The speed of execution can be improved by running elements of the algorithm in parallel by using multiple 'workers' or by running on a GPU. Consider the following example timings on a system with an AMD Ryzen 5800X and an Nvidia GeForce RTX 5060 Ti GPU, each equipped with 16GB of RAM. The size of the input matrix was 1024x16384.

| STRIP Optimization | Time (s) | Speedup |
| ------------- | ------: | -----: |
| No optimization | 23.5 | - |
| With workers set to 6 | 11.5 | x2.04 |
| Using GPU | 1.55 | x15.16 |

It is clear that using the Nvidia GPU is the fastest option and if your system has one it is highly recommended to use it. If not, performance can still be improved by running on a CPU using more than one worker. The optimal number of workers will depend on the particular CPU being used. In practice processing will take a little longer, since the execution of STRIP is just a single part of the processing. Other things that need to happen are for the 2rr and 2ii files to be read in, the shearing of the data to remove the 45 degree tilt and the results to be written out to a 2rr file. The amount of time that these operations take is not included in the timings above.

## How to install strip_xpy3

If you have an Nvidia GPU that you would like to use the first step is to install the Nvidia CUDA toolkit. This can be done by following the Nvidia CUDA toolkit installation instructions at <https://docs.nvidia.com/cuda/index.html>. Depending on the model of your GPU the major version of your CUDA toolkit may be 12 or 13 (or perhaps higher in future). Remember this number since you will need to use it later. There is no need to install the CUDA toolkit if you do not intend to use a GPU for STRIP processing.

The code can be installed from a zip or tar file (which can be found on GitHub or ResearchGate) or can be cloned directly from the GitHub repository (git clone https://github.com/C-J-Bauer/strip_xpy3). If a tar or zip file is used the version number will be appended to the root directory name. For example, if you download strip_xpy3-1.0.2.zip then the root directory of the code will be called strip_xpy3-1.0.2. If you clone directly from GitHub the version number will not be appended and the root directory will simply be called strip_xpy3. The following instructions assume that the root directory is called strip_xpy3. If you have a version number appended to your root directory (and you wish to keep that name) then change all instances of "strip_xpy3" in the instructions in this document to the appropriate name. Alternatively, rename the root directory to strip_xpy3.

Next, either get a release zip (or tar) file from GitHub and extract the contents into your chosen directory or clone the repository with git. It will create a sub-directory called strip_xpy3 containing the python scripts. These scripts have a dependency on other Python modules such as NumPy, SciPy, nmrglue, and a couple of modules supplied by Bruker within the TopSpin application tree. The use of nmrglue to perform the reading and writing of Bruker data files is required for this script to work. This is because using the Bruker TopSpin API to perform these tasks causes failures when using large file sizes. It may be that as a user of a system you are unable to change the modules used by the instance of Python installed within TopSpin. This is not a problem, but it will require a small amount of work on your part when installing strip_xpy3. The standard solution to this type of issue is to install a local python environment that includes the required modules and then use that for running strip_xpy3. The following instructions are for setting up such an environment. It assumes you already have a python3 executable in your path, but if not it can be installed from <https://www.python.org/downloads/> (or the Microsoft store on Windows).

Change directory into the root directory of the unpacked or cloned files and create a virtual environment called env with python.

    cd strip_xpy3
    python -m venv env

The next step is to activate it in your current command line session. On Linux and macOS, use this command:

    source env/bin/activate

Whereas on Windows systems, you should run these commands in a PowerShell window:

    .\env\Scripts\Activate.ps1

Once you are in the environment you will notice a change to the shell prompt - it will show (env). Now you can install the required packages using pip:

    pip install numpy scipy nmrglue

We also need to install the two modules provided by Bruker. These you should be able to find in your TopSpin application directory, within the python examples directory. For example, assuming that we have the version 5.0.0 of the TopSpin Processing these modules would likely be located in /opt/topspinpr5.0.0/python/examples on Linux or c:\Bruker\TopSpinPr5.0.0\python\examples on Windows. The names of the modules needed are of the form ts_remote_api-XXXXX-py3-none-any.whl and bruker_nmr_api_XXXXX-py3-none-any.whl (where the XXXXX is a version number). The easiest way to install these would be to (within your custom shell environment) to cd to the directory containing the modules, then type

    pip install ts_*.whl bruker_*.whl

Finally, if you intend to use an Nvidia GPU (and have already installed the CUDA toolkit as described above) you should also run a command to install CuPy. The CuPy module to install will depend on the major version of the CUDA toolkit that you have already installed. The minor version number is not used in the package name and is replaced with an 'x'. For example, if you have installed version 13.3 you will need to install cupy-cuda13x. Be careful to install the correct package.

For a CUDA major version of 12 type

    pip install cupy-cuda12x

Whereas for a CUDA major version of 13, use

    pip install cupy-cuda13x

## Configuring TopSpin

The strip_xpy3 scripts use the TopSpin API through a network interface. This is used to allow the scripts to determine the current dataset being worked on. The STRIP scripts will fail if the TopSpin network interface has not been started. Starting it involves clicking on the 'Setup Preferences' gearwheel button in the top right corner of the TopSpin window and then selecting the 'Change' button alongside the 'Manage TopSpin Network Interface' item of the Python3+ section. There is a start button in the popup that appears. There is a checkbox that says "Start every time that TopSpin is started" to avoid the necessity of starting it manually each time you open TopSpin. However, on some platforms (such as Linux) the 'OK' button to confirm this change is broken. Pressing 'Cancel' will still leave the interface running (if it was started), but will not register the checkbox change.

Also in the Python3+ section it is possible to change the path to the Python executable. On some platforms (such as Windows) a Python executable is provided within TopSpin. On other platforms, such as Linux, it isn't. It may be that your Linux installation has already been configured for you and no changes are required, if not enter the path to the standard 'vanilla' Python3 shipped with your system - such as /usr/bin/python3.

It should now be possible to test the STRIP processing. Display a spectrum containing phase-twist peaks as described above. In the command entry box in TopSpin type:

    xpy3 {path to your strip_xpy3 directory}/strip.py

On my Linux system I installed strip_xpy3 into /home/chris/projects/nmr/strip_xpy3 so I would type:

    xpy3 /home/chris/projects/nmr/strip_xpy3/strip.py

On my Windows system I installed strip_xpy3 into c:\Users\Chris\NMR\strip_xpy3 so I would type:

    xpy3 C:\Users\Chris\NMR\strip_xpy3\strip.py

These are quite fiddly commands to enter so I would recommend creating a macro 'strip' in the user section of the TopSpin macro editor 'edmac'. This will make it possible to run STRIP processing on the spectrum just by typing 'strip'.  

Experienced Python programmers may be wondering how the python environment that we created earlier is used. The answer is that the python script that we call, strip.py, is just a simple 'wrapper' script that executes the main script strip_xpy3.py that does all of the work. That script is run within the custom environment we created. This ensures that all of the required packages are available to strip_xpy3.py even though strip.py could be executed from a Python environment within TopSpin potentially lacking the required modules.

## Post installation configuration of STRIP defaults

There are various options that can be set in the script strip_defaults.py so that you can customize your STRIP processing.  Alternatively most of these options can be overridden on the command line when running the xpy3 script from within TopSpin. Sadly macro commands do not allow for setting parameters on the fly, so parameters must be appended to the full xpy3 command rather than a 'strip' macro. The good news is that once you have set up strip_xpy3 for your hardware, by customizing strip_defaults.py, it is unlikely that you will ever want to override any defaults.

The installation contents of strip_defaults.py are as follows:

    # These defaults can be overridden by command line arguments
    NUMBER_OF_ITERATIONS     = 15      # Number of iterations for the STRIP algorithm
    QUICK_AND_DIRTY          = False   # Set to True to use the quick and dirty version of the STRIP algorithm, False to use the full version
    PHASE_TWIST_REFLECTED    = True    # Set to True if the phase twist is reflected, False otherwise
    SHEAR_DATA               = True    # Set to True to shear the data to remove the 45 degree tilt, False otherwise
    REVERSE_SHEAR            = False   # Set to True to reverse the shear, False otherwise
    OVERWRITE_EXISTING_DATA  = False   # Set to True to overwrite existing data, False to create new proc number
    SCIPY_WORKERS            = 6       # Number of workers for parallel processing in SciPy (irrelevant if using GPU)
    ABSOLUTE_VALUE           = False   # If true perform an absolute value (magnitude) calculation instead of STRIP processing

    # This default cannot be overridden by command line arguments. It is for testing purposes only.
    # It forces the use of the CPU even if a GPU is available. This is useful for testing the CPU implementation of the STRIP algorithm. 
    FORCE_CPU                = False   # Set to True to force the use of CPU even if GPU is available

It is quite likely you will not need to change anything. But I will explain what each of these options does.

### Number of iterations

The number of iterations for the STRIP algorithm. The default value is 15, which should give excellent results.

### Quick and dirty version

This option determines whether or not to use the quick and dirty version of the STRIP algorithm. This is a faster but noisier version of STRIP. Only for the curious. It is not recommended to use this method.

### Phase twist reflected

The need for this parameter stems from the way that spectral data is represented. If a spectrum has been reflected in either of the F1 or F2 dimensions an immediately obvious change to the spectrum is that the direction of the diagonal changes. For example, it may change from slanting upwards / to slanting downwards \ or vice versa. A more subtle change is to the nature of phase twist peaks. A phase-twist peak consists of an absorption and a dispersion component. Reflecting an absorption component appears identical to a translation, whereas reflecting a dispersion component appears identical to a translation and an inversion. It follows that a reflected phase-twist peak is different and a slightly altered implementation of STRIP must be used to remove the dispersion component. The default value for this parameter is True. This is to handle the case of 2D J-Spectra in TopSpin where by default it reverses an axis. This is why the 45 degree tilt slants in the \ direction. If for some reason you have an upward / slant set this parameter to be False.

### Shear data

If set to True, the data will be sheared so that the 45 degree tilt is removed from the spectrum. This makes it easier to display multiplets.

### Reverse shear

The shear direction is calculated according to the value of Phase Twist Reflected. You should never need to manually override the shear direction, but in the unlikely event you ever do, set this flag to True to reverse the shear direction.

### Overwrite existing data

The standard behaviour of this program is to create a new proc number each time it is run. If you want to overwrite the original proc number, set this flag to True.

### SciPy workers

If you have not configured a GPU to run STRIP you will be reliant on your CPU. Improvements in CPU performance can be achieved by increasing the number of workers used by SciPy. The optimal number of workers to use should be entered here. The value will depend on the model of CPU you are using. Performance will be slower if you enter a number that is too low or too high. It is recommended that if you will be using the CPU for STRIP that you run STRIP several times with different numbers of workers to determine which number works best for your system. The output from each run reports the time spent within STRIP.

### Absolute value

If True STRIP is not performed and a magnitude calculation is performed instead.

### Force CPU

If True a calculation on the CPU is performed.

## Overriding default options with command line arguments

All of the above default options (apart from Force CPU) can be overridden from the command line. To see the how this can be done call the xpy3 program with the -h option. Note that if there is an option that you frequently override it is possible to create an additional macro in edmac with that overridden value. For example, the number of iterations is set with the -i option. If you find that sometimes you prefer to use 20 iterations you can create a macro called strip_20 and append the command line argument "-i 20" in the macro.
