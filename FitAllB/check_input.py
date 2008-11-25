#!/usr/bin/env python

#
# Checking input  
#

from string import split
import sys, os 
import write_output 
import conversion
from xfab import tools
from xfab import symmetry
from xfab import detector
import ImageD11.columnfile as ic
import numpy as n
import logging
import minuit
from copy import deepcopy


logging.basicConfig(level=logging.DEBUG,format='%(levelname)s %(message)s')

class parse_input:
    def __init__(self,input_file = None):
        self.filename = input_file
        self.files = {}
        self.fit = {}
        self.param = {}
        self.param_near = {}
        
        self.needed_items = {
                    'w_step': 'Missing input: omega step size in deg',
                    'log_file' : 'Missing input: grainspotter log file',
                    'flt_file' : 'Missing input: peaksearch filtered peaks file',
                    'par_file' : 'Missing input: ImageD11 detector.par file'
                    }
        self.optional_items = {
            'dety_size': 2048,
            'detz_size': 2048,
            'near_dety_size': 1536,
            'near_detz_size': 1024,
            'w': 0,
            'tilt': 0,
            'pixel': 0,
            'center': 0,
            'L': 0,
            'euler': 1,
            'xyz': 1,
            'eps': 1,
            'printmode': 0,
            'strategy': 0,
            'limit': [5,10], 
            'mad': [5,25],
            'overlap': 0.5,
			'hesse': 0,
            'skip': [],
            'resume': None,
            'near_resume':None,
            'res_file': None,
            'rej_file': None,
            'structure_file': None,
            'near_flt_file': None,
            'near_par_file': None,
            'bg': 100,
            'near_bg': 67,
            'const': 1,
            'ia': 0.1,
            'min_refl': 12,
            'near_min_refl': 6,
            'near_const': 1e5,
            'goon': 'start',
            'tol_start': 1e-1,
            'tol_euler': 1e-1,
            'tol_xyz': 1e-1,
            'tol_rotpos': 1e-2,
            'tol_eps': 1e-2,
            'tol_grain': 1e-3,
            'title': 'Title',
            'w_limit': None,
            'crystal_system': None,
            'c11': None,
            'c12': None,
            'c13': None,
            'c14': None,
            'c15': None,
            'c16': None,
            'c22': None,
            'c23': None,
            'c24': None,
            'c25': None,
            'c26': None,
            'c33': None,
            'c34': None,
            'c35': None,
            'c36': None,
            'c44': None,
            'c45': None,
            'c46': None,
            'c55': None,
            'c56': None,
            'c66': None
            }

        self.newreject = 0
        self.fit['outliers'] = 0
        self.fit['rejectgrain'] = []
        self.fit['rejectid'] = []
        self.fit['hh'] = []
        self.fit['kk'] = []
        self.fit['ll'] = []
        self.fit['rejectvalue'] = []
			
            
    def read(self):     
        try:
            f = open(self.filename,'r')
        except IOError:
            logging.error('No file named %s' %self.filename)
            raise IOError
        
        input = f.readlines()
        f.close()

        for lines in input:
            if lines.find('#') != 0:
                if lines.find('#') > 0:
                    lines = split(lines,'#')[0]
                line = split(lines)
                if len(line) != 0:
                    key = line[0]
                    val = line[1:]

                    valtmp = '['
                    if len(val) > 1 or key == 'skip':
                        for i in val:
                            valtmp = valtmp + i +','
							
                        val = valtmp + ']'
                    else:
                        val = val[0]

					# save input file names in self.files and fitting info in self.fit
                    if 'file' in key:
                        self.files[key] = val
                    else:
                        try:
                            self.fit[key] = eval(val)
                        except:
                            self.fit[key] = val
        
        stem = split(self.filename,'.')[0]		
        self.fit['stem'] = stem
        self.fit['direc'] = deepcopy(stem)
				
                
						
    def check(self):
        # Needed items
        self.missing = False
        for item in self.needed_items:
            if item not in self.files:
                if item not in self.fit:
                    print self.needed_items[item]
                    self.missing = True

			
            
    def initialize(self): 
        # Does output directory exist?
        print 'stem=',self.fit['stem']
        if not os.path.exists(self.fit['stem']):
            os.mkdir(self.fit['stem'])
        sys.path.insert(0,self.fit['stem'])
        print sys.path[0]
        #sys.exit()
        # Set default options
        for item in self.optional_items:
            if 'file' in item and item not in self.files:
                self.files[item] = self.optional_items[item] 
            elif 'file' not in item and item not in self.fit:
                self.fit[item] = self.optional_items[item] 
                
        # calculate stiffness tensor
        if self.fit['crystal_system'] == None:
            self.C = n.zeros((6,6))
        else:
            self.C = conversion.formStiffnessMV(self.fit['crystal_system'],
                                                c11=self.fit['c11'],c12=self.fit['c12'],c13=self.fit['c13'],c14=self.fit['c14'],c15=self.fit['c15'],c16=self.fit['c16'],
                                                                    c22=self.fit['c22'],c23=self.fit['c23'],c24=self.fit['c24'],c25=self.fit['c25'],c26=self.fit['c26'],
                                                                                        c33=self.fit['c33'],c34=self.fit['c34'],c35=self.fit['c35'],c36=self.fit['c36'],
                                                                                                            c44=self.fit['c44'],c45=self.fit['c45'],c46=self.fit['c46'],
                                                                                                                                c55=self.fit['c55'],c56=self.fit['c56'],
                                                                                                                                                    c66=self.fit['c66'])
        #print self.C                       
           
           
    def read_par(self,par_file): # read detector.par
        try:
            f=open(par_file,'r')
        except IOError:
            logging.error('No file named %s' %filename)
            raise IOError
        
        input = f.readlines()
        f.close()

        for lines in input:
            if lines.find('#') != 0:
                if lines.find('#') > 0:
                    lines = split(lines,'#')[0]
                line = split(lines)
                if len(line) != 0:
                    key = line[0]
                    val = line[1]

                    # evaluate and store parameters in self.param 
                    try:
                        self.param[key] = eval(val)
                    except:
                        self.param[key] = val
                        
        self.unit_cell = n.array([self.param['cell__a'],self.param['cell__b'],self.param['cell__c'],self.param['cell_alpha'],self.param['cell_beta'],self.param['cell_gamma']])
        self.param['unit_cell'] = self.unit_cell
        (dety_center, detz_center) = detector.xy2detyz([self.param['z_center'],self.param['y_center']],
                                                        self.param['o11'],self.param['o12'],self.param['o21'],self.param['o22'],
                                                        self.fit['dety_size'],self.fit['detz_size'])
        self.param['y_center'] = dety_center
        self.param['z_center'] = detz_center
				
                
    def read_flt(self,flt_file): # read peaks_t##.flt and calculate experimental variances Sww,Syy,Szz
        # create parameters, must be lists in order to append
		
        #read as columnfile to avoid problems if peaksearch output is changed
        flt = ic.columnfile(flt_file)
        self.int = flt.getcolumn('sum_intensity')
        intmax = flt.getcolumn('IMax_int')
        self.w = flt.getcolumn('omega')
        sigw = flt.getcolumn('sigo')
        spot = flt.getcolumn('spot3d_id')        
        sc = flt.getcolumn('sc')
        fc = flt.getcolumn('fc')
        sigs = flt.getcolumn('sigs')
        sigf = flt.getcolumn('sigf')
        self.dety = []
        self.detz = []
        sigy = []
        sigz = []
        for i in range(flt.nrows):
            (dety,detz) = detector.xy2detyz([sc[i],fc[i]],
                                              self.param['o11'],
                                              self.param['o12'],
                                              self.param['o21'],
                                              self.param['o22'],
                                              self.fit['dety_size'],
                                              self.fit['detz_size'])
            self.dety.append(dety)				
            self.detz.append(detz)
            (sy,sz) = detector.xy2detyz([sigs[i],sigf[i]],
                                              self.param['o11'],
                                              self.param['o12'],
                                              self.param['o21'],
                                              self.param['o22'],
                                              self.fit['dety_size'],
                                              self.fit['detz_size'])
            sigy.append(abs(sy))				
            sigz.append(abs(sz))

        # convert into arrays so sorting according to spotid is possible 
        self.dety = n.array(self.dety)
        self.detz = n.array(self.detz)	
        sigy = n.array(sigy)
        sigz = n.array(sigz)
        # do the sorting
        self.w = self.w[n.argsort(spot)]
        self.dety = self.dety[n.argsort(spot)]
        self.detz = self.detz[n.argsort(spot)]
        sigw = sigw[n.argsort(spot)]
        sigy = sigy[n.argsort(spot)]
        sigz = sigz[n.argsort(spot)]
        self.int = self.int[n.argsort(spot)]
        intmax = intmax[n.argsort(spot)]

        # we now have arrays on length len(self.spot), but in the end we want lists of length maxspotno+1
        # therefore create temporary lists with zero values of length maxspotno+1
        self.param['total_refl'] = int(max(spot))+1 #necessary if spots are not consequtively numbered
        tw = [0.]*self.param['total_refl']
        tdety = [0.]*self.param['total_refl']
        tdetz = [0.]*self.param['total_refl']
        tsigw = [-1.]*self.param['total_refl']
        tsigy = [-1.]*self.param['total_refl']
        tsigz = [-1.]*self.param['total_refl']
        tint = [0.]*self.param['total_refl']
        tintmax = [1.]*self.param['total_refl']
        missing = 0
        # update temporary lists for all read reflections
        for i in range(self.param['total_refl']):
            if i in spot:
                tw[i] = self.w[i-missing]
                tdety[i] = self.dety[i-missing]
                tdetz[i] = self.detz[i-missing]
                tsigw[i] = sigw[i-missing]
                tsigy[i] = sigy[i-missing]
                tsigz[i] = sigz[i-missing]
                tint[i] = self.int[i-missing]
                tintmax[i] = intmax[i-missing]
            else:
                missing = missing+1

        #copy temporary lists to variables        
        self.w = tw
        self.dety = tdety
        self.detz = tdetz
        sigw = tsigw
        sigy = tsigy
        sigz = tsigz
        self.int = tint
        intmax = tintmax
        
        # set default variances
        self.Sww = [self.fit['w_step']**2/12.]*self.param['total_refl']
        self.Syy = [1.]*self.param['total_refl']
        self.Szz = [1.]*self.param['total_refl']
