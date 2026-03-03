import numpy as np
class ImageController:
    def __init__(self, model, view):
        self.model = model
        self.view = view

    def display_images(self, index):
        # Display images for selected index/group
        """"""
        #What's next: You've just changed the index to the index of the dataframe. Make sure all
        # subsequent code works
        # if self.view.show_groups.get():
        #     group = self.model.df.loc[index,'group'].unique()[0]
        #     self.view.display(self.model.get_group_image(group))
        #     return
        
        # df_slice = self.model.get_df_slice(index)
        # self.view.display(self.model.get_single_image(df_slice))
        img, stats = self.model.make_image(index)
        self.view.display.update(img)
        self.display_statistics(stats)
        
        return

    def display_histograms(self, index):
        """Display a histogram for the image at *index*."""
        img, stats = self.model.make_histogram(index)
        self.view.display.update(img)
        self.display_statistics(stats)
        

    def display_statistics(self, stats):
        # Display statistics for selected index/group
        if self.view.show_groups.get():
            stats = "Statistics"
            self.view.buttons.items['Statistics'].configure(text=stats)
            return
        stats = [np.round(stats[key], 3) for key in stats.keys()]
        stats = ("Mean:" + str(stats[0]) + ", Median:" + str(stats[1]) +
                 ", Max:" + str(stats[2]) + ", Stdev:" + str(stats[3]) +
                 ", SE:" + str(stats[4]) + ",  Count: " + str(int(stats[5])))
        self.view.labels.update('Statistics', stats)

    def update_display(self, idx):
        # Update image/histogram/statistics display for selected index
        # df_idx = self.convert_index(listbox_idx)
        if self.view.show_histograms.get():
            self.display_histograms(idx)
        else:
            self.display_images(idx)
        # self.display_statistics(idx)
        return