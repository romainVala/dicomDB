
import common as c
import numpy as np
import os,math,dicom,datetime,time
import dcmstack
#from nibabel.spatialimages import HeaderDataError
from dcmstack import extract , NiftiWrapper
#import warnings
from glob import glob
from do_common import alpha_num_str
import pdb
class Exam_info:
    'Class to collected dicom information from dicom dirs'    
    
    def __init__(self,verbose=True,log=0,
                 nifti_dir='/network/lustre/iss01/cenir/raw/irm/nifti_raw/',
                 dicom_dir = '/export/home/romain.valabregue/dicom_raw',
                 dicom_ext = '*.dic', send_mail = False,send_mail_file= '',
                 smtp_pwd= '',skip_derived_series=True):
                  
        self.verbose = verbose
        self.nifti_dir = nifti_dir
        self.dicom_dir = dicom_dir
        self.dicom_ext = dicom_ext
        self.send_mail = send_mail
        self.send_mail_file = send_mail_file
        self.skip_derived_series = skip_derived_series
        self.smtp_pwd = smtp_pwd
        
        if dicom_dir[-1]=='/':
            dicom_dir = dicom_dir[:-1]
            
        #self.dicom_doublon = os.path.join(os.path.dirname(dicom_dir),'recup')
        self.dicom_doublon = os.path.join(dicom_dir,'doublon')
        
        self.log = log
 
        #self.log.info('UUUUUUU %s  %s', self.dicom_doublon,self.dicom_dir)


    def get_exam_information(self,in_dir,convert_to_nii=False,is_dir_level_series=False):
        dicinfo=[]
        
        if type(in_dir) is not list:
            in_dir = [in_dir]
        
        if self.verbose:
            self.log.info("Searching exam info in %d dirs : %s \n",len(in_dir),in_dir)    
        
        for adir in in_dir :        
            if is_dir_level_series : #if --input_dir is use
                if adir[-1]=='/':
                    adir=adir[:-1]
                series_dir = [adir]
                adir = os.path.dirname(adir)
            else:                
                series_dir = c.get_subdir_regex(adir,'^S')
                
            if len(series_dir)==0:
                msg = "REMOVE : %s has no series dir"%(adir)
                self.log.warning(msg)
                continue
            
            self.log.info('nbser %d',len(series_dir))
            
            series_list = self.separate_exam_series(series_dir)
            
            for nbexam in range(len(series_list)):
        
                series_dir = series_list[nbexam]
                dicinfo_serie=[]
                for oneserie in series_dir:
                    all_file,ttt = self.get_all_dicom_file(oneserie)
                    dic = self.get_dicom_serie_info(all_file,convert_to_nii)                
                    dicinfo_serie.append(dic)
                    
                fdicinfo = dicinfo_serie[0]
                if "_first_file" in fdicinfo :
                    first_file = fdicinfo["_first_file"]
                else :
                    raise Exception('should_no_happend')
                    first_file = self.get_first_dicom_file(series_dir[0],1)

                fdicinfo = dicinfo_serie[-1]
                if "_last_file" in fdicinfo :
                    last_file = fdicinfo["_last_file"]
                else :
                    raise Exception('should_no_happend')
                    self.log.warning("last file from alphabetic order for ser %s",fdicinfo["SName"])
                    last_dir = series_dir[-1]
                    last_file = self.get_last_dicom_file(last_dir)
                                                                
        
                dic = self.get_dicom_exam_info(first_file,last_file,dicinfo_serie)
                dic["dicom_dir"] = adir
                dic["serie_info"] = dicinfo_serie
                dicinfo.append(dic)        
        
                if self.verbose:
                    self.log.info("%s \tdate: %s  \tdur : %d \t first %s \t last: %s ",dic["PatientsName"],dic["AcquisitionTime"],\
                    dic["ExamDuration"],dic["FirstSerieName"],dic["LastSerieName"])


        if self.verbose & False :
            da=[]
            du=[]
            for d in dicinfo:
                da.append(d["AcquisitionTime"].year)
                du.append(d["ExamDuration"])
            nda = np.array(da,np.int16)
            ndu = np.array(du,np.int16)
            [nu,ii,indu] = np.unique(nda,True,True)
            for k in range(ii.size):
                self.log.info("annee %d \t%d sujet\t%f heure",nda[ii[k]],len(ndu[indu==k]),np.sum(ndu[indu==k])/60.)
                
        
        
        return dicinfo
                 
         
  
    def get_dicom_exam_info(self,dic1,dic2,dicinfo_serie):
        """
        get the dicom exam information from the first file and compute the exam duration 
        as the diference between acquisition time of the second and first dicom file
        """
        
        dicinfo={}
    
        p1=dicom.read_file(dic1,stop_before_pixels=True)
        
        if 'StudyID' not in p1:
            dicinfo["ExamNum"] = 1
        else: 
            if p1.StudyID is '' :
                dicinfo["ExamNum"] = 1
            else:                       
                try:
		    dicinfo["ExamNum"] = int(p1.StudyID)
		except Exception as e:
		    dicinfo["ExamNum"] = p1.StudyID

        dicinfo["EUID"] = "%s" % (p1.StudyInstanceUID)  #hmm but make the job
        
        if 'ManufacturersModelName' not in p1:
            if 'Manufacturer' in p1:
                p1.ManufacturersModelName = p1.Manufacturer
	  
        dicinfo["MachineName"] = p1.ManufacturersModelName
	#pour les wip GE changement du machinename !                
        if "Ox Offline Recon" in dicinfo["MachineName"]:
            dicinfo["MachineName"]="SIGNA PET/MR"

        if 'GE MEDICAL SYSTEMS' in p1.Manufacturer:
            if 'ProtocolName' in p1 and len(p1.ProtocolName)>0 and p1.ProtocolName!= ' ':
                dicinfo["ExamName"]= alpha_num_str(p1.ProtocolName)
                dicinfo["StudyDescription"]= alpha_num_str(p1.ProtocolName)
            elif 'StudyDescription' in p1 and len(p1.StudyDescription)>0:
                dicinfo["ExamName"]= alpha_num_str(p1.StudyDescription)
                dicinfo["StudyDescription"]=alpha_num_str(p1.StudyDescription)
            else:                
                dicinfo["ExamName"]="Atrier"
        
        elif "StudyDescription" in p1:
            if len(p1.StudyDescription)>0:
                dicinfo["ExamName"] = alpha_num_str(p1.StudyDescription) 
                dicinfo["StudyDescription"]=alpha_num_str(p1.StudyDescription)
        
        dicinfo["PatientsName"] = alpha_num_str(p1.PatientsName)
        
        #appen date to SacisitionTime and format time
        if 'AcquisitionDate' in p1:
        	dstr = p1.AcquisitionDate
        else :
        	dstr = p1.StudyDate

	if 'AcquisitionTime' in p1:
		tstr = p1.AcquisitionTime
	else:
		tstr = p1.StudyTime

	#dicinfo["AcquisitionTime"] = dstr[0:4] + "-" + dstr[4:6] + "-" + dstr[6:] + " " + tstr[0:2] + ":" + tstr[2:4] + ":" + tstr[4:6]
        dicinfo["AcquisitionTime"] = datetime.datetime(int(dstr[0:4]),int(dstr[4:6]),int(dstr[6:]),int(tstr[0:2]),int(tstr[2:4]),int(tstr[4:6]))

        dstr = p1.StudyDate
        tstr = p1.StudyTime
        if len(tstr)==0: tstr = p1.AcquisitionTime
        dicinfo["StudyTime"] = datetime.datetime(int(dstr[0:4]),int(dstr[4:6]),int(dstr[6:]),int(tstr[0:2]),int(tstr[2:4]),int(tstr[4:6]))
        
        if dicinfo["AcquisitionTime"] < dicinfo["StudyTime"] : #bug for TENSOR series
           dicinfo["AcquisitionTime"] =  dicinfo["StudyTime"]
           if 'TENSOR' not in alpha_num_str(p1.SeriesDescription):
               self.log.warning('I thougth it was only for TENSOR ...check AcquisitionTime')               

        
        #sorte dicom series      
        nn = sorted(dicinfo_serie,key=lambda k: k["SNumber"])
        
        first_ser = nn[0]
        last_ser = nn[-1]
        
        if "Duration" in last_ser: 
            last_dur = last_ser["Duration"]
            if last_dur>0:
                dur= last_ser["AcqTime"] - first_ser["AcqTime"]
                dicinfo["ExamDuration"] = int(math.ceil((dur.seconds + last_dur)/60.))
            elif 'GE MEDICAL SYSTEMS' in p1.Manufacturer:
                dur= last_ser["AcqTime"] - first_ser["AcqTime"]
                dicinfo["ExamDuration"] = int(math.ceil((dur.seconds + last_dur)/60.))
            else:
                dur=0
                dicinfo["ExamDuration"] =0
        else:
            self.log.error("last serie %s has no duration set (duration old way)" ,last_ser['SName'])
            p2=dicom.read_file(dic2,stop_before_pixels=True)        
            if p2.has_key(0x051100a):
                dur = self.get_series_duration_from_siemens_tag(p2[0x051100a].value)    
            elif [0x19,0x105a] in p2:
                dur= p2[0x19,0x105a].value/1000000
            else:
                dur = self.get_series_duration_from_file(dic2)
            
            deltadur = get_second_from_time_str(p2.AcquisitionTime) - get_second_from_time_str(p1.AcquisitionTime)
            if int(p2.AcquisitionTime[0:2]) < int(p2.AcquisitionTime[0:2]) : #scan hour over midnight
                deltadur+=24*3600
    
            if deltadur<0:
                msg = "ERROR Negative acquisition time for %s compare to %s" % (os.path.dirname(dic2),os.path.basename(os.path.dirname(dic1) ))
                deltadur = math.fabs(deltadur)
                self.log.error(msg)

            dicinfo["ExamDuration"] = int(math.ceil((deltadur + dur)/60.))
        
        if 'PatientsWeight' in p1: dicinfo["PatientsWeight"] = int(p1.PatientsWeight)        
        dstr = p1.PatientsBirthDate
        if len(p1.PatientBirthDate)>0:
            dicinfo["PatientsBirthDate"] = datetime.date(int(dstr[0:4]) , int(dstr[4:6]), int(dstr[6:8]))
        
        if 'PatientsAge' not in p1:
            dicinfo["PatientsAge"] = "NULL"
        else:
            if len(p1.PatientsAge)>0:
                dicinfo["PatientsAge"] = int(p1.PatientsAge[0:3])
            
        if "PatientsBirthDate" not in dicinfo:
            dicinfo["PatientsBirthDate"]="NULL"
            
        if "PatientsSex" not in p1:
            p1.PatientsSex='Unknown'
        
        if len(p1.PatientsSex)>0:
            dicinfo["PatientsSex"] = p1.PatientsSex
        if "SoftwareVersions" in p1:
            dicinfo["SoftwareVersions"] = p1.SoftwareVersions
            if 'GE MEDICAL SYSTEMS' in p1.Manufacturer:
                dicinfo["SoftwareVersions"] = p1.SoftwareVersions[-1]
        
        dicinfo["LastSerieName"] = os.path.basename(os.path.dirname(dic2))
        dicinfo["FirstSerieName"] = os.path.basename(os.path.dirname(dic1))
        dicinfo["LastSerieDuration"] = dur
        
        if p1.ManufacturersModelName.startswith("Verio"):
            dicinfo["rid"] = 19        
    
        elif p1.ManufacturersModelName.startswith("TrioTim"):
            dicinfo["rid"] = 1
    
        elif p1.ManufacturersModelName.startswith("Prisma_fit"):
            dicinfo["rid"] = 1   
            
        elif "MachineName" in dicinfo and dicinfo["MachineName"].startswith("SIGNA"):
            dicinfo["rid"] = 29  
        elif "MachineName" in dicinfo and dicinfo["MachineName"].startswith("Bruker"):
            dicinfo["rid"] = 39

        else:
            #raise NameError('this Dicom file is not from TrioTim, Verio or Signa PETMR ')
            self.log.warning('this Dicom file is not from TrioTim, Verio or Signa PETMR ')
        
        if "StudyDescription" in dicinfo: 
            if dicinfo["StudyDescription"].startswith("PROTO_") or dicinfo["StudyDescription"].startswith("VERIO_"):
                dicinfo["eid"] = dicinfo["StudyDescription"][6:]
                dicinfo["facturable"]=1
            elif  dicinfo["StudyDescription"].startswith("PRISMA_") :
                dicinfo["eid"] = dicinfo["StudyDescription"][7:]
                dicinfo["facturable"]=1
            else:
                dicinfo["eid"] = dicinfo["StudyDescription"]
                dicinfo["facturable"]=0
          
        return dicinfo
        
    def deduce_other_info(self,dicinfo):
        
        if 'SeqName' not in dicinfo:
            dicinfo["SeqType"]='todo'
            return dicinfo

        seqname = dicinfo["SeqName"]
        if "SeqName2" in dicinfo:
            seqname2 = dicinfo["SeqName2"]
        else:
            seqname2=seqname
            
        if 'ep_b' in seqname: 
            dicinfo["SeqType"] = 'DWI'
        elif 'epfid' in seqname:
            dicinfo["SeqType"] = 'EPI'
        elif 'spc3d' in seqname:
            dicinfo["SeqType"] = 'SPACE3D'
        elif 'tfl3d' in seqname:
            if 'mp2rage' in seqname2:
                if 'INV1' in dicinfo["SName"]:
                    dicinfo["SeqType"] = 'MP2RAGE_INV1'
                elif 'INV2' in dicinfo["SName"]:
                    dicinfo["SeqType"] = 'MP2RAGE_INV2'
                elif 'T1_Images' in dicinfo["SName"]:
                    dicinfo["SeqType"] = 'MP2RAGE_T1MAP'
                elif 'UNI_Images' in dicinfo["SName"]:
                    dicinfo["SeqType"] = 'MP2RAGE_UNI'
                else:
                    dicinfo["SeqType"] = 'MP2RAGE_SHOULD_NOT_HAPPEN'
            else:
                dicinfo["SeqType"] = 'MPRAGE'
        
        elif 'fm2d2r' in seqname :
            dicinfo["SeqType"] = 'GreFieldMap'

        #GRE
        elif 'GR%SiemensSeq%gre_2D' in seqname2 : 
            dicinfo["SeqType"] = 'GRE_2D'

        elif 'GR%SiemensSeq%gre_3D' in seqname2 : 
            dicinfo["SeqType"] = 'GRE_3D'

        elif 'eja_svs' in seqname:
            dicinfo["SeqType"] = 'spectroSVS'
            
        else:
            if not "SeqType" in dicinfo :
                dicinfo["SeqType"] = 'to_be_defined'
        
            
        return dicinfo
        
    def get_dicom_serie_info(self,alldic,convert_to_nii=False):
        """
        extract series dicom info
        """
        
        self.log.info('Extracting info for %s',alldic[0])
        
        dicinfo={}
    
        dic1 = alldic[0]
        p1=dicom.read_file(dic1,stop_before_pixels=True)
    
        if len(p1.dir("AcquisitionDate"))==0:
            dstr = p1.StudyDate
            tstr = p1.StudyTime  #I do not know why the Acquisition Time is bad for series where AcquisitionDate missing    
            # well it seems not to be always the case
            if len(tstr)==0:
                tstr = p1.AcquisitionTime
        else:
            dstr = p1.AcquisitionDate
            tstr = p1.AcquisitionTime
            
        #dicinfo["AcquisitionTime"] = dstr[0:4] + "-" + dstr[4:6] + "-" + dstr[6:] + " " + tstr[0:2] + ":" + tstr[2:4] + ":" + tstr[4:6]
        dicinfo["AcqTime"] = datetime.datetime(int(dstr[0:4]),int(dstr[4:6]),int(dstr[6:]),int(tstr[0:2]),int(tstr[2:4]),int(tstr[4:6]))
        
        dstrs = p1.StudyDate
        tstrs = p1.StudyTime
        if len(tstrs)==0: tstrs = p1.AcquisitionTime

        dicStudyTime = datetime.datetime(int(dstrs[0:4]),int(dstrs[4:6]),int(dstrs[6:]),int(tstrs[0:2]),int(tstrs[2:4]),int(tstrs[4:6]))
        
        if dicinfo["AcqTime"] < dicStudyTime : #bug for TENSOR series
           if 'TENSOR' not in alpha_num_str(p1.SeriesDescription):
               self.log.warning('I thougth it was only for TENSOR ...taking AcqTime')
               self.log.warning('Acqtime %s  is before studyTime %s  ', dicinfo["AcqTime"],dicStudyTime)
           else:
               dicinfo["AcqTime"] =  '0000-00-00 00:00:00' #dicStudyTime
           dicinfo["AcqTime"] = dicStudyTime
               
        

        dicinfo["dicom_sdir"] = os.path.basename(os.path.dirname(dic1))
        
        if 'SeriesDescription' in p1 :
            dicinfo["SName"] = alpha_num_str(p1.SeriesDescription)
        else:
            dicinfo["SName"] = alpha_num_str(p1.ProtocolName)
        
        dicinfo["SNumber"] = int(p1.SeriesNumber)
        
        dicinfo["SUID"] = "%s"%(p1.SeriesInstanceUID)
        if "ImageType" in p1:
            
            dicinfo["ImageType"] = my_list_to_str(p1.ImageType,sep='_')    
        else:
            dicinfo["ImageType"] =p1.Modality
            
                 
        if "ScanOptions" in p1:
            dicinfo["ImageType"] = dicinfo["ImageType"] + "|" + my_list_to_str(p1.ScanOptions,sep='')
        
        makeitshort=False
        #make it short for special images
        if p1.has_key(0x291008):
            csatype = p1[0x291008].value
            
            if csatype.find('SPEC NUM')>=0:
                dicinfo["SeqType"] = 'spectro'
