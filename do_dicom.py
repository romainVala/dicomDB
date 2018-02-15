#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 11:00:43 2012

@author: romain
"""

import common as c
import numpy as np
import os,math,re,dicom,time,logging,datetime,sys
import MySQLdb as mdb

db_field_all = ("eid","rid","PatientsName","AcquisitionTime","ExamDuration","PatientsBirthDate","PatientsAge","PatientsSex","PatientsWeight",\
    "SoftwareVersions","FirstSerieName","LastSerieName")
    

#logging.basicConfig(filename="log_do_dicom.log",format='%(levelname)s:%(message)s',level=logging.INFO)

#formatter = logging.Formatter('%(asctime)s - %(name)-2s: %(levelname)-2s : %(message)s')

formatter = logging.Formatter('%(asctime)-2s: %(levelname)-2s : %(message)s')

console = logging.StreamHandler()
console.setFormatter(formatter)

#fhdl = logging.FileHandler(filename = '/servernas/nasDicom/log_update_db.log',mode='a')
#fhdl.setFormatter(formatter)

# add the handler to totot logger
log = logging.getLogger('do_dicom')
#logw = logging.getLogger('do_dicom_warning')
#log.addHandler(fhdl)
#log.setLevel(logging.INFO)


#def parse_exam_in_dicom_raw():
#
#    d_proto = c.get_subdir_regex('/nasDicom/dicom_raw','.*')
#    t1=time.clock()
#    t2 = time.time()    
#    for proto in d_proto[0:1]:
#        tic = time.clock()
#        d_exam = c.get_subdir_regex(proto,'.*')
#        log.info("working on %s \t  %d exams ",os.path.basename(proto),len(d_exam))
#        #print "working on %s \t  %d exams "%(os.path.basename(proto),len(d_exam))
#        send_all_exam_info_to_sqldb(d_exam,verbose=False)
#        #get_exam_information(d_exam,False)
#        toc =  time.clock()
#        #print "%s \t  %d exams \t done in %f " % (os.path.basename(proto),len(d_exam),toc-tic)
#        
#    log.info("Temps ecoule %f mn Total cpu time %f mn ",(time.time()-t2)/60,(time.clock()-t1)/60)
    
def remove_duplicate_exam():
    
    con = mdb.connect(host = 'mysql.lixium.fr', user = 'cenir', passwd =  'y0p4l4sql', db = 'cenir')
    cur = con.cursor(mdb.cursors.DictCursor)

    #sqlcmd = "select * from gg_examen e1  where exists (select * from gg_examen e2 where e1.crid <> e2.crid and abs(time_to_sec(timediff(e1.AcquisitionTime,e2.AcquisitionTime))) < 300  and substr(e2.AcquisitionTime,1,4) = '2014' and e1.rid=e2.rid ) order by e1.AcquisitionTime;"   
    sqlcmd = "select * from gg_examen e1  where exists (select * from gg_examen e2 where e1.crid <> e2.crid and abs(time_to_sec(e1.AcquisitionTime) -time_to_sec(e2.AcquisitionTime)) < 300 and substr(e1.AcquisitionTime,1,10)=substr(e2.AcquisitionTime,1,10) and substr(e2.AcquisitionTime,1,4) = '2014' and e1.rid=e2.rid ) order by e1.AcquisitionTime;"   
    cur.execute(sqlcmd)
    rows = cur.fetchall()   
    fr = open('./remove_series_sql.sh','w+')
    
    for k in  range(0,len(rows),2):
        r1 = rows[k]
        r2 = rows[k+1]
        if r1['PatientsName'] != r2['PatientsName']:
            print 'please chek %s %s/%s | %s versus %s %s/%s | %s'%(r1['crid'],r1['eid'],r1['PatientsName'],r1['AcquisitionTime'],
                                                                    r2['crid'],r2['eid'],r2['PatientsName'],r2['AcquisitionTime'])
            continue
        
        if r1['relu'] != r2['relu']:
            print 'different relu for %s/%s '%(r1['eid'],r1['PatientsName'])
            if r1['relu']:
                fr.write("delete from gg_examen where crid=%d;\n"%(r2['crid']))   
            else:
                fr.write("delete from gg_examen where crid=%d;\n"%(r1['crid'])) 
        
        if r1['maj_le']>r2['maj_le']:
            fr.write("delete from gg_examen where crid=%d;\n"%(r1['crid'])) 
        else:
            fr.write("delete from gg_examen where crid=%d;\n"%(r2['crid'])) 
        
    fr.close()
    
    for r in rows:
        print "%s %s %s %s %s" %(r['crid'] , r['eid'] , r['PatientsName'] , r['AcquisitionTime'] , r['maj_le'] )
        
def toto():
    con = mdb.connect(host = 'mysql.lixium.fr', user = 'cenir', passwd =  'y0p4l4sql', db = 'cenir')

    #con = mdb.connect(host = '127.0.0.1', user = 'cenir', passwd =  'pschitt', db = 'cenir')
 
    cur = con.cursor(mdb.cursors.DictCursor)

   
    cur.execute("SELECT * FROM gg_examen WHERE PatientsName = %s",("kevin"))

def update_exam_sql_db(Ei,test=False,do_only_insert=False):
    """
    input a list of exam dir: get the exam info and submit to the cenir db if the line does not exist
    or if some parameter has change
    """
    con = mdb.connect(host = 'mysql.lixium.fr', user = 'cenir', passwd =  'y0p4l4sql', db = 'cenir')
    cur = con.cursor(mdb.cursors.DictCursor)
    cur2 = con.cursor()
    
    sqlcmds = "SELECT * from gg_examen WHERE "
    
    #field_new_value = []
    #field_old_value = []
    
    #Ei = get_exam_information(in_dir)
    #Ei[0]["PatientsName"]='totqsdfo'
    
    for E in Ei:
        #bad name to test update E["PatientsName"]='totqsdfo'
        
        #sqlcmd = "%s rid = %s AND AcquisitionTime = '%s'" % (sqlcmds,E["rid"],E["AcquisitionTime"])
        sqlcmd = "%s rid = %s AND abs(time_to_sec(AcquisitionTime)-time_to_sec('%s'))<100 AND substr(AcquisitionTime,1,10)=substr('%s',1,10)" % (sqlcmds,E["rid"],E["AcquisitionTime"],E["AcquisitionTime"])
        #print sqlcmd        
        cur.execute(sqlcmd)
        if cur.rowcount == 1 :
            data = cur.fetchone()
            #ppoo
            #check if some field have change
            dicom_changes=False
            field_change = []
            for f in db_field_all:
                #print f + "  E : " + str(E[f]) + "   sql : " + str(data[f])
                if data[f] != E[f] :
                    #log.info('field %s differ sdb : %s dic : %s',f,data[f],E[f])
                    dicom_changes=True
                    field_change.append(f)
                    #field_new_value.append(E[f])
                    #field_old_value.append(data[f])
            if do_only_insert is False:                    
                if dicom_changes:
                    infostr = "SQL UPDATE of pat=%s : proto=%s : date=%s "%(E['PatientsName'],E['eid'],E['AcquisitionTime'])
                    #logw.warning("SQL UPDATE of pat=%s : proto=%s : date=%s ",E['PatientsName'],E['eid'],E['AcquisitionTime'])
                    infostr += "\n\tFiled change : "
                    for f in field_change:
                        infostr += "\n\t %s : \t %s \t -> \t\t%s" %(f,data[f],E[f])
                    infostr+='\n\n'
                    log.warning(infostr) 
                    #logw.warning(infostr) 
                    
                    #if test:
                    cmd_sql = get_sql_update_cmd(E,data['crid'])
                    log.info('SQL update will be %s',cmd_sql)
                        
                    if test is False :
                        cur2.execute(cmd_sql)
                        con.commit()
                
        elif cur.rowcount == 0:
            
            log.info("SQL INSERT of pat=%s : proto=%s : date=%s ",E['PatientsName'],E['eid'],E['AcquisitionTime'])

            #check if there is the same subject the same day WHERE `AcquisitionTime` LIKE '2013-08-06%'
            sqlcmd = "SELECT * from gg_examen WHERE rid = %s AND AcquisitionTime LIKE '%s%%' AND PatientsName='%s'" % (E["rid"],E['AcquisitionTime'].date(),E["PatientsName"])
            cur.execute(sqlcmd)
            if cur.rowcount == 1 :
                data = cur.fetchone()
                difftime = data["AcquisitionTime"]-E['AcquisitionTime']
                difftimesecond = difftime.days*86400 + difftime.seconds #si negative il met -1 jour et les second correspondante
                log.warning("New insert BUT already the same subject the same daye  :  %d second before",difftimesecond)
            
            if test is False :
                cur2.execute(get_sql_insert_cmd(E))
                con.commit()
        else:
            msg = "ERROR Found more than 1 line for %s " % (sqlcmd)
            log.warning(msg)
            data = cur.fetchall()
            rrr = ''
            for r in data:
                rrr = '%s\n\t doublon %s %s/%s %s'%(rrr,r['crid'],r['eid'],r['PatientsName'],r['AcquisitionTime']) 
            log.warning(rrr)
            #raise NameError(msg)
    
    con.close()
                
                
def get_sql_update_cmd(E,crid):
    
            
    sqlcmd = "UPDATE gg_examen SET "
    for ff in db_field_all:
        if type(E[ff]) is str or type(E[ff]) is datetime.date or type(E[ff]) is datetime.datetime :
            sqlcmd = "%s %s='%s'," % (sqlcmd,ff,E[ff])
        elif type(E[ff]) is int or type(E[ff]) is float:
            sqlcmd = "%s %s=%d," % (sqlcmd,ff,E[ff])
        else:
            msg = "ERROR How to write field %s with %s" % (ff,type(E[ff]))
            raise NameError(msg)
    
    #sqlcmd = sqlcmd[:-1] + " WHERE rid = %s AND AcquisitionTime = '%s' " % (E["rid"],E["AcquisitionTime"])
    sqlcmd = sqlcmd[:-1] + " WHERE crid = %s " % (crid)
    return sqlcmd

def get_sql_insert_cmd(E):

    sqlcmd = "INSERT INTO gg_examen ("
    for ff in db_field_all:
        sqlcmd = "%s %s," % (sqlcmd,ff)       
    
    sqlcmd = sqlcmd[:-1]+") VALUES("
    
    for ff in db_field_all:
        if type(E[ff]) is str or type(E[ff]) is datetime.date or type(E[ff]) is datetime.datetime :
            sqlcmd = "%s '%s'," % (sqlcmd,E[ff])
        elif type(E[ff]) is int or type(E[ff]) is float:
            sqlcmd = "%s %d," % (sqlcmd,E[ff])
        else:
            msg = "ERROR How to write field %s with %s" % (ff,type(E[ff]))
            raise NameError(msg)
    
    sqlcmd = sqlcmd[:-1]+")"
    return sqlcmd
    
#def send_all_exam_info_to_sqldb(in_dir,verbose=True):
#    """
#    input a list of exam dir: get the exam info and submit to the cenir db
#    """
#
#    Ei = get_exam_information(in_dir,verbose)
#
#    #construct the sql INSERT comand
#    
#    sqlcmd = "INSERT INTO gg_examen ("
#    for ff in db_field_all:
#        sqlcmd = "%s %s," % (sqlcmd,ff)       
#    
#    sqlcmd = sqlcmd[:-1]+") VALUES("
#    for E in Ei:
#        for ff in db_field_all:
#            if type(E[ff]) is str or type(E[ff]) is datetime.date or type(E[ff]) is datetime.datetime :
#                sqlcmd = "%s '%s'," % (sqlcmd,E[ff])
#            elif type(E[ff]) is int or type(E[ff]) is float:
#                sqlcmd = "%s %d," % (sqlcmd,E[ff])
#            else:
#                msg = "ERROR How to write field %s with %s" % (ff,type(E[ff]))
#                raise NameError(msg)
#        sqlcmd = sqlcmd[:-1]+"),("
#        
#    sqlcmd = sqlcmd[:-2]
#
#    if verbose:
#        print "Sending SQL insert for all exam"
#        
#    #execute the sql command
#    con = mdb.connect(host = 'mysql.lixium.fr', user = 'cenir', passwd =  'y0p4l4sql', db = 'cenir');    
#    cur = con.cursor()
#    cur.execute(sqlcmd)
#    con.commit()
#    
#    con.close()

