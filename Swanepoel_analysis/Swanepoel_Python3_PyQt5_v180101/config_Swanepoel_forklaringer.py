STEP 0: Plot raw data and pay attention to the random electronic noise, fringes frequency and fringes amplitude vs. electronic noise. Especially the relative amplitude of the electronic noise can impact Gaussian filter performance. 

STEP 1. Find all the minima and maxima positions using Gaussian filter settings. Flattening is applied to the to raw data in order to catch the small vertical oscillations. Transmission corrections for slit width are applied here. Transmission corrections grow fast with the photon energy and the measured transmission.

Gaussian filters are required in the search for local minima Tmin and local maxima Tmax in transmission curves with noisy backgrounds. Different spectral parts have different noise levels and therefore different gaussian factor should be applied. For instance, 5 gaussian borders requires 4 gaussian factors resulting in division of the spectrum into 4 parts. It seems easiest to determine gauissian borders and gaussian factors using eV as a unit for the X axis during visual inspection of the raw data.
HIGH gaussian factor = broadband noise filtering.
LOW gaussian factor = narrowband noise filtering.
High gauissian factors (>2) will result in relatively large deviation from the raw data. Gauissian factor of zero or near zero (<0.5) will follow or almost follow the path of the raw data, respectively. Gaussian borders should be typed in the ascending order and their number of enteries is always one more compared with the number of enteries for the gaussian factors.

Interpolation method for local minima Tmin and local maxima Tmax can only be linear or spline.  

STEP 2. Minimize dispersion in the film thickness d by ignoring a number of data points using visual graph inspection. By ingonring data points you will change the order number m_start and the mean film thickness d. It seems best practice to ignore number of data points such that the mean film thickness d falls into the region where it is expected to be. 

STEP 3. Plot refractive index n assuming transparent region (n_trans) and assuming weak and medium absorption region (n1) and correcting n1 for the dispersion in the film thickness d (n2).

STEP 4. Extrapolate the refractive index n2 into the strong absorption region using a polynomial function. The polynomial function is determined by the polyfit order (up to 5th order). Some of the calculated n2 points might not be suitable for the extrapolation. You can exclude these bad points by specifying a range. You can also specify more than one range.

STEP 5. Plot wavenumber k using previously calculated value of absorption alpha.