#            return self.get_dicom_serie_spectro_info(p1,dicinfo)
                
        #Dicoms Lists PET
        if "ImageType" not in p1:
            p1.ImageType='PETorUnknown'
        if "MIP_SAG" in p1.ImageType or "MIP_COR" in p1.ImageType or "MIP_TRA" in p1.ImageType :
            dicinfo["SeqName"] = "MIP"
            makeitshort=True
            
        if 'DERIVED' in p1.ImageType and 'SPEC' in p1.ImageType and 'SECONDARY' in p1.ImageType :
            dicinfo["SeqName"] = "spectroCSI"            
            makeitshort=True

        if 'PHYSIO' in p1.ImageType :
            dicinfo["SeqName"] = "physio"            
            makeitshort=True

                    
        if 'FA' in p1.ImageType or 'DERIVED' in p1.ImageType or  \
            'ADC' in p1.ImageType or 'TENSOR' in p1.ImageType or 'TRACEW' in p1.ImageType \
            or 'FSM' in p1.ImageType  or 'Service Patient' in p1.PatientsName \
            or 'MOCO' in p1.ImageType or 'DUMMY IMAGE' in p1.ImageType or 'TTEST' in p1.ImageType :
                dicinfo["SeqName"] = "DERIVED"
                makeitshort=True
        if 'DERIVED' in p1.ImageType and 'PRIMARY' in p1.ImageType and 'UNI' in p1.ImageType: #exception for mp2rage UNI
            makeitshort=False
                    
        if 'ImageComments' in p1:
            if p1.ImageComments.find('Design Matrix')>=0 or p1.ImageComments.find('Merged Image: t')>=0 or \
            p1.ImageComments.find('t-Map')>=0 :
                dicinfo["SeqName"] = "DERIVED"
                makeitshort=True
        
        if 'GE MEDICAL SYSTEMS' in p1.Manufacturer:
            makeitshort=False
        
            
        
        if makeitshort and self.skip_derived_series :
            dicinfo["Duration"] = 0
            dicinfo["_first_file"] , dicinfo["_last_file"] = dic1 , dic1
            return dicinfo
            
        #parsing the siemens private field, where all parameters are store in a string
        extractor = extract.MetaExtractor()
        
        try : 
            meta = extractor(p1)
        except Exception as e:
            self.log.warning('BAD DICOM first file ? %s becaus %s',alldic[0],e)
            dicinfo["corrupt"] = "Bad DICOMextract"
            return dicinfo                            

        #Pas de sequence name dans les sequences IRM de GE
        if [0x19,0x109c] in p1:
            dicinfo["SeqName"] = p1[0x19,0x109c].value        
               
        if 'SequenceName' in p1:
            dicinfo["SeqName"] = p1.SequenceName 
                        
        if 'SequenceName' in p1 or [0x19,0x109c] in p1:
            dicinfo["TR"] =  float(p1.RepetitionTime)

            te = p1.EchoTime
            if not te and not te==0 : # some sequence PRISMA_CHAMPIGNON/2016_06_02_CENIR_DEV_PHANTOM/S15_CombinedEchoes_fixed_weights TE=0 but other are defined
                dicinfo["TE"] = 0
            else:
                dicinfo["TE"] = int(p1.EchoTime)
                dicinfo["FA"] = int(p1.FlipAngle)
                dicinfo["PixelBw"] = int(p1.PixelBandwidth)
                
                aa=p1.PixelSpacing
                dicinfo["dimX"] = int(p1.Rows)
                dicinfo["dimY"] = int(p1.Columns) #do not work for mosaic
                dicinfo["dimZ"] = 0
    
                if 'NumberOfPhaseEncodingSteps' in p1:
                    dicinfo["dimPhase"] = int(p1.NumberOfPhaseEncodingSteps)
                
                dicinfo["sizeX"] = float(aa[0])
                dicinfo["sizeY"] = float(aa[1])
                dicinfo["sizeZ"] = float(p1.SliceThickness)
                
                if "SliceSpacing" in p1:
                    dicinfo["Slicegap"] = float(p1.SpacingBetweenSlices)-dicinfo["sizeZ"]
                else:
                    dicinfo["SliceGap"] = 0
                
                if "InPlanePhaseEncodingDirection" in p1:
                    dicinfo["PhaseDir"] =p1.InPlanePhaseEncodingDirection
                #dicinfo[""] = dicinfo[""]
            
                if "InversionTime" in p1:
                    dicinfo["TI"] = int(p1.InversionTime)
    
                    
                dicinfo["Affine"] = my_list_to_str(p1.ImageOrientationPatient)
                dicinfo["Affine"] = dicinfo["Affine"]  + my_list_to_str(p1.ImagePositionPatient)
                
                scan_seq = my_list_to_str(p1.ScanningSequence)
                acquisitionType =  str(p1.MRAcquisitionType)
            
        elif "PT" in p1.Modality: #for PT params
            dicinfo["Seqname"]=p1.SeriesDescription
            
            aa=p1.PixelSpacing
            dicinfo["dimX"] = int(p1.Rows)
            dicinfo["dimY"] = int(p1.Columns) #do not work for mosaic
            dicinfo["dimZ"] = 0
            
            dicinfo["sizeX"] = float(aa[0])
            dicinfo["sizeY"] = float(aa[1])
            dicinfo["sizeZ"] = float(p1.SliceThickness)
            acquisitionType=p1.SeriesType[0]
        
        
            
        else:        #try to find equivalent just in the CSA header (some data missing the elementary dicom field)
            if "SeqType" not in dicinfo : #so this is not a spectro dataset
                self.log.warning("No SequenceName in dicom of  %s so loking in csa_siemens_header",alldic[0])  
            
            if 'CsaImage.SequenceName' in meta :
                dicinfo["SeqName"] =  meta.get('CsaImage.SequenceName')     
                dicinfo["TR"] =  float( meta.get('CsaImage.RepetitionTime'))
                dicinfo["TE"] = float(  meta.get('CsaImage.EchoTime'))
                dicinfo["FA"] = float( meta.get('CsaImage.FlipAngle'))
                if 'CsaImage.PixelBandwidth' in meta :
                    dicinfo["PixelBw"] = int(meta.get('CsaImage.PixelBandwidth'))

                    dicinfo["dimX"] = int(meta.get('CsaImage.Rows'))
                    dicinfo["dimY"] = int(meta.get('CsaImage.Columns'))
                    if 'CsaImage.ProtocolSliceNumber' in meta:
                        dicinfo["dimZ"] = int(meta.get('CsaImage.ProtocolSliceNumber'))
        
                    dicinfo["dimPhase"] = int(meta.get('CsaImage.NumberOfPhaseEncodingSteps'))
            
                    aa=meta.get( 'CsaImage.PixelSpacing')
                    dicinfo["sizeX"] = float(aa[0])
                    dicinfo["sizeY"] = float(aa[1])
                    dicinfo["sizeZ"] = float( meta.get('CsaImage.SliceThickness'))

            #no slicespacing in meta so compute from slice position   
                if 'CsaSeries.MrPhoenixProtocol.sSliceArray.asSlice[0].sPosition.dTra' in meta and \
                       'CsaSeries.MrPhoenixProtocol.sSliceArray.asSlice[1].sPosition.dTra' in meta :
                    d11 = meta.get('CsaSeries.MrPhoenixProtocol.sSliceArray.asSlice[0].sPosition.dTra')
                    d12 = meta.get('CsaSeries.MrPhoenixProtocol.sSliceArray.asSlice[0].sPosition.dSag')
                    d13 = meta.get('CsaSeries.MrPhoenixProtocol.sSliceArray.asSlice[0].sPosition.dCor')
                    pos1 = np.array([d11,d12,d13])            
                    d11 = meta.get('CsaSeries.MrPhoenixProtocol.sSliceArray.asSlice[1].sPosition.dTra')
                    d12 = meta.get('CsaSeries.MrPhoenixProtocol.sSliceArray.asSlice[1].sPosition.dSag')
                    d13 = meta.get('CsaSeries.MrPhoenixProtocol.sSliceArray.asSlice[1].sPosition.dCor')
                    pos2 = np.array([d11,d12,d13])            
                    gap = np.linalg.norm(pos2-pos1) - dicinfo["sizeZ"]
                    if gap<1e-5:
                        gap=0
                    dicinfo["SliceGap"] = gap
            
                dicinfo["PhaseDir"] =meta.get('CsaImage.PhaseEncodingDirection')
                if 'CsaImage.ImageOrientationPatient' in meta:
                    dicinfo["Affine"] = my_list_to_str(meta.get('CsaImage.ImageOrientationPatient'))
                    dicinfo["Affine"] = dicinfo["Affine"]  + my_list_to_str(meta.get('CsaImage.ImagePositionPatient'))
                
                if 'CsaImage.ScanningSequence' in meta:
                    scan_seq = my_list_to_str(meta.get('CsaImage.ScanningSequence')) 
                    
            if meta.has_key('InversionTime'):
                dicinfo["TI"] = int(meta.get('InversionTime'))                
            
            if meta.has_key('ScanningSequence'):
                scan_seq = my_list_to_str(meta.get('ScanningSequence'))
            else :
            	scan_seq = ''                   
            
            if meta.has_key('MRAcquisitionType'):
                acquisitionType = str(meta.get('MRAcquisitionType')) #may be empty
            else:
                acquisitionType = ''
            
            
        if 0x051100e in p1:
             dicinfo["Orient"] = p1[0x051100e].value

        
        if meta.has_key('CsaSeries.MrPhoenixProtocol.lTotalScanTimeSec'):
            dicinfo["Duration"]  = int(meta.get('CsaSeries.MrPhoenixProtocol.lTotalScanTimeSec'))
        elif [0x19,0x105a] in p1:
            if isinstance(p1[0x19,0x105a].value, str):
            	dicinfo["Duration"]  = p1[0x19,0x105a]
            else:
            	dicinfo["Duration"]  = p1[0x19,0x105a].value/1000000
            
        else:
            dicinfo["Duration"] = 0