#sereies in one exam dir may have been acquiered with 
def get_first_dicom_file(ser,first):

    ff = os.listdir(ser)
    if len(ff)==0:
        log.warning('Empty Serie :  %s',ser)
        return ff
    
    ff.sort()
    isdicom=False
    
    if first==1:
        thefile = ff[0]
        while True:
            try:
                ps=dicom.read_file(os.path.join(ser,thefile))
                break
            except:
                if not thefile.search("dicom_info"):
                    print thefile + "  is not DICOM"
                del ff[0]
                if len(ff)==0:
                    log.warning('Empty Serie :  %s',ser)
                    return ff
                thefile = ff[0]
                pass
                
        
#        while (thefile.find("diffusion") > -1 or thefile.find("dicom_info")>-1) and isdicom:
#            del ff[0]            
#            thefile = ff[0]
            
    if first==0:
        thefile = ff[-1]
            
        while thefile.find("diffusion") > -1 or thefile.find("dicom_info")>-1:
            del ff[-1]
            thefile = ff[-1]

    thefile = os.path.join(ser,thefile)
    return thefile
    
def get_all_dicom_file(ser):

    ff = os.listdir(ser)
    if len(ff)==0:
        log.warning('Empty Serie :  %s',ser)
        return ff
    
    #print("ser list %d from %s",len(ff),ser)
    #print ff[0]
    
    kdel = []
    kind = 0
    
    newff=[]
    for thefile in ff:
        if thefile.find("diffusion") > -1 or thefile.find("dicom_info")>-1:
            kdel.append(kind)
            kind=kind+1
        else:
            newff.append(thefile)
    kdel.reverse()
    for kk in kdel:
        del ff[kk]
    
    #print("ser list %d from %s",len(ff),ser)
    #print ff[0]
    #les 2 marche ff ou newff 
    return newff
    