#        self.Syy = [1./12.]*self.param['total_refl']
#        self.Szz = [1./12.]*self.param['total_refl']

        
        #NB! should be sig**2/int, the -1 term is a temporary fix and so are the limits of 1, this should be 0
        # Error expressions taken from Withers, Daymond and Johnson (2001), J.Appl.Cryst.34,737.
        for j in range(len(self.int)):
            if self.int[j] > 0:
                if sigw[j] > 1:
                    self.Sww[j] = self.fit['const']*(1+n.sqrt(8)*self.fit['bg']/intmax[j])*(sigw[j]**2-1)/self.int[j]
                if sigy[j] > 1:
                    self.Syy[j] = self.fit['const']*(1+n.sqrt(8)*self.fit['bg']/intmax[j])*(sigy[j]**2-1)/self.int[j]
                if sigz[j] > 1:
                    self.Szz[j] = self.fit['const']*(1+n.sqrt(8)*self.fit['bg']/intmax[j])*(sigz[j]**2-1)/self.int[j]       
#            print '%e, %e, %e' %(self.Sww[j],self.Syy[j],self.Szz[j])
        if self.fit['w_limit'] == None:
            self.fit['w_limit'] = [min(self.w),max(self.w)]
        else:
            assert len(self.fit['w_limit']) % 2 == 0, 'An even number of omega-limits must be given'
            self.fit['w_limit'].sort()

 
    def read_log(self): # read grainspotter.log
        self.nrefl = []
        self.euler = []
        self.h = []
        self.k = []
        self.l = []
        self.id = []
        self.x = []
        self.y = []
        self.z = []
        self.eta = [0]*self.param['total_refl']
        self.tth = [0]*self.param['total_refl']
        ia = []
		
        try:
            f=open(self.files['log_file'],'r')
        except IOError:
            logging.error('No file named %s' %self.files['log_file'])
            raise IOError
        
        input = f.readlines()
        f.close()

        self.no_grains = int(split(input[0])[1])
        nn = 23 # jumping to first grain

        for gr in range(self.no_grains):
            nn = nn + 1
            self.nrefl.append(int(split(input[nn])[1]))
            nn = nn + 1
            # read grain positions from new grainspotter output
            if len(split(input[nn])) >= 4: 
                ia.append(eval(split(input[nn])[0]))
                self.x.append(eval(split(input[nn])[1]))
                self.y.append(eval(split(input[nn])[2]))
                self.z.append(eval(split(input[nn])[3]))
            nn = nn + 11
            self.euler.append([eval(split(input[nn])[0]),eval(split(input[nn])[1]),eval(split(input[nn])[2])])
            nn = nn + 3
            idgr = []
            h = []
            k = []
            l = []
            for refl in range(self.nrefl[gr]):
                nn = nn + 1
                idgr.append(int(split(input[nn])[2]))
                h.append(int(split(input[nn])[3]))
                k.append(int(split(input[nn])[4]))
                l.append(int(split(input[nn])[5]))
                self.tth[int(split(input[nn])[2])]=float(split(input[nn])[12])
                self.eta[int(split(input[nn])[2])]=float(split(input[nn])[18])

            self.id.append(idgr)				
            self.h.append(h)				
            self.k.append(k)				
            self.l.append(l)
            nn = nn + 2
        
        # calculate self.F2vol which is the intensity divided the Lorentz factor, thus the squared structure factor times the volume
        self.F2vol = [0]*self.param['total_refl']
        for i in range(self.param['total_refl']):
            self.F2vol[i] = self.int[i]*abs(n.sin(self.eta[i]*n.pi/180.))*n.sin(self.tth[i]*n.pi/180.)
            
        self.param['theta_min'] = min(self.tth)/2.
        self.param['theta_max'] = max(self.tth)/2.
        
        # delete grains with an internal angle above the set threshold
        for i in range(self.no_grains):
            if ia[i] > self.fit['ia']:
                self.fit['skip'].append(i+1)
                
        for i in range(1,self.no_grains):
            Ui = tools.euler2U(self.euler[i][0]*n.pi/180,self.euler[i][1]*n.pi/180,self.euler[i][2]*n.pi/180)
            for j in range(i):
                Uj = tools.euler2U(self.euler[j][0]*n.pi/180,self.euler[j][1]*n.pi/180,self.euler[j][2]*n.pi/180)
                Umis = symmetry.Umis(Ui,Uj,7)
                mis = 180.
                for k in range(len(Umis)):
                    if Umis[k][1] < mis:
                        mis = Umis[k][1]
                if mis < 5:
                    dist = n.sqrt((self.x[i]-self.x[j])**2+(self.y[i]-self.y[j])**2)
                    if  dist < 0.1:
                        print i+1,j+1,mis,self.x[i],self.y[i],self.z[i],self.x[j],self.y[j],self.z[j],dist
            
            
        
            

    def read_res(self): # read file of positions, orientations and strain tensor components to resume refinement
        try:
            f=open(self.files['res_file'],'r')
            f.close()
            print 'Resume refinement'
            res = ic.columnfile(self.files['res_file'])
            self.grainno = res.getcolumn('grainno')
            self.grainno = self.grainno.astype(n.int)
            self.grainno = self.grainno.tolist()
            self.x = res.getcolumn('x')
            self.y = res.getcolumn('y')
            self.z = res.getcolumn('z')
            self.phia = res.getcolumn('phi1')
            self.PHI = res.getcolumn('PHI')
            self.phib = res.getcolumn('phi2')
            self.eps11 = res.getcolumn('eps11')
            self.eps22 = res.getcolumn('eps22')
            self.eps33 = res.getcolumn('eps33')
            self.eps23 = res.getcolumn('eps23')
            self.eps13 = res.getcolumn('eps13')
            self.eps12 = res.getcolumn('eps12')
        except:
            print 'Start refinement from scratch' 
            return


                
    def read_rej(self): # read file containing rejected peaks to resume refinement
        try:
            f=open(self.files['rej_file'],'r')
        except:
            print 'Start refinement without apriori information about peak rejection' 
            return
        print 'Use apriori information about peak rejections' 
        
        input = f.readlines()
        f.close()

        # build rejection list in rigth format
        rejectid = []
        for i in range(self.no_grains):
            rejectid.append([])
                    
        # read parameters by appending
        for line in input:
            if 'Rejected peak id' in line:
                rejectid[int(split(line)[7])-1].append(int(split(line)[4]))
                self.fit['rejectid'].append(int(split(line)[4]))
                self.fit['rejectgrain'].append(int(split(line)[7]))
                self.fit['hh'].append(int(split(line)[9]))
                self.fit['kk'].append(int(split(line)[10]))
                self.fit['ll'].append(int(split(line)[11]))
                try:
                    self.fit['rejectvalue'].append(eval(split(line)[13]))
                except:
                    self.fit['rejectvalue'].append(split(line)[13])
                self.fit['outliers'] = self.fit['outliers'] + 1
            if 'Skip grains' in line:
                string = ''
                for i in range(2,len(split(line))):
                    string = string+split(line)[i]
                self.fit['skip'].extend(eval(string))
        for i in range(self.no_grains):
            for j in range(self.nrefl[i]-1,-1,-1): # loop backwards to make pop work
                if self.id[i][j] in rejectid[i]:
                    self.id[i].pop(j)
                    self.h[i].pop(j)
                    self.k[i].pop(j)
                    self.l[i].pop(j)
                    self.nrefl[i] = self.nrefl[i] - 1


    def set_start(self): # build fcn, initiate minuit and set starting values and errors

        self.values = {}
        # grain values
        for i in range(self.no_grains):
            self.values['x%s' %i] = 0.0
            self.values['y%s' %i] = 0.0
            self.values['z%s' %i] = 0.0
            self.values['epsaa%s' %i] = 0.0 
            self.values['epsab%s' %i] = 0.0  
            self.values['epsac%s' %i] = 0.0
            self.values['epsbb%s' %i] = 0.0 
            self.values['epsbc%s' %i] = 0.0 
            self.values['epscc%s' %i] = 0.0
            self.values['phia%s' %i] = self.euler[i][0]
            self.values['PHI%s' %i]  = self.euler[i][1]
            self.values['phib%s' %i] = self.euler[i][2]
        # grain values for resuming refinement
        if self.files['res_file'] != None:
            for i in range(self.no_grains):
                if i+1 in self.grainno:
                    self.values['x%s' %i] = 1000.*self.x[self.grainno.index(i+1)]
                    self.values['y%s' %i] = 1000.*self.y[self.grainno.index(i+1)]
                    self.values['z%s' %i] = 1000.*self.z[self.grainno.index(i+1)]
                    self.values['epsaa%s' %i] = self.eps11[self.grainno.index(i+1)] 
                    self.values['epsab%s' %i] = self.eps12[self.grainno.index(i+1)] 
                    self.values['epsac%s' %i] = self.eps13[self.grainno.index(i+1)]
                    self.values['epsbb%s' %i] = self.eps22[self.grainno.index(i+1)]
                    self.values['epsbc%s' %i] = self.eps23[self.grainno.index(i+1)]
                    self.values['epscc%s' %i] = self.eps33[self.grainno.index(i+1)]
                    self.values['phia%s' %i] = self.phia[self.grainno.index(i+1)] 
                    self.values['PHI%s' %i]  = self.PHI[self.grainno.index(i+1)] 
                    self.values['phib%s' %i] = self.phib[self.grainno.index(i+1)] 
        # else if start from scratch with new grainspotter log file use positions from this
        elif len(self.x) == self.no_grains:
            for i in range(self.no_grains):
                self.values['x%s' %i] = 1000.*self.x[i]
                self.values['y%s' %i] = 1000.*self.y[i]
                self.values['z%s' %i] = 1000.*self.z[i]
        
        self.errors = {}
        # global errors
        self.param['chi_error'] = 0.001
        self.param['wedge_error'] = 0.001
        self.param['tilt_x_error'] = 0.001
        self.param['tilt_y_error'] = 0.001
        self.param['tilt_z_error'] = 0.001
        self.param['y_size_error'] = 0.1
        self.param['z_size_error'] = 0.1
        self.param['y_center_error'] = 0.1
        self.param['z_center_error'] = 0.1
        self.param['distance_error']  = 1
        self.param['i_error']  = 1
        self.param['j_error']  = 1
        # grain errors
        for i in range(self.no_grains):
            self.errors['x%s' %i] = self.param['y_size']/5.
            self.errors['y%s' %i] = self.param['y_size']/5.
            self.errors['z%s' %i] = self.param['z_size']/10.
            self.errors['epsaa%s' %i] = 0.0001 
            self.errors['epsab%s' %i] = 0.0001
            self.errors['epsac%s' %i] = 0.0001
            self.errors['epsbb%s' %i] = 0.0001
            self.errors['epsbc%s' %i] = 0.0001
            self.errors['epscc%s' %i] = 0.0001
            self.errors['phia%s' %i] = 0.1
            self.errors['PHI%s' %i]  = 0.1
            self.errors['phib%s' %i] = 0.1
    

        self.fit['newreject_grain'] = []
        
            
    def reject(self): # carry out initial rejections

        import reject
        print '\n\nNumber of assigned reflections (from GrainSpotter): ', n.sum(self.nrefl)
        # set starting values
        self.newreject = 0
        self.fit['newreject_grain'] = []
        self.residual = []
        self.volume = []
        for i in range(self.no_grains):
            self.residual.append([])
            self.volume.append([])
            for j in range(self.nrefl[i]):
                self.residual[i].append(1)
                self.volume[i].append(1)
        # do the actual rejections
        reject.intensity(self)
        reject.residual(self,self.fit['limit'][0])
        reject.merge(self)
        reject.multi(self)
        #reject.friedel(self)

		
    def write_rej(self): # write the rejected peaks to rejection file
    
        import reject
        reject.unique_list(self.fit['skip'])
        print 'Skip the following grains:', self.fit['skip']
        print 'Number of grains from grainspotter', self.no_grains
        print 'Actual number of grains in fit', self.no_grains - len(self.fit['skip']),'\n'	
       
        write_output.write_rej(self,message=('%s\n\ncheck_input' %self.fit['title']))
        