#        else:
#            if p1.has_key(0x051100a):
#                dicinfo["Duration"] = self.get_series_duration_from_siemens_tag(p1[0x051100a].value)            
        if p1.has_key(0x051100a):
            try:
                
                dicinfo["Duration2"] = self.get_series_duration_from_siemens_tag(p1[0x051100a].value)            
            except: 
                pass
        
        if meta.has_key('CsaImage.ImaCoilString'):
            dicinfo["CoilName"] = str(meta.get('CsaImage.ImaCoilString'))
        elif meta.has_key('CsaSeries.MrPhoenixProtocol.asCoilSelectMeas[0].asList[0].sCoilElementID.tCoilID'):
            dicinfo["CoilName"] = str(meta.get('CsaSeries.MrPhoenixProtocol.asCoilSelectMeas[0].asList[0].sCoilElementID.tCoilID'))
        elif meta.has_key('CsaSeries.MrPhoenixProtocol.sCoilSelectMeas.sCoilStringForConversion'):  #for prisma it seems to be an other field
            dicinfo["CoilName"] = str(meta.get('CsaSeries.MrPhoenixProtocol.sCoilSelectMeas.sCoilStringForConversion'))
        else:
            dicinfo["CoilName"] = "NULL"

        if meta.has_key('CsaSeries.MrPhoenixProtocol.tSequenceFileName'):   
            dicinfo["SeqName2"] = str(meta.get('CsaSeries.MrPhoenixProtocol.tSequenceFileName'))
            dicinfo["SeqName2"] = scan_seq + dicinfo["SeqName2"] + '_' + acquisitionType
        
        if meta.has_key('CsaSeries.MrPhoenixProtocol.sSliceArray.asSlice[0].dInPlaneRot'):
            dicinfo["PhaseAngle"] = float(meta.get('CsaSeries.MrPhoenixProtocol.sSliceArray.asSlice[0].dInPlaneRot'))
        else:
            dicinfo["PhaseAngle"] = 0
             
        if meta.has_key('CsaImage.PhaseEncodingDirectionPositive'):
            phase_sign = int(meta['CsaImage.PhaseEncodingDirectionPositive'])
            if phase_sign>0:
                dicinfo["PhaseDir"] += '+'
            else:
                dicinfo["PhaseDir"] += '-'
        
        if meta.has_key('CsaImage.MosaicRefAcqTimes'):
            dicinfo["SliceTime"] = str( meta.get('CsaImage.MosaicRefAcqTimes') )
        
        if meta.has_key('CsaSeries.AbsTablePosition'):
            dicinfo["TablePos"] = int( meta.get('CsaSeries.AbsTablePosition') )
        
        if meta.has_key('CsaSeries.MrPhoenixProtocol.sPat.ucPATMode'):
            patmod = meta.get('CsaSeries.MrPhoenixProtocol.sPat.ucPATMode')
            if int(patmod)>1:
                patmod = 'PAT_'+str(patmod) + ' PE_' + str(meta.get('CsaSeries.MrPhoenixProtocol.sPat.lAccelFactPE')) +\
                ' 3D_' + str(meta.get('CsaSeries.MrPhoenixProtocol.sPat.lAccelFact3D')) + ' RefL_' +\
                str(meta.get('CsaSeries.MrPhoenixProtocol.sPat.lRefLinesPE')) + ' RefS_' +\
                str(meta.get('CsaSeries.MrPhoenixProtocol.sPat.ucRefScanMode'))
            dicinfo["PatMode"] = str(patmod)
            
        #slice order 1 ascending 2 descending 4 interleaved  cf CsaImage.MosaicRefAcqTimes
        if meta.has_key('CsaSeries.MrPhoenixProtocol.sSliceArray.ucMode'):
            dicinfo["slicemode"] = meta.get('CsaSeries.MrPhoenixProtocol.sSliceArray.ucMode')
        
        #compute for  echo spacing or dwell time
        if meta.has_key("CsaImage.BandwidthPerPixelPhaseEncode") :
            hz = meta.get("CsaImage.BandwidthPerPixelPhaseEncode") 
            dicinfo["PhaseBw"] = float(hz)
            #echo_spacing = 1000 ./ hz / dim(fps_dim(2)); % in ms  c'est toujours dimY ?
        
        if meta.has_key("CsaSeries.SliceArrayConcatenations"):
            dicinfo["Concat"] = int( meta.get("CsaSeries.SliceArrayConcatenations"))

        if meta.has_key("CsaSeries.MrPhoenixProtocol.sPhysioImaging.sPhysioECG.lScanWindow"):
            dicinfo["CGating"] = int( meta.get("CsaSeries.MrPhoenixProtocol.sPhysioImaging.sPhysioECG.lScanWindow"))
        
        dicinfo = self.deduce_other_info(dicinfo)
        
        
        #expected number of slices
        if 'spectro' in dicinfo["SeqType"] : 
            nb_slice = len(alldic)
            nb_file = len(alldic)
            nb_vol=1
        else:
            nb_slice=1
            if acquisitionType == '2D' :
                nb_slice = meta.get('CsaSeries.MrPhoenixProtocol.sSliceArray.lSize')
                #if 'CsaSeries.MrPhoenixProtocol.sSliceArray.lSize' in vol[1]:
            elif acquisitionType == '3D' :
                #if nb_slice==1:
                nb_slice = meta.get('CsaSeries.MrPhoenixProtocol.sKSpace.lImagesPerSlab')
            if nb_slice is None :
                nb_slice=1
                
            nb_vol=1
            #DTI info
            if 'CsaSeries.MrPhoenixProtocol.sDiffusion.lDiffDirections' in meta :
                nbdif = int(meta.get('CsaSeries.MrPhoenixProtocol.sDiffusion.lDiffWeightings'))            
                bval_field = 'CsaSeries.MrPhoenixProtocol.sDiffusion.alBValue[%d]'%(nbdif-1)
                if bval_field in meta : #so it has bweihted
                    dicinfo["DiffBval"] = meta.get(bval_field)
                    dicinfo["DiffNbDir"] = meta.get('CsaSeries.MrPhoenixProtocol.sDiffusion.lDiffDirections')
                    nb_vol = dicinfo["DiffNbDir"] + nbdif - 1 #work only if 1 or 2 DiffWeight
                    
                else : #so it is only b0 reference
                    if 'CsaSeries.MrPhoenixProtocol.lRepetitions' in meta :
                        nb_vol = meta.get('CsaSeries.MrPhoenixProtocol.lRepetitions') + 1   

            #EPI nbvol
            elif 'CsaSeries.MrPhoenixProtocol.lRepetitions' in meta :
                nb_vol = meta.get('CsaSeries.MrPhoenixProtocol.lRepetitions') + 1   
            if 'ImageType' in meta: 
                imatype = meta.get('ImageType')
            else:
                imatype= "Other"
            if 'CsaSeries.MrPhoenixProtocol.lContrasts' in meta :
                #Attention que pour les field map
                if (not 'P' in imatype) or (dicinfo["SeqType"]!='GreFieldMap') :#for Field Map phase: 1 serie only : the diff is saved
                    nb_vol = nb_vol * int(meta.get('CsaSeries.MrPhoenixProtocol.lContrasts'))            
            
            if 'CsaSeries.MrPhoenixProtocol.sPhysioImaging.lPhases' in meta : #For angio velocity
                nb_vol = nb_vol * int(meta.get('CsaSeries.MrPhoenixProtocol.sPhysioImaging.lPhases')) 
                
            if 'CsaSeries.MrPhoenixProtocol.ucUncombImages' in meta: #so it save each coil element
                nbcoil=0
                coilelement = 'CsaSeries.MrPhoenixProtocol.asCoilSelectMeas[0].asList[%d].lElementSelected'%(nbcoil)
                while coilelement in meta:
                    nbcoil+=1
                    coilelement = 'CsaSeries.MrPhoenixProtocol.asCoilSelectMeas[0].asList[%d].lElementSelected'%(nbcoil)
                if meta.get('CsaImage.UsedChannelMask')!=-1: #if -1 then it is the summmed series
                    nb_vol = nb_vol*nbcoil
                
            if 'MOSAIC' in imatype :
                nb_file = nb_vol
            else :
                nb_file = nb_vol*nb_slice

        dicinfo["_nb_vol"] = nb_vol
        dicinfo["_nb_slice"] = nb_slice
        dicinfo["_nb_file"] = nb_file
        
        dicinfo["nb_dic_file"] = len(alldic)
        
        pg,dicom_file_size,n_ommited  = self.get_group_stack_from_dic(alldic)
        dicinfo["fsize"] = dicom_file_size            

        dicinfo["_first_file"] , dicinfo["_last_file"], dicinfo["corrupt"]  = self.get_first_and_last_dicom_InstanceNumber(pg,dicinfo)
        
        if n_ommited>0:
            dicinfo["corrupt"] += str(n_ommited) + "Bad DICOM"

        if 'spectro' in dicinfo["SeqType"] : 
            return dicinfo

        #do the dcmstack stuff

        if len(pg)>1 : 
            dicinfo["dim4"] = len(pg)
        
        all_stack=[]
                
        mf =dcmstack.make_key_regex_filter(['nothingtoremove'])

        for v in pg.itervalues():