def separate_exam_series(series_dir):

    series_dir = filter(os.path.isdir,series_dir)
    
    ser_ok=[]
    actime=[]
    acdate=[]

    for ser in series_dir :
        thefile = get_first_dicom_file(ser,1)
        if len(thefile)==0:
            continue
        ps=dicom.read_file(thefile)
        
        if not 'ImageType' in ps :
            log.warning("Oups No imageType skiping ser %s",ser)
            continue
        
        if 'FA' in ps.ImageType or 'DERIVED' in ps.ImageType or 'OTHER' in ps.ImageType or \
        'ADC' in ps.ImageType or 'TENSOR' in ps.ImageType or 'TRACEW' in ps.ImageType \
        or 'FM' in ps.ImageType or 'FSM' in ps.ImageType  or 'Service Patient' in ps.PatientsName \
        or 'MOCO' in ps.ImageType :
            continue
        
        if len(ps.dir("AcquisitionDate"))==0:
            if len(ps.dir("StudyDate"))==0:
                log.warning("STrange dicom file %s has no tag Acquisition Date and non Study dateskiping serie",thefile)            
                continue
            else:
                acdate.append(ps.StudyDate)
                actime.append(ps.SeriesTime)  #I do not know why the Acquisition Time is bad for series where AcquisitionDate missing
        else:
            acdate.append(ps.AcquisitionDate)
            actime.append(ps.AcquisitionTime)  
     
        ser_ok.append(ser)
        
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

