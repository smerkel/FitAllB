from __future__ import absolute_import
import numpy as n
from xfab import tools
from xfab import symmetry
from xfab import detector
from . import reject
import sys
import logging
from . import conversion
from copy import deepcopy
from string import split
from six.moves import range
logging.basicConfig(level=logging.DEBUG,format='%(levelname)s %(message)s')

		
def write_cov(lsqr,i):
    """
    Calculate and save the covariance matrix for grain i
    Jette Oddershede June 13th 2008
    """
    
    # clear cov file at first visit 
    filename = '%s/%s_cov.txt' %(lsqr.inp.fit['direc'],lsqr.inp.fit['stem'])
    if i == 0 and lsqr.inp.fit['goon'] == 'grain':
        f = open(filename,'w')
        f.close()
    # now open for appending
    f = open(filename,'a' )
    if i == 0:
        f.write('\n \t\n**********%s********** \n\t' %lsqr.inp.fit['goon'])
    lines = 0
    for entry1 in lsqr.grains[i]:
        if lsqr.mg.fixed[entry1] == False:
            if lines == 0:
                string = '\n         '
                for entry2 in lsqr.grains[i]:
                    if lsqr.mg.fixed[entry2] == False:
                        string = string + '%13s  ' %entry2
                string = string + '\n'
                f.write(string)
                lines = 1					
            string = '%13s  ' %entry1
            for entry2 in lsqr.grains[i]:
                if lsqr.mg.fixed[entry2] == False:
                    string = string + '%8e  ' %lsqr.mg.covariance[('%s' %entry1, '%s' %entry2)] 
            string = string + '\n'
            f.write(string)
        
    f.close()		


def write_cor(lsqr,i):
    """
    Calculate and save the correlation matrix for grain i
    Jette Oddershede June 13th 2008
    """
    
    # clear cor file at first visit
    filename = '%s/%s_cor.txt' %(lsqr.inp.fit['direc'],lsqr.inp.fit['stem'])
    if i == 0 and lsqr.inp.fit['goon'] == 'grain':
        f = open(filename,'w')
        f.close()
    # now open for appending
    f = open(filename,'a' )
    if i == 0:
        f.write('\n \t\n**********%s********** \n\t' %lsqr.inp.fit['goon'])
    lines = 0
    for entry1 in lsqr.grains[i]:
        if lsqr.mg.fixed[entry1] == False:
            if lines == 0:
                string = '\n         '
                for entry2 in lsqr.grains[i]:
                    if lsqr.mg.fixed[entry2] == False:
                        string = string + '%8s  ' %entry2
                string = string + '\n'
                f.write(string)
                lines = 1					
            string = '%8s  ' %entry1
            for entry2 in lsqr.grains[i]:
                if lsqr.mg.fixed[entry2] == False:
                    string = string + '%8f  ' %(lsqr.mg.covariance[('%s' %entry1, '%s' %entry2)]/(n.sqrt(lsqr.mg.covariance[('%s' %entry1, '%s' %entry1)])*n.sqrt(lsqr.mg.covariance[('%s' %entry2, '%s' %entry2)]))) 
            string = string + '\n'
            f.write(string)
        
    f.close()		


def write_global(lsqr):
    """
    Calculate and save the correlation and covariance matrices for the global parameters
    Jette Oddershede August 20th 2008
    """
    
    # clear cor file at first visit
    filename = '%s/%s_global.txt' %(lsqr.inp.fit['direc'],lsqr.inp.fit['stem'])
    if lsqr.inp.fit['goon'] == 'globals0':
        f = open(filename,'w')
        f.write('NB! The beam center coordinates refer to the internal coordinate system \n')
        f.write('    unlike the values of cy and cz output in the log file \n')
        f.close()
    # now open for appending
    f = open(filename,'a' )
    f.write('\n\n\n**********%s********** \n' %lsqr.inp.fit['goon'])
    f.write('\n\n**********correlation matrix**********\n')
    lines = 0
    for entry1 in lsqr.globals:
        if lsqr.m.fixed[entry1] == False:
            if lines == 0:
                string = '\n         '
                for entry2 in lsqr.globals:
                    if lsqr.m.fixed[entry2] == False:
                        string = string + '%8s  ' %entry2
                string = string + '\n'
                f.write(string)
                lines = 1					
            string = '%8s  ' %entry1
            for entry2 in lsqr.globals:
                if lsqr.m.fixed[entry2] == False:
                    string = string + '%8f  ' %(lsqr.m.covariance[('%s' %entry1, '%s' %entry2)]/(n.sqrt(lsqr.m.covariance[('%s' %entry1, '%s' %entry1)])*n.sqrt(lsqr.m.covariance[('%s' %entry2, '%s' %entry2)]))) 
            string = string + '\n'
            f.write(string)
        
    f.write('\n\n**********covariance matrix********** \n')
    lines = 0
    for entry1 in lsqr.globals:
        if lsqr.m.fixed[entry1] == False:
            if lines == 0:
                string = '\n         '
                for entry2 in lsqr.globals:
                    if lsqr.m.fixed[entry2] == False:
                        string = string + '%8s  ' %entry2
                string = string + '\n'
                f.write(string)
                lines = 1					
            string = '%8s  ' %entry1
            for entry2 in lsqr.globals:
                if lsqr.m.fixed[entry2] == False:
                    string = string + '%8e  ' %(lsqr.m.covariance[('%s' %entry1, '%s' %entry2)]) 
            string = string + '\n'
            f.write(string)

    f.close()		