#            my_stack = dcmstack.DicomStack(meta_filter=mf,time_order='AcquisitionTime')
            my_stack = dcmstack.DicomStack(meta_filter=mf,time_order='InstanceNumber')
            n_ommited=0
            n_repeat=0
            duplicate_dicom=[]
            for vol in v: #vol[0] champs de pydicom vol[1] ordererd dict
                
                try:
                    """
                    Add infos to meta to keep the diffusion directions in the GE PET-MR system
                    meta["Diffusioninfos"]=[dir1 dir2 dir3 bval]
                    """        
                    if [0x19,0x10bb] in p1:
                        vol[1]["Diffusioninfos"]=[vol[0][0x19,0x10bb].value, vol[0][0x19,0x10bc].value, vol[0][0x19,0x10bd].value, vol[0][0x43,0x1039][0]]
                        
                    my_stack.add_dcm(vol[0],meta=vol[1])
                    
                except dcmstack.IncongruentImageError:
                    n_ommited += 1
                except dcmstack.ImageCollisionError:
                    duplicate_dicom.append(vol[2])
                    n_repeat += 1
                except Exception : 
                    n_ommited +=1

#                dicom_file_size += os.path.getsize(vol[2])
            if n_repeat>0:
                self.log.warning("Found %d stack duplicate dicom file",n_repeat)
                dicinfo["corrupt"] += str(n_repeat)  + "Duplicate"
                
                if True: # dicinfo['_nb_file']*2== dicinfo['nb_dic_file']: #it seems each file is duplicate
                    if len(self.send_mail_file)>0: #write a log file containing the mv
                        (pdic,ff)=os.path.split(dicinfo['_first_file'])
                        doublondir = os.path.join(pdic,'doublon')
                        
                        (exa,suj,ser) = self.get_exam_suj_ser_from_dicom_meta(vol[1])
                        (pp,ff)=os.path.split(self.send_mail_file)
                        filename = pp + '/move_doublon' + exa+'_'+suj+'_'+ser+ '.sh'
                        ff = open(filename,'a+')
                        ff.write('mkdir -p %s\n'%(doublondir))
                        for dicff in duplicate_dicom:
                            ff.write('mv %s %s\n'%(dicff,doublondir))
