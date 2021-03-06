# This script is just a test of trying out the edge analysis. I use the TPS
# dose profiles since those are all that I can open at this time. I shall have
# to require the inputed dose profiles to be in DICOM format not in RIT's rv4
# or any other. I do this because I am unaware of any python libraries that
# can allow me to open them.


# Import various libraries.
import numpy, scipy, scipy.ndimage, scipy.signal, dicom
import matplotlib.pyplot, pylab
import skimage.filter.tv_denoise


def savitzky_golay(y, window_size, order, deriv=0):
    try:
        window_size = numpy.abs(numpy.int(window_size))
        order = numpy.abs(numpy.int(order))
    except ValueError, msg:
        raise ValueError("window_size and order have to be of type int")
    if window_size % 2 != 1 or window_size < 1:
        raise TypeError("window_size size must be a positive odd number")
    if window_size < order + 2:
        raise TypeError("window_size is too small for the polynomials order")
    order_range = range(order+1)
    half_window = (window_size -1) // 2
    # precompute coefficients
    b = numpy.mat([[k**i for i in order_range] for k in range(-half_window, \
	  	                                               half_window+1)])
    m = numpy.linalg.pinv(b).A[deriv]
    # pad the signal at the extremes with
    # values taken from the signal itself
    firstvals = y[0] - numpy.abs( y[1:half_window+1][::-1] - y[0] )
    lastvals = y[-1] + numpy.abs(y[-half_window-1:-1][::-1] - y[-1])
    y = numpy.concatenate((firstvals, y, lastvals))
    return numpy.convolve( m, y, mode='valid')


def sg2d( z, window_size, order, derivative=None):
    """
    """
    # number of terms in the polynomial expression
    n_terms = ( order + 1 ) * ( order + 2)  / 2.0

    if  window_size % 2 == 0:
        raise ValueError('window_size must be odd')

    if window_size**2 < n_terms:
        raise ValueError('order is too high for the window size')

    half_size = window_size // 2
 
    # exponents of the polynomial. 
    # p(x,y) = a0 + a1*x + a2*y + a3*x^2 + a4*y^2 + a5*x*y + ... 
    # this line gives a list of two item tuple. Each tuple contains 
    # the exponents of the k-th term. First element of tuple is for x
    # second element for y.
    # Ex. exps = [(0,0), (1,0), (0,1), (2,0), (1,1), (0,2), ...]
    exps = [ (k-n, n) for k in range(order+1) for n in range(k+1) ]
 
    # coordinates of points
    ind = numpy.arange(-half_size, half_size+1, dtype=numpy.float64)
    dx = numpy.repeat(ind, window_size)
    dy = numpy.tile(ind,[window_size, 1]).reshape(window_size**2, )

    # build matrix of system of equation
    A = numpy.empty( (window_size**2, len(exps)) )
    for i, exp in enumerate( exps ):
        A[:,i] = (dx**exp[0]) * (dy**exp[1])
 
    # pad input array with appropriate values at the four borders
    new_shape = z.shape[0] + 2*half_size, z.shape[1] + 2*half_size
    Z = numpy.zeros( (new_shape) )
    # top band
    band = z[0, :]
    Z[:half_size, half_size:-half_size] = \
		    band - numpy.abs(numpy.flipud(z[1:half_size+1, :]) - band)
    # bottom band
    band = z[-1, :]
    Z[-half_size:, half_size:-half_size] = \
		    band + numpy.abs(numpy.flipud(z[-half_size-1:-1, :]) -band)
    # left band
    band = numpy.tile(z[:,0].reshape(-1,1), [1,half_size])
    Z[half_size:-half_size, :half_size] = \
		    band - numpy.abs(numpy.fliplr(z[:, 1:half_size+1]) - band)
    # right band
    band = numpy.tile(z[:,-1].reshape(-1,1), [1,half_size])
    Z[half_size:-half_size, -half_size:] = \
		    band + numpy.abs(numpy.fliplr(z[:, -half_size-1:-1]) - band)
    # central band
    Z[half_size:-half_size, half_size:-half_size] = z
 
    # top left corner
    band = z[0,0]
    Z[:half_size,:half_size] = band - numpy.abs(numpy.flipud(numpy.fliplr(z[1:half_size+1,1:half_size+1])) - band)
    # bottom right corner
    band = z[-1,-1]
    Z[-half_size:,-half_size:] = band + numpy.abs(numpy.flipud(numpy.fliplr(z[-half_size-1:-1,-half_size-1:-1]) ) - band)
 
    # top right corner
    band = Z[half_size,-half_size:]
    Z[:half_size,-half_size:] = band - numpy.abs(numpy.flipud(Z[half_size+1:2*half_size+1,-half_size:]) - band)
    # bottom left corner
    band = Z[-half_size:,half_size].reshape(-1,1)
    Z[-half_size:,:half_size] = band - numpy.abs(numpy.fliplr(Z[-half_size:, half_size+1:2*half_size+1]) - band)
 
    # solve system and convolve
    if derivative == None:
        m = numpy.linalg.pinv(A)[0].reshape((window_size, -1))
        return scipy.signal.fftconvolve(Z, m, mode='valid')



