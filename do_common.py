#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 11:00:43 2012

@author: romain
"""
import common as c

import os, logging , sys
from optparse import OptionParser

class doit:
    'Class to handel logs and options fo executable'    
    
    def __init__(self):
                
        self.log = self.init_log()

        self.options = ''
        
    def get_log(self):
        
        return self.log
        
    def init_log(self):
        
        log = logging.getLogger('Do_dicom_serie')
    
        self.formatter = logging.Formatter("%(asctime)-2s: %(levelname)-2s : %(message)s")
        if not len(log.handlers):
            console = logging.StreamHandler(sys.stdout)
            console.setFormatter(self.formatter)
            log.addHandler(console)
        
        log.setLevel(logging.INFO)
        return log
    
    def update_log(self,file):

            fhdl = logging.FileHandler(filename = file,mode='a')
            fhdl.setFormatter(self.formatter)
            self.log.addHandler(fhdl)
            self.log.setLevel(logging.INFO)


        
    def add_options_common(self,parser) :

        parser.add_option("-l","--logfile", action="store", dest="logfile", default='',
                                    help="full path to the log file default=''")

        parser.add_option("--debug", action ="store_true",dest="debug",default=False,
                                  help="if specify this will print more and more info")

        parser.add_option("-m","--send_mail", action ="store_true",dest="send_mail",default=False,
                                  help="if specify this send a mail for missing dicom file")
        parser.add_option("--send_mail_file", action ="store",dest="send_mail_file",default='',
                                  help="if specify (absolute root name' this will print the mail in a file")
        parser.add_option("--smtp_pwd", action ="store",dest="smtp_pwd",default='xxx',
                                  help="give the spmtp passord note the user and smtp server are hard codeed")
        parser.add_option("-c","--conf_section", action ="store",dest="conf_section",
                                  help="reading default value from the config file section DEFAULT")
        
        conffile = os.path.join(os.getenv('HOME'),'do_dicom_seriesDB.conf')
        parser.add_option("--conf_file", action ="store",dest="conf_file",default=conffile,
                                  help="path of the config file default $HOME/do_dicom_seriesDB.conf")
    
        parser.add_option("--write_conf_to_section", action ="store",dest="write_conf_to_section",
                                  help="specify the name of the section where to write the param")

        return parser

    def add_options_parse_data(self,parser) :
        parser.add_option("-r","--rootdir", action="store", dest="rootdir", default='/network/lustre/iss01/cenir/raw/irm/dicom_raw',
                                    help="full path to the root directorie dicom files (where liste of protocol are) default=/network/lustre/iss01/cenir/raw/irm/dicom_raw'")
        parser.add_option("-p","--proto_reg", action="store", dest="proto_reg", default='.*',
                                    help="regular expression to select protocol dir default='.*' ")
        parser.add_option("-s","--suj_reg", action="store", dest="suj_reg", default='.*',
                                    help="regular expression to select subjec dir default='.*' ")
        parser.add_option("-S","--ser_reg", action="store", dest="ser_reg", default='',
                                    help="regular expression to select series dir default=''  ")
        return parser
        
    def add_options_import_dicom(self,parser) :

        parser.add_option("-d","--days", action="store", dest="nb_days", default=0,type="int",
                                    help="get only exam in rootdir newer than n days  ")
        parser.add_option("--from_logfile", action="store_true", dest="from_logfile", default=False,
                                    help="will research exam newer than the last time it has be runed ")

        parser.add_option("-b","--data_base", action="store_true", dest="do_db",default=False,
                                    help="commit the exam to the cenir database ")
                                    
        parser.add_option("-g","--data_base_gg", action="store_true", dest="do_db_gg",default=False,
                                    help="commit the exam to the GG database ")
                                    
        parser.add_option("-w","--write-nifti", action="store_true", dest="convert_to_nii",default=False,
                                    help="convert dicom to nifti")
        parser.add_option("-t","--test_data_base", action="store_true", dest="test_db",default=False,
                                    help="Just write the log of what changes should be donne in the cenir database (for the selected exams). It won't take the -b option ")
        parser.add_option("-i","--do_only_insert", action="store_true", dest="do_only_insert",default=False,
                                    help="it will only insert new exam in the cenir database (it will not modify existing record) ")

        parser.add_option("-f","--find_double", action="store_true", dest="find_double",default=False,
                                    help="This will print duplicate exam in the given search ")
        parser.add_option("--dicom_ext", action ="store",dest="dicom_ext",default='*.dic',
                                  help="Dicom file extention default is *.dic")
        parser.add_option("--nifti_dir", action ="store",dest="nifti_dir",default='/network/lustre/iss01/cenir/raw/irm/nifti_raw',
                                  help="Root output directorie for nifti files")
        parser.add_option("--input_dir", action ="store",dest="input_dir",default='',
                                  help="if specify this will get (recursivly) all dicom file from this directory")
        parser.add_option("--tri_dicom", action ="store_true",dest="tri_dicom",default=False,
                                  help="if specify this will tri and coppy all dicom in the rootdir")
        parser.add_option("--mv_file", action ="store_true",dest="mv_file",default=False,
                                  help="if specify this will write a file containing the mv command after tri")
        parser.add_option("--tri_move", action ="store_true",dest="tri_move",default=False,
                                  help="if specify this will move the dicom instead of copy")
        parser.add_option("--skip_derived", action ="store_false",dest="skip_derived",default=True,
                                  help="if specify all dicom series will be converted (if not derived series are skiped) ")
        return parser                                  
    
        
    def get_option(self,def_type=''):
        
        from Cenir_DB import add_options as CDB_opt
        from do_results_DB import add_options as RES_opt
        
        if def_type.find('import_dicom')==0 :
            usage= "usage: %prog [options] select dir of dicom exam with the option and insert them into cenir SDB (exam) "
            # Parse input arguments
            p = OptionParser(usage=usage)
            
            p = self.add_options_parse_data(p)
            p = self.add_options_import_dicom(p)
            p = self.add_options_common(p)            
            p = CDB_opt(p)

            
        elif def_type.find('results_db')==0  :
            usage= "usage: %prog todo "
            p = OptionParser(usage=usage)

            p = self.add_options_parse_data(p)
            p = self.add_options_common(p)        
            p = CDB_opt(p)
            p = RES_opt(p)     
        
        parser=p
        (options, args) = parser.parse_args()
    
        conffile = options.conf_file
        if os.path.isfile(conffile) & (options.conf_section is not None): 
            import ConfigParser
            config = ConfigParser.RawConfigParser()
            config.read(conffile)
            if config.has_section(options.conf_section) :
                self.log.info('Reading default from %s sections in $HOME/do_dicom_seriesDB.conf',options.conf_section)
                dd = dict(config.items(options.conf_section))
                dd = convert_str_to_boolean(dd)
                parser.set_defaults(**dd)
                (options, args) = parser.parse_args()
            else:
                self.log.info('could not find sections %s in $HOME/do_dicom_seriesDB.conf\n there is only :\n%s',options.conf_section,config.sections())
                sys.exit()
    
        if len(options.logfile)>0:    
            self.update_log(options.logfile)
                
        if options.write_conf_to_section is not None :        
            write_configfile(vars(options),conffile,options.write_conf_to_section)


        self.options = options
        
        if options.debug :
            self.log.setLevel(logging.DEBUG)

        self.log.info('Runing with option \n%s',self.options_to_str())
        
            
        return options
    
    def options_to_str(self):
        optstr = ''
        for v in vars(self.options):
            optstr += '%-12s: %s\n'%(v,getattr(self.options,v))
        return optstr
    
    def handel_main_exception(self,e):
        
        if self.options.send_mail:
            self.log.warning(format_exception(e))
            msg = format_exception(e) + "\n runing with \n" + self.options_to_str()
            c.send_mail(msg,'Main error do_dicom_series',self.options.smtp_pwd)
        else:
            self.log.warning("\n MAIN exection : \n%s",format_exception(e))


def convert_str_to_boolean(dd):
    for k,v in dd.iteritems():
        if v == 'False':
            dd[k] = False
        elif v == 'True':
            dd[k] = True
    
    return dd

def format_exception(e):
    import traceback

    exception_list = traceback.format_stack()
    exception_list = exception_list[:-2]
    exception_list.extend(traceback.format_tb(sys.exc_info()[2]))
    exception_list.extend(traceback.format_exception_only(sys.exc_info()[0], sys.exc_info()[1]))

    exception_str = "Traceback (most recent call last):\n"
    exception_str += "".join(exception_list)
    # Removing the last \n
    #exception_str = exception_str[:-1]

    return exception_str
        
def write_configfile(options_dict,conffile,confsection):
    import ConfigParser
        
    config = ConfigParser.RawConfigParser()
    config.read(conffile)
    if not config.has_section(confsection):
        config.add_section(confsection)
    #    config = ConfigParser.RawConfigParser()

    for k,v in options_dict.iteritems():
        config.set(confsection,k,str(v))
    with open(conffile, 'wb') as cf:
        config.write(cf)

def alpha_num_str(stri):
    from dcmstack import extract
    import re
    
    if len(stri)==0:
        return stri
        
#    if type(stri) is not unicode:
#        stri = make_unicode(stri)
    
#    if type(stri) is str:
#        stri=stri.replace('\xe9','e')
#        stri=stri.replace('\xf4','o')
    indice_mu = stri.find(u'\xb5') #µ is not changed in matlab convert dicom so keep it
    if indice_mu>0:
        stri = stri[0:indice_mu]+u'm'+stri[indice_mu+1:len(stri)]
    #correspond au caractere e accent aigu et e accent grave
    stri=stri.replace(u'\xe9','e')
    stri=stri.replace(u'\xe8','e')
    #correspond au caractere o chapeau
    stri=stri.replace(u'\xf4','o')
    #correspond au caractere i trema
    stri=stri.replace(u'\xef','i')
    #correspond au caractere a accent grave
    stri=stri.replace(u'\xe0','a')
    #correspond au caractere a chapeau
    stri=stri.replace(u'\xe2','a')
    #correspond au caractere a chapeau
    #stri=stri.replace(make_unicode('/'), '_')
    stri=stri.replace('/', '_')
    #convert to string and ignore other strange caractere
    stri=stri.encode('utf-8').decode('ascii','ignore')
    stri = str(stri)
    
    
    stri = re.sub('\W','_',stri)   
    
    #remove several occurence of _
    while stri.find('__')>0:
        stri = stri.replace('__','_')
    #do not let a '_' at the end of the string
    if stri[-1]=='_':
        stri = stri[:-1]
    #do not let a '_' at the end of the string
    if stri[0]=='_':
        stri = stri[1:]
    
#    if indice_mu>0:
#        stri = stri[0:indice_mu]+'µ'+stri[indice_mu+1:len(stri)]
    
    return stri 
    
def alpha_num_str_min(stri):
    from dcmstack import extract
#    import re
    
#    if type(stri) is not unicode:
#        stri = make_unicode(stri)
    
#    if type(stri) is str:
#        stri=stri.replace('\xe9','e')
#        stri=stri.replace('\xf4','o')
    
    #correspond au caractere e accent aigu et e accent grave
    stri=stri.replace(u'\xe9','e')
    stri=stri.replace(u'\xe8','e')
    #correspond au caractere o chapeau
    stri=stri.replace(u'\xf4','o')
    #correspond au caractere i trema
    stri=stri.replace(u'\xef','i')
    #correspond au caractere a accent grave
    stri=stri.replace(u'\xe0','a')
    #correspond au caractere a chapeau
    stri=stri.replace(u'\xe2','a')
    
    #convert to string and ignore other strange caractere
    stri=stri.encode('utf-8').decode('ascii','ignore')
    stri = str(stri)

#    stri = re.sub('\W','_',stri)   
    
    #remove several occurence of _
    while stri.find('__')>0:
        stri = stri.replace('__','_')
    #do not let a '_' at the end of the string
    if stri[-1]=='_':
        stri = stri[:-1]
    #do not let a '_' at the end of the string
    if stri[0]=='_':
        stri = stri[1:]
    
    
    return stri 

def make_unicode(in_str):
    '''Try to convetrt in_str to unicode'''
    for encoding in ('utf8', 'latin1'):
        try:
            result = unicode(in_str, encoding=encoding)
        except UnicodeDecodeError:
            pass
        else:
            break
    else:
        raise ValueError("Unable to determine string encoding: %s" % in_str)
    return result
    

#plu efficace
#def sanitize_path_comp(path_comp):
#    result = []
#    for char in path_comp:
#        if not char in string.letters + string.digits + '-_.' :
#            result.append('_')
#        else:
#            result.append(char)
#    return ''.join(result)