#                    os.makedirs(doublondir)
#                    import shutil
#                    for ff in duplicate_dicom:
#                        shutil.copy2(doublondir,ff)


            if n_ommited>0:
                self.log.warning("Found %d stack incongruent dicom file",n_ommited)
                dicinfo["corrupt"] += str(n_ommited) + "Bad DICOM in stack"
#                self.log.warning("INVALIDE STACK could not add volume %s because %s ",vol[2],detail)

            try:
                #all_stack.append(my_stack.to_nifti(voxel_order='', embed_meta=True))
                all_stack.append(my_stack.to_nifti(voxel_order='LAS', embed_meta=True))
#how to make it basic this doeas not works                all_stack.append(my_stack.to_nifti(voxel_order='', embed_meta=True))
            
            except (dcmstack.InvalidStackError, dcmstack.IncongruentImageError) as detail:
                self.log.warning("INVALIDE STACK  because %s ",detail)
                dicinfo["corrupt"] += "Bad STACK"
                return dicinfo
            except Exception as e :
                self.log.warning("INVALIDE STACKdic  because %s ",e)    
                dicinfo["corrupt"] += "Bad STACKdic"
                return dicinfo
            
        
        shape = my_stack.get_shape()

        dicinfo["dimX"] = shape[0]
        dicinfo["dimY"] = shape[1]
        dicinfo["dimZ"] = shape[2]
        
        
        if len(shape)>3:
            dicinfo["dim4"] = shape[3]
            #nw=my_stack.to_nifti_wrapper(voxel_order='')
            nw=NiftiWrapper(all_stack[0])
            
            if nw.get_meta('EchoTime') is None : #this means it has different values for volumes
                te='[ '
                for k in range(shape[3]):
                    te = te + str(nw.get_meta('EchoTime',(0,0,0,k))) +' '
                te += ']'
                dicinfo["TEvec"] = te
            #get the duration from volume or image Acquisition Time
            if shape[3] >3 : #to skip localizer that may have several volume  
                dicinfo["Duration2"] = dicinfo["Duration"]
                ti1str = nw.get_meta('AcquisitionTime',(0,0,0,0) )
                ti2str = nw.get_meta('AcquisitionTime',(0,0,0,shape[3]-1) )
                ti1 = get_second_from_time_str( ti1str )
                ti2 = get_second_from_time_str( ti2str )
                dicinfo["Duration"] = ti2-ti1     
                if int(ti2str[0:2]) < int(ti1str[0:2]): #scan hour over midnight
                    dicinfo["Duration"] += 24*3600
                                
        if (convert_to_nii):
            
            nbs=0
            dicinfo["nifti_volumes"]=''
            for nii in all_stack:
                o_path,o_name = self.convert_series(nii,meta,stack_num=nbs)
                nbs+=1
                dicinfo["nifti_volumes"]+=o_name+','
            dicinfo["nifti_volumes"] = dicinfo["nifti_volumes"][:-1]
            dicinfo["nifti_dir"] = o_path
           
            if len(shape)>3:
                if dicinfo["SeqType"] is 'DWI' :
                    self.write_diff_to_file(nw,o_path)
                
                elif "Manufacturer" in meta and "GE MEDICAL SYSTEMS" in meta.get("Manufacturer") and "ScanningSequence"in meta and "EP" in meta.get("ScanningSequence"):  
                    self.write_diff_to_file(nw,o_path)
        elif "Manufacturer" in meta and  "Bruker" in meta.get("Manufacturer") and "MRDiffusionSequence" in meta:
            self.write_diff_to_file(nw,o_path)
                
        return dicinfo
 
    def get_group_stack_from_dic(self,alldic,
                                 group_keys =  ('SeriesInstanceUID','SeriesNumber','ProtocolName','ImageOrientationPatient','CsaImage.UsedChannelMask','EchoTime')):
#                                 group_keys =  ('SeriesInstanceUID','SeriesNumber','ProtocolName','ImageOrientationPatient','CsaImage.UsedChannelMask','EchoTime')):
                    #Attention que pour les field map j'ajoute le EchoTime
        import os
#        import psutil
#        #from sys import getsizeof
#        p = psutil.Process(os.getpid())

        extractor = extract.MetaExtractor()
        
        dcm=[]    
        warn_on_except=1
        force=False
        dicom_file_size=0
        n_ommited=0

#        self.log.info('MEMM2 %0.0f M ',p.get_memory_info().rss/1024/1024)
        for dcm_path in alldic:
            #Read the DICOM file
            
            try:
                dicdcm =  dicom.read_file(dcm_path, force=force)
                meta = extractor(dicdcm)
                
            except Exception, e:
                if warn_on_except:
                    self.log.warning('dcmstack Skiping Bad dicom Error reading file %s: %s' % (dcm_path, str(e)))
                    n_ommited+=1
                    continue
                else:
                    raise
            dcm.append ((dicdcm,meta,dcm_path))
            dicom_file_size += os.path.getsize(dcm_path)

#        self.log.info('MEMM3 %0.0f M ',p.get_memory_info().rss/1024/1024)
            
        pg = dcmstack.parse_and_group_dcm(dcm,group_by=group_keys)

#        self.log.info('MEMM4 %0.0f M ',p.get_memory_info().rss/1024/1024)
        
        return pg,dicom_file_size,n_ommited

# alternative but then you do not know the number of bad dicom
#            try : 
#                pg = dcmstack.parse_and_group(alldic, warn_on_except=True,force=True)
#            except Exception as e:
#                self.log.warning('BAD DICOM files ? %s becaus %s',alldic[0],e)
#                dicinfo["corrupt"] += "Bad group"
#                return dicinfo                    
        
    def _add_dirty_dcm_to_stack(self,stack,dcm):
        try:
            meta = self._meta_extractor(dcm)
            stack.add_dcm(dcm,meta=meta)
        except dcmstack.IncongruentImageError:
            self.n_ommited += 1
        except dcmstack.ImageCollisionError:
            self.n_repeat += 1

    def _stack_dicom_files(self):

        mf =dcmstack.make_key_regex_filter('nothingtoremove')
            
        dicom_stack = dcmstack.DicomStack(meta_filter=mf)

        for src_path in self.dicom_files:
            try:
                src_dcm = dicom.read_file(src_path)
                self.add_dirty_dcm_to_stack(dicom_stack,src_dcm)
            except dicom.filereader.InvalidDicomError: # not a dicom file
                self.n_ommited += 1
        print '%d files removed, considered as dummy/failed' % self.n_ommited
        print '%d files removed, considered as repeat' % self.n_repeat
        try:
            self.nii_wrp=dicom_stack.to_nifti_wrapper(self.inputs.voxel_order)
        finally:
            del dicom_stack



    def convert_series(self,nii,meta,stack_num=0):
        from dcmstack.dcmmeta import NiftiWrapper
        
        (exa,suj,ser) = self.get_exam_suj_ser_from_dicom_meta(meta)
        dest_dir = os.path.join(self.nifti_dir,exa,suj,ser)
        

        output_ext='.nii.gz'
        if len(nii.get_shape() )>3:
            out_fmt = ['f%d' % nii.get_shape()[3]]
        else:
            out_fmt = ['s']
            
        if 'SeriesNumber' in meta:
            out_fmt.append('S%02d' % meta.get('SeriesNumber'))
        if 'ProtocolName' in meta:
            out_fmt.append((meta.get('ProtocolName')))
        elif 'SeriesDescription' in meta:
            out_fmt.append((meta.get('SeriesDescription')))
        else:
            out_fmt.append('series')
        if stack_num>0:
            out_fmt.append('V%03d'%(stack_num+1))
        out_fmt = '-'.join(out_fmt)
    
        out_fmt = alpha_num_str(out_fmt )
        out_fn = out_fmt + output_ext
        
        out_path = os.path.join(dest_dir, out_fn)
                        
        if not os.path.isdir(dest_dir):
            os.makedirs(dest_dir)  
                                                
        nii.set_qform(nii.get_qform(),code=1)
        nii.set_sform(nii.get_sform(),code=1)
        t1 = time.time()
        
        convert_nii = True
        if os.path.isfile(out_path):
            convert_nii = False
            try :
                nw1=NiftiWrapper.from_filename(out_path)
                data1=nw1.nii_img.get_data()
            except Exception as e:
                os.remove(out_path)
                convert_nii=True
        
        if convert_nii==False :   
            data2=nii.get_data()
            different=False
            if np.equal(nii.get_shape(),nw1.nii_img.get_shape()).all():
                if ~ np.equal(data1,data2).all() :
                    different=True
            else:
                different=True
                
            if different:
                out_fn = 'duplicate_but_different'
                self.log.warning('different (data) but same Nifti name : file exist %s',out_path)
                #self.log.info('convert_nii is %s stack is %d',convert_nii,stack_num)
                
            del data1
            del data2
            del nw1
            
        if convert_nii:
            try:
		nii.to_filename(out_path)
            	self.log.info("Writing stack %s (in %f s)",out_path,time.time()-t1)

	    #except IOError as (errno, strerror):
    	#	print "I/O error({0}): {1}".format(errno, strerror)
	#	self.log.info('convert_niiii is %s stack is %d',convert_nii,stack_num)
	#    except ValueError:
	#    	print "Could not convert data to an integer."
	#	self.log.info('convert_niiii is %s stack is %d',convert_nii,stack_num)
	    except:
	        #print "Unexpected error:", sys.exc_info()[0]
		self.log.error('convert_niiii is %s stack is %d',convert_nii,stack_num)

            nii_wrp = NiftiWrapper(nii)
            path_tokens = out_path.split('.')
            if path_tokens[-1] == 'gz':
                path_tokens = path_tokens[:-1]
            if path_tokens[-1] == 'nii':
                path_tokens = path_tokens[:-1]
            meta_path = '.'.join(path_tokens + ['json'])
            pps=meta_path.split('/')
            pps[-1] = 'dic_param_' + pps[-1]
            meta_path = '/'.join(pps)
            out_file = open(meta_path, 'w')
            out_file.write(nii_wrp.meta_ext.to_json())
            out_file.close()
            del nii_wrp
        
        return dest_dir,out_fn
    
    def get_exam_suj_ser_from_dicom_meta(self,meta):
          
        if "StudyDescription" not in meta : #Service patient on prisma has none
            if "ProtocolName" not in meta :
                
                exa = "ServicePatient"
                if "AcquisitionDate" not in meta:
                    str_date = str(meta["StudyDate"])
                else : 
                    str_date = str(meta["AcquisitionDate"])

                str_date = str_date[0:4]+'_'+str_date[4:6] + '_' + str_date[6:8] 
                suj = str_date + '_' + alpha_num_str(meta["PatientName"])            
                ser = 'S%02d' % meta.get('SeriesNumber')
                
                if "Manufacturer" in meta and "GE MEDICAL SYSTEMS" in meta.get("Manufacturer"):
                    exa="Atrier"
                    str_date = str(meta["AcquisitionDate"])
                    str_date = str_date[0:4]+'_'+str_date[4:6] + '_' + str_date[6:8] 
                    suj = str_date + '_' + alpha_num_str(meta["PatientName"])         
                    ser = alpha_num_str(meta.get('SeriesDescription'))
                    if 'LST' in meta.get("Modality"):
                        ser=alpha_num_str(meta.get("Modality"))
                    if 'RAW' in meta.get("Modality"):
                        ser=alpha_num_str(meta.get("Modality"))
                
                return(exa,suj,ser)
            else:
                exa = alpha_num_str(meta["ProtocolName"]) 
        else:
            exa = alpha_num_str(meta["StudyDescription"]) 
        
        if "StudyDate" not in meta:
        	study_date = ''
        else :
        	study_date = str(meta["StudyDate"])

        if study_date=='':
			study_date = str(meta["SeriesDate"])

        study_date = study_date[0:4]+'_'+study_date[4:6] + '_' + study_date[6:8]

        # change exam field for GE data
    	if 'Manufacturer' in meta:
    		if 'GE MEDICAL SYSTEMS' in meta["Manufacturer"]:
    			if 'ProtocolName' in meta and len(meta["ProtocolName"])>0 and meta["ProtocolName"]!= ' ':
    				exa = alpha_num_str(meta["ProtocolName"])