# Read in the dose profiles using the Cheese and Teflon Phantoms, respectively.
#CheesePath = "Alford,Louis_800013095/Ali_LA_RA_HalfCheese_TPS.dcm"
#TeflonPath = "Alford,Louis_800013095/Ali_LA_RA_Teflon_TPS.dcm"
CheesePath = "Charles,John_366241460/Ali_JC_RA_HalfCheese_TPS.dcm"
TeflonPath = "Charles,John_366241460/Ali_JC_RA_Teflon_TPS.dcm"
#CheesePath = "Davis,Adlai_957042695/Ali_AD_RA_HalfCheese_TPS.dcm" 
#TeflonPath = "Davis,Adlai_957042695/Ali_AD_RA_Teflon_TPS.dcm"
#CheesePath = "Perryman,Deola_957043663/Ali_DP_RA_HalfCheese_TPS.dcm"
#TeflonPath = "Perryman,Deola_957043663/Ali_DP_RA_Teflon_TPS.dcm"
#CheesePath = "Sturges,John_20020682/Ali_JS_RA_HalfCheese_TPS.dcm"
#TeflonPath = "Sturges,John_20020682/Ali_JS_RA_Teflon_TPS.dcm"
#CheesePath = "Walker,Pauline_957044312/Ali_PW_RA_HalfCheese_TPS.dcm"
#TeflonPath = "Walker,Pauline_957044312/Ali_PW_RA_Teflon_TPS.dcm"
CheeseProfile = dicom.read_file(CheesePath)
TeflonProfile = dicom.read_file(TeflonPath)
print CheesePath
print TeflonPath


# Grab the pixel array data for both phantom profiles. Data is given as 6 digit 
# integers giving the dose in units of 10^-5 Gy.
CheeseArray = CheeseProfile.pixel_array
TeflonArray = TeflonProfile.pixel_array

# Show the dose profiles.
pylab.imshow(CheeseArray, cmap=pylab.cm.gray)
pylab.show()
pylab.imshow(TeflonArray, cmap=pylab.cm.gray)
pylab.show()

# Show a horizontal cross section of the dose profiles right through the 
# middle before the denoising.
matplotlib.pyplot.plot(range(1,513), CheeseArray[255,:], "ro", \
		       label="Cheese Original")
matplotlib.pyplot.plot(range(1,513), TeflonArray[255,:], "bo", \
		       label="Teflon Original")

# Use scipy's built-in functions to compute the gradient magnitude of the dose
# profiles using the Sobel operator after Total Variation Denoising.
CheeseArray = skimage.filter.tv_denoise(CheeseArray, weight=1)
TeflonArray = skimage.filter.tv_denoise(TeflonArray, weight=1)

# Show a horizontal cross section of the gradient profiles right through the 
# middle after the denoising.
matplotlib.pyplot.plot(range(1,513), CheeseArray[255,:], "r-", \
		       label="Cheese Denoised")
matplotlib.pyplot.plot(range(1,513), TeflonArray[255,:], "b-", \
		       label="Teflon Denoised")
matplotlib.pyplot.xlim([0,512])
matplotlib.pyplot.legend()
matplotlib.pyplot.show()

# Compute the gradient magnitude profiles and convert from units of 10^-5 Gy to
# units of 10^-2 Gy.
CheeseGrad = scipy.ndimage.generic_gradient_magnitude(CheeseArray, \
		scipy.ndimage.filters.sobel)
TeflonGrad = scipy.ndimage.generic_gradient_magnitude(TeflonArray, \
		scipy.ndimage.filters.sobel)
CheeseGrad = CheeseGrad/1000
TeflonGrad = TeflonGrad/1000

# Define threshold values. **look for something better**
CheeseThresh = CheeseGrad[255,:].max()*0.75
TeflonThresh = TeflonGrad[255,:].max()*0.75
print CheeseThresh,TeflonThresh