def get_exam_information(in_dir,verbose=True):
    dicinfo=[]
    if type(in_dir) is not list:
        in_dir = [in_dir]

    if verbose:
        log.info("Searching infon in %d dirs : %s \n",len(in_dir),in_dir)    
    
    for adir in in_dir :        
        series_dir = c.get_subdir_regex(adir,'^S')
        if len(series_dir)==0:
            msg = "REMOVE : %s has no series dir"%(adir)
            log.warning(msg)
            continue

        series_list = separate_exam_series(series_dir)
        for nbexam in range(len(series_list)):
            series_dir = series_list[nbexam]
            
            first_file = get_first_dicom_file(series_dir[0],1)

            last_dir = series_dir[-1]
            last_file = get_first_dicom_file(last_dir,0)
            p1=dicom.read_file(last_file)
            
            ff = get_all_dicom_file(last_dir)
            #test if last_file is the last dicom (instance number) should be the number of file
            #sometime (PROTO_MOMIC/MOMIC_COUAD_38) the last volume is sended first ...

            if p1.InstanceNumber != len(ff):
                #print "taking first file as last"
                last_file = os.path.join(last_dir,ff[0])
                print last_file
                
                
                p1=dicom.read_file(last_file)
                if len(p1.dir('ScanningSequence')) == 0:
                    p1.ScanningSequence='SPECTRO'
                    #print 'arrrrggg'

                if p1.InstanceNumber != len(ff):
                    if p1.ScanningSequence == 'GR rrr': #GRE
                        pass
                    elif p1.ScanningSequence == 'SE rrr': #spin echo anatomic
                        pass
                    else :
                        log.info("looking at all file in %s file %d / %d",last_dir,p1.InstanceNumber,len(ff))
                        find_max=False
                        imax=0
                        for f in ff:
                            p=dicom.read_file(os.path.join(last_dir,f))
                            #print "Inum %d t: %s" % (p.InstanceNumber,p.AcquisitionTime)
                            if p.InstanceNumber > imax:
                                imax=p.InstanceNumber
                                ffmax = f
                            if imax == len(ff):
                                break
                        
                        last_file = os.path.join(last_dir,ffmax)
                        
                        if imax != len(ff):
                            log.warning(" Serie %s : %s  Instance number %d but %d files ",last_dir ,p1.ScanningSequence,imax,len(ff))

            dic = get_dicom_exam_info(first_file,last_file)
            dic["dicom_dir"] = adir
            dicinfo.append(dic)        

            if verbose:
                log.info("%s \tdate: %s  \tdur : %d \t first %s \t last: %s ",dic["PatientsName"],dic["AcquisitionTime"],\
                dic["ExamDuration"],dic["FirstSerieName"],dic["LastSerieName"])
    
    #            print "%s \tdate: %s  \tdur : %d \t durlast : %d - %d = %d \t last: %s \t(%s:%s=%s)" % (dic["PatientsName"],dic["AcquisitionDate"],\
    #            dic["ExamDuration"],dd["ExamDuration"],dd["LastSerieDuration"]\
    #            ,int(dd["ExamDuration"])-dd["LastSerieDuration"],dic["LastSerieName"]\
    #            ,dd["Fi"],dd["Li"],len(ff))
    
                #print " %s : %s numfile %d" % (dd["Fi"],dd["Li"],len(ff))
                #print last_filefirst
    
    if verbose:
        da=[]
        du=[]
        for d in dicinfo:
            da.append(d["AcquisitionTime"].year)
            du.append(d["ExamDuration"])
        nda = np.array(da,np.int16)
        ndu = np.array(du,np.int16)
        [nu,ii,indu] = np.unique(nda,True,True)
        for k in range(ii.size):
            log.info("annee %d \t%d sujet\t%f heure",nda[ii[k]],len(ndu[indu==k]),np.sum(ndu[indu==k])/60.)

    return dicinfo
                 
         
  