#        if "AcquisitionDate" not in meta : 
#            str_date = study_date
#        else:
#            str_date = str(meta["AcquisitionDate"])
#            str_date = str_date[0:4]+'_'+str_date[4:6] + '_' + str_date[6:8] 
#        
#            #dicom bug only for DTI tensor : AcquisitionDate is bad and anterior
#            if study_date > str_date : 
#                str_date = study_date

        if "SeriesDate" not in meta : 
            str_date = study_date
        else:
            str_date = str(meta["SeriesDate"])
            str_date = str_date[0:4]+'_'+str_date[4:6] + '_' + str_date[6:8] 
        
            #dicom bug only for DTI tensor : AcquisitionDate is bad and anterior
            if study_date > str_date : 
                str_date = study_date
                
        
        suj = str_date + '_' + alpha_num_str(meta["PatientName"])
        try :
            exaid = meta["StudyID"]
        except:
            exaid='1'
                
        if len(exaid)>1 : #Service patient has strange Eid
            suj += '_E' + exaid
        elif int(exaid)>1:
            suj += '_E' + exaid
            
        if 'SeriesDescription' not  in meta:
            meta["SeriesDescription"] = 'nodescription'
            
        ser = 'S%02d' % meta.get('SeriesNumber') + '_' + alpha_num_str(meta["SeriesDescription"])
        if "ImageType" in meta and "P" in meta["ImageType"]:
            ser = ser + '_phase'
        
        return(exa,suj,ser)
        
    def write_diff_to_file(self,nw,dest_dir):
        
        shape = nw.nii_img.get_shape()
        bval=[]
        bvec=[]
        
        for ind in range(shape[3]):
            if 'GE MEDICAL SYSTEMS' in nw.get_meta("Manufacturer"):
                diffinfos=nw.get_meta("Diffusioninfos",(0,0,0,ind))
                diffdir=diffinfos[0:3]
                bvaltmp=diffinfos[3]
                bval.append(bvaltmp)
            elif 'Bruker' in nw.get_meta("Manufacturer"):
                diffall = nw.get_meta("MRDiffusionSequence",(0,0,0,ind))
                diffdir = diffall[0]["DiffusionGradientDirectionSequence"][0]["DiffusionGradientOrientation"]
                bvaltmp = diffall[0]["DiffusionBValue"]
                bval.append(bvaltmp)
            else:
                diffdir = nw.get_meta("CsaImage.DiffusionGradientDirection",(0,0,0,ind))
                bval.append( nw.get_meta("CsaImage.B_value",(0,0,0,ind)))

            if diffdir is None:
              diffdir =  [0, 0, 0]

            bvec.append( diffdir )
        
        bv = np.matrix(bvec)
        bval = np.array(bval,ndmin=2).T #bval.reshape((bval.size,1))
        mat = np.matrix(nw.nii_img.get_affine())           
        mat=mat[0:3,0:3]
        vox = np.sqrt(np.diag(np.dot(mat.T,mat)))
        mivox =  np.matrix((np.identity(3) * vox)).I
        rotnii = np.dot(mat,mivox)
        #I do not know why I have to change some sign ... (deduce from try and test)      

        if 'GE MEDICAL SYSTEMS' in nw.get_meta("Manufacturer"):  
            rot = rotnii
        else:
            rot = np.dot(np.diag([-1, -1 ,1]),rotnii)

        #dicom orientation
        patorient = nw.get_meta('ImageOrientationPatient')
        # For GE Oblique sequence more than one ImageOrientation (but all very close)     
        if patorient is None:
            patorient = nw.get_meta('ImageOrientationPatient',(0,0,0,0))

        patorient = np.reshape(patorient, (2, 3)).T

        rotations = np.eye(3)
        rotations[:, :2] = patorient

        # Third direction cosine from cross-product of first two
        # TODO it may not always be the cross-product ... genral case should look at each slices
        rotations[:, 2] = np.cross(patorient[:, 0], patorient[:, 1])
        #rotations = np.dot(rotnii,rotations) ca marche pas !!! pour GE il manque -1 sur x et pour siemens -1 sur y arggg
        #pour GE ne pas appliquer la rotation aux bvecs car deja dans le repere de la boite
        if 'GE MEDICAL SYSTEMS' in nw.get_meta("Manufacturer"):
            bvecnew=bvec
        else:
            bvecnew = np.dot(bv,rot)

        bvecnew_dic = np.dot(bv,rotations)
        out_path = os.path.join(dest_dir, 'diffusion_dir.bvecs')        
        out_path_dic = os.path.join(dest_dir, 'diffusion_dir.dicom_vec')        
        if os.path.isfile(out_path) :
            self.log.info('Skiping writting diffusion dir, because exist')
        else:
            np.savetxt(out_path,np.array(bvecnew).T,'%1.5f',' ')
            np.savetxt(out_path_dic,np.array(bvecnew_dic).T,'%1.5f',' ')
            out_path = os.path.join(dest_dir, 'diffusion_dir.bvals')
            np.savetxt(out_path,np.array(bval).T,'%d')
            out_path = os.path.join(dest_dir, 'diffusion_dir.txt')
            np.savetxt(out_path,np.concatenate((bval,bv),axis=1),'%1.5f')

    def get_first_dicom_file(self,ser,first):
        
        ff,tt = self.get_all_dicom_file(ser)
        if len(ff)==0:
            #if it contains S* direc this is a exam level so no warning
            ffd = glob(os.path.join(ser,'S*'))
            if len(ffd)==0: 
                self.log.warning('Empty Serie :  %s',ser)
            return []
        
        ff.sort()
        
        if first==1:
            thefile = ff[0]
                    
        if first==0:
            thefile = ff[-1]
            
        return os.path.join(ser,thefile)
        
    def get_last_dicom_file(self,ser):
        
        last_file = self.get_first_dicom_file(ser,0)
        p1=dicom.read_file(last_file,stop_before_pixels=True)
        
        ff,nb_of_dic_file = self.get_all_dicom_file(ser)
        #test if last_file is the last dicom (instance number) should be the number of file
        #sometime (PROTO_MOMIC/MOMIC_COUAD_38) the last volume is sended first ...

        if p1.InstanceNumber != nb_of_dic_file:
            #print "taking first file as last"
            last_file = ff[0]
            print last_file
            
            
            p1=dicom.read_file(last_file,stop_before_pixels=True)
            if len(p1.dir('ScanningSequence')) == 0:
                p1.ScanningSequence='SPECTRO'
                #print 'arrrrggg'

            if p1.InstanceNumber != nb_of_dic_file:
                if p1.ScanningSequence == 'GR rrr': #GRE
                    pass
                elif p1.ScanningSequence == 'SE rrr': #spin echo anatomic
                    pass
                else :
                    self.log.info("OUPS : LOOKING  at all file in %s file %d / %d",ser,p1.InstanceNumber,len(ff))
                    imax=0
                    for f in ff:
                        p=dicom.read_file(os.path.join(ser,f),stop_before_pixels=True)
                        #print "Inum %d t: %s" % (p.InstanceNumber,p.AcquisitionTime)
                        if p.InstanceNumber > imax:
                            imax=p.InstanceNumber
                            ffmax = f
                        if imax == nb_of_dic_file:
                            break
                    
                    last_file = ffmax
                    
                    if imax != nb_of_dic_file:
                        self.log.warning(" Serie %s : %s  Instance number %d but %d files ",ser ,p1.ScanningSequence,imax,nb_of_dic_file)
        
        return last_file
             
    def get_all_dicom_file(self,ser,verbose=True):
        '''return all dicom files sorted by Instance Number    '''
        #print 'ser'+ ser + self.dicom_ext
        
        ff = glob(os.path.join(ser,self.dicom_ext))
        
        if len(ff)==0:
            if verbose :
                #if it contains S* direc this is a exam level so no warning
                ffd = glob(os.path.join(ser,'S*'))
                if len(ffd)==0: 
                    self.log.warning('Empty Serie :  %s',ser)
            return ff,0
        
        newff=[]
        inum=[]
        for thefile in ff:
            if os.path.isfile(thefile):
                if is_dicom(thefile):
                    p=dicom.read_file(thefile,stop_before_pixels=True)
                    if 'InstanceNumber' in p:
                        inum.append(p.InstanceNumber)
                        newff.append(os.path.join(ser,thefile))
                else:
                    self.log.warning("BAD DICOM DESCRIPTOR dicom corrupt ? : %s",os.path.join(ser,thefile))
        
        sortedff = [x for y, x in sorted(zip(inum, newff))]
        
        return sortedff,len(sortedff)
        
    def get_first_and_last_dicom_InstanceNumber(self,pg,dicinfo):
        ifirst = 10000;
        ilast = 0;
        nb_dic_file=0
        for v in pg.itervalues():
            for vol in v: #vol[0] champs de pydicom vol[1] ordererd dict
                i = int(vol[0].InstanceNumber)
                nb_dic_file+=1
                if i<ifirst:
                    ifirst=i
                    first_file = vol[2]
                if i>ilast:
                    ilast = i
                    last_file = vol[2]
        if ilast==ifirst:
            last_file = first_file
            
        nb_slice= dicinfo["_nb_slice"]
        nb_vol  = dicinfo["_nb_vol"]
        nb_file = dicinfo["_nb_file"]
        corrupt = ''
        

