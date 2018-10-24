"""
The goal of this script is to enable FoM emulation for WL+CL+LSS given a set of FoMs on a grid of
(area, depth).

Still to do:
- Get files from Tim.
- Check file read-in for consistency with area, depth.
- Inspect plots.
- Set up actual emulation.
- Look at outputs; plot along with grid values, output in more convenient format.
- Do the depth optimization.
"""
import numpy as np
import matplotlib.pyplot as plt
import glob
import os
cm = plt.cm.get_cmap('RdYlBu')

# Set some defaults.
year_vals = ['Y1', 'Y3', 'Y6', 'Y10']
# Should we fake the area scaling of the covariances?  For now this is necessary, since the inputs
# have issues off of the diagonal.
fake_area = False
# Should we renormalize by some strategy at some year?  Use None if not.
renorm_strategy = 'kraken_2026'

renorm_value = -100.0

areas = np.zeros((3,4)) # 3 grid values, 4 years
areas[:,0] = np.array([7.5, 13., 16.]) * 1000.0 # deg^2 for Y1
areas[:,1] = np.array([10., 15., 20.]) * 1000.0 # for Y3, Y6, Y10
areas[:,2] = np.array([10., 15., 20.]) * 1000.0 # for Y3, Y6, Y10
areas[:,3] = np.array([10., 15., 20.]) * 1000.0 # for Y3, Y6, Y10

depths = np.zeros((3,4)) # 3 grid values, 4 years
depths[:,0] = np.array([24.9, 25.2, 25.5])
depths[:,1] = np.array([25.5, 25.8, 26.1])
depths[:,2] = np.array([25.9, 26.1, 26.3])
depths[:,3] = np.array([26.3, 26.5, 26.7])

area_mid = areas[1,1] # arbitrary area for rescaling

husni_metric = \
    {'rolling_10yrs_opsim': [19.17009607686149, 67.03196, 140.13828, 233.02816],
     'rolling_mix_10yrs_opsim': [17.827055447412253, 62.7963, 133.4886, 223.60182],
     'baseline2018a': [14.59823342079436, 65.08548, 147.00488, 258.2933],
     'colossus_2664': [13.983119554695064, 64.04174, 143.77374, 252.1407],
     'colossus_2665': [14.675119972692409, 65.4227, 145.51038, 257.6914],
     'colossus_2667': [14.156289402581807, 67.01718, 150.84012, 267.87976],
     'kraken_2026': [15.50727567502652, 67.57038, 150.43662, 267.03468],
     'kraken_2035': [15.751901825752723, 67.16228, 147.68512, 262.56644],
     'kraken_2036': [15.746321613278274, 54.3136, 111.16146, 216.34454],
     'kraken_2042': [16.66430918416413, 72.25023000920037, 162.07506150123004, 283.98536],
     'kraken_2044': [10.745318502725427, 49.68256, 114.5921, 201.4586],
     'mothra_2045': [30.52469022205864, 57.79377338482163, 107.63368, 181.36768],
     'nexus_2097': [11.600585597575709, 49.2615, 105.93476, 196.6197],
     'pontus_2002': [11.785008704101049, 51.90274, 113.13634, 200.76312],
     'pontus_2489': [24.132090956403378, 96.123, 208.12806, 369.85366],
     'alt_sched': [19.97984, 56.72922, 112.04002, 185.9261],
     'alt_sched_rolling': [37.47584628358029, 53.85072, 109.68314, 184.13812],
     'pontus_2502': [15.488642770841723, 62.17139085035306, 129.36377275455092, 210.57829565913184],
    'mothra_2049': [24.335122196054208, 45.69528, 103.20514, 188.75324]}

