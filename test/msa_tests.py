import unittest
from msa_model import MultispectralModel
import msa_view
import msa_controller

import unittest
from unittest.mock import Mock, patch
import numpy as np
import pandas as pd
from pathlib import Path
import multispectral_analysis as msa

class TestMultispectralModel(unittest.TestCase):

    def setUp(self):
        self.model = MultispectralModel()

    def test_init(self):
        self.assertEqual(len(self.model.df.columns), 11)

    def test_match_csv(self):
        csv1 = ['label_123.csv', 'natural_123.csv', 'natural_1.csv', 'natural_231.csv']
        csv_wavenum = '123'
        target = 'label_'
        result = self.model.match_csv(csv1, csv_wavenum, target)
        self.assertEqual(result, 'natural_123.csv')

    def test_group_files(self):
        


    @patch('multispectral_analysis.correct_spectra')
    @patch('multispectral_analysis.threshold')
    @patch('multispectral_analysis.compute_ratio')
    def test_ratio_images(self, mock_compute_ratio, mock_threshold, mock_correct_spectra):
        # Set up mock return values
        label_data = np.array([[1, 2], [3, 4]])
        natural_data = np.array([[2, 3], [4, 5]])
        label_correction_data = np.array([[5, 6], [7, 8]])
        natural_correction_data = np.array([[6, 7], [8, 9]])
        lcf = 1
        ncf = 1
        threshold = 0.5
        corrected_label = np.array([[0.5, 1], [1.5, 2]])
        corrected_natural = np.array([[1, 1.5], [2, 2.5]])        
        thresholded_natural = np.array([[0, 1], [1, 1]])
        ratio = np.array([[0.5, 0.1], [1.0, 1.3]])
        
        mock_correct_spectra.side_effect = [corrected_label, corrected_natural]
        mock_threshold.return_value = (thresholded_natural, None)
        mock_compute_ratio.return_value = ratio
        
        result = self.model.ratio_images(label_data, natural_data, label_correction_data, natural_correction_data, lcf, ncf, threshold)
        
        self.assertTrue(np.array_equal(result, ratio))
        mock_correct_spectra.assert_any_call(label_data, label_correction_data, lcf)
        mock_correct_spectra.assert_any_call(natural_data, natural_correction_data, ncf)
        mock_threshold.assert_called_once_with(corrected_natural, threshold)
        mock_compute_ratio.assert_called_once_with(corrected_label, thresholded_natural)
    
    @patch('numpy.loadtxt')
    def test_add_files(self, mock_loadtxt):
        mock_loadtxt.return_value = np.array([[1, 2], [3, 4]])
        files = ['file1.csv', 'file2.csv']
        summary_stats = [1, 2, 3, 4, 5, 6]
        
        with patch('multispectral_analysis.summarize', return_value=(np.array(summary_stats), None)):
            self.model.add_files(files)
        
        self.assertEqual(len(self.model.df), 2)
        self.assertEqual(self.model.df.iloc[0]['fpath'], 'file1.csv')
        self.assertEqual(self.model.df.iloc[1]['fpath'], 'file2.csv')
        self.assertEqual(self.model.df.loc[0, 'Mean'], 1)
        self.assertEqual(self.model.df.loc[1, 'Mean'], 1)

    @patch('matplotlib.pyplot.savefig')
    def test_save_image(self, mock_savefig):
        data = np.random.random((10, 10))
        title = 'test_image'
        self.model.save_image(data, title)
        mock_savefig.assert_called_once_with(title + ".jpg", dpi=self.model.dpi)

    def test_sort_wavenumbers(self):
        files = ['label_123.csv', 'natural_123.csv', 'label_corr_123.csv', 'natural_corr_123.csv']
        label, natural, label_corr, natural_corr = self.model.sort_wavenumbers(files, 'label', 'natural', 'label_corr', 'natural_corr')
        self.assertEqual(label, 'label_123.csv')
        self.assertEqual(natural, 'natural_123.csv')
        self.assertEqual(label_corr, 'label_corr_123.csv')
        self.assertEqual(natural_corr, 'natural_corr_123.csv')

if __name__ == '__main__':
    unittest.main()