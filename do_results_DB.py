#! /usr/bin/env python
# -*- coding: utf-8 -*-

import common as c
import do_common, os 
#import re
import Cenir_DB
import sys

#pour le send dicom (check)
from netdicom.applicationentity import AE
from netdicom.SOPclass import *
from dicom.dataset import Dataset, FileDataset
from dicom.UID import ExplicitVRLittleEndian, ImplicitVRLittleEndian, ExplicitVRBigEndian
#import netdicom
import tempfile

from do_common import alpha_num_str
import glob

def add_options(parser):

    parser.add_option("--res_dir", action="store_true", dest="res_dir",default='/export/dataCENIR/dicom/nifti_proc/',
                                help="result rootdir default /export/dataCENIR/dicom/nifti_proc/")
    parser.add_option("--set_results", action="store_true", dest="set_results",default=False,
                                help="parse the serie database an set the results table ")

    #parser.add_option("-r","--rootdir", action="store", dest="rootdir", default='/servernas/nasDicom/dicom_raw',
    #                            help="full path to the root directorie dicom files (protocol dir) default='/nasDicom/dicom_raw'")
    parser.add_option("--check_send", action="store_true", dest="check_send",default=False,
                        help="Dicom query verio and prisma and compare to dicom dir ")
    parser.add_option("--patient_search", action="store", dest="patient_search", default='*',
                                help="define the string to search for patient in remote dicom server default='*'")
  
    parser.add_option("--create_tar", action="store_true", dest="create_tar",default=False,
                        help="create series directorie tar file in the dicom suj dir ")

    return parser
                                
# call back
def OnAssociateResponse(association):
    print "Association response received"


def OnAssociateRequest(association):
    print "Association resquested"
    return True

def OnReceiveStore(SOPClass, DS):
    print "Received C-STORE", DS.PatientName
    try:
        # do something with dataset. For instance, store it.
        file_meta = Dataset()
        file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'
        file_meta.MediaStorageSOPInstanceUID = "1.2.3"  # !! Need valid UID here
        file_meta.ImplementationClassUID = "1.2.3.4"  # !!! Need valid UIDs here
        filename = '%s/%s.dcm' % (tempfile.gettempdir(), DS.SOPInstanceUID)
        ds = FileDataset(filename, {}, file_meta=file_meta, preamble="\0" * 128)
        ds.update(DS)
        ds.save_as(filename)
        print "File %s written" % filename
    except:
        pass
    # must return appropriate status
    return SOPClass.Success
                                