def load_foms(dir='FoM', prior=False, fake_area=False):
    """Script to load some FoM values on a 3x3 grid in (area, depth)."""

    # Get list of files in directory.
    file_list = glob.glob(os.path.join(dir, '*'))
    
    # Initialize FoM arrays.  The first dimension is area, second is depth, 3rd is year.
    fom_arr = np.zeros((3,3,len(year_vals)))

    # Find the ones with Y1, Y3, Y6, Y10.  For each, get the right types of FoMs in order.
    for year_str in year_vals:
        # Find the one that has that year string and no other, otherwise Y1 and Y10 are confused.
        my_file = None
        for file_name in file_list:
            # Find the one that has that year string.
            if year_str in file_name:
                # Then make sure none of the others is there.
                other_found = False
                for tmp_year_str in year_vals:
                    if tmp_year_str != year_str and not tmp_year_str in year_str:
                        if tmp_year_str in file_name:
                            other_found = True
                if not other_found:
                    if my_file is None:
                        my_file = file_name
                    else:
                        if my_file != file_name:
                            raise ValueError(
                                "Year %s found more than once in dir %s!"%\
                                (year_str, dir))
        if my_file is None:
            raise ValueError("Year %s not found in dir %s!"%(year_str, dir))
        print('Found file %s for year %s in dir %s'%(my_file, year_str, dir))

        # Now read in the relevant parts of the file.
        lines = [line.rstrip('\n') for line in open(my_file)]

        # Find the right lines based on whether they include/exclude the Stage III prior.
        if prior:
            grep_str = 'incl'
        else:
            grep_str = 'excl'


        year_ind = year_vals.index(year_str)
        n_found = 0
        for line in lines:
            if grep_str in line:
                tmp_fom = float(line.split('=')[1])
                fom_arr[int(n_found / 3), n_found % 3, year_ind] = tmp_fom
                n_found += 1
        print('%s relevant lines found'%n_found)

        if fake_area:
            print('Faking FoM area scaling so as to only use diagonals!')
            # In [:,0] -> shallowest -> force the FoMs for the larger areas to be rescaled from the
            # smaller areas.
            fom_arr[1,0,year_ind] = fom_arr[0,0,year_ind]*areas[1,year_ind]/areas[0,year_ind]
            fom_arr[2,0,year_ind] = fom_arr[0,0,year_ind]*areas[2,year_ind]/areas[0,year_ind]
            # In [:,1] -> middle depth -> rescale FoMs for larger and smaller area based on middle
            # area.
            fom_arr[0,1,year_ind] = fom_arr[1,1,year_ind]*areas[0,year_ind]/areas[1,year_ind]
            fom_arr[2,1,year_ind] = fom_arr[1,1,year_ind]*areas[2,year_ind]/areas[1,year_ind]
            # In [:,2] -> deepest -> rescale FoMs for smaller and middle area based on largest
            # area.
            fom_arr[0,2,year_ind] = fom_arr[2,2,year_ind]*areas[0,year_ind]/areas[2,year_ind]
            fom_arr[1,2,year_ind] = fom_arr[2,2,year_ind]*areas[1,year_ind]/areas[2,year_ind]
            
    return fom_arr

def load_strategy_table(year_str = 'Y1'):
    infile = './strategy_table_%s.txt'%year_str
    if not os.path.exists(infile):
        raise ValueError("Cannot find file %s for year %s!"%(infile, year_str))

    # Read it in
    lines = [line.rstrip('\n') for line in open(infile)]

    strat_name = []
    area = []
    median_depth = []
    niexp = []

    year_ind = year_vals.index(year_str) 
    for line in lines:
        tmp_vals = line.split("|")
        strat_name.append(tmp_vals[1].strip())
        area.append(float(tmp_vals[3].strip()))
        median_depth.append(float(tmp_vals[4].strip()))
        if len(tmp_vals) == 14 and tmp_vals[13]!='':
            niexp.append(int(tmp_vals[13].strip()))
        else:
            # take from dict.
            if tmp_vals[1].strip() in husni_metric.keys():
                niexp.append(int(husni_metric[tmp_vals[1].strip()][year_ind]))
            else:
                niexp.append(0)
    print('Strategy table loaded: %d lines in %s for year %s!'%\
          (len(strat_name), infile, year_str))
    return np.array(strat_name), np.array(area), np.array(median_depth), np.array(niexp)

def area_depth_func(x, a, b, c):
    """ a * (area / area_0)^b * (depth - depth_0)^c """
    areas = x[0,:]
    depths = x[1,:]
    area_renorm = areas / areas[4]
    depth_renorm = depths / depths[4]
    return (a + b*depth_renorm)*(area_renorm**c)   

