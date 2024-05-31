#multispectral_analysis

#import necessary packages
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from numpy import genfromtxt
import matplotlib.image as im
import matplotlib.cm as cm
from matplotlib_scalebar.scalebar import ScaleBar
import csv
import os

#This function bins the multispectral image in a 2x2 fashion, if using it should always be applied before thresholding and ratioing so that thresholded pixels dont get averaged into pixels with non-zero intensity#
def bin_image(image_data, image_name=""): #variables are the image to bin (a singlewavenumber image save as a csv) and the name you would like to call it#
    # Binning#
    height, width = image_data.shape
    binned_height = height // 2
    binned_width = width // 2

    binned_image = np.zeros((binned_height, binned_width), dtype=np.float64)

    for i in range(0, height - 1, 2):
        for j in range(0, width - 1, 2):
            block = image_data[i:i+2, j:j+2]
            binned_image[i//2, j//2] = np.mean(block)

    # Construct a unique name for the binned image#
    binned_image_name = f"{image_name}_binned"

    return binned_image, binned_image_name 

def correct_spectra(data, reference, correction_factor: float) :
    return data - correction_factor * reference

#Thresholds the image to select for only areas with high enough lipid signal and then ratios two single wavenumber images#

def threshold(data,threshpercent=0.05): # the thresholdpercent is automatically set to 5% but can be changed by inputting that variable#
    maxsignal = np.max(data)
    print('max signal =', maxsignal)
    threshval = maxsignal * threshpercent
    #threshold out low lipid areas
    data[data<threshval] = 0
    return data, maxsignal
    
def compute_ratio(top, bottom):
    #ratio two single wavenumber images. this does not do any corrections for water or amide-I, that has to be done beforehand
    return np.divide(top, bottom, out = np.zeros_like(top), where = bottom != 0)

#analysis function, this simply runs some basic statistics on our images after taking out the threholded pixels (as to not average in a bunch of zeros) This also writes the statistics to a csv file in your  "directroy for saving"
def summarize(data, header_name: str = ''):#, fname: str = None):
    data_foravg = data[data != 0] #remove the thresholded pixels that have been set to 0
    mean_value = np.mean(data_foravg)
    median_value = np.median(data_foravg)
    max_signal = np.max(data_foravg)
    std_deviation = np.std(data_foravg)
    standard_error = std_deviation / np.sqrt(np.size(data_foravg))
    size = np.size(data_foravg)
    
    return np.array([[mean_value, median_value, max_signal, std_deviation, standard_error, size],\
        ['Average','Median','Max', 'Std','Se','n']])

#histogram function This produces an automatic histogram using seaborn from your data 
def histogram(data, fname: str = None, lower_bound: float = None, upper_bound: float = None):
    data = data[data != 0]
    flat = data.flatten()
    sns.set_style('darkgrid')
    fig, ax = plt.subplots()
    g = sns.histplot(data = flat, kde = True)
    if lower_bound != None or upper_bound != None:
        plt.xlim([lower_bound,upper_bound])
    ax.set_xlabel("Ratio")
    fig = g.get_figure()
    #save = np.savetxt(directory+ output_subfolder + general_file_name + '0removed_flattened' + named + '.csv', flat, delimiter=',')
    #save_fig = fig.savefig(directory+ output_subfolder + general_file_name +  'histogram_thresh' + named + '.png')
    return flat, fig

#plot function
def ratio_image(data, lower_bound: float = None, upper_bound: float = None, scalebar_size: float = 0, ax = None):
    # Display the image
    ax = ax or plt.gca()
    # if ax == None:
    #     fig, ax = plt.subplots()
    if lower_bound != None or upper_bound != None:
        im_obj = plt.imshow(data, cmap='CMRmap', vmin=lower_bound, vmax=upper_bound)
        plt.clim([lower_bound, upper_bound],ax=ax)
    else:
        im_obj = plt.imshow(data, cmap='CMRmap')
    plt.colorbar(im_obj, cmap='CMRmap',ax=ax)
    ax.axis('off')
    if scalebar_size > 0:
        scalebar = ScaleBar(scalebar_size, "um", label="10 μm", width_fraction=0.015, location=3, frameon=None, color="white", fixed_value=10, box_alpha=0, scale_loc="none")
        ax.add_artist(scalebar)
    return ax