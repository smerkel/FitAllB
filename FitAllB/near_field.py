from __future__ import absolute_import
from __future__ import print_function
import numpy as n
from xfab import tools
from xfab import detector
from polyxsim import reflections
import sys
from six.moves import range


def find_refl(inp):
        """
        From U, (x,y,z) and B determined for the far-field case 
        calculate the possible reflection on the near-field detector 
        output[grainno][reflno]=[h,k,l,omega,dety,detz,tth,eta]
        """
        S = n.array([[1, 0, 0],[0, 1, 0],[0, 0, 1]])
        R = tools.detect_tilt(inp.param['tilt_x'],
                              inp.param['tilt_y'],
                              inp.param['tilt_z'])
        inp.possible = []

        # if structure info is given use this
        if  inp.files['structure_file'] != None:
            inp.param['structure_phase_0'] = inp.files['structure_file']
            xtal_structure = reflections.open_structure(inp.param,0)
            HKL = reflections.gen_miller(inp.param,0)
        else:
            inp.param['unit_cell_phase_0'] = inp.unit_cell		
            inp.param['sgno_phase_0'] = inp.fit['sgno']
            HKL = reflections.gen_miller(inp.param,0)

        for grainno in range(inp.no_grains):
            inp.possible.append([])
            if grainno+1 not in inp.fit['skip']:
                B = tools.epsilon_to_b(n.array([inp.values['epsaa%s' %grainno],
                                                inp.values['epsab%s' %grainno],
                                                inp.values['epsac%s' %grainno],
                                                inp.values['epsbb%s' %grainno],
                                                inp.values['epsbc%s' %grainno],
                                                inp.values['epscc%s' %grainno]]),
                                       inp.unit_cell)
                U = tools.rod_to_u([inp.rod[grainno][0]+inp.values['rodx%s' %grainno],
                                    inp.rod[grainno][1]+inp.values['rody%s' %grainno],
                                    inp.rod[grainno][2]+inp.values['rodz%s' %grainno]])
                gr_pos = n.array([inp.values['x%s' %grainno],
                                  inp.values['y%s' %grainno],
                                  inp.values['z%s' %grainno]])
            

  
                for hkl in HKL:
                    Gc = n.dot(B,hkl[0:3])
                    Gw = n.dot(S,n.dot(U,Gc))
                    tth = tools.tth2(Gw,inp.param['wavelength'])
#                    print hkl[0:3],tth*180./n.pi
                    costth = n.cos(tth)
                    (Omega, Eta) = tools.find_omega_general(inp.param['wavelength']/(4.*n.pi)*Gw,
                                                            tth,
                                                            inp.values['wx']*n.pi/180,
                                                            inp.values['wy']*n.pi/180)  
                    if len(Omega) > 0:
                        for solution in range(len(Omega)):
                            omega = Omega[solution]
                            eta = Eta[solution]
                            for i in range(len(inp.fit['w_limit'])/2):
                                if  (inp.fit['w_limit'][2*i]*n.pi/180) < omega and\
                                    omega < (inp.fit['w_limit'][2*i+1]*n.pi/180):
                                # form Omega rotation matrix
                                    Om = tools.form_omega_mat_general(omega,inp.values['wx']*n.pi/180,inp.values['wy']*n.pi/180)  
                                    Gt = n.dot(Om,Gw) 
                                # Calc crystal position at present omega
                                    [tx,ty,tz]= n.dot(Om,gr_pos)
                                # Calc detector coordinate for peak 
                                    (dety, detz) = detector.det_coor(Gt,costth,
                                                                    inp.param['wavelength'],
                                                                    inp.param['distance'],
                                                                    inp.param['y_size'],
                                                                    inp.param['z_size'],
                                                                    inp.param['y_center'],
                                                                    inp.param['z_center'],
                                                                    R,tx,ty,tz)
                            #If peak within detector frame store it in possible
                                    if (-0.5 < dety) and\
                                        (dety < inp.fit['dety_size']-0.5) and\
                                        (-0.5 < detz) and\
                                        (detz < inp.fit['detz_size']-0.5):
                                        inp.possible[grainno].append([hkl[0],
                                                                      hkl[1],
                                                                      hkl[2],
                                                                      omega*180/n.pi,
                                                                      dety,
                                                                      detz,
                                                                      tth,
                                                                      eta])
                                            

def match(inp):
        """
        Match up inp.possible containing the possible reflections from find_refl
        with the actual spots listed in inp.omega, inp.dety and inp.detz
        Create inp.id, inp.h, inp.k, inp.l and inp.nrefl to be used in FCN
        and inp.F2vol to be used for intensity based outlier rejection
        """
        
        inp.id = []
        inp.h = []
        inp.k = []
        inp.l = []
        inp.nrefl = []
        inp.tth = [0]*inp.param['total_refl']
        inp.eta = [0]*inp.param['total_refl']
        inp.F2vol = [0]*inp.param['total_refl']
        
#        w_tol = inp.fit['w_step']*2
#        dety_tol = 100 # +-100micronc
#        detz_tol = 5  # +-25 microns
        
        for i in range(inp.no_grains):
            inp.id.append([])
            inp.h.append([])
            inp.k.append([])
            inp.l.append([])
            for m in range(len(inp.possible[i])):
#                print inp.possible[i][m]
                w_tol = 0
                dety_tol = 0
                detz_tol = 0
                matches = 0
                
                cycles = int(round(inp.fit['tol_fw_proj']))
                for k in range(cycles):
                    if matches > 0:
                        break
                    else:
                        w_tol = w_tol + inp.fit['w_step']
                        dety_tol = dety_tol + 4
                        detz_tol = detz_tol + 3
                        for j in range(inp.param['total_refl']):
                            if abs(inp.possible[i][m][3]-inp.w[j]) < w_tol and \
                                abs(inp.possible[i][m][4]-inp.dety[j]) < dety_tol and \
                                abs(inp.possible[i][m][5]-inp.detz[j]) < detz_tol:
                                matches = matches + 1
                                inp.id[i].append(j)
                                inp.h[i].append(inp.possible[i][m][0])
                                inp.k[i].append(inp.possible[i][m][1])
                                inp.l[i].append(inp.possible[i][m][2])
                                inp.tth[j] = inp.possible[i][m][6]*180./n.pi #NB! was radians, now degrees
                                inp.eta[j] = inp.possible[i][m][7]*180./n.pi #NB! was radians, now degrees
                                
                                rho = n.pi/2.0 + inp.eta[j]*n.pi/180.0 + inp.fit['beampol_direct']*n.pi/180.0 
                                P = 0.5 * (1. + n.cos(inp.tth[j]*n.pi/180.0)**2 + inp.fit['beampol_factor']*n.cos(2*rho)*n.sin(inp.tth[j]*n.pi/180.0)**2)
                                Linv = (n.sin(inp.tth[j]*n.pi/180.0)*abs(n.sin(inp.eta[j]*n.pi/180.0)))
                                inp.F2vol[j] = inp.int[j]*Linv/P

                                
            inp.nrefl.append(len(inp.id[i]))            
            print('grain', i+1, 'possible', len(inp.possible[i]),'actual', inp.nrefl[i])
                       
                       
                       
