#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 11:00:43 2012

@author: romain
"""
import common as c
import Exam_info 
import os
import logging
import sys
import numpy as np
import dcmstack

def convert_str_to_boolean(dd):
    for k,v in dd.items():
        if v == 'False':
            dd[k] = False
        elif v == 'True':
            dd[k] = True
    
    return dd

def get_data_from_dicom(alldic,Ei):
    
    #Ei = Exam_info.Exam_info()
    mf =dcmstack.make_key_regex_filter(['nothingtoremove'])
    pg,dicom_file_size,n_ommited  = Ei.get_group_stack_from_dic(alldic)

    all_stack=[]
    dicom_ok=True
            
    for v in pg.values():
        my_stack = dcmstack.DicomStack(meta_filter=mf,time_order='InstanceNumber')
        n_ommited=0
        n_repeat=0
        
        for vol in v: #vol[0] champs de pydicom vol[1] ordererd dict
            try:
                my_stack.add_dcm(vol[0],meta=vol[1])
            except dcmstack.IncongruentImageError :
                n_ommited += 1
                dicom_ok=False
            except dcmstack.ImageCollisionError:
                n_repeat += 1
                dicom_ok=False
            except Exception as e: 
                log.info("oups dic %s because expection"%(vol[2]))
                print( e )
                n_ommited +=1
                dicom_ok=False
            
#                dicom_file_size += os.path.getsize(vol[2])
        if n_repeat>0:
            log.info("Found %d duplicate dicom file",n_repeat)
        if n_ommited>0:
            log.info("Found %d stack incongruent dicom file",n_ommited)
            
        try:
            all_stack.append(my_stack.to_nifti(voxel_order='LAS', embed_meta=True))
        
        except (dcmstack.InvalidStackError, dcmstack.IncongruentImageError) as detail:
            log.info( "INVALIDE STACK  because %s ",detail)
            dicom_ok=False
        except Exception: 
            log.info( "STACK error" )
            dicom_ok=False
            
            

    alldata = []
    
    for nii in all_stack:
        data=nii.get_data()
        alldata.append(data)                 
        
    return alldata,dicom_ok
    
    
def configfile(options_dict,conffile,confsection):
    import ConfigParser
        
    config = ConfigParser.RawConfigParser()
    config.read(conffile)
    if not config.has_section(confsection):
        config.add_section(confsection)
    #    config = ConfigParser.RawConfigParser()

    for k,v in options_dict.items():
        config.set(confsection,k,str(v))
    with open(conffile, 'wb') as cf:
        config.write(cf)
        
if __name__ == '__main__':

    log = logging.getLogger('Do_dicom_serie')

    formatter = logging.Formatter("%(asctime)-2s: %(levelname)-2s : %(message)s")
    if not len(log.handlers):
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(formatter)
        log.addHandler(console)
    
    log.setLevel(logging.INFO)
    
    from optparse import OptionParser
    usage= "usage: %prog [options] select dir of dicom exam with the option and insert them into cenir SDB (exam) "

    # Parse input arguments
    parser=OptionParser(usage=usage)
    #parser.add_option("-h", "--help", action="help")
    parser.add_option("-r","--recupdir", action="store", dest="recupdir", default=None,
                      help="full path to the root directorie dicom files default current dir")

    parser.add_option("-l","--logfile", action="store", dest="logfile", default='',
                      help="full path to the log file default=''")
    parser.add_option("--write_conf_to_section", action ="store",dest="write_conf_to_section",
                              help="specify the name of the section where to write the param")
        
    
    (options, args) = parser.parse_args()

    recup_dir = options.recupdir
    if recup_dir is None:
        recup_dir = os.getcwd
    #dicom_dir0 = '/nasDicom/dicom_raw/'
    dicom_dir = '/network/lustre/iss01/cenir/raw/irm/dicom_raw'

    if len(options.logfile)==0:
        options.logfile = os.path.join(recup_dir,'log_compare_recup')

    if len(options.logfile)>0:        
#        if not len(log.handlers):
        fhdl = logging.FileHandler(filename = options.logfile,mode='a')
        fhdl.setFormatter(formatter)
        log.addHandler(fhdl)
        log.setLevel(logging.INFO)
            

    ###
    workdir = os.getcwd()
    fmove = open(os.path.join(workdir,'move_missing.sh'),'w+')
    fmovesql = open(os.path.join(workdir,'sql_missing.sh'),'w+')
    fmovecorupt   = open(os.path.join(workdir,'delete_corrupt.sh'),'w+')
    fmoverecup    = open(os.path.join(workdir,'delete_recup.sh'),'w+')
    
    in_dir= c.get_subdir_regex(recup_dir,['.*','.*'])
    
    for sujrecup in in_dir:        
        pp,suj = os.path.split(sujrecup)
        pp,proto = os.path.split(pp)

        log.info('looking at %s',suj)
        
        sujdic = c.get_subdir_regex(dicom_dir,[proto,'^'+ suj+'$'])
        
        if len(sujdic)==0:
            log.info('Missing Subject %s/%s ',proto,suj)
            #fmove.write('cp -r %s %s;\n'%(sujrecup,os.path.join(dicom_dir0,proto,suj)))
            #fmove.write('   chmod 755 %s \n'%(os.path.join(dicom_dir0,proto,suj)))
            #fmove.write('   chmod 755 %s/* \n'%(os.path.join(dicom_dir0,proto,suj)))
            #fmove.write('   chmod 644 %s/*/* \n'%(os.path.join(dicom_dir0,proto,suj)))
            fmove.write('mv %s %s;\n'%(sujrecup,os.path.join(dicom_dir,proto,suj)))
            fmove.write('   chmod 755 %s \n'%(os.path.join(dicom_dir,proto,suj)))
            fmove.write('   chmod 755 %s/* \n'%(os.path.join(dicom_dir,proto,suj)))
            fmove.write('   chmod 644 %s/*/* \n'%(os.path.join(dicom_dir,proto,suj)))
            fmovesql.write('do_dicom_series_DB -c import_db --input_dir=%s\n'%(os.path.join(dicom_dir,proto,suj)))
            
        else:
            in_recup_ser = c.get_subdir_regex(sujrecup,'.*')
            
            for serrecup in in_recup_ser:
                pp,ser = os.path.split(serrecup)                
                
                if ser.endswith('_again') :
                    continue
                
                serdic = c.get_subdir_regex(sujdic[0],'^'+ ser +'$')
                
                if len(serdic) == 0 :                    
                    log.info('Missing Serie %s/%s',sujdic[0],ser)
                    #fmove.write('cp -r %s %s/;\n'%(serrecup,os.path.join(dicom_dir0,proto,suj)))
                    #fmove.write('   chmod 755 %s \n'%(os.path.join(dicom_dir0,proto,suj)))
                    #fmove.write('   chmod 755 %s/* \n'%(os.path.join(dicom_dir0,proto,suj)))
                    #fmove.write('   chmod 644 %s/*/* \n'%(os.path.join(dicom_dir0,proto,suj)))

                    fmove.write('mv %s %s \n'%(serrecup,os.path.join(sujdic[0],ser)))
                    fmove.write('   chmod 755 %s \n'%(os.path.join(sujdic[0],ser)))
                    fmove.write('   chmod 644 %s/* \n'%(os.path.join(sujdic[0],ser)))
                    fmovesql.write('do_dicom_series_DB -c import_db --input_dir=%s\n'%(os.path.join(sujdic[0],ser)))

                else:
                    Ei = Exam_info.Exam_info(log=log)

                    ffd,ttt = Ei.get_all_dicom_file(serdic[0])      #c.get_subdir_regex_files(serdic,'.*dic$')
                    ffr,ttt = Ei.get_all_dicom_file(serrecup)    #c.get_subdir_regex_files(serrecup,'.*dic$')
                    
                    if len(ffr) != len(ffd):
                        
                        if len(ffr)>len(ffd):
                            log.info('OK MISSING files in dicom\n    %d | %d  (recup | dicom) Serie %s/%s/%s wrong Number\n so remove dicom',len(ffr),len(ffd),proto,suj,ser)                            
                            fmove.write('rm -rf %s\n'%serdic[0])
                            #fmove.write('rm -rf %s\n'%os.path.join(dicom_dir0,proto,suj,ser))
                            #fmove.write('cp -r %s %s/;\n'%(serrecup,os.path.join(dicom_dir0,proto,suj)))
                            #fmove.write('   chmod 755 %s \n'%(os.path.join(dicom_dir0,proto,suj)))
                            #fmove.write('   chmod 755 %s/* \n'%(os.path.join(dicom_dir0,proto,suj)))
                            #fmove.write('   chmod 644 %s/*/* \n'%(os.path.join(dicom_dir0,proto,suj)))

                            fmove.write('   mv %s %s \n'%(serrecup,os.path.join(sujdic[0],ser)))
                            fmove.write('   chmod 755 %s \n'%(os.path.join(sujdic[0],ser)))
                            fmove.write('   chmod 644 %s/* \n'%(os.path.join(sujdic[0],ser)))
                            fmovesql.write('do_dicom_series_DB -c import_db --input_dir=%s\n'%(os.path.join(sujdic[0],ser)))
                            
                        else :
                            log.info('WARNING less files in recup\n    %d | %d  (recup | dicom) Serie %s/%s/%s wrong Number\n so remove recup',len(ffr),len(ffd),proto,suj,ser)
                            fmoverecup.write('rm -rf %s\n'%serrecup)
                    else:
                        datar,dicok_r = get_data_from_dicom(ffr,Ei)
                        datad,dicok_d = get_data_from_dicom(ffd,Ei)
                        different='Identical'
                        
                        if dicok_r is False:
                            log.info('WARNING Recup data has wrong volumic data')
                            dicsizer=0
                            for f in ffr:
                                dicsizer+=os.path.getsize(f)
                                
                            dicsized=0
                            for f in ffd:
                                dicsized+=os.path.getsize(f)
                            if   dicsizer==dicsized :
                                log.info('BUT same size of dicom files so remove recup')
                                fmoverecup.write('rm -rf %s\n'%serrecup)
                            else:
                                log.info('DOUBLE WARNING Different dicom size recup %d dicom %d',dicsizer,dicsized)
                                
                        else :
                            for nbd in range(len(datar)):
                                s1 = datar[nbd].shape
                                s2 = datad[nbd].shape
                                if np.equal(s1,s2).all():
                                    if ~ np.equal(datar[nbd],datad[nbd]).all() :
                                        different='different (content)'
                                        break
                                else:
                                    different='different (size)'
                                    break
                            
                            log.info( '%s data for %s ',different,os.path.join(proto,suj,ser))
                            
                            if different != 'Identical':
                                fmovecorupt.write('rm -rf %s\n'%serdic[0])
                                #fmovecorupt.write('rm -rf %s\n'%os.path.join(dicom_dir0,proto,suj,ser))
                                #fmovecorupt.write('cp -r %s %s/;\n'%(serrecup,os.path.join(dicom_dir0,proto,suj)))
                                #fmovecorupt.write('   chmod 755 %s \n'%(os.path.join(dicom_dir0,proto,suj)))
                                #fmovecorupt.write('   chmod 755 %s/* \n'%(os.path.join(dicom_dir0,proto,suj)))
                                #fmovecorupt.write('   chmod 644 %s/*/* \n'%(os.path.join(dicom_dir0,proto,suj)))

                                fmovecorupt.write('   mv %s %s \n'%(serrecup,os.path.join(sujdic[0],ser)))
                                fmovecorupt.write('   chmod 755 %s \n'%(os.path.join(sujdic[0],ser)))
                                fmovecorupt.write('   chmod 644 %s/* \n'%(os.path.join(sujdic[0],ser)))
                            
                            else :
                                fmoverecup.write('rm -rf %s\n'%serrecup)
    
    fmove.close()    
    fmovecorupt.close()
    fmoverecup.close()
    fmovesql.close()
                        
                        
                    