def write_values(lsqr):
    """
    Save the fitted grain parameters, pos, U and eps

    INPUT: The parameter set from the final fitting
    OUTPUT: grainno mean_IA grain_volume x y z rodx rody rodz 
            U11 U12 U13 U21 U22 U23 U31 U32 U33 
            eps11   eps22   eps33   eps23   eps13   eps12
            eps11_s eps22_s eps33_s eps23_s eps13_s eps12_s
            sig11   sig22   sig33   sig23   sig13   sig12
            sig11_s sig22_s sig33_s sig23_s sig13_s sig12_s
 
    Jette Oddershede, Risoe DTU, April 21 2008
    """


    filename = '%s/%s_%s.gff' %(lsqr.inp.fit['direc'],lsqr.inp.fit['stem'],lsqr.inp.fit['goon'])
    f = open(filename,'w')
    format = "%d "*1 + "%f "*8 + "%0.12f "*9 + "%e "*24 +"\n"
    out = "# grainno mean_IA grainvolume x y z rodx rody rodz U11 U12 U13 U21 U22 U23 U31 U32 U33 eps11 eps22 eps33 eps23 eps13 eps12 "
    out = out + "eps11_s eps22_s eps33_s eps23_s eps13_s eps12_s sig11 sig22 sig33 sig23 sig13 sig12 sig11_s sig22_s sig33_s sig23_s sig13_s sig12_s\n"
    f.write(out)
    for i in range(lsqr.inp.no_grains):
        if i+1 in lsqr.inp.fit['skip']:
            pass
        else:
            U = tools.rod_to_u([lsqr.inp.rod[i][0]+lsqr.m.values['rodx%s' %i],lsqr.inp.rod[i][1]+lsqr.m.values['rody%s' %i],lsqr.inp.rod[i][2]+lsqr.m.values['rodz%s' %i],])
            eps = n.array([[lsqr.m.values['epsaa%s' %i],lsqr.m.values['epsab%s' %i],lsqr.m.values['epsac%s' %i]],
                           [lsqr.m.values['epsab%s' %i],lsqr.m.values['epsbb%s' %i],lsqr.m.values['epsbc%s' %i]],
                           [lsqr.m.values['epsac%s' %i],lsqr.m.values['epsbc%s' %i],lsqr.m.values['epscc%s' %i]]])
            eps_s = conversion.grain2sample(eps,U)
            sig = conversion.strain2stress(eps,lsqr.inp.C)
            sig_s = conversion.grain2sample(sig,U)            
            out = format %(i+1,
    			           n.sum(lsqr.inp.mean_ia[i])/len(lsqr.inp.mean_ia[i]),#0,
#	    				   sum(lsqr.inp.volume[i])/lsqr.inp.nrefl[i],
	    				   reject.median(lsqr.inp.volume[i]),
                           lsqr.m.values['x%s' %i]/1000,
                           lsqr.m.values['y%s' %i]/1000,
                           lsqr.m.values['z%s' %i]/1000,
                           lsqr.inp.rod[i][0]+lsqr.m.values['rodx%s' %i],
                           lsqr.inp.rod[i][1]+lsqr.m.values['rody%s' %i],
                           lsqr.inp.rod[i][2]+lsqr.m.values['rodz%s' %i],
                           U[0,0],
                           U[0,1],
                           U[0,2],
                           U[1,0],
                           U[1,1],
                           U[1,2],
                           U[2,0],
                           U[2,1],
                           U[2,2],
                           eps[0][0],
                           eps[1][1],
                           eps[2][2],
                           eps[1][2],
                           eps[0][2],
                           eps[0][1],
                           eps_s[0][0],
                           eps_s[1][1],
                           eps_s[2][2],
                           eps_s[1][2],
                           eps_s[0][2],
                           eps_s[0][1],
                           sig[0][0],
                           sig[1][1],
                           sig[2][2],
                           sig[1][2],
                           sig[0][2],
                           sig[0][1],
                           sig_s[0][0],
                           sig_s[1][1],
                           sig_s[2][2],
                           sig_s[1][2],
                           sig_s[0][2],
                           sig_s[0][1]
                          )
            f.write(out)
    f.close()   