#it does not work for fieldMap magnitude           
#        if nb_dic_file != ilast:
#            self.log.warning('Missing dicom file (last instance number %d != number of dic file %d)',ilast,nb_dic_file)
#            corrupt += 'missingDicomFile_last_'
            
        if (nb_file != nb_dic_file) & (nb_vol == 1):
            if nb_file > nb_dic_file:
                corrupt += 'missingDicomFile_%d'%(nb_file-nb_dic_file)
                strinfo = 'Missing some dicom file : \n'
            else:
                corrupt += 'tomuchDicomFile_'
                strinfo = 'Too much dicom file : \n'
            strinfo += '\t nbdicfile in dir  = %d  Expected %d (%d vol %d slices)\n' %(nb_dic_file,nb_file,nb_vol,nb_slice)
            self.log.warning(strinfo)
            
                
        if (nb_file != nb_dic_file) & (nb_vol > 1):
            if ilast == nb_dic_file :
                strinfo = 'Missing some dicom file ( May be the sequence was interupted) \n'
                strinfo += '\tnbdicfile in dir = %d  Expected %d (%d vol %d slices)\n' %(nb_dic_file,nb_file,nb_vol,nb_slice)
                self.log.info(strinfo)
            else :
                strinfo = 'Missing some dicom file last instance number %d BUT nr of dicom files  %d \n'%(ilast,nb_dic_file)
                corrupt += 'missingDicomFile_%d'%(ilast-nb_dic_file)
                self.log.warning(strinfo)
                    
        if len(corrupt)>0:
            (exa,suj,ser) = self.get_exam_suj_ser_from_dicom_meta(vol[1])
            strinfo += '\n Please check \t%s \t%s \t%s  \n %s'%(exa,suj,ser,vol[2])
            if self.send_mail:
				try :
					if len(self.send_mail_file)>0:
						oname = self.send_mail_file + exa+'_'+suj+'_'+ser
						c.send_mail_file(strinfo,oname)
					else:
						c.send_mail(strinfo,'Dicom files problem',self.smtp_pwd)
				except Exception as e:
					self.log.warning('FAIL to send mail because %s ',e)
        
        return first_file,last_file,corrupt
        
    def separate_exam_series(self,series_dir):
        #for so exam there are series from different acquisition time we will then split the series_list
        series_dir = filter(os.path.isdir,series_dir)
         
        ser_ok=[];        actime=[];        acdate=[];        
        
        for ser in series_dir :
            thefile = self.get_first_dicom_file(ser,1)

            if len(thefile)==0:
                #self.log.info('Siking %s because empyt', ser)
                continue
            try:
                
                ps=dicom.read_file(thefile,stop_before_pixels=True)
            except:
                """
                la fonction dicom read file ne fonctionne pas sur les GEMS PET RAW  pas de transformation en NIFTI possible de toute facon
                """
                continue
            # I remove exclusion of 'FM' imagetype because it is present in some T1 (ex MS_SPI S02)
            # remove     or 'DERIVED' in ps.ImageType because of mp2rage uni (DERIVED\PRIMARY\M\ND\UNI)
            if "ImageType" in ps:
                if 'FA' in ps.ImageType or 'OTHER' in ps.ImageType or \
                'ADC' in ps.ImageType or 'TENSOR' in ps.ImageType or 'TRACEW' in ps.ImageType \
                or 'FSM' in ps.ImageType  or 'Service Patient' in ps.PatientsName \
                or 'MOCO' in ps.ImageType or 'DUMMY IMAGE' in ps.ImageType or 'TTEST' in ps.ImageType :
                #self.log.info('Skiping %s because imageType is %s', ser,ps.ImageType)
                    if self.skip_derived_series:
                        self.log.info(" Skiping because derived %s",thefile)
                        continue

                    
            if 'ImageComments' in ps:
                if ps.ImageComments.find('Design Matrix')>=0 or ps.ImageComments.find('Merged Image: t')>=0 or \
                ps.ImageComments.find('t-Map')>=0 :
                    if self.skip_derived_series:
                        self.log.info(" Skiping because derived %s",thefile)
                        continue
            
            if len(ps.dir("AcquisitionDate"))==0:
                self.log.warning("STrange dicom file %s has no tag Acquisition Date skiping serie Taking Study time and date",thefile)
                if len(actime)==0:
                    ps.AcquisitionTime = ps.StudyTime
                    ps.AcquisitionDate = ps.StudyDate              
                else:                                                        
                    ps.AcquisitionTime = actime[-1]
                    ps.AcquisitionDate = acdate[-1]
                
                
            ser_ok.append(ser)
            actime.append(ps.AcquisitionTime)  
            acdate.append(ps.AcquisitionDate)

#        series_list=[]
#        if len(ser_ok)==0:
#            return ser_ok
#        series_list.append(ser_ok)                
#        return series_list