def get_dicom_exam_info(dic1,dic2):
    """
    get the dicom exam information from the first file and compute the exam duration 
    as the diference between acquisition time of the second and first dicom file
    """
    
    dicinfo={}
    field_to_read = ("ManufacturersModelName","StudyDescription","PatientsName","PatientsSex","PatientsAge","PatientsWeight",\
    "PatientsBirthDate", "StudyTime","AcquisitionTime","SoftwareVersions")

    p1=dicom.read_file(dic1)
    p2=dicom.read_file(dic2)

    for ff in field_to_read:
        dicinfo[ff] = p1.get(ff)

    #remove no character strings
    dicinfo["StudyDescription"] = re.sub('\W','_',dicinfo["StudyDescription"])
    dicinfo["PatientsName"] = re.sub('\W','_',dicinfo["PatientsName"])
    
    #appen date to SacisitionTime and format time
    if len(p1.dir("AcquisitionDate"))==0:
        dstr = p1.StudyDate
        tstr = p1.SeriesTime  #I do not know why the Acquisition Time is bad for series where AcquisitionDate missing

    else:
        dstr = p1.AcquisitionDate
        tstr = dicinfo["AcquisitionTime"]

    
    #dicinfo["AcquisitionTime"] = dstr[0:4] + "-" + dstr[4:6] + "-" + dstr[6:] + " " + tstr[0:2] + ":" + tstr[2:4] + ":" + tstr[4:6]
    dicinfo["AcquisitionTime"] = datetime.datetime(int(dstr[0:4]),int(dstr[4:6]),int(dstr[6:]),int(tstr[0:2]),int(tstr[2:4]),int(tstr[4:6]))

    dicinfo["PatientsWeight"] = int(dicinfo["PatientsWeight"])
    
    dstr = p1.PatientsBirthDate
    dicinfo["PatientsBirthDate"] = datetime.date(int(dstr[0:4]) , int(dstr[4:6]), int(dstr[6:8]))

    if "PatientsAge" in dicinfo:
        pa = dicinfo["PatientsAge"]
        #if pa[-1]=='Y':
        if not pa[-1].isdigit() : 
            pa = pa[0:-1]
        dicinfo["PatientsAge"] = int(pa)

    if p2.has_key(0x051100a):
        dur = get_series_duration_from_siemens_tag(p2[0x0051,0x100a].value)
        
    else:
        dur = get_series_duration_from_file(dic2)
    
    if len(p2.dir("AcquisitionDate"))==0 or len(p2.dir("AcquisitionTime"))==0:
        deltadur = get_second_from_time_str(p2.SeriesTime) - get_second_from_time_str(p1.SeriesTime)
    else:
        deltadur = get_second_from_time_str(p2.AcquisitionTime) - get_second_from_time_str(p1.AcquisitionTime)
        
    if deltadur<0:
        msg = "ERROR Negative acquisition time for %s compare to %s" % (os.path.dirname(dic2),os.path.basename(os.path.dirname(dic1) ))
        deltadur = math.fabs(deltadur)
        log.error(msg)
    
    dicinfo["ExamDuration"] = int(math.ceil((deltadur + dur)/60.))
    
    dicinfo["LastSerieName"] = os.path.basename(os.path.dirname(dic2))
    dicinfo["FirstSerieName"] = os.path.basename(os.path.dirname(dic1))
    dicinfo["LastSerieDuration"] = dur
    
    #for the CENIR database we need a field rid =1 for trio and 19 for Verio
    #and a fiel eid : StudyDescription without PROTO_ neither VERIO_
    if p1.ManufacturersModelName.startswith("Verio"):
        dicinfo["rid"] = 19        
    elif p1.ManufacturersModelName.startswith("TrioTim"):
        dicinfo["rid"] = 1
    elif p1.ManufacturersModelName.startswith("Prisma_fit"):
        dicinfo["rid"] = 1        
    else:
        raise NameError('this Dicom file is not from TrioTim neither Verio')
        
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
    
