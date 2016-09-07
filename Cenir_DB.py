#!/usr/bin/env python


import datetime
import os
from do_common import alpha_num_str_min

def add_options(parser):

    parser.add_option("--sql_doublon", action="store_true", dest="sql_doublon",default=False,
                                help="find sql doublon base on the sql database ")
    parser.add_option("--db_name", action ="store",dest="db_name",default='cenir',
                              help="Name of the database default cenir")
    parser.add_option("--db_host", action ="store",dest="db_host",default='10.5.90.15',
                              help="hostname of the database default 10.5.90.15")
                              
                              
                              
    return parser

                              
class Cenir_DB:
    'Class to collected dicom information from dicom dirs'    
    
    def __init__(self,verbose=True,log=0,opt=None):
        self.verbose = verbose
        
        self.log = log
        self.db_exam_field = ("ExamName","EUID","ExamNum","MachineName","PatientsName","AcquisitionTime","StudyTime","ExamDuration","PatientsBirthDate","PatientsAge",\
        "PatientsSex","PatientsWeight","SoftwareVersions","FirstSerieName","LastSerieName","dicom_dir")
        self.db_examID_field = ("ExamName","EUID","ExamNum","MachineName","PatientsName","AcquisitionTime","StudyTime","PatientsBirthDate","PatientsAge",\
        "PatientsSex","PatientsWeight","SoftwareVersions")
        
        #Pour le cas GE
        self.db_GEexamID_field = ("ExamName","EUID","ExamNum","MachineName","PatientsName","StudyTime")
        
        
        if opt is not None:
            self.db_name = opt.db_name
            self.db_host = opt.db_host


    
    def open_sql_connection(self):
        import MySQLdb as mdb
        #con = mdb.connect(host = '134.157.205.8', user = 'cenir', passwd =  'pschitt', db = self.db_name)
        con = mdb.connect(host = self.db_host, user = 'cenir', passwd =  'pschitt', db = self.db_name)
        cur = con.cursor(mdb.cursors.DictCursor)
        
#        self.con = con
#        self.cur = cur
#        self.cur2 = con.cursor()
        
        return con,cur

    def open_sql_connection_lixum(self):
        import MySQLdb as mdb
        con = mdb.connect(host = 'mysql.lixium.fr', user = 'cenir', passwd =  'y0p4l4sql', db = 'cenir')
        cur = con.cursor(mdb.cursors.DictCursor)
        return con,cur

    def update_exam_sql_db(self,Ei,test=False,do_only_insert=False):
    
        """
        input a list of exam dir: get the exam info and submit to the cenir db if the line does not exist
        or if some parameter has change
        """
        con,cur = self.open_sql_connection()
        cur2 = con.cursor()
        
        for E in Ei:
            
            exist_line = self.get_sql_exam_line(E,cur)
            if len(exist_line)>0 : 
                self.log.info("Skiping (because exist) Exam insert of pat=%s : proto=%s : date=%s ",E['PatientsName'],E['ExamName'],E['AcquisitionTime'])
                examID = exist_line['Eid']
                
                insert_serie=0
                if test is False :
                    for dicser in E["serie_info"] :
                        dicser["ExamRef"] = int(examID)
                        exist_UID_serie = self.get_sql_select_line('serie','SUID',dicser['SUID'],cur)
                       
                        if len(exist_UID_serie)==0:
                            self.log.info("SQL INSERT serie %s num %d", dicser['SName'] , dicser['SNumber'])
                            #print self.get_sql_serie_insert_cmd(dicser)
                            cur2.execute(self.get_sql_serie_insert_cmd(dicser))    
                            con.commit()
                            insert_serie+=1
                        else :
                            exist_serie = self.get_sql_select_serie_line(dicser,cur,exclude_key=['Affine','AcqTime','nifti_dir','SliceTime','SeqName','TE'])
                            if len(exist_serie)==0:
                                self.log.info("SQL UPDATE serie %s num %d", dicser['SName'] , dicser['SNumber'])
                                cur2.execute(self.get_sql_serie_update_cmd(dicser,exist_UID_serie['Sid']))    
                                con.commit()

                            else:                                    
                                self.log.info("Skiping because exist Ser %s S %d dic:%s",dicser['SName'] , dicser['SNumber'],dicser['dicom_sdir'])
                                
                if insert_serie>0:
                    self.log.info("Updating Exam time and duration from series info")
                    self.update_Exam_duration_from_sql(examID,con,cur)

            else : 
                
                self.log.info("SQL INSERT of pat=%s : proto=%s : date=%s ",E['PatientsName'],E['ExamName'],E['AcquisitionTime'])
    