#this part is just for the case your search at the exam level in an exam dir where serie have different AcquisitionTime (different day)
        nda = np.array(acdate,np.int16)        
        [nu,ii,indu] = np.unique(nda,True,True)
        
        
        #regroup series with the same acquisition date and order give the acquisition time    
        series_list=[]        
        for ne in range(ii.size):
            ser_one_exam=[]
            actime_one_exam=[]
            for ns in range(indu.size):
                if indu[ns]==ne:
                    ser_one_exam.append(ser_ok[ns])    
                    actime_one_exam.append(actime[ns])
            aa=zip(actime_one_exam,ser_one_exam)
            aa.sort()
            actime_one_exam,ser_one_exam = zip(*aa)
            series_list.append(ser_one_exam)

        return series_list
    
    
    def get_dicom_serie_spectro_info(self,p1,dicinfo):
        
        dicinfo["SeqName"] = "spectro"
    
    
        return dicinfo
        
    
    def get_series_duration_from_siemens_tag(self,serie_time):
        """
        private tag [0x0051,0x100a] contain an string with the acquisition time ex TA 03:50*3
        """
        if serie_time[5]==".":
            dur=float(serie_time[3:5])+1
        elif serie_time[5]==":":
            dur=float(serie_time[3:5])*60 + float(serie_time[6:8])
        else:
            self.log.error("SHOULD NOT HAPPEND")
        ind = serie_time.find("*")
        if ind>-1:
            multfac = float(serie_time[ind+1:])
        else:
            multfac = 1
            
        dur = dur*multfac;
        return dur
        
    def get_series_duration_from_file(self,dic_file):
        """
        return the series total duration in second as read in the text part of the dicom format
        the problem with EPI is that this time is the total series time : nbvolume*TR regardless 
        if the serie has been interupted so for EPI one must take the get_series_duration_from_siemens_tag
        """
        
        out = c.cmdWoutput(["strings" , dic_file ],verbose=False)
        out = out.split()
        
        try:
            ind = out.index("lTotalScanTimeSec")
        except ValueError:
            self.log.warning( "Arg no lTatalScanTimeSec in %s",dic_file)
            return 0
        
        #for one dicom file thhe lTotalScanTimeSec was present before without any value ...
        try:
            scan_time = int(out[ind+2])
        except ValueError:
            ind = out.index("lTotalScanTimeSec",ind+1)
            scan_time = int(out[ind+2])
        
        return scan_time
    
    
    def find_double_exam(self,Ei):
        self.log.info('\n\n *******LOKING FOR DOUBLED EXAM*******')
        for k in range(len(Ei)):
            oneE = Ei[k]
            for kk in range(k+1,len(Ei)):
                otherE = Ei[kk]
                if oneE["AcquisitionTime"] == otherE["AcquisitionTime"] and oneE["MachineName"] == otherE["MachineName"] :
                    self.log.info('Find a double exam')
                    self.log.info(oneE["StudyDescription"]+" Suj "+oneE["PatientsName"] + " dir : " + oneE["dicom_dir"])
                    self.log.info(otherE["StudyDescription"]+" Suj "+otherE["PatientsName"]+ " dir : " + otherE["dicom_dir"])
                    
                    ser1 = c.get_subdir_regex(oneE["dicom_dir"],'^S')
                    ser2 = c.get_subdir_regex(otherE["dicom_dir"],'^S')
                    if len(ser1)!=len(ser2):
                        self.log.warning('Different number of series')
                        
                    ffile1 = self.get_first_dicom_file(ser1[0],1)
                    ffile2 = self.get_first_dicom_file(ser2[0],1)
                    
                    if os.path.getmtime(ffile1)>os.path.getmtime(ffile2):
                        self.log.info('The first listed was created %d hours after  %s',(os.path.getmtime(ffile1)-os.path.getmtime(ffile2))/3600,ffile1)
                    else:
                        self.log.info('The last listed was created %d hours after  %s',(os.path.getmtime(ffile2)-os.path.getmtime(ffile1))/3600,ffile2)
                        
                        
                                    
                    
        self.log.info('done\n')


    def tri_dicom_dir(self,in_dir,verbose=True,mv_file=False,tri_move=False):
        import shutil         
        import os
#        import psutil
#        #from sys import getsizeof
#        p = psutil.Process(os.getpid())
        
        if mv_file:
            f1=open(os.path.join(self.dicom_dir,'./move_after_tri.sh'), 'w+')
        new_dicom_dir=[]
        
        for dir_path in in_dir:
            
            #self.log.info('MEM1 %0.0f M pg %0.0f',p.get_memory_info().rss/1024/1024,getsizeof(pg))

            alldic,nb_of_dic_file = self.get_all_dicom_file(dir_path,verbose=verbose)
            if nb_of_dic_file>0:
                self.log.info('Reading %d file in %s',len(alldic),dir_path)                                
#                self.log.info('MEM2 %0.0f M ',p.get_memory_info().rss/1024/1024)
                #We got rid of the 'ProtocolName' in group_keys for the formation of stacks as it created problems with GE files
                group_keys =  ('SeriesInstanceUID','SeriesNumber')
                
                pg,dicom_file_size,n_ommited  = self.get_group_stack_from_dic(alldic,group_keys=group_keys)
                
#                self.log.info('MEM3 %0.0f M ',p.get_memory_info().rss/1024/1024)
      
                for v in pg.itervalues():
                    vol = v[0]
                    (exa,suj,ser) = self.get_exam_suj_ser_from_dicom_meta(vol[1])
                    dest_dir = os.path.join(self.dicom_dir,exa,suj,ser)
                    if os.path.isdir(dest_dir):
                        dest_dir =  os.path.join(self.dicom_doublon,exa,suj,ser)
                        
                    while os.path.isdir(dest_dir):
                        ser += '_again'
                        dest_dir = os.path.join(self.dicom_doublon,exa,suj,ser)
                
                    os.makedirs(dest_dir)  
                    new_dicom_dir.append(dest_dir)
                        
                    self.log.info('Copying %d files in %s',len(v),dest_dir)
                    iii=1
                    for vol in v: #vol[0] champs de pydicom vol[1] ordererd dict meta vol[2] file_path
                        (pp ,fin)=os.path.split(vol[2])
                        nn , ee = os.path.splitext(fin)
                        if len(ee)==0:
                            fin = nn+'.dic'
                        
                        indn =  fin.find('(null)')
                        if indn >0 :
                            fout =  fin[:indn-1]+fin[indn+6:]
                            fintxt = fin[:indn]+'\\'+fin[indn:indn+5]+'\\'+fin[indn+5:]
                            p1 = vol[0]
                            if 'AcquisitionNumber' in p1 and 'InstanceNumber' in p1 :
                                fout = 'spectre_S%d_A%.3d_U%.3d_%s'%(p1.SeriesNumber,p1.AcquisitionNumber,p1.InstanceNumber,fout)
                            else:
                                fout = 'unknown_i%.4d'%(iii)
                                iii+=1
                        else:
                            fintxt = fin
                            fout = fin
                        
                        fin = os.path.join(pp,fin)
                        fout = os.path.join(dest_dir,fout)
                        fintxt = os.path.join(pp,fintxt)
                        
                        #Rangement des fichiers LIST PET en gardant l'arborescence GE au sein de l'arborescence CENIR
                        try:
                            
                            if 'GEMS PET LST' in fin:
                                # Mettre l'arborescence correspondant au fichier LIST (PESI/pXX/eXX/sXX/GEMS PET LSTDC pour pouvoir les remettres sur la machine)        
                                path=os.path.dirname(fout)
                                fin2=fin[fin.rfind('PESI'):]
                                fout=os.path.join(path,fin2)
                                dirGEMS=os.path.dirname(fout)
                                
                                if not os.path.isdir(dirGEMS):
                                    os.makedirs(dirGEMS)
                                try:
                                    
                                    flist=vol[0][0x09,0x10da].value
                                
                                    flistin=fin[:fin.rfind('PESI')]+flist
                                
                                
                                    foutlist=path+flist
                                    
                                    
                                    if not os.path.isfile(foutlist):
                                        dirlist=os.path.dirname(foutlist)
                                        os.makedirs(dirlist)
                                        if tri_move:
                                            shutil.move(flistin,foutlist)
                                        else:
                                            shutil.copy2(flistin,foutlist)
                                except:
                                    print 'Tried to copy PETlistfile without success'
                        except:
                            pass
                            
                        if tri_move:
                            shutil.move(fin,fout)
                        else:
                            shutil.copy2(fin,fout)
                        
                        if mv_file:            
                            f1.write(('rm -f %s\n'%(fintxt)))
                        del vol
        if mv_file:
            f1.close()
            
        return new_dicom_dir                
        

    
def clean_str(stri):

    stri = stri.encode('ascii','ignore').decode()
    stri = stri.replace('^','_')
    stri = stri.replace(' ','_')

    return stri
    

def get_second_from_time_str(tstr):
    return int(tstr[0:2])*3600 + int(tstr[2:4])*60 + int(tstr[4:6])


def is_dicom(fname):

    fobj = open(fname, 'rb') 
    fobj.seek(128)
    dicm = fobj.read(4)
    fobj.close()
    return dicm == b'DICM'

def my_list_to_str(l,sep=' ') :
    if type(l) is str:
        return l
        
    s=''
    for li in l:
        li = str(li)
        if len(li)>0:
            s = s + li + sep
    return s




'''
avant de connaitre la fonction extractor

    if (dicom.tag.Tag(0x291020) in p1):
        dic_str = p1[0x291020].value
        
        i1=dic_str.find('tCoilID')
        if i1:
            i2 = dic_str.find('""',i1)
            i3 = dic_str.find('""',i2+2)
            dicinfo["CoilName"] = dic_str[i2+2:i3]
        else:
            dicinfo["CoilName"] = "NULL"
        
        i1=dic_str.find('tSequenceFileName')
        if i1>0:
            i2 = dic_str.find('""',i1)
            i3 = dic_str.find('""',i2+2)
            dicinfo["SeqName2"] = dic_str[i2+2:i3]
        else:
            dicinfo["SeqName2"] = "NULL"
        
        i1=dic_str.find('dInPlaneRot')
        if i1>0:
            i2 = dic_str.find('=',i1)
            i3 = dic_str.find('\n',i2+2)
            dicinfo["PhaseAngle"] = float(dic_str[i2+2:i3])
        else:
            dicinfo["PhaseAngle"] = "NULL"
                       
        i1=dic_str.find('sWiPMemBlock.tFree')
        if i1>0:
            i2 = dic_str.find('""',i1)
            i3 = dic_str.find('""',i2+2)
            dicinfo["SeqName2"] = dicinfo["SeqName2"] + dic_str[i2+2:i3]
'''
'''
    import nibabel.nicom.dicomwrappers as nw
    dw=nw.wrapper_from_data(p1)
    #dw=nw.SiemensWrapper(p1)
sg = dcmstack.parse_and_group(src_paths)
for k,v in sg.iteritems():
    for vol in v:
       print vol[2] #vol[0] champs de pydicom vol[1] ordererd dict
for k,v in m2.iteritems():
    if k.find('Pat')>=0 :
        print k , ' : ' , v 
        # (type:',type(v)

for k,v in m2.iteritems():
    if type(v) is list:
        if type(v[0]) is str:
            if v[0].find('TA')>=0 :
                print k , ' : ' , v 
    if type(v) is str or type(v) is unicode:
        if v[0].find('TA')>=0 :
            print k , ' : ' , v 

   
aa=vol[1]
for k,v in aa.iteritems():
    print k

'''