# Filter out the long horizontal edges.
for i in range(188,198):
	for j in range(0,512):
		if CheeseGrad[i,j] < CheeseThresh:
			CheeseGrad[i,j] = 0
		#end
for i in range(320,330):
	for j in range(0,512):
		if CheeseGrad[i,j] < CheeseThresh:
			CheeseGrad[i,j] = 0
		#end
for i in range(188,199):
	for j in range(0,512):
		if TeflonGrad[i,j] < TeflonThresh:
			TeflonGrad[i,j] = 0
		#end
for i in range(320,330):
	for j in range(0,512):
		if TeflonGrad[i,j] < TeflonThresh:
			TeflonGrad[i,j] = 0
		#end


# Show the gradient profiles.
pylab.imshow(CheeseGrad, cmap=pylab.cm.gray)
pylab.show()
pylab.imshow(TeflonGrad, cmap=pylab.cm.gray)
pylab.show()
#print CheeseGrad.max(),TeflonGrad.max()

# Show some cross sections of the gradient profiles.
#   -Through the middle horizontally
#   -Through the middle vertically
#   -Through the high gradient edge at the bottom horizontally
matplotlib.pyplot.plot(range(1,513), CheeseGrad[255,:], "ro", \
		       label="Horizontal")
matplotlib.pyplot.plot(range(1,513), CheeseGrad[:,250], "bo", \
		       label="Vertical")
matplotlib.pyplot.plot(range(1,513), CheeseGrad[301,:], "go", \
		       label="High Grad")
matplotlib.pyplot.xlim([0,512])
matplotlib.pyplot.legend()
matplotlib.pyplot.show()
matplotlib.pyplot.plot(range(1,513), TeflonGrad[255,:], "ro", \
		       label="Horizontal")
matplotlib.pyplot.plot(range(1,513), TeflonGrad[:,250], "bo", \
		       label="Vertical")
matplotlib.pyplot.plot(range(1,513), TeflonGrad[301,:], "go", \
		       label="High Grad")
matplotlib.pyplot.xlim([0,512])
matplotlib.pyplot.legend()
matplotlib.pyplot.show()


# Denoise the gradient profiles.  **look for something better**
#CheeseGrad = sg2d(CheeseGrad, 299, 4)
#TeflonGrad = sg2d(TeflonGrad, 49, 4)

# Create a histogram of the doses
CheeseGradMin = int(CheeseThresh)
TeflonGradMin = int(TeflonThresh)
CheeseGradMax = int(CheeseGrad.max()) + 1
TeflonGradMax = int(TeflonGrad.max()) + 1
CheeseGradNum = len(range(CheeseGradMin,CheeseGradMax))
TeflonGradNum = len(range(TeflonGradMin,TeflonGradMax))
CheeseHist = scipy.ndimage.measurements.histogram(CheeseGrad, \
		                                  CheeseGradMin, \
		                                  CheeseGradMax, \
				                  CheeseGradNum)
TeflonHist = scipy.ndimage.measurements.histogram(TeflonGrad, \
		                                  TeflonGradMin, \
		                                  TeflonGradMax, \
				                  TeflonGradNum)



# De-noise the histogram.  **Look for something better**
#CheeseHist = scipy.ndimage.uniform_filter1d(CheeseHist, 3)
#TeflonHist = scipy.ndimage.uniform_filter1d(TeflonHist, 3)
#CheeseHist = scipy.ndimage.gaussian_filter1d(CheeseHist, 3)
#TeflonHist = scipy.ndimage.gaussian_filter1d(TeflonHist, 3)
CheeseHist = savitzky_golay(CheeseHist, 199, 4)
TeflonHist = savitzky_golay(TeflonHist, 67, 4)
#CheeseHist = scipy.ndimage.spline_filter1d(CheeseHist)
#TeflonHist = scipy.ndimage.spline_filter1d(TeflonHist)

# Show the resulting histograms. The Cheese phantom's histogram data is plotted
# in red while the Teflon phantom's histogram data is plotted in blue.
matplotlib.pyplot.plot(range(CheeseGradMin,CheeseGradMax), CheeseHist, "r-", \
		       label="Cheese")
matplotlib.pyplot.plot(range(TeflonGradMin,TeflonGradMax), TeflonHist, "b-", \
		       label="Teflon")
matplotlib.pyplot.xlim([TeflonGradMin,CheeseGradMax])
matplotlib.pyplot.ylim([0,25])
matplotlib.pyplot.legend()
matplotlib.pyplot.show()

print CheeseHist.sum(),TeflonHist.sum()

#End