def write_errors(lsqr,i):
    """
    Save the fitted grain error parameters, pos, U and eps

    INPUT: The error set from the final fitting
    OUTPUT: grainno mean_IA grainvolume x y z rodx rody rodz
            U11 U12 U13 U21 U22 U23 U31 U32 U33 
            eps11   eps22   eps33   eps23   eps13   eps12
            eps11_s eps22_s eps33_s eps23_s eps13_s eps12_s
            sig11   sig22   sig33   sig23   sig13   sig12
            sig11_s sig22_s sig33_s sig23_s sig13_s sig12_s
 
    Jette Oddershede, Risoe DTU, June 23 2008
    """
    

    # error transformation into other coordinate system and from strain to stress under construction
    U = tools.rod_to_u([lsqr.inp.rod[i][0]+lsqr.m.values['rodx%s' %i],lsqr.inp.rod[i][1]+lsqr.m.values['rody%s' %i],lsqr.inp.rod[i][2]+lsqr.m.values['rodz%s' %i],])
    eps_ref = False
    rodx_err = 0
    rody_err = 0
    rodz_err = 0
    for key in lsqr.mg.covariance.keys():
        if 'epsaa%s' %i in key:
            eps_ref = True
            break

    if eps_ref == False:
        cov_eps = n.zeros((6,6))
    else:
        free = list(lsqr.mg.fixed.values()).count(False)
        assert free >= 6, 'wrong dimensions of covariance matrix'
        covariance = n.zeros((free,free))
        j1 = 0
        for entry1 in lsqr.grains[i]:
            if lsqr.mg.fixed[entry1] == False:
                j2 = 0
                for entry2 in lsqr.grains[i]:
                    if lsqr.mg.fixed[entry2] == False:
                        covariance[j1][j2] = lsqr.mg.covariance[('%s' %entry1, '%s' %entry2)]
                        j2 = j2 + 1
                j1 = j1 + 1
                
        if free == 6:
            cov_eps = covariance
        else:
            derivatives = n.linalg.inv(covariance)
            derivatives_rod = derivatives[len(derivatives)-9:len(derivatives)-6,len(derivatives)-9:len(derivatives)-6]
            cov_rod = n.linalg.inv(derivatives_rod)
            vars_rod = n.linalg.eig(cov_rod)[0]
            derivatives = derivatives[len(derivatives)-6:,len(derivatives)-6:]
            cov_eps = n.linalg.inv(derivatives)

    # old way of doing it including covariances with orientations in strain errors
    try:
        cov_eps = n.array([[lsqr.mg.covariance[('epsaa%s' %i, 'epsaa%s' %i)],lsqr.mg.covariance[('epsaa%s' %i, 'epsbb%s' %i)],lsqr.mg.covariance[('epsaa%s' %i, 'epscc%s' %i)],
                        lsqr.mg.covariance[('epsaa%s' %i, 'epsbc%s' %i)],lsqr.mg.covariance[('epsaa%s' %i, 'epsac%s' %i)],lsqr.mg.covariance[('epsaa%s' %i, 'epsab%s' %i)]],
                       [lsqr.mg.covariance[('epsbb%s' %i, 'epsaa%s' %i)],lsqr.mg.covariance[('epsbb%s' %i, 'epsbb%s' %i)],lsqr.mg.covariance[('epsbb%s' %i, 'epscc%s' %i)],
                        lsqr.mg.covariance[('epsbb%s' %i, 'epsbc%s' %i)],lsqr.mg.covariance[('epsbb%s' %i, 'epsac%s' %i)],lsqr.mg.covariance[('epsbb%s' %i, 'epsab%s' %i)]],
                       [lsqr.mg.covariance[('epscc%s' %i, 'epsaa%s' %i)],lsqr.mg.covariance[('epscc%s' %i, 'epsbb%s' %i)],lsqr.mg.covariance[('epscc%s' %i, 'epscc%s' %i)],
                        lsqr.mg.covariance[('epscc%s' %i, 'epsbc%s' %i)],lsqr.mg.covariance[('epscc%s' %i, 'epsac%s' %i)],lsqr.mg.covariance[('epscc%s' %i, 'epsab%s' %i)]],
                       [lsqr.mg.covariance[('epsbc%s' %i, 'epsaa%s' %i)],lsqr.mg.covariance[('epsbc%s' %i, 'epsbb%s' %i)],lsqr.mg.covariance[('epsbc%s' %i, 'epscc%s' %i)],
                        lsqr.mg.covariance[('epsbc%s' %i, 'epsbc%s' %i)],lsqr.mg.covariance[('epsbc%s' %i, 'epsac%s' %i)],lsqr.mg.covariance[('epsbc%s' %i, 'epsab%s' %i)]],
                       [lsqr.mg.covariance[('epsac%s' %i, 'epsaa%s' %i)],lsqr.mg.covariance[('epsac%s' %i, 'epsbb%s' %i)],lsqr.mg.covariance[('epsac%s' %i, 'epscc%s' %i)],
                        lsqr.mg.covariance[('epsac%s' %i, 'epsbc%s' %i)],lsqr.mg.covariance[('epsac%s' %i, 'epsac%s' %i)],lsqr.mg.covariance[('epsac%s' %i, 'epsab%s' %i)]],
                       [lsqr.mg.covariance[('epsab%s' %i, 'epsaa%s' %i)],lsqr.mg.covariance[('epsab%s' %i, 'epsbb%s' %i)],lsqr.mg.covariance[('epsab%s' %i, 'epscc%s' %i)],
                        lsqr.mg.covariance[('epsab%s' %i, 'epsbc%s' %i)],lsqr.mg.covariance[('epsab%s' %i, 'epsac%s' %i)],lsqr.mg.covariance[('epsab%s' %i, 'epsab%s' %i)]]])
    except:
        cov_eps = n.zeros((6,6))
            
            
            
            
            
    cov_eps_s = conversion.CovarianceRotation(cov_eps,U)
    cov_sig = conversion.CovarianceTransformation(cov_eps,lsqr.inp.C)
    cov_sig_s = conversion.CovarianceRotation(cov_sig,U)
    
    filename = '%s/%s_errors.gff' %(lsqr.inp.fit['direc'],lsqr.inp.fit['stem'])
    filename2 = '%s/%s_%s_errors.gff' %(lsqr.inp.fit['direc'],lsqr.inp.fit['stem'],lsqr.inp.fit['goon'])
    try:
        f = open(filename,'r')
        lines = f.readlines()
        f.close()
    except:
        f = open(filename,'w')
        out = "# grainno mean_IA grainvolume x y z rodx rody rodz U11 U12 U13 U21 U22 U23 U31 U32 U33 eps11 eps22 eps33 eps23 eps13 eps12 "
        out = out + "eps11_s eps22_s eps33_s eps23_s eps13_s eps12_s sig11 sig22 sig33 sig23 sig13 sig12 sig11_s sig22_s sig33_s sig23_s sig13_s sig12_s\n"
        f.write(out)
        f.close()   
        f = open(filename,'r')
        lines = f.readlines()
        f.close()

    index = 0
    for j in range(1,len(lines)):
        if i+1 == eval(split(lines[j])[0]):
            index = j
            break
    if index == 0:
        index = len(lines)
        lines.append('')
    
    format = "%d "*1 + "%f "*8 + "%0.1f "*9 + "%e "*24 +"\n"
    
    lines[index] = format %(i+1,
			       reject.spread(lsqr.inp.mean_ia[i]),#0
#                   reject.spread(lsqr.inp.volume[i]),
                   reject.median_absolute_deviation(lsqr.inp.volume[i]),
                   lsqr.mg.errors['x%s' %i]/1000,
                   lsqr.mg.errors['y%s' %i]/1000,
                   lsqr.mg.errors['z%s' %i]/1000,
                   lsqr.mg.errors['rodx%s' %i],
                   lsqr.mg.errors['rody%s' %i],
                   lsqr.mg.errors['rodz%s' %i],
  			       0,
   			       0,
   			       0,
   			       0,
   			       0,
   			       0,
   			       0,
   			       0,
   			       0,
                   n.sqrt(cov_eps[0][0]),
                   n.sqrt(cov_eps[1][1]),
                   n.sqrt(cov_eps[2][2]),
                   n.sqrt(cov_eps[3][3]),
                   n.sqrt(cov_eps[4][4]),
                   n.sqrt(cov_eps[5][5]),
                   n.sqrt(cov_eps_s[0][0]),
                   n.sqrt(cov_eps_s[1][1]),
                   n.sqrt(cov_eps_s[2][2]),
                   n.sqrt(cov_eps_s[3][3]),
                   n.sqrt(cov_eps_s[4][4]),
                   n.sqrt(cov_eps_s[5][5]),
                   n.sqrt(cov_sig[0][0]),
                   n.sqrt(cov_sig[1][1]),
                   n.sqrt(cov_sig[2][2]),
                   n.sqrt(cov_sig[3][3]),
                   n.sqrt(cov_sig[4][4]),
                   n.sqrt(cov_sig[5][5]),
                   n.sqrt(cov_sig_s[0][0]),
                   n.sqrt(cov_sig_s[1][1]),
                   n.sqrt(cov_sig_s[2][2]),
                   n.sqrt(cov_sig_s[3][3]),
                   n.sqrt(cov_sig_s[4][4]),
                   n.sqrt(cov_sig_s[5][5])
                  )
    f = open(filename,'w')
    for j in range(len(lines)):
        f.write(lines[j])
    f.close()   
    f = open(filename2,'w')
    for j in range(len(lines)):
        f.write(lines[j])
    f.close()   

		