class Results_DB:
    'Class to handel DataBase of results'    
    
    def __init__(self,verbose=True,log=0,opt=None):
        
        self.verbose = verbose
        
        self.log = log
        if opt is not None:
            self.db_name = opt.db_name
            self.db_host = opt.db_host
            self.res_dir = opt.res_dir
            self.opt = opt
            self.rootdir = opt.rootdir
            self.patient_search = opt.patient_search
    
    def set_results_DB(self):
        
        CDB = Cenir_DB.Cenir_DB(log=self.log,opt=self.opt)

        con,cur = CDB.open_sql_connection()
        cur2 = con.cursor()
        
        #sqlcmd="select Sid, ExamName, PatientsName, SName,SNumber,dicom_dir,dicom_sdir from ExamSerie where SeqType like 'MPRAGE';";
        sqlcmd="select Sid,nifti_dir from ExamSerie where SeqType like 'MPRAGE';";

        cur.execute(sqlcmd)
        rows = cur.fetchall()
        
        self.log.info('checking %d rows',len(rows))
        
        found=0
        res_list=[]

        for row in rows:
            if row['nifti_dir'] is None:
                log.info('Serie Sid %d has no nifti',row['Sid'])
            else:
                pp,ser = os.path.split(row['nifti_dir'])
                pp,suj = os.path.split(pp)
                pp,proto = os.path.split(pp)
                procdir = os.path.join(self.res_dir,proto,suj,ser,'vbm8')
                if os.path.isdir(procdir):                    
                    found+=1
                    res = {}                
                    res["Sid"] = row['Sid']
                    res['dir_path'] = procdir
                    
                    restext = c.get_subdir_regex_files(procdir,'.*seg8.txt')
                    if len(restext)==1:
                        res['status'] = 1
                        text_file = open(restext[0], "r")
                        # si plusieur tab text_list = re.split(r'\t+',line)
                        line = text_file.readline().split('\t')
                        if len(line)>3:
                            res['vbmgrayvol'] = line[0]
                            res['vbmwhitevol'] =line[1] 
                            res['vbmcsfvol'] = line[2]
                        else :
                            #self.log.info("corrupt seg8 files %s ",restext)
                            res['status'] = 0
                            
                        text_file.close()
                    else:
                        res['status'] = 0

                    res_list.append(res)
            
                else:
                    #print "mising " + procdir
                    pass
        
        self.log.info("found %d vbm dir",found)

        for  res in res_list:
            exist_line = CDB.get_sql_select_line('results_anat',"Sid",res["Sid"],cur)
            
            if len(exist_line)==0:
                sqlcmd = CDB.get_sql_insert_cmd_from_dict(res,'results_anat')
            
            else:
                sqlcmd = CDB.get_sql_update_cmd_from_dict(res,'results_anat','Sid',exist_line['Sid'])
                
            cur2.execute(sqlcmd)    
            con.commit()
    
        con.close()
        
        
    def set_results_DB_dicomdir_test(self):
        #il n'ent trouve que 6997 7142 soit 145 mauvaise dicomdir name
        CDB = Cenir_DB.Cenir_DB(log=self.log,opt=self.opt)

        con,cur = CDB.open_sql_connection()
        #sqlcmd="select Sid, ExamName, PatientsName, SName,SNumber,dicom_dir,dicom_sdir from ExamSerie where SeqType like 'MPRAGE';";
        sqlcmd="select Sid,dicom_dir,dicom_sdir from ExamSerie where SeqType like 'MPRAGE';";
        sqlcmd="select Sid,dicom_dir,dicom_sdir from ExamSerie where SeqType like 'MPRAGE';";

        cur.execute(sqlcmd)
        rows = cur.fetchall()
        self.log.info('checking %d rows',len(rows))
        
        found=0
        
        for row in rows:
            pp,suj = os.path.split(row['dicom_dir'])
            pp,proto = os.path.split(pp)
            procdir = os.path.join(self.res_dir,proto,suj,row['dicom_sdir'],'vbm8')
            if os.path.isdir(procdir):
                found+=1
                
            else:
                #print "mising " + procdir
                pass
                    
        self.log.info("found %d vbm dir",found)

    def get_exam_suj_ser_from_dicom_dataset(self,ds):
        #identical to get_exam_suj_ser_from_dicom_meta in Exam_info just from an other input
#        (se.StudyDescription, se.StudyDate, se.PatientName, se.SeriesNumber, se.SeriesDescription)
        
#        if "StudyDescription" not in meta : #Service patient on prisma has none
#            exa = "ServicePatient"
#            str_date = str(meta["AcquisitionDate"])
#            str_date = str_date[0:4]+'_'+str_date[4:6] + '_' + str_date[6:8] 
#            suj = str_date + '_' + alpha_num_str(meta["PatientName"])            
#            ser = 'S%02d' % meta.get('SeriesNumber')
#            return(exa,suj,ser)
#        else:
#            exa = alpha_num_str(meta["StudyDescription"]) 
        exa = alpha_num_str(ds.StudyDescription)
        #exa = alpha_num_str(ds.AcquisitionDate)
        
#        study_date = str(meta["StudyDate"])
#        study_date = study_date[0:4]+'_'+study_date[4:6] + '_' + study_date[6:8]
#
#        if "AcquisitionDate" not in meta : 
#            str_date = study_date
#        else:
#            str_date = str(meta["AcquisitionDate"])
#            str_date = str_date[0:4]+'_'+str_date[4:6] + '_' + str_date[6:8] 
#        
#            #dicom bug only for DTI tensor : AcquisitionDate is bad and anterior
#            if study_date > str_date : 
#                str_date = study_date
        str_date = ds.StudyDate
        str_date = str_date[0:4]+'_'+str_date[4:6] + '_' + str_date[6:8] 
        
        #suj = str_date + '_' + alpha_num_str(meta["PatientName"])
        suj = str_date + '_' + alpha_num_str(ds.PatientName)
        
        exaid = ds.StudyID
        if len(exaid)>1 : #Service patient has strange Eid
            suj += '_E' + exaid
        elif int(exaid)>1:
            suj += '_E' + exaid

