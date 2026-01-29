class ImageController:
    def __init__(self, model, view):
        self.model = model
        self.view = view

    def display_images(self, index):
        # Display images for selected index/group
        """"""
        #What's next: You've just changed the index to the index of the dataframe. Make sure all
        # subsequent code works
        if self.view.show_groups.get():
            group = self.model.df.loc[index,'group'].unique()[0]
            self.view.display(self.model.get_group_image(group))
            return
        
        df_slice = self.model.get_df_slice(index)
        self.view.display(self.model.get_single_image(df_slice))
        return

    def display_histograms(self, index):
        # Display histograms for selected index/group
        if self.view.show_groups.get():
            group = self.model.df.loc[index,'group'].unique()[0]
            self.view.display(self.model.get_group_histogram(group))
            return
        
        df_slice = self.model.get_df_slice(index)
        self.view.display(self.model.get_single_histogram(df_slice))
        return
        

    def display_statistics(self, index):
        # Display statistics for selected index/group
        if self.view.show_groups.get():
            stats = "Statistics"
            self.view.Button_Statistics.configure(text=stats)
            return
        stats = self.model.df[['Mean', 'Median', 'Max_Signal', 'Standard Deviation', 'Standard Error', 'Count']]
        stats = np.round(stats.iloc[index,:].astype(float), 3)
        stats = ("Mean:" + str(stats.iloc[0]) + ", Median:" + str(stats.iloc[1]) +
                 ", Max:" + str(stats.iloc[2]) + ", Stdev:" + str(stats.iloc[3]) +
                 ", SE:" + str(stats.iloc[4]) + ",  Count: " + str(int(stats.iloc[5])))
        self.view.Button_Statistics.configure(text=stats)

    def update_display(self, listbox_idx):
        # Update image/histogram/statistics display for selected index
        df_idx = self.convert_index(listbox_idx)
        if self.view.show_histograms.get():
            self.display_histograms(df_idx)
        else:
            self.display_images(df_idx)
        self.display_statistics(df_idx)
        return