def emulate_fom(area_vals, depth_vals, grid_area_vals, grid_depth_vals, grid_fom_vals,
                niexp, figpref=None, strategy_name=None):
    print('Starting emulator')
    from scipy import interpolate
    f = interpolate.interp2d(grid_area_vals, grid_depth_vals, grid_fom_vals, bounds_error=False)
    emulated_grid_fom_vals = f(grid_area_vals[:,0], grid_depth_vals[0,:])

    if renorm_strategy is not None:
        global renorm_value
        print('Renormalizing by strategy %s'%renorm_strategy)
        if renorm_value > 0:
            print('Renormalizing by pre-existing value %f'%renorm_value)
        else:
            # Find the strategy in the list:
            if strategy_name is None:
                raise ValueError("No strategy list was passed in!")
            else:
                tmp_ind = list(strategy_name).index(renorm_strategy)
                renorm_value = f(area_vals[tmp_ind], depth_vals[tmp_ind])[0]
                print ('Renormalizing by newly-found value %f'%renorm_value)
        tmp_renorm_value = renorm_value
    else:
        tmp_renorm_value = 1.0


    if figpref is not None:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        sc = ax.scatter(grid_area_vals, grid_depth_vals, c=emulated_grid_fom_vals/grid_fom_vals-0.5,
                        cmap=cm, s=80, edgecolors='none')
        plt.colorbar(sc)
        plt.title('Emulator ratio - 0.5')
        plt.xlabel('Area [sq. deg.]')
        plt.ylabel('Median i-band depth')
        plt.savefig('figs/%s_ratio.pdf'%figpref)

        finer_area = np.linspace(np.min(area_vals), np.max(area_vals), 20)
        finer_depth = np.linspace(np.min(depth_vals), np.max(depth_vals), 20)
        finer_area_grid, finer_depth_grid = np.meshgrid(finer_area, finer_depth)
        test_emulator = f(finer_area, finer_depth)
        fig = plt.figure()
        ax = fig.add_subplot(111)
        sc = ax.scatter(finer_area_grid, finer_depth_grid, c=test_emulator/np.max(test_emulator),
                        cmap=cm, s=80, edgecolors='none')
        use_niexp = np.where(niexp > 0)[0]
        no_niexp = np.where(niexp==0)[0]
        mean_niexp = np.mean(niexp[use_niexp])
        ax.scatter(area_vals[no_niexp], depth_vals[no_niexp], color='k', marker='x')
        ax.scatter(area_vals[use_niexp], depth_vals[use_niexp], color='k', marker='o', s=20*(niexp[use_niexp]/mean_niexp)**3)
        plt.colorbar(sc)
        plt.title('Emulated FoM / max')
        plt.xlabel('Area [sq. deg.]')
        plt.ylabel('Median i-band depth')
        plt.savefig('figs/%s_finer.pdf'%figpref)

        fig = plt.figure()
        ax = fig.add_subplot(111)
        plt.contour(finer_area_grid, finer_depth_grid, test_emulator/tmp_renorm_value, 15, linewidths=1, colors='k')
        plt.pcolormesh(finer_area_grid, finer_depth_grid, test_emulator/tmp_renorm_value, cmap=cm)
        ax.scatter(area_vals[no_niexp], depth_vals[no_niexp], color='k', marker='x')
        ax.scatter(area_vals[use_niexp], depth_vals[use_niexp], color='k', marker='o', s=20*(niexp[use_niexp]/mean_niexp)**3)
        #m1 = np.array(area_vals) < 15.2e3
        #m2 = np.array(area_vals) < 20.5e3
        #plt.plot(np.array(area_vals)[m1], -2.33e-5*np.array(area_vals)[m1]+25.39, 'm-')
        #plt.plot(np.array(area_vals)[m2], -2.11e-5*np.array(area_vals)[m2]+25.24, 'm-')
        plt.colorbar()
        if renorm_strategy is None:
            plt.title('Emulated FoM')
        else:
            plt.title('Emulated FoM versus %s Y1'%renorm_strategy)
        plt.xlabel('Area [sq. deg.]')
        plt.ylabel('Median i-band depth')
        plt.savefig('figs/%s_contour.pdf'%figpref)        
        
    fom_vals = []
    for ind in range(len(area_vals)):
        fom_vals.append(f(area_vals[ind], depth_vals[ind])[0] / tmp_renorm_value)
    fom_vals = np.array(fom_vals)
    return fom_vals

# Get FoM values.
foms_prior = load_foms(prior=True, fake_area=fake_area)
print(foms_prior[:,:,0])
foms_noprior = load_foms(prior=False, fake_area=fake_area)
print(foms_noprior[:,:,0])

