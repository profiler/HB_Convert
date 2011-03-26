#!/usr/bin/env python
#
#  Copyright (c)2010 Ton van Twuyver @ <profiler1234@gmail.com>
#
#  This script is written with "HomeBank" in mind.
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

#### Convert ######CsvConvert####################################

class CsvConvert:
    """ reads and converts [import.csv] with [definition.def] rules """
    
    def __init__(self, fromfile_, deffile_, tofile_, logfile_):
        # read definition-file
        def_eof = False
        hb      = []    # homebank conversion-list
        ip      = []    # import   conversion-list
        while not def_eof:
            def_line = deffile_.readline()
            # def_eof
            if len(def_line) < 1:
                def_eof = True
            def_line = def_line.rstrip('\n')
            d = def_line.split(';')
            # line valid ?
            if (len(d) == 5) and (d[2].rstrip() !=''):
                # Extract Details for 
                # Date
                if  int(d[0]) == 0:     date = d[4]
                # PayCode
                elif int(d[0]) == 1:    code = d[4]
                # Sign (Amount)
                elif int(d[0]) == 5:    posneg = d[4]
                
                # create conversion-lists        
                hb.append(int(d[0]))
                ip.append(int(d[2]))

        # parse import.csv
        n = 0
        imp_eof = False
        header  = False
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
                    CsvConvert.fail = n                  # Error => Store record-/line-number
                    logfile_.write('Error in record[%s]: Field[%s] contains illegal "Separator" -> %s\n'% (n,i,rec[i]))
                else:                    
                    rec[i] = rec[i].strip('"')

            # header indicating new account (multi accounts import)
            # format: account-number; "Homebank account-name" [For now unknown '']
            if header == False:
                print '%s;%s'% (rec[hb[0]],'')
                tofile_.write('%s;%s\n'% (rec[hb[0]],''))
                header = True
            
            if CsvConvert.fail == 0:                     # >>>>> skip record with error !
                # Assemble Homebank records
                hb_old  = 0
                record  = ''
                for j in range(len(hb)):
                    h = hb[j]        
                    b = ip[j]
                    rec_new = rec[b]
                    
                    # "date" conversion
                    if h == 0:                        
                        dd = date.find('DD')
                        mm = date.find('MM')
                        yy = date.find('YYYY')
                        rec_new = '%s-%s-%s'% (rec[b][dd:(dd+2)],rec[b][mm:(mm+2)],rec[b][yy:(yy+4)])
                    # "paycode" conversion
                    if (code != '') and (h == 1):
                        k = 0
                        cd = code.split(',')
                        offset = len(cd)/2
                        for c in cd:
                            if c == rec[b]:     rec_new = cd[k + offset]
                            k += 1
                    # "amount" conversion
                    if (posneg != '') and (h == 5):
                        # Sign
                        rec_new = ''
                        pn = posneg.split(',')
                        if   rec[b] == pn[0]:   rec_new = '-%s'% am
                        elif rec[b] == pn[1]:   rec_new = am
                        # Amount
                        else:
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
                           
                    # Init (first) Bank-field
                    if (j == 0):
                        record = rec_new
                        hb_old = h
                    # Combine multiple description(h:4) "not empty" Bank-records
                    elif (hb_old == h) and (h == 4):
                        if (len(rec_new) != 0):
                            record = '%s_%s'% (record,rec_new)
                    # Single "not empty" Bank-record
                    elif (rec_new != '') and (h < 7):
                        hb_old = h
                        record = '%s;%s'% (record,rec_new)
                    # Single "empty" Bank-record
                    elif h == 6:
                        hb_old = h
                        record = '%s;%s'% (record,rec_new)

                print record
                tofile_.write('%s\n'% record)
                
#### Convert ##########################################
      
class convert:
    """ Converts <unknown> csv-file """
    # 1- where are the csv-files?   =>  commandline
    # 2- Convert via definition-file 
    # 3- what is csv-separator comma, semicolon ?
    # 4- Skip "corrupted" bank-file records
    # 5- include header with account number in output.csv
    # 6- Log all conversion process-items
      
    def __init__(self):
    
        error = 'Input error!____ Type ./convert.py [import.csv] [output.csv] [import.def] ____\n\n\
                 [import.csv] = ("bank".csv)    file exported from bank\n\
                 [output.csv] = (homebank.csv)  file to be created\n\
                 [import.def] = ("bank".def)    definition-file "bank" <> "Homebank"\n\n\
                 Logging conversion process -> log.txt\n'
        homebank = ['date','paymode','offset','payee','description','amount','category']
        
        if (len(sys.argv) != 4):
            print error
            exit(1)

        if os.path.isfile(sys.argv[3]):
            deffile = open(sys.argv[3],'r')
        else: 
            print error
            exit(1)
            
        fromfile = open(sys.argv[1],'r')
        tofile   = open(sys.argv[2],'w')
        logfile  = open('log.txt', 'w')
        
        logfile.write('Opening import     %s\n' % fromfile)
        logfile.write('        export     %s\n' % tofile)
        logfile.write('        definition %s\n' % deffile)

        CsvConvert(fromfile, deffile, tofile, logfile)
                
        logfile.write('Closing output file\n')
        logfile.close()
        fromfile.close()
        tofile.close()
        deffile.close()

if __name__ == "__main__":
    convert()