#                #check if there is the same subject the same day WHERE `AcquisitionTime` LIKE '2013-08-06%'
#                sqlcmd = "SELECT * from exam WHERE MachineName = '%s' AND AcquisitionTime LIKE '%s%%' AND PatientsName='%s'" % (E["MachineName"],E['AcquisitionTime'].date(),E["PatientsName"])
#                cur.execute(sqlcmd)
#                if cur.rowcount == 1 :
#                    data = cur.fetchone()
#                    difftime = data["AcquisitionTime"]-E['AcquisitionTime']
#                    difftimesecond = difftime.days*86400 + difftime.seconds #si negative il met -1 jour et les second correspondante
#                    self.log.warning("New insert BUT already the same subject the same daye  :  %d second before",difftimesecond)
                
                if test is False :
                    cur2.execute(self.get_sql_insert_cmd(E))
                    con.commit()
                    examID =  cur2.lastrowid
                    
                    for dicser in E["serie_info"] :
                        dicser["ExamRef"] = int(examID)
                        #print get_sql_serie_insert_cmd(dicser)
                        cur2.execute(self.get_sql_serie_insert_cmd(dicser))
                    con.commit()
                        
        
        con.close()
    def find_sql_doublon(self):
        #self.remove_lixium_duplicate_exam()
        #self.check_dicom_remove()        
        self.remove_duplicate_exam()
        #self.remove_duplicate_exam_correct()
        #self.remove_duplicate_serieUID()
        #self.remove_duplicate_serie()
        
    def check_dicom_remove(self):
        con,cur = self.open_sql_connection()
        sqlcmd="select Eid,  ExamName, PatientsName, ExamName, dicom_dir from exam where 1;";
        ff = open('./remove_missing_dicom_dir.sh','w+')
        print sqlcmd
        cur.execute(sqlcmd)
        rows = cur.fetchall()
        self.log.info('checking %d rows',len(rows))

        for row in rows:
            if os.path.isdir(row['dicom_dir']) is False:
                strinfo = '\nFind missing dicom E:%s  %s %s %s'%(row['Eid'],row['ExamName'],row['PatientsName'],row['dicom_dir'])
                self.log.info(strinfo)
                ff.write("delete from exam where Eid=%d;\n"%(row['Eid']))

        con.close()
        ff.close()
      

    def remove_duplicate_serieUID(self):
        con,cur = self.open_sql_connection()
        
        #find double exams
        self.log.info('Looking for serieUID duplicate')
        
        sqlcmd="select count(*) as doublon, SUID from ExamSeries group by SUID having count(*)>1;  "
        cur.execute(sqlcmd)
        rows = cur.fetchall()

        ffs= [open('./remove_series_sql.sh', 'w+'),              
              open('./reimport_series.sh', 'w+'),
              open('./check_sereies.sh', 'w+')]

        for row in rows:
            sqlcmd = "select ExamRef, dicom_dir, dicom_sdir from ExamSeries where SUID='%s' "%(row['SUID'])
            cur.execute(sqlcmd)
            drows = cur.fetchall()
            if len(drows)==2:
                if drows[0]['ExamRef'] == drows[1]['ExamRef'] :
                    if drows[0]['dicom_dir'] == drows[1]['dicom_dir']:
                        if drows[0]['dicom_sdir'] == drows[1]['dicom_sdir']:                        
                            self.log.info('Duplicate same dir \n delete from db reimport')
                            ffs[0].write("delete from exam where Eid=%s;\n"%(drows[0]['ExamRef']))
                            ffs[1].write("do_dicom_series_DB.py -c import --input_dir=%s;\n"%(drows[0]['dicom_dir']))
                        else:                        
                            self.log.info('Duplicate but different  sdir \n')
                            ffs[1].write("check %s series %s and %s have same uid\n"%(drows[0]['dicom_dir'],drows[0]['dicom_sdir'],drows[1]['dicom_sdir']))
                    else:
                        self.log.info('Duplicate but different exam dicom dir \n')
                        ffs[1].write("\n\n same uid \n %s \n %s \n\n"%(drows[0]['dicom_dir'],drows[1]['dicom_dir']))    
                            
                    #self.log.info('Duplicat serie from same Eid %s \n dicom1 %s/%s \n dicom2 %s/%s',drows[0]['Eid'],drows[0]['dicom_dir'],drows[0]['dicom_sdir'],drows[1]['dicom_dir'],drows[1]['dicom_sdir'])
                else:
                    if drows[0]['dicom_dir'] == drows[1]['dicom_dir']:
                        self.log('same dicomdir but different exam ...')
                        ffs[0].write("delete from exam where Eid=%s;\n"%(drows[0]['ExamRef']))
                        ffs[0].write("delete from exam where Eid=%s;\n"%(drows[1]['ExamRef']))
                        ffs[1].write("do_dicom_series_DB.py -c import --input_dir=%s;\n"%(drows[0]['dicom_dir']))
                    else:
                        self.log.warning('DIFERENT Eid %s %s and Dicom dir',drows[0]['ExamRef'],drows[1]['ExamRef'])
                    
            else:
                self.log.warning("WARNING TODO MORE THAN 2 DUPLICATE for \nSUID='%s'\n",row['SUID'])
                    
            
        for ff in ffs :
            ff.close()
        con.close()
        self.log.info('Done')
        
        
    def remove_duplicate_serie(self):
        con,cur = self.open_sql_connection()
        
        #find double exams
        sqlcmd="select Eid, Sid, PatientsName, ExamName, dicom_dir ,nifti_dir, dicom_sdir from ExamSerie where nifti_volumes like 'duplicate_equal_data%'"
        #poru la spectro select count(*) as doublon, s.* from serie s group by  AcqTime , nifti_dir , SName, SNumber  having count(*)>1
        #duplicate avec different dicom 
        #select count(*) as doublon, s.* from serie s where nifti_dir is not NULL group by   nifti_dir , SName, SNumber  having count(*)>1 
        #plus general
        #select count(*) as doublon, s.* from ExamSerie s group by Eid, SName, SNumber  having count(*)>1 \g
        
        cur.execute(sqlcmd)
        rows = cur.fetchall()
        self.log.info('looking for serie duplicate (close acquisition time)')
        if len(rows)==0:
            self.log.info('Did not find Any  duplicate series double')
        else:
            ffs= [open('./remove_series_doublon_cluster.sh', 'w+'),              
                  open('./remove_series_doublon_dicom_raw.sh', 'w+'),
                  open('./remove_series_doublon_AC.sh', 'w+'),
                  open('./remove_series_sql.sh','w+')]
            
            dout = ['/export/home/romain.valabregue/img/doublon_dicom',
                    '/nasDicom/doublon_dicom',
                    '/icm/donnees_irm/PROTO_FINI/doublon_dicom']
            din  = ['/export/home/CENIR/dicom_raw',
                    '/nasDicom/dicom_raw',
                    '/icm/donnees_irm/PROTO_FINI/dicom_raw']
            self.log.info('%d duplicate series ',len(rows))
            
            for row in rows:
                strinfo = '\nFind serie doublon E:%s S:%s %s %s %s'%(row['Eid'],row['Sid'],row['ExamName'],row['ExamName'],row['dicom_sdir'])
                dicdir = row['dicom_dir']
                serdir = row['dicom_sdir']
                pp,suj = os.path.split(dicdir)
                pp,prot = os.path.split(pp)
    
                ffs[3].write(( "delete from serie where Sid=%s ; \n"%(row['Sid'])))
                for k in range(len(dout)):
                    doutdir = os.path.join(dout[k],prot,suj)
                    dindir  = os.path.join(din[k],prot,suj)                        
                    ffs[k].write(("mkdir -p %s; cd %s; mv %s %s \n"%(doutdir,dindir,serdir,doutdir)))                
                                
                strinfo += "\n\n"
                self.log.info(strinfo)
            
            for ff in ffs :
                ff.close()
        con.close()
        # pour enlever les exam siemens ...   delete from gg_examen  where PatientsBirthDate is NULL;
        
    def remove_lixium_duplicate_exam(self):
        conl,curl = self.open_sql_connection_lixum()
        con,cur = self.open_sql_connection()
        
        self.log.info('Looking for lixium sql Exam duplicate')
        
        sqlcmd="select count(*) as doublon, e.* , substr(AcquisitionTime,1,10) as ttime from gg_examen e where e.rid in (1,19) AND substr(AcquisitionTime,1,4) like '2014'  group by  ttime ,rid, PatientsName having count(*)>1;"
        curl.execute(sqlcmd)
        rows = curl.fetchall()
        for row in rows:
            sqlcmd = "select * from gg_examen where PatientsName like '%%%s%%' and substr(AcquisitionTime,1,0) like '%s'"%(row['PatientsName'],row['ttime'])
            #print sqlcmd
            curl.execute(sqlcmd)
            
            #print 'Patient  %s has %d line' %(row['PatientsName'],curl.rowcount)
            
            sqlcmd = "select * from exam where PatientsName like '%%%s%%' and  substr(AcquisitionTime,1,10) like '%s'"%(row['PatientsName'],row['ttime'])
            cur.execute(sqlcmd)
            
            if cur.rowcount==1:
                print 'there may be a problem for ' + row['PatientsName']
            if cur.rowcount==0:
                print 'Can not find ' + row['PatientsName']
            
        con.close()
        conl.close()

    def remove_duplicate_exam(self):
        con,cur = self.open_sql_connection()
        import common as c 
         
        #pour voir les exam partiellement duplique (quelque series)
             # select count(*), Eid, dicom_dir,dicom_sdir , SName from ExamSerie group by SNumber, AcqTime, MachineName having count(*)>1;

        #find double exams
        #sqlcmd="select count(*) as doublon, e.* from exam e group by  AcquisitionTime ,MachineName having count(*)>1"
        #sqlcmd="select count(*) as doublon, e.* , substr(AcquisitionTime,1,17) as ttime from exam e group by  ttime ,MachineName having count(*)>1"
        sqlcmd="select count(*) as doublon, e.* , substr(AcquisitionTime,1,19) as ttime from exam e group by  ttime ,MachineName having count(*)>1"
        cur.execute(sqlcmd)
        rows = cur.fetchall()
        self.log.info('Looking for sql Exam duplicate')
        
        if len(rows)==0:
            self.log.info('Did not find Any exam double')
        else:
            f1=open('./remove_exam_doublon_cluser_nifti.sh', 'w+')
            f11=open('./remove_exam_doublon_cluser_dicom.sh', 'w+')
            f2=open('./remove_exam_doublon_dicom_raw.sh', 'w+')
            f3=open('./remove_exam_doublon_AC.sh', 'w+')
            f4 = open('./remove_exam_sql','w+')
            
            self.log.info('%d exam doublons',len(rows))
            for row in rows:
                #sqlcmd = "select  * from exam where AcquisitionTime='%s' and MachineName='%s'"%(row['AcquisitionTime'],row['MachineName'])
                sqlcmd = "select  * from exam where AcquisitionTime = '%s' and MachineName='%s'"%(row['ttime'],row['MachineName'])
                cur.execute(sqlcmd)
                drows = cur.fetchall()
                timedir = []
                strinfo = '\nFind %d doublon '%(row['doublon'])
                #correction 01 2016 getmtime -> getctime
                for drow in drows:
                    #timedir.append(os.path.getctime(drow['dicom_dir']))
                    # if modification time from directories it may not work ... 
                    #timedir.append(os.path.getmtime(serdir[0]))
                    #timedir.append(drow['EUID']) do not work
                    serdir = c.get_subdir_regex(drow['dicom_dir'],'^S01');
                    files = c.get_subdir_regex_files(serdir[0],'.*dic')                    
                    timedir.append(os.path.getmtime(files[0]))
                    
                    strinfo+='\n  suj (%s) : %s dicom_dir : %s'%(drow['Eid'],drow['PatientsName'],drow['dicom_dir'])
                
                if drows[0]['dicom_dir'] == drows[1]['dicom_dir']:
                    strinfo += '\nWARNING SAME DICOM DIR Please reimport'
                    self.log.info(strinfo)
                    continue
    
                sind = sorted(range(len(timedir)), key=timedir.__getitem__)
                strinfo += '\n the last created is line %d'%(sind[-1]+1)
    
                #find series of the first
                sqlcmd = "select count(*) as nbs ,sum(nb_dic_file) as nbd from serie s where ExamRef='%d'"%(drows[sind[0]]['Eid'])
                cur.execute(sqlcmd)
                serbad = cur.fetchone()
                sqlcmd = "select count(*) as nbs , sum(nb_dic_file) as nbd from serie s where ExamRef='%d'"%(drows[sind[-1]]['Eid'])
                cur.execute(sqlcmd)
                serok = cur.fetchone()
    
                if serok['nbd'] == serbad['nbd']:
                    strinfo+='\nsame number of dicom files'
                else :
                    strinfo+='\nWARNING different number of dicom files'
                    strinfo+='\n  the bad has %d files'%(serbad['nbd'])
                    strinfo+='\n  the ok  has %d files'%(serok['nbd'])
                
                for ind in sind[:-1]:
                    dicdir = drows[ind]['dicom_dir']
                    pp,suj = os.path.split(dicdir)
                    pp,prot = os.path.split(pp)
                    strinfo+="\nMoving cd %s ;cd %s; mv %s"%(pp,prot,suj)
    
                    #f1.write(('cd %s;cd %s; mv %s /export/home/romain.valabregue/img/doublon_dicom/\n'%(pp,prot,suj)))
                    f11.write(('cd /export/dataCENIR/dicom/dicom_raw/;cd %s; mv %s /export/dataCENIR/dicom/doublon_dicom/\n'%(prot,suj)))
                    f2.write(('cd /nasDicom/dicom_raw/;cd %s; mv %s /nasDicom/doublon_dicom/\n'%(prot,suj)))
                    f3.write(('cd  /C2_donnees_irm/PROTO_FINI/dicom_raw;cd %s; rm -rf %s \n'%(prot,suj)))
                    
                    strinfo+= "\ndelete from exam where Eid='%s' " % (drows[ind]['Eid'])
    
                    sqlcmd = "select distinct nifti_dir  from serie s where ExamRef='%d'"%(drows[ind]['Eid'])
                    cur.execute(sqlcmd)
                    serbad = cur.fetchone()
                    if serbad['nifti_dir'] is None:
                        niftidir = None
                    else:
                        niftidir = os.path.dirname(serbad['nifti_dir'] )
                        
                        sqlcmd = "select distinct nifti_dir  from serie s where ExamRef='%d'"%(drows[sind[-1]]['Eid'])
                        cur.execute(sqlcmd)
                        serok = cur.fetchone()
                        if serok['nifti_dir'] != None:
                            niftidir_ok = os.path.dirname(serok['nifti_dir'] )                                               
                            
                            pp,suj = os.path.split(niftidir)
                            pp,prot = os.path.split(pp)
                            pp='/export/dataCENIR/dicom/nifti_raw'
                            if niftidir_ok == niftidir:
                                strinfo += "\nSTRANGE different dicom dir lead to the same nifti dir %s : do not delete"%(niftidir)
                            else :                
                                strinfo += "\ncd %s; cd %s; rm -rf %s" % (pp,prot,suj)
                                f1.write(('cd %s;cd %s; rm -rf %s\n'%(pp,prot,suj)))
                                f2.write(('cd /nasDicom/spm_raw/;cd %s; rm -rf  %s \n'%(prot,suj)))
    
                    
                    sqlcmd = "delete from exam where Eid='%s' ;\n" % (drows[ind]['Eid'])
                    f4.write(sqlcmd)
                             
                strinfo += "\n\n"
                self.log.info(strinfo)
                
            f1.close()
            f11.close()
            f2.close()
            f3.close()
            f4.close()
            
        con.close()

    def remove_duplicate_exam_correct(self):
        con,cur = self.open_sql_connection()
        import common as c 
        #pour voir les exam partiellement duplique (quelque series)
             # select count(*), Eid, dicom_dir,dicom_sdir , SName from ExamSerie group by SNumber, AcqTime, MachineName having count(*)>1;

        #find double exams
        #sqlcmd="select count(*) as doublon, e.* from exam e group by  AcquisitionTime ,MachineName having count(*)>1"
        #sqlcmd="select count(*) as doublon, e.* , substr(AcquisitionTime,1,17) as ttime from exam e group by  ttime ,MachineName having count(*)>1"
        sqlcmd="select count(*) as doublon, e.* , substr(AcquisitionTime,1,19) as ttime from exam e group by  ttime ,MachineName having count(*)>1"
        cur.execute(sqlcmd)
        rows = cur.fetchall()
        self.log.info('Looking for sql Exam duplicate')
        
        if len(rows)==0:
            self.log.info('Did not find Any exam double')
        else:
            f1=open('./remove_exam_doublon_cluser_nifti.sh', 'w+')
            f11=open('./remove_exam_doublon_cluser_dicom.sh', 'w+')
            f2=open('./remove_exam_doublon_dicom_raw.sh', 'w+')
            f3=open('./remove_exam_doublon_AC.sh', 'w+')
            f4 = open('./remove_exam_sql','w+')
            f5 = open('./remove_reimport.sh','w+')
            
            self.log.info('%d exam doublons',len(rows))
            for row in rows:
                #sqlcmd = "select  * from exam where AcquisitionTime='%s' and MachineName='%s'"%(row['AcquisitionTime'],row['MachineName'])
                sqlcmd = "select  * from exam where AcquisitionTime = '%s' and MachineName='%s'"%(row['ttime'],row['MachineName'])
                cur.execute(sqlcmd)
                drows = cur.fetchall()
                timedir = []
                strinfo = '\nFind %d doublon '%(row['doublon'])
                #correction 01 2016 getmtime -> getctime
                for drow in drows:
                    # if modification time from directories it may not work ... 
                    #serdir = c.get_subdir_regex(drow['dicom_dir'],'^S01');
                    #timedir.append(os.path.getmtime(drow['dicom_dir']))
                    #timedir.append(os.path.getmtime(serdir[0]))

                    #timedir.append(drow['EUID']) do not work
                    serdir = c.get_subdir_regex(drow['dicom_dir'],'^S01');
                    files = c.get_subdir_regex_files(serdir[0],'.*dic')                    
                    timedir.append(os.path.getmtime(files[0]))
                    
                    
                    strinfo+='\n  suj (%s) : %s dicom_dir : %s'%(drow['Eid'],drow['PatientsName'],drow['dicom_dir'])
                
                if drows[0]['dicom_dir'] == drows[1]['dicom_dir']:
                    strinfo += '\nWARNING SAME DICOM DIR Please reimport'
                    self.log.info(strinfo)
                    continue
    
                sind = sorted(range(len(timedir)), key=timedir.__getitem__)
                strinfo += '\n the last created is line %d'%(sind[-1]+1)
    
                #find series of the first
                sqlcmd = "select count(*) as nbs ,sum(nb_dic_file) as nbd from serie s where ExamRef='%d'"%(drows[sind[0]]['Eid'])
                cur.execute(sqlcmd)
                serbad = cur.fetchone()
                sqlcmd = "select count(*) as nbs , sum(nb_dic_file) as nbd from serie s where ExamRef='%d'"%(drows[sind[-1]]['Eid'])
                cur.execute(sqlcmd)
                serok = cur.fetchone()
    
                if serok['nbd'] == serbad['nbd']:
                    strinfo+='\nsame number of dicom files'
                else :
                    strinfo+='\nWARNING different number of dicom files'
                    strinfo+='\n  the bad has %d files'%(serbad['nbd'])
                    strinfo+='\n  the ok  has %d files'%(serok['nbd'])
                
                for ind in sind[:-1]:
                    dicdir = drows[ind]['dicom_dir']
                    pp,suj = os.path.split(dicdir)
                    pp,prot = os.path.split(pp)

                    if prot=='doublon_dicom':
                        strinfo+='\n this was a real doublon so delete sql %s'%(drows[ind]['Eid'])
                        sqlcmd = "delete from exam where Eid='%s' ;\n" % (drows[ind]['Eid'])
                        f4.write(sqlcmd)

                    else :                            
                        strinfo+="\nMoving cd %s ;cd %s; mv %s"%(pp,prot,suj)

                        dicdirok = drows[sind[-1]]['dicom_dir']
                        pp,sujok = os.path.split(dicdirok)                 
                        protok = drows[sind[-1]]['ExamName']                 
                        
                        #f1.write(('cd %s;cd %s; mv %s /export/home/romain.valabregue/img/doublon_dicom/\n'%(pp,prot,suj)))
                        f11.write('cd /export/dataCENIR/dicom/doublon_dicom/; mv %s /export/dataCENIR/dicom/dicom_raw/%s/\n'%(sujok,protok))
                        f11.write(('cd /export/dataCENIR/dicom/dicom_raw/;cd %s; mv %s /export/dataCENIR/dicom/doublon_dicom/\n\n'%(prot,suj)))
                        f5.write('do_dicom_series_DB.py -c import_db --input_dir=/export/dataCENIR/dicom/dicom_raw/%s/%s\n'%(protok,sujok))
                        f2.write(('cd /nasDicom/doublon_dicom/; mv %s /nasDicom/dicom_raw/%s/\n'%(sujok,protok)))
                        f2.write(('cd /nasDicom/dicom_raw/;cd %s; mv %s /nasDicom/doublon_dicom/\n'%(prot,suj)))
                        f3.write(('cd  /C2_donnees_irm/PROTO_FINI/dicom_raw;cd %s; rm -rf %s \n'%(prot,suj)))
                        
                        strinfo+= "\ndelete from exam where Eid='%s' " % (drows[ind]['Eid'])
        
                        sqlcmd = "select distinct nifti_dir  from serie s where ExamRef='%d'"%(drows[ind]['Eid'])
                        cur.execute(sqlcmd)
                        serbad = cur.fetchone()
                        if serbad['nifti_dir'] is None:
                            niftidir = None
                        else:
                            niftidir = os.path.dirname(serbad['nifti_dir'] )
                            
                            sqlcmd = "select distinct nifti_dir  from serie s where ExamRef='%d'"%(drows[sind[-1]]['Eid'])
                            cur.execute(sqlcmd)
                            serok = cur.fetchone()
                            if serok['nifti_dir'] != None:
                                niftidir_ok = os.path.dirname(serok['nifti_dir'] )                                               
                                
                                pp,suj = os.path.split(niftidir)
                                pp,prot = os.path.split(pp)
                                pp='/export/dataCENIR/dicom/nifti_raw'
                                if niftidir_ok == niftidir:
                                    strinfo += "\nSTRANGE different dicom dir lead to the same nifti dir %s : do not delete"%(niftidir)
                                else :                
                                    strinfo += "\ncd %s; cd %s; rm -rf %s" % (pp,prot,suj)
                                    f1.write(('cd %s;cd %s; rm -rf %s\n'%(pp,prot,suj)))
                                    f2.write(('cd /nasDicom/spm_raw/;cd %s; rm -rf  %s \n\n'%(prot,suj)))
        
                        
                        sqlcmd = "delete from exam where Eid='%s' ;\n" % (drows[ind]['Eid'])
                        f4.write(sqlcmd)
                             
                strinfo += "\n\n"
                self.log.info(strinfo)
                
            f1.close()
            f11.close()
            f2.close()
            f3.close()
            f4.close()
            
        con.close()

    def get_sql_exam_line(self,E,cur):
        
        sqlcmd = "SELECT * from exam WHERE "
            
        if "SIGNA PET/MR" in E["MachineName"]:
            for f in self.db_GEexamID_field:
                
                sqlcmd = "%s %s = '%s' AND" %(sqlcmd,f,E[f])
        else:
            for f in self.db_examID_field :
                if f=='AcquisitionTime':
                    aa='%s'%(E[f])
                    sqlcmd = "%s substr(AcquisitionTime,1,10) = '%s' AND" %(sqlcmd,aa[0:10])
                else:
                    sqlcmd = "%s %s = '%s' AND" %(sqlcmd,f,E[f])
        
        sqlcmd = sqlcmd[:-3]
        cur.execute(sqlcmd)
        data={}
        if cur.rowcount>0:
            data = cur.fetchone()
            
        self.log.debug('sql get_exam line %s', sqlcmd)
        
        return data

