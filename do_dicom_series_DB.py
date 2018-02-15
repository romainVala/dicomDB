#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 11:00:43 2012

@author: romain
"""
import common as c, do_common
#from Exam_info import Exam_info 
import Exam_info 
import Cenir_DB
import os
import sys
import pdb
if __name__ == '__main__':
    
    doit = do_common.doit()
    log = doit.get_log()        
    
    options = doit.get_option('import_dicom')
    
    try :
        ###choose the input directories
        is_series_dir=False
        
        if options.sql_doublon:
            CDB = Cenir_DB.Cenir_DB(log=log,opt=options)
            #CDB.remove_duplicate_exam()
            CDB.find_sql_doublon()
            
            sys.exit()
    
        if options.nb_days:
            in_dir= c.get_all_newer_subdir(options.rootdir,1,nbdays=options.nb_days)
        elif options.from_logfile :
            import datetime as da
    
            today = da.datetime.today()    
            logtime =  da.datetime.fromtimestamp(os.path.getmtime("/servernas/nasDicom/log_update_db.log"))
            nbdays = today - logtime;
            nbdays = nbdays.days + 1
            
           
            log.info("\n ********************************\n Searching exam older than %s days \n",(nbdays))
            in_dir= c.get_all_newer_subdir(options.rootdir,1,nbdays=nbdays)
        elif len(options.input_dir)>0:
            in_dir= c.get_all_recursif_dir(options.input_dir)
            is_series_dir=True
            
        else:
            if len(options.ser_reg)>0:
                is_series_dir=True
                in_dir= c.get_subdir_regex(options.rootdir,[options.proto_reg,options.suj_reg,options.ser_reg])
            else:
                in_dir= c.get_subdir_regex(options.rootdir,[options.proto_reg,options.suj_reg])
    
       
        
        E = Exam_info.Exam_info(log=log,nifti_dir=options.nifti_dir,dicom_ext = options.dicom_ext,dicom_dir=options.rootdir,
                      send_mail = options.send_mail,send_mail_file = options.send_mail_file , smtp_pwd = options.smtp_pwd,
                      skip_derived_series = options.skip_derived)
                      
        CDB = Cenir_DB.Cenir_DB(log=log,opt=options)
    
        #tri dicom if ask
        if options.tri_dicom:
            in_dir= E.tri_dicom_dir(in_dir,verbose=False,mv_file=options.mv_file,tri_move=options.tri_move)
        
        #read dicom files
        for onedir in in_dir :
            Ei = E.get_exam_information(onedir,convert_to_nii=options.convert_to_nii,is_dir_level_series=is_series_dir)
        
            if options.find_double :
                E.find_double_exam(Ei)
            
            test=False

            if options.test_db :
                log.info("\n\n**************************\nChecking CENIR data base change on the selected exams (but no change)\n")
                test=True
                
            if options.do_db :
                log.info("\nPERFORMING Database update\n")
                CDB.update_exam_sql_db(Ei,test=test,do_only_insert=options.do_only_insert) 
            if options.do_db_gg :
                log.info("\nPERFORMING GG Database update\n")
                CDB.update_exam_sql_db_gg(Ei,test=test,do_only_insert=options.do_only_insert) 
            

        log.info('done so enjoy')
        
    except Exception as e :
        #raise
        doit.handel_main_exception(e)
            
                

'''
test the tri_dicom memory
import common as c
in_dir= c.get_subdir_regex('/nasDicom/dicom_raw/PROTO_MEMOEPI',['^2013_12','MBB3_ep2d_TR1730_2iso'])
#in_dir= c.get_all_recursif_dir(options.input_dir)

import os
import psutil
p = psutil.Process(os.getpid())

import Exam_info 
import dcmstack
E = Exam_info.Exam_info()
group_keys =  ('SeriesInstanceUID','SeriesNumber','ProtocolName')
allpg=[]

for dir_path in in_dir :
    alldic,nb_of_dic_file = E.get_all_dicom_file(dir_path,verbose=True)
    print 'reading %d files' % (len(alldic))
    print 'MEM2 %0.0f M '%(p.get_memory_info().rss/1024/1024)
    pg,dicom_file_size,n_ommited  = E.get_group_stack_from_dic(alldic,group_keys=group_keys)
    #allpg.append(pg)



'''
