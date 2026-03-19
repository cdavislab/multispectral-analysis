import os
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import warnings
from pathlib import Path
import multispectral_analysis as msa
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib_scalebar.scalebar import ScaleBar
from matplotlib import ticker

logger = logging.getLogger(__name__)

# Model class for managing data, analysis, and file operations
class MultispectralModel:
    def __init__(self):
        # Initialize data structures, preferences, and group tracking
        warnings.filterwarnings("ignore")
        # Initialize master DataFrame and other variables/booleans 
        self.df = pd.DataFrame(columns=['fpath', 'fname', 'im_path', 'hist_path', 'group', 'type',
                                        'Mean', 'Median', 'Max_Signal', 'Standard Deviation',
                                        'Standard Error', 'Count'])
        self.files = []  # List to hold file paths
        self.isAnalyzed = False  # Flag to check if files are analyzed
        self.preferences = {'dpi': 300,
                            'export_folder': 'msa_analysis',
                            'subdivide_files': True,
                            'filetype': '.jpg',
                            'save_correction_freq1': False,
                            'save_correction_freq2': False,
                            'save_threshold_freq2': False,
                            'freq1_label': 'freq1',
                            'freq2_label': 'freq2',
                            'freq1c_label': 'freq1c',
                            'freq2c_label': 'freq2c',
                            'ratio_label': 'ratio',
                            'font':"arial", 
                            'font_size':10,
                            'font_weight':'normal', 
                            'cmap': 'CMRmap',
                            'vmin': 0,
                            'vmax':None,
                            'cunits': '',
                            'ratio_vmin': 0,
                            'ratio_vmax': None,
                            'ratio_cunits': '',
                            'pixel_scale':1,
                            'scale_bar':0.25,
                            'scale_bar_units':'',
                            'scale_bar_color':'white',
                            'scale_bar_location':'lower left',
                            'scale_bar_fixed_value':0,
                            'num_ticks':'auto'}
        self.steps = None
        self.group_names = []
        self.group_images = []
        self.group_histograms = []
        self.n_groups = 0
        self.old_groups = [0]
        self.group_history = dict()
    def group_files(self, file_list: list, label: str, natural: str, label_corr:str, natural_corr: str) -> pd.DataFrame:
        """
        Groups files based on shared common name and wavenumber labels.
        Returns a DataFrame with grouped file paths.
        """
        df = pd.DataFrame(columns=["identifier", "freq1", "freq2", "freq1c", "freq2c"], dtype=str)
        # Error case
        if label_corr is None:
            label_corr = ""
        if natural_corr is None:
            natural_corr = ""
        for file in file_list:
            identifier = (file
                          .replace(label, "")
                          .replace(natural, "")
                          .replace(label_corr, "")
                          .replace(natural_corr, ""))
            if identifier not in df["identifier"].values:
                df.loc[df.shape[0]] = [identifier, "", "", "", "",]
            idx = df[df["identifier"] == identifier].index[0]
            if label in file:
                df.loc[idx, "freq1"] = file
            elif natural in file:
                df.loc[idx, "freq2"] = file
            elif label_corr in file:
                df.loc[idx, "freq1c"] = file
            elif natural_corr in file:
                df.loc[idx, "freq2c"] = file

        return df

    # Function to save a data array as an image
    def save_image(self, data, title, suffix='', isRatio=False):
        # Save a numpy array as an image with colorbar and optional ratio settings
        if isRatio:
            vmin_var = 'ratio_vmin'
            vmax_var = 'ratio_vmax'
            cunits_var = 'ratio_cunits'
        else:
            vmin_var = 'vmin'
            vmax_var = 'vmax'
            cunits_var = 'cunits'
        vmin = self.get_pref(vmin_var)
        vmax = self.get_pref(vmax_var)
        
        plt.rcdefaults() #HACK to reset settings as seaborn changes them
        # Enable constrained layout for better spacing and alignment
        plt.rcParams.update({'figure.constrained_layout.use': True})

        fig, ax = plt.subplots()

        font = {'family': self.get_pref('font'),
                'size': self.get_pref('font_size'),
                'weight': self.get_pref('font_weight')} # bold or normal
        plt.rc('font', **font)

        ax.grid(False)
        cax = ax.imshow(data, cmap=self.get_pref('cmap'),
                   vmin=vmin,
                   vmax=vmax)
        cbar = fig.colorbar(cax)
        # Set custom colormap and vmin, vmax
        cax.set_cmap(self.get_pref('cmap'))
        cax.set_clim(vmin,
                     vmax)  # setting vmin and vmax
        cbar.set_label(self.get_pref(cunits_var))
            # Add a black border to the figure and colorbar
        for spine in ax.spines.values():
            spine.set_edgecolor('black')
            spine.set_linewidth(1)

        cbar.outline.set_edgecolor('black')
        cbar.outline.set_linewidth(1)

        self.fix_number_of_ticks(ax, font)

        # Add a scale bar
        fixed_value = self.get_pref('scale_bar_fixed_value')
        if self.is_nonzero_number(fixed_value):
            label = str(self.get_pref('scale_bar_fixed_value')) + ' ' + self.get_pref('scale_bar_units')
            scalebar = ScaleBar(self.get_pref('pixel_scale'),
                                label=label,
                                scale_loc='none',
                                width_fraction=0.015,
                                location=self.get_pref('scale_bar_location'),
                                frameon=None,
                                color=self.get_pref('scale_bar_color'),
                                box_alpha=0,
                                fixed_value=self.get_pref('scale_bar_fixed_value'))
            ax.add_artist(scalebar)

        self.saveimg(title + suffix)
        plt.close()
        return

    def is_nonzero_number(self, value):
        # Utility: check if value is a nonzero number
        try:
            return float(value) > 0
        except ValueError:
            return False

    def fix_number_of_ticks(self, ax, font):
        # Set the number of axis ticks or remove them if not specified
        if not(self.is_nonzero_number(self.get_pref('num_ticks'))):
            ax.set_xticks([])
            ax.set_yticks([])
            return

        label_format = '{:,.0f}'

        xticks = ax.get_xticks()
        ax.xaxis.set_major_locator(ticker.MaxNLocator(self.get_pref('num_ticks')))
        ax.set_xticklabels(xticks, fontdict=font)

        yticks = ax.get_yticks()
        ax.yaxis.set_major_locator(ticker.MaxNLocator(self.get_pref('num_ticks')))
        ax.set_yticklabels(yticks, fontdict=font)
        return

    def save_data(self, data, title):
        # Save numpy array as CSV
        np.savetxt(title + ".csv", data, delimiter=",")
        return

    # Function to compute ratio images from freq1, freq2, and correction files
    def _correct_and_ratio(self, data, entries):
        # Apply corrections and compute ratio image
        freq1_corrected = data['freq1']
        freq2_corrected = data['freq2']

        # Support multiple corrections/factors if provided
        if 'multiple_corrections' in entries and 'multiple_factors' in entries:
            for corr, factor in zip(entries['multiple_corrections'], entries['multiple_factors']):
                if corr and factor:
                    # Apply correction to freq1 if present in filename
                    if corr in getattr(data, 'freq1c', '') or corr in getattr(data, 'freq1', ''):
                        freq1_corrected = msa.correct_spectra(freq1_corrected, data.get(corr, None), factor)
                    # Apply correction to freq2 if present in filename
                    if corr in getattr(data, 'freq2c', '') or corr in getattr(data, 'freq2', ''):
                        freq2_corrected = msa.correct_spectra(freq2_corrected, data.get(corr, None), factor)
        else:
            # Fallback to single correction
            if data['freq1c'] is not None:
                freq1_corrected = msa.correct_spectra(data['freq1'], data['freq1c'], entries['freq1cf'])
            if data['freq2c'] is not None:
                freq2_corrected = msa.correct_spectra(data['freq2'], data['freq2c'], entries['freq2cf'])

        freq2_thresholded, _ = msa.threshold(freq2_corrected, entries['threshold'])
        ratio = msa.compute_ratio(freq1_corrected, freq2_thresholded)
        return freq1_corrected, freq2_corrected, freq2_thresholded, ratio

    # Function to sort files in a group into freq1, freq2, and corrections
    def sort_wavenumbers(self, group, freq1, freq2, 
                         freq1c, freq2c):
        # Sort files in a group into freq1, freq2, and corrections
        for file in group:
            if freq1 in file:
                freq1_file = file
                self.df.loc[self.df['fpath'] == file, 'type'] = 'Freq1'
            elif freq2 in file:
                freq2_file = file
                self.df.loc[self.df['fpath'] == file, 'type'] = 'Freq2'
            elif freq1c in file:
                freq1c_file = file
                self.df.loc[self.df['fpath'] == file, 'type'] = 'Freq1c'
            elif freq2c in file:
                freq2c_file = file
                self.df.loc[self.df['fpath'] == file, 'type'] = 'Freq2c'
            else:
                warnings.warn("Warning: " + file + " could not be sorted into a wavenumber group")
        if freq1c is None:
            freq1c_file = None
        if freq2c is None:
            freq2c_file = None
        if freq1c == freq2c:
            freq2c_file = freq1c_file
        return freq1_file, freq2_file, freq1c_file, freq2c_file

    def get_dir(self, file):
        # Determine output directory for a file, create if needed
        outfolder = self.get_pref('export_folder')
        if self.get_pref('subdivide_files'):
            parent = Path(file).parent.name
            outfolder = os.path.join(self.get_pref('export_folder'), parent)
        Path(outfolder).mkdir(parents=True, exist_ok=True)
        return outfolder

    # Function to add files to the model and process them
    def add_files(self, file, outfolder):
        # Add a file to the model, process and summarize it
        # Add each unique file to the DataFrame with a summary and create an image
        if file in self.df['fpath'].unique():
            return
        
        # data = np.loadtxt(file, delimiter=',')
        data = self.load_files(file)
        if data == []:
            return
        data = data[0]
        outpath = os.path.join(outfolder, Path(file).stem)
        image_path = outpath + self.get_ext()
        hist_path = outpath + "_hist" + self.get_ext()
        summary = msa.summarize(data)
        summary = list(summary[0].astype('float'))
        self.df.loc[self.df.shape[0]] = [file, Path(file).stem, image_path, hist_path, 0, None] + summary
        self.save_image(data, outpath)
        self.create_histogram(data, outpath)
        return

    
    def load_files(self, *filepaths):
        """
        Loads multiple files using np.loadtxt and returns the loaded data.
        
        Parameters
        ----------
        *filepaths : str
            Any number of file paths to load.

        Returns
        --------
        out : list
        A list of numpy arrays containing the data from the files.
        """
        loaded_data = []
        
        for filepath in filepaths:
            # If the file path is None (i.e. file is unused), append None to the list
            if filepath is None:
                loaded_data.append(None)
                continue
            try:
                # data = np.loadtxt(filepath, delimiter=',')
                data = pd.read_csv(filepath, header=None).values
                if data.dtype == 'O':
                    raise Exception(filepath + " contains non-numeric data")
                loaded_data.append(data)
            except Exception as e:
                logger.warning("Error loading file %s: %s", filepath, e)
        
        return loaded_data

    def is_grouped(self, fpaths):
        # Return True if all fpaths have a non-zero group number in dataframe
        for fpath in fpaths:
            row = self.df[self.df['fpath'] == fpath]
            group = row['group']
        return all(self.df[self.df['fpath'].isin(fpaths)]['group'] != 0)

    def get_new_group(self):
        # Get the next available group number
        return self.df['group'].max() + 1

    def change_group_number(self, fpaths):
        # Change group number for a set of file paths
        old_group = self.df.loc[self.df['fpath'].isin(fpaths), 'group']
        old_group = old_group.values[0]
        new_group = self.get_new_group()
        # Append
        if old_group in self.group_history.keys():
            self.group_history[old_group].append(new_group)
        else:
            self.group_history[old_group] = [new_group]

        self.df.loc[self.df['fpath'].isin(fpaths), 'group'] = new_group
        return

    def assign_groups(self, groups_series: pd.Series):
        # Assign a new group number to a series of file paths
        new_group_num = self.get_new_group()
        
        for item in groups_series:
            ## Place group number in row for each group in the class-wide dataframe
            self.df.loc[self.df['fpath'] == item, 'group'] = new_group_num
        return

    def pre_analyze_files(self, entries, idx, unique_types):
        # Prepare groups for analysis, assign group numbers, and track new groups
        fpaths = self.df.loc[idx, :]
        # Remove fpaths that are ratios
        fpaths = fpaths[fpaths['type'] != 'Ratio']
        fpaths = fpaths['fpath']

        groups_df = self.group_files(fpaths, entries['freq1'], entries['freq2'],
            entries['freq1c'], entries['freq2c'])
        # Find row in groups_df with least number of empty strings
        def count_non_empty_strings(row):
            return sum(bool(str(cell).strip()) for cell in row)

        groups_df = groups_df[groups_df.apply(count_non_empty_strings, axis=1) > unique_types]
        if groups_df.shape[0] == 0:
            return None
        
        for idx, row in groups_df.iterrows():
            if self.is_grouped(row[1:]):
                self.change_group_number(row[1:])
            else:
                self.assign_groups(row[1:])

        groups = self.df['group'].unique()

        groups = np.delete(groups, np.isin(groups, self.old_groups)) # Previously analyzed and ungrouped items
        n_new_groups = len(groups)
        self.old_groups += list(groups)

        self.group_images += ([None for _ in range(n_new_groups)])
        self.group_histograms += ([None for _ in range(n_new_groups)])

        return groups

    def _save_output_data(self, freq1_corrected, freq2_corrected, freq2_thresholded,
                          ratio, entries, fname, group_id):
        # Save output data arrays and images for a group
        path = self.get_pref('export_folder')
        if self.get_pref('save_correction_freq1'):
            fpath = os.path.join(path, fname+"_"+entries['freq1']+"_corr_"+str(group_id))
            self.save_data(freq1_corrected, fpath)
        if self.get_pref('save_correction_freq2'):
            fpath = os.path.join(path, fname+"_"+entries['freq2']+"_corr_"+str(group_id))
            self.save_data(freq2_corrected, fpath)
        if self.get_pref('save_threshold_freq2'):
            fpath = os.path.join(path, fname+"_"+entries['freq2']+"_thresh_"+str(group_id))
            self.save_data(freq2_thresholded, fpath)
        _, ratio_fpath, _, _ = self.create_paths(fname, "_ratio")
        self.save_image(ratio, ratio_fpath+"_"+str(group_id), isRatio=True)
        self.save_data(ratio, ratio_fpath+"_"+str(group_id))
        self.create_histogram(ratio, ratio_fpath+"_"+str(group_id))

    def create_paths(self, fname, extra):
        # Generate file paths for output images and data
        path = self.get_pref('export_folder')
        fname = fname + extra
        fpath = os.path.join(path, fname)
        image_path = os.path.join(path, fname + self.get_ext())
        histogram_path = os.path.join(path, fname + "_hist" +self.get_ext())
        return fname, fpath, image_path, histogram_path
    

    def _summarize_and_save_to_df(self, data, fname, group_idx=None, type=None):
        # Summarize data and add to the main DataFrame
        type_to_fname = {"Ratio": "_ratio_"+str(group_idx)}
        summary = msa.summarize(data)
        summary = list(summary[0].astype('float'))
        fname, fpath, image_path, histogram_path = self.create_paths(fname, type_to_fname[type])
        self.df.loc[self.df.shape[0]] = [fpath, fname, image_path, histogram_path, group_idx, type] + summary
        return
    
    # Function to analyze files and compute ratio images
    # Labels wavenumbers as freq1, freq2, freq1c, and freq2c,
    # loads data, computes ratio, saves ratio, 
    def analyze_files(self, entries, group_idx):
        """
        Main function to analyze files. Groups files, computes ratio images, and saves results.
        """
        data, fname = self._load_group(entries, group_idx)
        output_data = self._correct_and_ratio(data, entries)
        self._save_output_data(*output_data, entries, fname, group_idx)
        ratio = output_data[3]
        self._summarize_and_save_to_df(ratio, fname, group_idx, 'Ratio')
        data['ratio'] = ratio
        if entries['freq1c'] == entries['freq2c']: # if correction file names are the same..
            data.pop('freq2c') # HACK: Should be named correction if the same 
            
        self.group_images[group_idx-1] = self.create_group_image(data, group_idx)
        self.group_histograms[group_idx-1] = self.create_group_histogram(data, group_idx)
        return
    
    def _load_group(self, entries, group_idx):
        # Load all files for a group and return data dictionary and base name
        fpaths = self._get_group(group_idx)
        fpaths = self.sort_wavenumbers(fpaths, entries['freq1'], entries['freq2'], entries['freq1c'], entries['freq2c'])
        fname = self._find_base_name(fpaths[0], entries['freq1'])
        data = self.load_files(*fpaths)
        data = {'freq1': data[0], 'freq2': data[1], 'freq1c': data[2], 'freq2c': data[3]}
        self.set_group_name(fname, group_idx)
        return data, fname

    def _get_group(self, idx):
        # Get file paths for a group
        return self.df[self.df['group'] == idx]['fpath'].values

    def _find_base_name(self, file, extra):
        # Extract base name from file path
        return Path(file).stem.replace(extra, "")
        
    def generate_group_figure(self, num_images):
        # Create a matplotlib figure with subplots for group images
        layout_mapping = {
            1: (1, 1),
            2: (1, 2),
            3: (1, 3),
            4: (2, 2),
            5: (2, 3)
        }

        # Create the figure and subplots
        plt.rcdefaults() #HACK to reset settings as seaborn changes them
        # Enable constrained layout for better spacing and alignment
        # plt.rcParams.update({'figure.constrained_layout.use': True})
        plt.tight_layout()
        plot_layout = layout_mapping[num_images]
        fig, axs = plt.subplots(plot_layout[0], plot_layout[1], figsize=(10, 5))
        # fig.subplots_adjust(bottom=0.9)
        axs = axs.flatten()
        return fig, axs
    
    def create_histogram(self, data, title, suffix=''):
        # Create and save a histogram for a data array
        # fig, ax = self.generate_group_figure(1)
        fig, ax = plt.subplots(1, 1, figsize=(10, 5))
        plt.grid(False)
        msa.histogram(data, ax=ax, lower_bound=0)
        self.saveimg(title + "_hist" + suffix)
        plt.close()
        plt.close()
        return
        

    def create_group_histogram(self, data, group_id):
        # Create and save a histogram for a group of data arrays
        df_slice = self.df[self.df['group'] == group_id]
        fig, axs = self.generate_group_figure(len(df_slice))
        # max_value = self.find_max_value(df_slice) # First 4 elements are non-ratio matrices

        for i, description in enumerate(data.keys()): # Note: Only works in Python 3.7+. Otherwise, data is not ordered.
            selected = data[description]
            ax = axs[i]
            msa.histogram(selected, ax=ax, lower_bound=0)
            # ax.histogram(selected, cmap='CMRmap', vmin=0, vmax=max_value) #####################
            ax.set_title(description)

        hist_path = os.path.join(self.get_pref('export_folder'), "group_histogram_" + str(group_id)) #TODO: Make exporting a different function
        fig.subplots_adjust(hspace=0.5)
        self.saveimg(hist_path)
        plt.close()
        return hist_path + self.get_ext()

    def create_image(self, data, title, ax, vmin=None, vmax=None, isRatio=False):
        # Create an image with colorbar and optional scale bar
        if isRatio:
            vmin_var = 'ratio_vmin'
            vmax_var = 'ratio_vmax'
            cunits_var = 'ratio_cunits'
        else:
            vmin_var = 'vmin'
            vmax_var = 'vmax'
            cunits_var = 'cunits'
        if self.get_pref(vmin_var) != None:
            vmin = self.get_pref(vmin_var)
        if self.get_pref(vmax_var) != None:
            vmax = self.get_pref(vmax_var)

        ax.set_title(title)
        ax.axis('off')
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)

        # vmin = self.get_pref('vmin')


        font = {'family': self.get_pref('font'),
                'size': self.get_pref('font_size'),
                'weight': self.get_pref('font_weight')} # bold or normal
        plt.rc('font', **font)

        ax.grid(False)
        im = ax.imshow(data, cmap=self.get_pref('cmap'),
                   vmin=vmin,
                   vmax=vmax)
        
        # Set custom colormap and vmin, vmax
        im.set_cmap(self.get_pref('cmap'))  # changing to a different colormap for demonstration
        im.set_clim(vmin,
                     vmax)  # setting vmin and vmax
        

            # Add a black border to the figure and colorbar``
        for spine in ax.spines.values():
            spine.set_edgecolor('black')
            spine.set_linewidth(1)

        cbar = plt.colorbar(im, cax=cax)


        cbar.set_label(self.get_pref(cunits_var))
        cbar.outline.set_edgecolor('black')
        cbar.outline.set_linewidth(1)

        self.fix_number_of_ticks(ax, font)

        # Add a scale bar
        fixed_value = self.get_pref('scale_bar_fixed_value')
        if self.is_nonzero_number(fixed_value):
            label = str(self.get_pref('scale_bar_fixed_value')) + ' ' + self.get_pref('scale_bar_units')
            scalebar = ScaleBar(self.get_pref('pixel_scale'),
                                label=label,
                                scale_loc='none',
                                width_fraction=0.015,
                                location=self.get_pref('scale_bar_location'),
                                frameon=None,
                                color=self.get_pref('scale_bar_color'),
                                box_alpha=0,
                                fixed_value=self.get_pref('scale_bar_fixed_value'))
            ax.add_artist(scalebar)

        return

    def create_group_image(self, data, group_id):
        # Create and save a composite image for a group
        df_slice = self.df[self.df['group'] == group_id]
        fig, axs = self.generate_group_figure(len(df_slice))
        max_value = self.find_max_value(df_slice) # First 4 elements are non-ratio matrices

        # If there is only 1 key in data.keys() with the substring "_Corr", then rename the key "Label_Corr" to "Correction"
        if len([key for key in data.keys() if "c" in key]) == 1:
            data["Correction"] = data.pop("freq1c")
        # If None is in the dictionary, remove the key
        keys_to_remove = [k for k, v in data.items() if v is None]
        for key in keys_to_remove:
            del data[key]
        
        ratio = data.pop("ratio")

        for i, description in enumerate(data.keys()):
            selected = data[description]
            self.create_image(selected, self.get_item_description(description), axs[i], vmax=max_value)

        # Create the ratio image
        self.create_image(ratio, self.get_item_description('ratio'), axs[-1], vmax=ratio.max(), isRatio=True)

        img_path = os.path.join(self.get_pref('export_folder'), "group_" + str(group_id)) #TODO: Make exporting a different function
        # fig.subplots_adjust(bottom=300)
        self.saveimg(img_path)
        
        plt.close()
        data['ratio'] = ratio
        return img_path + self.get_ext()

    def set_steps(self, steps):
        # Update the analysis steps
        self.steps = steps
        return
    
    def print_steps(self):
        # Print the current analysis steps
        logger.info("Current analysis steps: %s", self.steps)
        return


    def find_max_value(self, df: pd.DataFrame, include_ratio=False) -> float:
        """ Helper function to find the maximum value among matrices in a DataFrame.
        Optionally include ratio images. """
        idx = df['type'] != 'Ratio'
        if include_ratio:
            idx = slice(None)
        return df.loc[idx, 'Max_Signal'].max()

    def get_item_description(self, item):
        # Get label for an item type from preferences
        if item == 'Correction':
            return self.get_pref('freq1c_label')
        return self.get_pref(item + '_label')

    def get_df_slice(self, index):
        """ Helper function to get a slice of the DataFrame
        based on the given index and filter options. """
        return self.df.loc[index, :]
    
    def get_single_histogram(self, df_slice):
        # Get histogram path for a single file
        return df_slice.loc['hist_path']

    def get_group_histogram(self, group_id):
        # Get histogram path for a group
        return self.group_histograms[group_id-1]

    def get_single_image(self, df_slice):
        # Get image path for a single file
        return df_slice.loc['im_path']

    def get_group_image(self, group_id):
        # Get image path for a group
        return self.group_images[group_id-1]

    def get_preferences(self):
        # Return the preferences dictionary
        return self.preferences

    def get_pref(self, preference):
        # Get a single preference value
        if preference not in self.preferences.keys():
            return None
        return self.preferences[preference]
    
    def set_pref(self, preference, value):
        # Set a single preference value
        self.preferences[preference] = value
        return

    def get_ext(self):
        # Get the current file extension for exports
        return self.preferences['filetype']

    def get_group_names(self):
        # Get the list of group names
        return self.group_names
    
    def set_group_name(self, name, group_id):
        # Set the name for a group
        if len(self.group_names) == group_id-1:
            self.group_names.append(name)
        elif len(self.group_names) > group_id-1:
            self.group_names[group_id-1] = name
        elif len(self.group_names) < group_id-1:
            raise ValueError("Group ID is out of range")
        else:
            raise ValueError("Invalid group ID:", str(group_id))
        return

    def saveimg(self, title):
        # Save the current matplotlib figure to file
        plt.savefig(title + self.get_ext(), dpi=self.get_pref('dpi'))
        return
        
    # Function to export the statistics to a CSV file
    def export_stats(self):
        # Export the DataFrame statistics to CSV
        self.df.to_csv(os.path.join(self.get_pref('export_folder'), "Summary.csv"), mode='a')
        return
    
    def export_filelist(self, path):
        # Export the list of file paths to a file
        # Ask for file name and location
        self.df['fpath'].to_csv(path, index=False, mode = 'w')
        # self.df['fpath'].to_csv(os.path.join(self.get_pref('export_folder'), f"fpaths_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"), index=False, mode = 'w')
        return