def get_second_from_time_str(tstr):
    return int(tstr[0:2])*3600 + int(tstr[2:4])*60 + int(tstr[4:6])

def get_series_duration_from_siemens_tag(serie_time):
    """
    private tag [0x0051,0x100a] contain an string with the acquisition time ex TA 03:50*3
    """
    if serie_time[5]==".":
        dur=float(serie_time[3:5])+1
    elif serie_time[5]==":":
        dur=float(serie_time[3:5])*60 + float(serie_time[6:8])
    else:
        log.error("SHOULD NOT HAPPEND")
    ind = serie_time.find("*")
    if ind>-1:
        multfac = float(serie_time[ind+1:])
    else:
        multfac = 1
        
    dur = dur*multfac;
    return dur
    
def get_series_duration_from_file(dic_file):
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
        log.warning( "Arg no lTatalScanTimeSec in %s",dic_file)
        return 0
    
    #for one dicom file thhe lTotalScanTimeSec was present before without any value ...
    try:
        scan_time = int(out[ind+2])
    except ValueError:
        ind = out.index("lTotalScanTimeSec",ind+1)
        scan_time = int(out[ind+2])
    
    return scan_time
def find_double_exam(Ei):
    log.info('\n\n *******LOKING FOR DOUBLED EXAM*******')
    for k in range(len(Ei)):
        oneE = Ei[k]
        for kk in range(k+1,len(Ei)):
            otherE = Ei[kk]
            if oneE["AcquisitionTime"] == otherE["AcquisitionTime"] and oneE["rid"] == otherE["rid"] :
                log.info('Find a double exam')
                log.info(oneE["StudyDescription"]+" Suj "+oneE["PatientsName"] + " dir : " + oneE["dicom_dir"])
                log.info(otherE["StudyDescription"]+" Suj "+otherE["PatientsName"]+ " dir : " + otherE["dicom_dir"])
                
                ser1 = c.get_subdir_regex(oneE["dicom_dir"],'^S')
                ser2 = c.get_subdir_regex(otherE["dicom_dir"],'^S')
                if len(ser1)!=len(ser2):
                    log.warning('Different number of series')
                    
                ffile1 = get_first_dicom_file(ser1[0],1)
                ffile2 = get_first_dicom_file(ser2[0],1)
                
                if os.path.getmtime(ffile1)>os.path.getmtime(ffile2):
                    log.info('The first listed was created %d hours after  %s',(os.path.getmtime(ffile1)-os.path.getmtime(ffile2))/3600,ffile1)
                else:
                    log.info('The last listed was created %d hours after  %s',(os.path.getmtime(ffile2)-os.path.getmtime(ffile1))/3600,ffile2)
                    
                    
                                
                
    log.info('done\n')
        
