#!/usr/bin/env python
#
#  Copyright (c)Ton van Twuyver @ <profiler1234@gmail.com>          Last updated 29-04-2011
#
#  This script is written with "HomeBank" in mind. <http://homebank.free.fr>
#  Purpose:    to convert any Bank-file.csv in Homebank.csv by means of a definition-file.
#  
#  Convert.py is written in Python(2.6) and free software,
#  It is distributed in the hope that it will be useful, but comes WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU General Public License for more details.
#  You can redistribute it and/or modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  GNU General Public License @ <http://www.gnu.org/licenses/>.
#
import os
import sys

#### CsvConvert####################################

class CsvConvert:
    """ reads and converts [import.csv] with [definition.def] rules """
    
    def __init__(self, fromfile_, deffile_, tofile_, logfile_):
    
        # parse definition-file and create conversion-lists
        def_eof = False
        n  = 0                                  # (definition line counter)
        d_old   = ''
        hb = []                                 # homebank conversion-list
        ip = []                                 # import   conversion-list
        while not def_eof:
            n += 1                              # line count
            def_line = deffile_.readline()
            # def_eof
            if len(def_line) < 1:
                def_eof = True
                
            def_line = def_line.rstrip('\n')
            d = def_line.split(';')
            # definition line valid ?
            if (len(d) == 5):
                # definition line contains in already defined field -> improper "not-in-use" data ?
                if (d_old == d[0]) and (int(d[2]) < 0):
                    print 'Error in definition-file-record[%s]: field already defined !'% n
                    logfile_.write('Error in definition-file-record[%s]: field already defined ! \n'% n)
                else:
                    # Extract Details for Date,Paycode,Sign:
                    if (d[2].rstrip() != ''):
                        #   Date
                        if  int(d[0]) == 0:     date = d[4]
                        #   PayCode
                        elif int(d[0]) == 1:
                            code = d[4]
                            # content needs checking
                            cod_ = (d[4].split(','))
                            cod_l = len(cod_)
                            if (len(cod_)-(len(cod_)/2)*2) != 0:
                                print 'Error in definition-file: paycode detail-data Incorrect, Not enough items'
                                logfile_.write('Error in definition-file: paycode detail-data Incorrect, Not enough items \n')
                        #   Sign (Amount)
                        elif int(d[0]) == 5:    posneg = d[4]
                        
                    # create conversion-lists        
                    hb.append(int(d[0]))
                    ip.append(int(d[2]))

                d_old = d[0]                    # remember curr. field-data

        print hb
        print ip
        
        # parse import.csv
        n = 0                                   # (import line counter)
        imp_eof = False
        acc_old = ''
        bank = {                                # All known accounts
        '0123456789':'Bank1',
        '0987654321':'Bank2'
        }
        while not imp_eof:
            n += 1                              # line count
            line = fromfile_.readline()
            # eof (import)
            if len(line) <= 3:
                imp_eof = True
                break
                
            # Cleanup
            line = line.rstrip('\r\n')          # get rid of CRLF
            line = line.replace("'",'"')        # harmonize all quotes ""
            # Find out Separator
            line_c = line.replace(',','')
            line_s = line.replace(';','')
            if len(line_c) > len(line_s):       # semicolon
                rec = line.split(';')
            else:                               # comma
                rec = line.split(',')
                
            # Caution: some files can contain comma's/semicolons within quotes !!!!!!
            # Check field-content for amount of quotes [0 or 2]
            CsvConvert.fail = 0
            for i in range(len(rec)):
                d = len(rec[i])-len(rec[i].replace('"',''))
                if (d != 0) and (d != 2):
                    CsvConvert.fail = n                 # Error => Store record-/line-number
                    logfile_.write('Error in record[%s]: Field[%s] contains illegal "Separator" -> %s\n'% (n,i,rec[i]))
                else:                    
                    rec[i] = rec[i].strip('"')
            
            if (len(hb)>=len(rec)):
                CsvConvert.fail = n                     # Error => Store record-/line-number
                logfile_.write('Error in record[%s]: Field(s) missing\n'% n)
            
            if (CsvConvert.fail == 0):                  # >>>>> skip record with error !
                # Assemble Homebank records
                hb_old  = 0
                record  = ''
                am = ''
                for j in range(len(hb)):
                    h = hb[j]        
                    b = ip[j]
                    rec_new = rec[b]
                    
                    # conversions
                    # "date"
                    if (h == 0):                        
                        dd = date.find('DD')
                        mm = date.find('MM')
                        yy = date.find('YYYY')
                        rec_new = '%s-%s-%s'% (rec[b][dd:(dd+2)],rec[b][mm:(mm+2)],rec[b][yy:(yy+4)])
                    # "paycode"
                    if (code != '') and (h == 1):
                        if code.find(rec[b]) < 0:   rec_new = ''    # Unknown code (Not in .def)
                        else:
                            k = 0
                            cd = code.split(',')
                            offset = len(cd)/2
                            for c in cd:
                                if c == rec[b]:     rec_new = cd[k + offset]
                                k += 1                            
                    # "amount"
                    if (h == 5):
                        rec_new = ''
                        # Amount
                        if (am == ''):
                            am = rec[b]
                            # integers(any number).fraction(0..2) 
                            # find decimal point
                            frac1 =len(am)-am.find('.')
                            frac2 =len(am)-am.find(',')
                            # No grouping & No fraction / decimal-point
                            if (frac1 == frac2):
                                am = '%s.00'% am
                            # xxx,xxx,xxx.xx    comma-grouping, dot-decimal
                            elif (frac1 < 4) and (frac1 > 0):
                                am = am.replace(',','')
                            # xxx.xxx.xxx,xx    dot-grouping,   comma-decimal
                            elif (frac2 < 4) and (frac2 > 0):
                                am = am.replace('.','')
                                am = am.replace(',','.')    # harmonize decimal-point
                            # grouping & No fraction / decimal-point
                            else:
                                am = am.replace(',','')
                                am = am.replace('.','')
                                am = '%s.00'% am
                        # Sign
                        elif (posneg != ''):
                            pn = posneg.split(',')
                            if   rec[b] == pn[0]:   am = '-%s'% am
                            elif rec[b] == pn[1]:   pass
                            rec_new = am

                    # assemble output-record
                    # skip if import.csv does not have this field: [-1]
                    if (ip[j] != -1):
                        # [date]
                        if (h == 0):
                            record = rec_new
                        # [paymode]    
                        elif (h == 1):
                            if rec_new != '':
                                record = '%s;%s'% (record,rec_new)
                            else:
                                print '>>>>> Unknown code: ' + rec[b]
                                logfile_.write('Unknown Paycode "%s" in record[%s]\n'% (rec[b],n))
                        # [info -> offset-account]
                        elif (h == 2):
                            if (len(rec_new) != 0) and (int(rec_new) > 0):
                                record = '%s;%s'% (record,rec_new)
                            else:
                                record = '%s;'% record
                        # [payee]
                        elif (h == 3):
                            record = '%s;%s'% (record,rec_new)
                        # [description]
                        elif (h == 4):
                            # Combine multiple "not empty" description Bank-records
                            if (hb_old == h):
                                if (len(rec_new) != 0):
                                    record = '%s_%s'% (record,rec_new)
                                else:
                                    pass
                            # First description Bank-record
                            else:
                                hb_old = h
                                if (len(rec_new) != 0):
                                    record = '%s;%s'% (record,rec_new)
                                # empty
                                else:
                                    record = '%s;'%  record
                        # [amount]
                        elif (h == 5):
                            if (len(rec_new) != 0):
                                record = '%s;%s'% (record,rec_new)
                            else:
                                pass
                        # [category]
                        elif (h == 6):
                            record = '%s;%s'% (record,rec_new)
                        # [account]    
                        # NOT IMPLEMENTED IN HOMEBANK CSV-import
                        #       multi accounts import: sequential account listing
                        #       at top of accountlist extra line with account-name
                        #       format: account-number; "Homebank account-name"
                        #       Needs Homebank 4.3 "import.c" adaptation (TvT(c)2010)
                        elif (h == 7):
                            # make banknumber 10 char.long
                            if len(rec_new) < 10:
                                rec_new = (10 - len(rec_new))*'0' + rec_new
                            # detect next account
                            if (rec_new != acc_old):
                                acc_old = rec_new
                                try:
                                    print bank[rec_new]
                                    tofile_.write('%s;%s\n'% (rec_new,bank[rec_new]))
                                except KeyError:
                                    print 'Unknown/New account number'
                                    tofile_.write('%s;%s\n'% (rec_new,'New_account'))
                        # [balance]            
                        # NOT IMPLEMENTED IN HOMEBANK CSV-import
                        #       Listed Balance value before/after transaction ?
                        #       Needs further investigation and Homebank 4.3 "import.c" adaptation
                        # TODO  Needs Homebank 4.3 "import.c" adaptation
                        elif (h == 8):
                            print float(rec_new) + float(am)

                    # No field available [-1]
                    elif (h < 7):
                        record = '%s;'% record
                        
                print record
                tofile_.write('%s\n'% record)
                