def set_globals(inp):
        # global values
        inp.values['wx'] = deepcopy(inp.param['chi'])
        inp.values['wy'] = deepcopy(inp.param['wedge'])
        inp.values['tx'] = deepcopy(inp.param['tilt_x'])
        inp.values['ty'] = deepcopy(inp.param['tilt_y'])
        inp.values['tz'] = deepcopy(inp.param['tilt_z'])
        inp.values['py'] = deepcopy(inp.param['y_size'])
        inp.values['pz'] = deepcopy(inp.param['z_size'])
        inp.values['cy'] = deepcopy(inp.param['y_center'])
        inp.values['cz'] = deepcopy(inp.param['z_center'])
        inp.values['L']  = deepcopy(inp.param['distance'])
        # global errors
        inp.errors['wx'] = deepcopy(inp.param['chi_error'])
        inp.errors['wy'] = deepcopy(inp.param['wedge_error'])
        inp.errors['tx'] = deepcopy(inp.param['tilt_x_error'])
        inp.errors['ty'] = deepcopy(inp.param['tilt_y_error'])
        inp.errors['tz'] = deepcopy(inp.param['tilt_z_error'])
        inp.errors['py'] = deepcopy(inp.param['y_size_error'])
        inp.errors['pz'] = deepcopy(inp.param['z_size_error'])
        inp.errors['cy'] = deepcopy(inp.param['y_center_error'])
        inp.errors['cz'] = deepcopy(inp.param['z_center_error'])
        inp.errors['L']  = deepcopy(inp.param['distance_error'])
        inp.errors['i']  = deepcopy(inp.param['i_error'])
        inp.errors['j']  = deepcopy(inp.param['j_error'])
    
    