def update_relecture(test=False,verbose=False):

    con = mdb.connect(host = 'mysql.lixium.fr', user = 'cenir', passwd =  'y0p4l4sql', db = 'cenir')
    cur = con.cursor(mdb.cursors.DictCursor)
    cur2 = con.cursor()

    #dd = c.get_subdir_regex('/home/cenir/Le_suivi_des_relectures_du_CENIR/SAMIA',['.*','.*'])
    dd = c.get_subdir_regex('/home/cenir/Le_suivi_des_relectures_du_CENIR/SAMIA','.*')
    xf = c.get_subdir_regex_files(dd,'xls')

    sqlcmds = "SELECT * from gg_examen WHERE "

    for xxf in xf:
        print "working on " + xxf
        suj = c.readxls_relecture_files(xxf)

        if verbose :        
            print "found"
            for v in suj:
                print ' comment | ' + v['comment'] + ' | ' + v['proto']+' sujname '+v['sujname']
        
        for v in suj:            
            sqlcmd = "%s eid = '%s' AND PatientsName = '%s'" % (sqlcmds,v['proto'],v['sujname'])
            #print sqlcmd
            cur.execute(sqlcmd)        
            
            if cur.rowcount >= 1 :
                for nbline in range(cur.rowcount):
                    data = cur.fetchone()
                    if nbline>0 :
                        print "%d iem suj foun for %s %s"%(nbline+1,v['proto'],v['sujname'])
                    if test is False:
                        sqlcmd = "UPDATE gg_examen SET relu=1,relu_par='samia' WHERE crid=%d "% (data['crid'])
                        cur2.execute(sqlcmd)
                        con.commit()
                        
            elif cur.rowcount == 0 :
                print "FUCK no exame %s %s in database" % (v['proto'],v['sujname'])
            
    con.close()