#    def get_sql_SUID_serie_line(self,ser,cur):
#
#        sqlcmd = "SELECT * from serie WHERE SUID like '%s' " %(ser["SUID"])
#        cur.execute(sqlcmd)
#        data={}
#        if cur.rowcount>0:
#            data = cur.fetchone()
#
#        return data
                
    def get_sql_select_line(self,table,id_field,id_val,sql_cur):

        sqlcmd = "SELECT * from %s WHERE %s like '%s' " %(table,id_field,id_val)
        sql_cur.execute(sqlcmd)
        data={}
        if sql_cur.rowcount>0:
            data = sql_cur.fetchone()

        return data
                
        
        
    def get_sql_select_serie_line(self,ser,cur,exclude_key=None):
        
        return self.get_sql_select_from_dict('serie',ser,cur,exclude_key)
                    
    def get_sql_update_cmd(self,E):
        
                
        sqlcmd = "UPDATE exam SET "
        for ff in self.db_exam_field :
            if type(E[ff]) is str or type(E[ff]) is datetime.date or type(E[ff]) is datetime.datetime :
                sqlcmd = "%s %s='%s'," % (sqlcmd,ff,E[ff])
            elif type(E[ff]) is int or type(E[ff]) is float:
                sqlcmd = "%s %s=%d," % (sqlcmd,ff,E[ff])
            else:
                msg = "ERROR How to write field %s with %s" % (ff,type(E[ff]))
                raise NameError(msg)
        
        sqlcmd = sqlcmd[:-1] + " WHERE MachineName = '%s' AND AcquisitionTime = '%s' " % (E["MachineName"],E["AcquisitionTime"])
        
        self.log.debug('SQL update is %s',sqlcmd)

        return sqlcmd

    def update_Exam_duration_from_sql(self,eid,con,cur):
        from math import ceil
        #TENSOR series have an AcqTime to None and a Duration=0, so skip thoses serie in the sql query
        cur2 = con.cursor()        
        #get first serie Acqtime
        sqlcmd = "SELECT duration, AcqTime from serie where ExamRef=%d and Snumber = (select min(SNumber) from serie where ExamRef=%d and Duration>0)" % (eid,eid)
        cur.execute(sqlcmd)
        data = cur.fetchone()
        t1 = data['AcqTime']
        
        sqlcmd = "SELECT duration, AcqTime from serie where ExamRef=%d and Snumber = (select max(SNumber) from serie where ExamRef=%d and Duration>0)" % (eid,eid)
        cur.execute(sqlcmd)
        data = cur.fetchone()
        t2 = data["AcqTime"]
        last_dur = data["duration"]
        if last_dur==None : #happen for Mip
            #do not update
            return            
            #last_dur=0
        if last_dur>0 : #in order to skip update wher reconstruct serie
            dur = t2-t1
            edur = int(ceil((dur.seconds + last_dur)/60.))
        
        #update exam
            sqlcmd = "UPDATE exam SET AcquisitionTime='%s', ExamDuration='%s' where Eid=%s "%(t1,edur,eid)
            cur2.execute(sqlcmd)        
            con.commit()
    
    def get_sql_insert_cmd(self,E):
    
        sqlcmd = "INSERT INTO exam ("
        for ff in self.db_exam_field :
            sqlcmd = "%s %s," % (sqlcmd,ff)       
        
        sqlcmd = sqlcmd[:-1]+") VALUES("
        
        for ff in self.db_exam_field :
            if type(E[ff]) is str or type(E[ff]) is datetime.date or type(E[ff]) is datetime.datetime or type(E[ff]) is unicode :
                if E[ff]=="NULL":
                    sqlcmd="%s %s," % (sqlcmd,E[ff])
                else:
                    sqlcmd = "%s '%s'," % (sqlcmd,E[ff])
            elif type(E[ff]) is int or type(E[ff]) is float:
                sqlcmd = "%s %d," % (sqlcmd,E[ff])
            else:
                msg = "ERROR How to write field %s with %s" % (ff,type(E[ff]))
                raise NameError(msg)
        
        sqlcmd = sqlcmd[:-1]+")"
        
        self.log.debug('sql insert line %s', sqlcmd)
        
        return sqlcmd
    
    def get_sql_serie_insert_cmd(self,E):
        
        return self.get_sql_insert_cmd_from_dict(E,'serie')
        
    def get_sql_serie_update_cmd(self,E,SID):
        
        return self.get_sql_update_cmd_from_dict(E,'serie','Sid',SID)        