#        if len(ds.SeriesDescription==0):
#            ser = 'S%02d' % ds.SeriesNumber + '_' 
#        else:
        ser = 'S%02d' % ds.SeriesNumber + '_' + alpha_num_str(ds.SeriesDescription)
        
        return(exa,suj,ser)

    def get_exam_suj_ser_from_dicom_dataset_new(self,ds):

        exa = alpha_num_str(ds.StudyDescription)
        str_date = ds.StudyDate
        
        str_date = ds.SeriesDate
        
        str_date = str_date[0:4]+'_'+str_date[4:6] + '_' + str_date[6:8] 
        
        suj = str_date + '_' + alpha_num_str(ds.PatientName)
        
        exaid = ds.StudyID
        if len(exaid)>1 : #Service patient has strange Eid
            suj += '_E' + exaid
        elif int(exaid)>1:
            suj += '_E' + exaid

        ser = 'S%02d' % ds.SeriesNumber + '_' + alpha_num_str(ds.SeriesDescription)

#        d = Dataset()
#        d.PatientID = ""
#        d.StudyInstanceUID = ds.StudyInstanceUID
#        d.QueryRetrieveLevel = "IMAGE"; #"INSTANCE"
#        d.SeriesInstanceUID=ds.SeriesInstanceUID
#        d.ImageType=""
#        
#        img = [x[1] for x in assoc.PatientRootFindSOPClass.SCU(d, 1)][:-1]
#        
#        toto
        
        return(exa,suj,ser)
 
    def check_send_dicom_from_remoteAE(self,assoc):
        d = Dataset()
        d.PatientsName = self.patient_search
        d.QueryRetrieveLevel = "PATIENT"
        d.PatientID = "*"
        patients = [x[1] for x in assoc.PatientRootFindSOPClass.SCU(d, 1)][:-1]
        
        
        self.log.info("Checking %d Exams ",len(patients))
        
        # loop on patients
        for pp in patients:
            if pp.PatientName=="Service Patient":
                print "skiping Service Patient"
                continue
        
            #self.log.info("Checking %s ",pp.PatientName)
            # find studies
            d = Dataset()
            d.PatientID = pp.PatientID
            d.QueryRetrieveLevel = "STUDY"
            d.PatientName = ""
            d.StudyInstanceUID = ""
            d.StudyDate = ""
            d.StudyTime = ""
            d.StudyID = ""
            d.ModalitiesInStudy = ""
            d.StudyDescription = ""
            d.NumberOfStudyRelatedInstances=""
            studies = [x[1] for x in assoc.PatientRootFindSOPClass.SCU(d, 1)][:-1]
            
            # loop on studies
            for st in studies:
                #print "    %s - %s %s ||| %s " % (st.StudyDescription, st.StudyDate, st.StudyTime,st.NumberOfStudyRelatedInstances)
                d = Dataset()
                d.QueryRetrieveLevel = "SERIES"
                d.StudyInstanceUID = st.StudyInstanceUID
                d.PatientID = "" # st.PatientID #rrr
                d.StudyDescription = ""
                d.StudyDate = ""
                d.PatientName = ""
                d.StudyID = ""
                d.AcquisitionDate = ""
                
                d.SeriesInstanceUID = ""
                d.InstanceNumber = ""
                d.Modality = ""
                d.SeriesNumber = ""
                d.SeriesDescription = ""
                d.SeriesDate = ""
                d.SeriesTime = ""
                d.SeriesID = ""
                d.NumberOfSeriesRelatedInstances = ""
                series = [x[1] for x in assoc.PatientRootFindSOPClass.SCU(d, 1)][:-1]
                
                # print series uid and number of instances
                for se in series:
                    if se.NumberOfSeriesRelatedInstances==0 : 
                        log.info('Empyt Serie in %s_%s',se.StudyDescription,se.PatientName)
                    else:
                        (exa,suj,ser) = self.get_exam_suj_ser_from_dicom_dataset(se)
                        dic_dir = os.path.join(self.rootdir,exa,suj,ser)                        
                        if not os.path.isdir(dic_dir):
                            dic_dir+='_phase'
                            if not os.path.isdir(dic_dir):
                                (exa,suj,ser) = self.get_exam_suj_ser_from_dicom_dataset_new(se)
                                dic_dir = os.path.join(self.rootdir,exa,suj,ser)
                                if not os.path.isdir(dic_dir):
                                    # i can not ask image instance level so do not kwon about IMAGETYPE so I check i _phase exist
                                    dic_dir_p = os.path.join(self.rootdir,exa,suj,ser+'_phase')
                                    if os.path.isdir(dic_dir_p):
                                        dic_dir=dic_dir_p
                        
                        if os.path.isdir(dic_dir) :
                            nbdic = glob.glob(os.path.join(dic_dir,"*dic"))
                            #print "nbd %d  nbi %s" %(len(nbdic),se.NumberOfSeriesRelatedInstances)
                            if len(nbdic) !=  se.NumberOfSeriesRelatedInstances:
                                self.log.warning(" MISSING DICOMS found %d instead of %s in %s",len(nbdic),se.NumberOfSeriesRelatedInstances,dic_dir)
                        else :
                            self.log.warning(" MISSING SERIES : %s",dic_dir)
        
                    #print "        %5s - %10s - %35s - %5s" % (se.SeriesNumber, se.Modality, se.SeriesDescription, se.NumberOfSeriesRelatedInstances)
                    #print "%s | %s |%s | %s | %s" % (se.StudyDescription, se.StudyDate, se.PatientName, se.SeriesNumber, se.SeriesDescription)
                    #print "%s | %s | %s" %(exa,suj,ser)
                   # print "%s | %s | %s | %s" % (se.StudyDescription,  se.PatientName, se.SeriesNumber, se.SeriesDescription)

    def check_send_dicom(self):
        
        ts = [ ExplicitVRLittleEndian, ImplicitVRLittleEndian, ExplicitVRBigEndian ]

            
        # create application entity with Find and Move SOP classes as SCU and
        # Storage SOP class as SCP
        MyAE = AE("DCMTK",9999, [PatientRootFindSOPClass, PatientRootMoveSOPClass, VerificationSOPClass], [StorageSOPClass], ts)
        MyAE.OnAssociateResponse = OnAssociateResponse
        MyAE.OnAssociateRequest = OnAssociateRequest
        MyAE.OnReceiveStore = OnReceiveStore
        MyAE.start()
        
        
        # remote application entity
        PrismaAE = dict(Address="134.157.205.1", Port=104, AET="AN_MRC35181")
        
        # create association with remote AE
        self.log.info("Request association on PRISMA")
        
        assoc = MyAE.RequestAssociation(PrismaAE)
       
       # perform a DICOM ECHO
        st = assoc.VerificationSOPClass.SCU(1)
        self.log.info('DICOM Echo done with status "%s"', st)
        
        try :
            self.check_send_dicom_from_remoteAE(assoc)
        except Exception as e:
            self.log.warning('CODE ERROR because of %s',e)
        
        assoc.Release(0)

        # AGAIN with VERIO
        VerioAE = dict(Address="134.157.205.51", Port=104, AET="MRC40527")
        
        # create association with remote AE
        self.log.info("Request association on VERIO")
        
        assoc = MyAE.RequestAssociation(VerioAE)
       
       # perform a DICOM ECHO
        st = assoc.VerificationSOPClass.SCU(1)
        self.log.info('DICOM Echo done with status "%s"', st)
        
        #try :
        self.check_send_dicom_from_remoteAE(assoc)
        #except Exception as e:
        #    self.log.warning('CODE ERROR because of %s',e)
        
        assoc.Release(0)
        
        
        MyAE.Quit()
        
    def create_dicom_tar(self,in_dir):
        
        for suj in in_dir:
            ser_dir= c.get_subdir_regex(suj,'.*')
            cmde = 'cd ' + suj
            for ser in ser_dir:
                commandline = cmde  + '; tar -czf ' + ser + '.tar.gz'
                print commandline
                
#            try:
#                outvalue=call(commandline)
#            except OSError:
#                print " XX ERROR: unable to find executable "+commandline[0]
#                return -1
#
        
if __name__ == '__main__':
    
    doit = do_common.doit()
    log = doit.get_log()        
    
    options = doit.get_option('results_db')
      
    RES = Results_DB(log=log,opt=options)

    if options.check_send:
        RES.check_send_dicom()
        sys.exit()

    if options.create_tar:
        in_dir= c.get_subdir_regex(options.rootdir,[options.proto_reg,options.suj_reg])
    
        RES.create_dicom_tar(in_dir)
        sys.exit()
        
    if options.set_results:   
        RES.set_results_DB()
        