if __name__ == '__main__':
    
    from optparse import OptionParser
    usage= "usage: %prog [options] select dir of dicom exam with the option and insert them into cenir SDB (gg_examen) "

    # Parse input arguments
    parser=OptionParser(usage=usage)
    #parser.add_option("-h", "--help", action="help")
    parser.add_option("-r","--rootdir", action="store", dest="rootdir", default='/export/dataCENIR/dicom/dicom_raw/',
                                help="full path to the directorie of protocol default='/export/dataCENIR/dicom/dicom_raw/'")
    parser.add_option("-p","--proto_regex", action="store", dest="proto_reg", default='.*',
                                help="regular expression to select protocol dir default='.*' ")
    parser.add_option("-s","--suj_regex", action="store", dest="suj_reg", default='.*',
                                help="regular expression to select protocol dir default='.*' ")
    parser.add_option("-d","--days", action="store", dest="nb_days", default=0,type="int",
                                help="get only exam in rootdir newer than n days  ")
    parser.add_option("-l","--from_logfile", action="store_true", dest="from_logfile", default=False,
                                help="will research exam newer than the last time it has be runed ")
    parser.add_option("-b","--data_base", action="store_true", dest="do_db",default=False,
                                help="commit the exam to the cenir database ")
    parser.add_option("--twice", action="store_true", dest="twice",default=False,
                                help="if define will to twice the DB update ")
    parser.add_option("-t","--test_data_base", action="store_true", dest="test_db",default=False,
                                help="Just write the log of what changes should be donne in the cenir database (for the selected exams). It won't take the -b option ")
    parser.add_option("-L","--LogFile", action="store", dest="logFile", default='/servernas/nasDicom/log_update_db.log',
                                help="full path to the log file default='/servernas/nasDicom/log_update_db.log'")
    parser.add_option("-i","--do_only_insert", action="store_true", dest="do_only_insert",default=False,
                                help="it will only insert new exam in the cenir database (it will not modify existing record) ")
    parser.add_option("-f","--find_double", action="store_true", dest="find_double",default=False,
                                help="This will print duplicate exam in the given search ")
    
    (options, args) = parser.parse_args()


    fhdl = logging.FileHandler(filename = options.logFile,mode='a')
    fhdl.setFormatter(formatter)
    log.addHandler(fhdl)
    log.setLevel(logging.INFO)
    
    console = logging.StreamHandler()
    console.setFormatter(formatter)


#    fhdlw = logging.FileHandler(filename = options.logFile+".warning",mode='a')
#    fhdlw.setFormatter(formatter)
#    logw.addHandler(fhdlw)
#    logw.setLevel(logging.WARNING)

    #parse_exam_in_dicom_raw()
    if options.nb_days:
        d = c.get_all_newer_subdir(options.rootdir,1,nbdays=options.nb_days)
    elif options.from_logfile :
        import datetime as da
        import time
        today = da.datetime.today()    
        logtime =  da.datetime.fromtimestamp(os.path.getmtime("/servernas/nasDicom/log_update_db.log"))
        nbdays = today - logtime;
        nbdays = nbdays.days + 1
        
        log.info("\n ********************************\n Searching exam older than %s days \n",(nbdays))
        d = c.get_all_newer_subdir(options.rootdir,1,nbdays=nbdays)
        
    else:
        d = c.get_subdir_regex(options.rootdir,[options.proto_reg,options.suj_reg],verbose=True)
    
    Ei = get_exam_information(d)

    if options.find_double :
        find_double_exam(Ei)
        
    if options.test_db :
        log.info("\n\n**************************\nChecking CENIR data base change on the selected exams (but no change)\n")
        update_exam_sql_db(Ei,test=True,do_only_insert=options.do_only_insert)
    elif options.do_db :
        log.info("\nPERFORMING Database update\n")
        update_exam_sql_db(Ei,do_only_insert=options.do_only_insert) 
        if options.twice :
            log.info("\nPERFORMING Database update A second Time \n ")
            update_exam_sql_db(Ei,do_only_insert=options.do_only_insert) 
            
  