# Make some basic plots:
# In each year, make a 2D color plot of the FoM vs. depth and area without and with prior, without
# and with removal of area scaling.
for year_ind in range(len(year_vals)):
    plot_areas = np.repeat(areas[:,year_ind],3).reshape(areas[:,year_ind].shape[0],3)
    plot_depths = np.repeat(depths[:,year_ind],3).reshape(depths[:,year_ind].shape[0],3).transpose()
    fom_max = max(np.max(foms_prior[:,:,year_ind]), np.max(foms_noprior[:,:,year_ind]))
    fom_max_rescale = max(np.max(foms_prior[:,:,year_ind]*area_mid/plot_areas),
                             np.max(foms_noprior[:,:,year_ind]*area_mid/plot_areas))
    max_val = max(fom_max, fom_max_rescale)

    # No prior, no area rescaling.
    if not fake_area:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        sc = ax.scatter(plot_areas, plot_depths, c=foms_prior[:,:,year_ind]/max_val,
                        cmap=cm, s=80, edgecolors='none')
        plt.colorbar(sc)
        plt.title('FoM/%d (with Stage III prior)'%max_val)
        plt.xlabel('Area [sq. deg.]')
        plt.ylabel('Median i-band depth')
        plt.savefig('figs/fom_emulator_%s_prior.pdf'%year_vals[year_ind])

    # Prior, no area rescaling.
    fig = plt.figure()
    ax = fig.add_subplot(111)
    sc = ax.scatter(plot_areas, plot_depths, c=foms_noprior[:,:,year_ind]/max_val,
                    cmap=cm, s=80, edgecolors='none')
    plt.colorbar(sc)
    plt.title('FoM/%d (no prior)'%max_val)
    plt.xlabel('Area [sq. deg.]')
    plt.ylabel('Median i-band depth')
    plt.savefig('figs/fom_emulator_%s_noprior.pdf'%year_vals[year_ind])

    # No prior, area rescaling.
    if not fake_area:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        sc = ax.scatter(plot_areas, plot_depths,
                        c=foms_prior[:,:,year_ind]*area_mid/plot_areas/max_val,
                        cmap=cm, s=80, edgecolors='none')
        plt.colorbar(sc)
        plt.title('(Rescaled FoM with Stage III prior)/%d'%max_val)
        plt.xlabel('Area [sq. deg.]')
        plt.ylabel('Median i-band depth')
        plt.savefig('figs/fom_emulator_%s_prior_rescaled.pdf'%year_vals[year_ind])

    # Prior, area rescaling.
    fig = plt.figure()
    ax = fig.add_subplot(111)
    sc = ax.scatter(plot_areas, plot_depths,
                    c=foms_noprior[:,:,year_ind]*area_mid/plot_areas/max_val,
                    cmap=cm, s=80, edgecolors='none')
    plt.colorbar(sc)
    plt.title('(Rescaled FoM without prior)/%d'%max_val)
    plt.xlabel('Area [sq. deg.]')
    plt.ylabel('Median i-band depth')
    plt.savefig('figs/fom_emulator_%s_noprior_rescaled.pdf'%year_vals[year_ind])

    # Evaluate various strategies using emulator as needed.

    # Load strategy tables:
    tmp_strat, tmp_area, tmp_depth, tmp_niexp = load_strategy_table(year_vals[year_ind])
    emulated_fom_noprior = emulate_fom(tmp_area, tmp_depth, plot_areas, plot_depths,
                                       foms_noprior[:,:,year_ind], tmp_niexp,
                                       figpref='test_noprior_%s'%year_vals[year_ind],
                                       strategy_name=tmp_strat)
    if not fake_area:
        emulated_fom_prior = emulate_fom(tmp_area, tmp_depth, plot_areas, plot_depths,
                                         foms_prior[:,:,year_ind], tmp_niexp,
                                         figpref='test_prior_%s'%year_vals[year_ind],
                                         strategy_name=tmp_strat)
    inds = emulated_fom_noprior.argsort()[::-1]
    print('')
    print('Emulated from best to worst in year %s'%year_vals[year_ind])
    if fake_area:
        print('Strategy, Area, median i-band depth, FoM without prior')
        for ind in inds:
            if renorm_strategy is None:
                print('%20s %d %.2f %d'%(tmp_strat[ind], tmp_area[ind], tmp_depth[ind],
                                         emulated_fom_noprior[ind]))
            else:
                print('%20s %d %.2f %f'%(tmp_strat[ind], tmp_area[ind], tmp_depth[ind],
                                         emulated_fom_noprior[ind]))
    else:
        print('Strategy, Area, median i-band depth, FoM without prior, FoM with prior')
        for ind in inds:
            if renorm_strategy is None:
                print('%20s %d %.2f %d %d'%(tmp_strat[ind], tmp_area[ind], tmp_depth[ind],
                                            emulated_fom_noprior[ind], emulated_fom_prior[ind]))
            else:
                print('%20s %d %.2f %f %f'%(tmp_strat[ind], tmp_area[ind], tmp_depth[ind],
                                            emulated_fom_noprior[ind], emulated_fom_prior[ind]))
    print('')

# Depth optimization.