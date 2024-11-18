# ETABS Connection Designer

This app allows you to verify the compliance of shear, moment, and baseplate standard connections based on the internal loads of your load combinations.

## Step 1

The first step of the app allows you to upload an `.xlsx` file. This file should be exported from ETABS and must contain all your model's results.

The app has two modes:  
1. You can either analyze the compliance of the connection by assigning a capacity.  
2. Or let the app calculate the optimal capacity based on the selected load combination.

![Step 1 Screenshot](app.viktor-template/Step1a.jpg)

After loading the `.xlsx` file, the app will display the connection groups. You can select in the array below which connection type and color should be associated with each group!

## Step 2

In this step, you can select a load combination. The app will use the inputs defined in the previous step to either verify the compliance of the connection or design the connection, depending on the "application mode" defined earlier.

On the right-hand side (RHS) of this view, a 3D model with the following color scheme will be displayed:
- Beams that comply with the selected capacities are colored **green**.
- Beams that do not comply are colored **red**.

![Step 2 Screenshot](app.viktor-template/Step2a.jpg)

The app allows you to visualize the frame's internal loads and capacities in a table view. Frames that comply with the assessment are highlighted in green, while those that do not are highlighted in red. You can export this view to an `.xlsx` file by clicking the **Export** button located at the bottom left.

![Step 2 Table View](app.viktor-template/Step2b.jpg)

Finally, you can download a comprehensive report that provides the results for each member analyzed in the current session.  
The report will include all relevant details, such as the input parameters, load combinations, and connection types.

![Report Screenshot](app.viktor-template/Step2c.jpg)