#### Convert ##########################################
      
class convert:
    """ Converts <unknown> csv-file """
    # 1- where are the csv-files?                   =>  commandline
    # 2- Convert via definition-file 
    # 3- what is csv-separator: comma, semicolon ?
    # 4- Skip "corrupted" bank-file records
    # 5- Include multi-accounts in output.csv       (NOT IMPLEMENTED IN HOMEBANK CSV-import)
    # 6- Include balance info in output.csv         (NOT IMPLEMENTED IN HOMEBANK CSV-import)
    # 7- Log all conversion process-items
      
    def __init__(self):
    
        error = 'Input error!____ Type ./convert.py [import.csv] [output.csv] [import.def] ____\n\n\
                 [import.csv] = ("bank".csv)    file exported from bank\n\
                 [output.csv] = (homebank.csv)  file to be created\n\
                 [import.def] = ("bank".def)    definition-file "bank" <> "Homebank"\n\n\
                 Logging conversion process -> log.txt\n'
        homebank = ['date','paymode','info','payee','description','amount','category']  # 4.3
        
        if (len(sys.argv) != 4):
            print error
            exit(1)

        if os.path.isfile(sys.argv[1]):
            fromfile = open(sys.argv[1],'r')
        else:
            print '\nInput error!____ import.csv: ' + sys.argv[1] + ' does not exist / cannot be opened !!\n'
            exit(1)
            
        try:
            tofile   = open(sys.argv[2],'w')
        except:
            print '\nInput error!____ output.csv: ' + sys.argv[2] + ' cannot be created !!\n'
            exit(1)
            
        if os.path.isfile(sys.argv[3]):
            deffile = open(sys.argv[3],'r')
        else: 
            print '\nInput error!____ import.def: ' + sys.argv[3] + ' does not exist / cannot be opened !!\n'
            exit(1)
            
        logfile  = open('log.txt', 'w')
        
        logfile.write('Opening import     %s\n' % fromfile)
        logfile.write('        export     %s\n' % tofile)
        logfile.write('        definition %s\n' % deffile)

        CsvConvert(fromfile, deffile, tofile, logfile)
                
        logfile.write('Closing files\n')
        logfile.close()
        fromfile.close()
        tofile.close()
        deffile.close()

if __name__ == "__main__":
    convert()