def write_log(lsqr):
    """
    Write fitting and rejection info in the log file
    """

    filename = '%s/%s_log.log' %(lsqr.inp.fit['direc'],lsqr.inp.fit['stem'])
    # clear log file at first visit
    filename = '%s/%s_log.log' %(lsqr.inp.fit['direc'],lsqr.inp.fit['stem'])
    if lsqr.inp.fit['goon'] == 'start':
        f = open(filename,'w')
        f.close()
    # now open for appending
    f = open(filename,'a' )
    # start writing output
    if lsqr.inp.fit['goon'] == 'start':
        f.write('%s\n' %lsqr.inp.fit['title'])
        f.write('Number of input grains %i \n' %lsqr.inp.no_grains)
        f.write('Number of fitted grains %i \n' %(lsqr.inp.no_grains-len(lsqr.inp.fit['skip'])))
        if len(lsqr.inp.fit['skip']) > 0:
            f.write('Skip the following grain numbers: %s\n' %lsqr.inp.fit['skip'])
    f.write('\n \t\n**********%s********** \n\t\n' %lsqr.inp.fit['goon'])
    if lsqr.ref == True:
        if 'start' in lsqr.inp.fit['goon']:
            f.write('Tolerance, %e \n' %lsqr.m.tol)
        else:
            f.write('Tolerance, %e \n' %lsqr.mg.tol)
    f.write('Time %i s \n' %lsqr.time)
    f.write('Value %e \n \t\n' %lsqr.fval)
    f.write('Grain data file: %s_%s.txt \n' %(lsqr.inp.fit['stem'],lsqr.inp.fit['goon']))
    # print values and errors of global parameters
    for entries in lsqr.globals:
            if lsqr.m.fixed[entries] == True:
                try:
                    f.write('%s %f\n' %(entries, lsqr.m.values[entries]))
                except:
                    pass
            else:
                try:
                    f.write('%s %f +- %f\n' %(entries, lsqr.m.values[entries], lsqr.m.errors[entries]))
                except:
                    pass
                    
	# print info on poor grains and rejected peaks	
    f.write('\nPoor grains: %s' %lsqr.inp.fit['poor'])
    f.write('\nPoor grains values: %s' %lsqr.poor_value)
    f.write('\nPoor grains nrefl: %s\n' %lsqr.poor_nrefl)
    f.write('\nSkip grains: %s\n' %lsqr.inp.fit['skip'])
    f.write('\nNumber of refined grains: %s\n' %(lsqr.inp.no_grains-len(lsqr.inp.fit['skip'])))
    f.write('Number of rejected outliers (new, total): (%i , %i)' %(lsqr.inp.newreject,lsqr.inp.fit['outliers']))
    observations = 0
    for i in range(lsqr.inp.no_grains):
        if i+1 in lsqr.inp.fit['skip']:
            pass
        else:
            for k in range(lsqr.inp.fit['no_det']):
                observations = observations + lsqr.inp.nrefl[k][i]
    f.write('\nNumber of assigned peaks: %s\n' %lsqr.inp.nrefl)                
 
    f.close()

        