def copy_globals(inp):
        # Necessary to save copies of global parameters in param when switching between near and farfiel detectors
        # global values
        inp.param['chi'] = deepcopy(inp.values['wx']) 
        inp.param['wedge'] = deepcopy(inp.values['wy']) 
        inp.param['tilt_x'] = deepcopy(inp.values['tx']) 
        inp.param['tilt_y'] = deepcopy(inp.values['ty']) 
        inp.param['tilt_z'] = deepcopy(inp.values['tz']) 
        inp.param['y_size'] = deepcopy(inp.values['py']) 
        inp.param['y_size'] = deepcopy(inp.values['pz']) 
        inp.param['y_center'] = deepcopy(inp.values['cy']) 
        inp.param['z_center'] = deepcopy(inp.values['cz']) 
        inp.param['distance'] = deepcopy(inp.values['L'])  
        # global errors
        inp.param['chi_error'] = deepcopy(inp.errors['wx']) 
        inp.param['wedge_error'] = deepcopy(inp.errors['wy']) 
        inp.param['tilt_x_error'] = deepcopy(inp.errors['tx']) 
        inp.param['tilt_y_error'] = deepcopy(inp.errors['ty']) 
        inp.param['tilt_z_error'] = deepcopy(inp.errors['tz']) 
        inp.param['y_size_error'] = deepcopy(inp.errors['py']) 
        inp.param['z_size_error'] = deepcopy(inp.errors['pz']) 
        inp.param['y_center_error'] = deepcopy(inp.errors['cy']) 
        inp.param['z_center_error'] = deepcopy(inp.errors['cz']) 
        inp.param['distance_error'] = deepcopy(inp.errors['L'])  
        inp.param['i_error'] = deepcopy(inp.errors['i'])  
        inp.param['j_error'] = deepcopy(inp.errors['j'])  
                   
        
        
 