#generic functions
    def get_sql_select_from_dict(self,table,ser,cur,exclude_key=None):
        
        sqlcmd = "SELECT * from %s WHERE " % (table)

        for k,v in ser.iteritems() :
            if k not in exclude_key and k[0]!='_' : #skip hidden field
               
                if type(v) is float:
                    sqlcmd = "%s round(%s*100000) = round(%s*100000) AND" %(sqlcmd,k,v)
                elif v is "NULL":
                    sqlcmd = "%s %s is NULL AND" %(sqlcmd,k)
                else:
                    sqlcmd = "%s %s like '%s' AND" %(sqlcmd,k,v)
                
        sqlcmd = sqlcmd[:-3]
        self.log.debug('sql select line %s', sqlcmd)
        
        cur.execute(sqlcmd)
        data={}
        if cur.rowcount>0:
            data = cur.fetchone()

        return data
        
    def get_sql_insert_cmd_from_dict(self,E,table):
    
        sqlcmd = "INSERT INTO %s (" %(table)
        
        for key in E.iterkeys():
            if key[0]=='_':
                continue  #skip hidden field
            sqlcmd = "%s %s," % (sqlcmd,key)       
        
        sqlcmd = sqlcmd[:-1]+") VALUES("
    
        for key,val in E.iteritems():
            if key[0]=='_':
                continue  #skip hidden field
            
            if type(val) is str or type(val) is unicode :
                if val.find("NULL")>=0:
                    sqlcmd = "%s (NULL)," % (sqlcmd)
                else:
                    if len(val)>0:
                        val = alpha_num_str_min(val)
                    sqlcmd = "%s '%s'," % (sqlcmd,val)
    
            elif type(val) is datetime.date or type(val) is datetime.datetime :
                sqlcmd = "%s '%s'," % (sqlcmd,val)
                    
            elif type(val) is int or type(val) is float or type(val) is long:
                sqlcmd = "%s %f," % (sqlcmd,val)
            else:
                msg = "ERROR How to write field %s with %s" % (key,type(val))
                raise NameError(msg)
        
        sqlcmd = sqlcmd[:-1]+")"
    
        return sqlcmd
        
    def get_sql_update_cmd_from_dict(self,E,table,where_field,where_value):
    
        sqlcmd = "UPDATE %s SET" %(table)
    
        for key,val in E.iteritems():
            if key[0]=='_':
                continue  #skip hidden field
            
            if type(val) is str or type(val) is unicode :
                if val.find("NULL")>=0:
                    sqlcmd = "%s %s = (NULL)," % (sqlcmd,key)
                else:
                    
                    sqlcmd = "%s %s = '%s'," % (sqlcmd,key,val)
    
            elif type(val) is datetime.date or type(val) is datetime.datetime :
                sqlcmd = "%s %s = '%s'," % (sqlcmd,key,val)
                    
            elif type(val) is int or type(val) is float or type(val) is long:
                sqlcmd = "%s %s = %f," % (sqlcmd,key,val)
            else:
                msg = "ERROR How to write field %s with %s" % (key,type(val))
                raise NameError(msg)
        
        whereclause = " WHERE %s=%s" %(where_field,where_value)
        sqlcmd = sqlcmd[:-1]+ whereclause

        return sqlcmd
              
        
        