def write_rej(inp, message = None):
    """
    Write rejection info in the rej file
    """
          
    if inp.files['rej_file'] == None:
        filename = '%s/%s_rej.txt' %(inp.fit['direc'],inp.fit['stem'])
    else:
        filename = inp.files['rej_file']
    # open for appending and write message
    f = open(filename,'a')
    if message != None:
        f.write('\n\n'+message+'\n')
    f.write('Skip grains: %s' %inp.fit['skip'])
    # write rejected peaks
    for j in range(inp.fit['outliers']-inp.newreject,inp.fit['outliers']):
        f.write('\n%i Rejected peak id %i detector %i from grain %i (hkl: %i %i %i ): %s' 
                %(j+1,inp.fit['rejectid'][j],inp.fit['rejectdet'][j],inp.fit['rejectgrain'][j]+1,inp.fit['hh'][j],inp.fit['kk'][j],inp.fit['ll'][j],inp.fit['rejectvalue'][j]))
 
    f.close()

    
def write_par(lsqr):
    """
    Save the detector parameters

    INPUT:  The refined detector info 
    OUTPUT: The corresponding detector.par file for FitAllB
            NB! The wedge convention follows FitAllB, thus righthanded, which is opposite of ImageD11

    Jette Oddershede, Risoe DTU, June 17 2008
    """

    for k in range(lsqr.inp.fit['no_det']):
        filename = '%s/%s_%s_fab%s.par' %(lsqr.inp.fit['direc'],lsqr.inp.fit['stem'],lsqr.inp.fit['goon'],k)
        f = open(filename,'w')
        
        (z_center, y_center) = detector.detyz_to_xy([lsqr.m.values['cy%s' %k],lsqr.m.values['cz%s' %k]],
                                                lsqr.inp.param['o11%s' %k],lsqr.inp.param['o12%s' %k],lsqr.inp.param['o21%s' %k],lsqr.inp.param['o22%s' %k],
                                                lsqr.inp.fit['dety_size%s' %k],lsqr.inp.fit['detz_size%s' %k])
			
        dout = "chi %f\n" %lsqr.m.values['wx']
        dout = dout + "distance %f\n" %(lsqr.m.values['L%s' %k]) 
        dout = dout + "fit_tolerance 0.5\n" 
        dout = dout + "o11 %i\n" %lsqr.inp.param['o11%s' %k]
        dout = dout + "o12 %i\n" %lsqr.inp.param['o12%s' %k]
        dout = dout + "o21 %i\n" %lsqr.inp.param['o21%s' %k]
        dout = dout + "o22 %i\n" %lsqr.inp.param['o22%s' %k]
        dout = dout + "omegasign %f\n" %lsqr.inp.param['omegasign']
        dout = dout + "t_x 0\n" 
        dout = dout + "t_y 0\n" 
        dout = dout + "t_z 0\n" 
        dout = dout + "tilt_x %f\n" %lsqr.m.values['tx%s' %k]
        dout = dout + "tilt_y %f\n" %lsqr.m.values['ty%s' %k]
        dout = dout + "tilt_z %f\n" %lsqr.m.values['tz%s' %k]
        dout = dout + "wavelength %f\n" %lsqr.inp.param['wavelength']
        dout = dout + "wedge %f\n" %(-1.*lsqr.m.values['wy']) #write jons wedge convention even though sorens is used internally in the program
        dout = dout + "y_center %f\n" %y_center
        dout = dout + "y_size %f\n" %lsqr.m.values['py%s' %k]
        dout = dout + "z_center %f\n" %z_center
        dout = dout + "z_size %f\n" %lsqr.m.values['pz%s' %k]

        out = "cell__a %f\n" %lsqr.m.values['a']
        out = out + "cell__b %f\n" %lsqr.m.values['b']
        out = out + "cell__c %f\n" %lsqr.m.values['c']
        out = out + "cell_alpha %0.3f\n" %lsqr.m.values['alpha']
        out = out + "cell_beta %0.3f\n" %lsqr.m.values['beta']
        out = out + "cell_gamma %0.3f\n" %lsqr.m.values['gamma']
        out = out + "cell_lattice_[P,A,B,C,I,F,R] %s\n" %lsqr.inp.param['cell_lattice_[P,A,B,C,I,F,R]']
        out = out + dout

        f.write(out)
        f.close()   

    