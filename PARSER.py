#------------------------import important packages-----------------------------#

import pdfplumber
import re
import os
import csv
from tqdm import tqdm

#------------------------CLASS PDF PARSER-----------------------------#

class PDF_PARSER:
    def __init__(self, pth):
        self.path = pth
        self.main()
    #------------------------LOADING FILES-----------------------------#
    def load_pdfs(self, path):
        return os.listdir(path)
        
    #------------------------GET PDF BASIC INFO------------------------#
    def BASIC_INFO(self, path):
        start_keyTerm = '''Quality, Currency, Availability of Textbooks and Other Instructional Materials'''
        end_keyTerm = '''School Facility Conditions and Planned Improvements'''
        PDF =  pdfplumber.open(path)
        PAGES = PDF.pages
        
        SCHOOL         = ''
        DISTRICT       = ''
        CDS_CODE       = ''
        COLLECTED_DATE = ''
        TEXT = []
        start = ''
        end = ''
          
        try:
            Tables = PAGES[1].extract_tables()
            if len(Tables) == 1:
                for row in Tables:
                    if 'School Name' in row:
                        ind = row.index('School Name')
                        SCHOOL = row[ind+1]
                    if 'County-District-School (CDS) Code' in row:
                        ind = row.index('County-District-School (CDS) Code')
                        CDS_CODE = row[ind+1]
            
                    if 'District Name' in row:
                        ind = row.index('District Name')
                        DISTRICT = row[ind+1]
            elif len(Tables) > 1:
                for table in Tables:
                    for row in table:
                        if 'School Name' in row:
                            ind = row.index('School Name')
                            SCHOOL = row[ind+1]
                        if 'County-District-School (CDS) Code' in row:
                            ind = row.index('County-District-School (CDS) Code')
                            CDS_CODE = row[ind+1]
                
                        if 'District Name' in row:
                            ind = row.index('District Name')
                            DISTRICT = row[ind+1]
            if SCHOOL == '':
                Tables = PAGES[2].extract_tables()
                if len(Tables) == 1:
                    for row in Tables:
                        if 'School Name' in row:
                            ind = row.index('School Name')
                            SCHOOL = row[ind+1]
                        if 'County-District-School (CDS) Code' in row:
                            ind = row.index('County-District-School (CDS) Code')
                            CDS_CODE = row[ind+1]
                
                        if 'District Name' in row:
                            ind = row.index('District Name')
                            DISTRICT = row[ind+1]
                elif len(Tables) > 1:
                    for table in Tables:
                        for row in table:
                            if 'School Name' in row:
                                ind = row.index('School Name')
                                SCHOOL = row[ind+1]
                            if 'County-District-School (CDS) Code' in row:
                                ind = row.index('County-District-School (CDS) Code')
                                CDS_CODE = row[ind+1]
                    
                            if 'District Name' in row:
                                ind = row.index('District Name')
                                DISTRICT = row[ind+1]
        except:
            pass
        try:
            for e, PAGE in enumerate(PAGES):
                if PAGE.search(start_keyTerm) != []:
                    start = e
                 
                if PAGE.search(end_keyTerm) != []:
                    end = e
                    break
                
            for i in range(start, end+1):
                TXT = PAGES[i].extract_text()    
                LST = TXT.split('\n')
                TEXT.extend(LST)
                TEXT.remove(TEXT[-1])
            limits = []
            for i in TEXT:
                if start_keyTerm in i:
                    limits.append(TEXT.index(i))
                if end_keyTerm in i:
                    limits.append(TEXT.index(i))
            TEXT = TEXT[limits[0]:limits[-1]]
            
            for i in TEXT:
                if 'Year and month in which the data were collected' in i:
                    COLLECTED_DATE = ''.join((i.replace('Year and month in which the data were collected', '')).strip())
                    TEXT = TEXT[TEXT.index(i)+1:]
            TEXT = [e for e in TEXT if e != ' ']
            try:
                TEXT = TEXT[TEXT.index('?  Copy ')+1:]
            except:
                pass
        except:
            pass
        DIC  = {'SCHOOL': SCHOOL, 'DISTRICT':DISTRICT, 'CDS_CODE':CDS_CODE, 'COLLECTED_DATE':COLLECTED_DATE,
                'TEXT_LST':TEXT}
        
        return DIC

    
    #---------------------CLEANING SENTENCE TEXT-------------------#
    def SENT_CLEANER(self, lst):
        Lst     = [] 
        for e, s in enumerate(lst):
            if s.endswith(' '):
                Lst.append(s[:-1])
            else:
                Lst.append(s)
        concat = []
        temp = []
        
        for e, l in enumerate(Lst):
            text = ''
            if l.endswith(',')  or l.endswith('-') or l.endswith(' ') or l.endswith(':') or l.split()[-1] == 'and':            
                text = l
                text+= ' '
                text+= Lst[e+1]
                temp.append(Lst[e+1])
                concat.append(text)
            else:
                concat.append(l)
            try:
                if Lst[e+1].startswith(',') or Lst[e+1].startswith(' ') or Lst[e+1].split()[0] == 'and': 
                    text += l
                    text += ' '
                    text += Lst[e+1]
                    temp.append(Lst[e+1])
                    concat.append(text)
            except:
                pass
                
        concat = [e for e in concat if e not in temp]
    
    
        new_lst = []
        
        for e, l in enumerate(concat):
            try:
                if len(l.split()) >= 5:
                    text = l
                    for s in concat[e+1:]:
                        if len(s.split()) < 5:
                            text += ' '
                            text += s
                        else:
                            break
                    new_lst.append(text)
                else: 
                    for s in concat[e+1:]:
                        st = l
                        if len(s.split()) < 5:
                            st += ' '
                            st += s 
                        else:
                            break
                    new_lst.append(st)
            except:
                new_lst.append(l)
    
        seen = set()
        dupes = [x for x in new_lst if x in seen or seen.add(x)] 
    
        if dupes != []:
            new_lst = list(set(new_lst))
        else:
            new_lst = new_lst
    
        return new_lst
    #----------------------GET SENTENCES FROM ROW TEXT-------------------#
    def SENT_RET(self, path):
        DATA = self.BASIC_INFO(path)
        TEXT_CLEANER = self.SENT_CLEANER
        DICT = {}
        SUBJECTS = ['Reading/Language Arts', 'Mathematics', 'Science', 'History-Social Science', 'Visual and Performing Arts', 
                'Foreign Language', 'Health', 'Visual and Performing Arts', 'Science Laboratory Equipment', 'English Language Arts/Literacy']
        LST = [re.sub(' \s+ ', '', s) for s in DATA['TEXT_LST']]
        LST = [e for e in LST if e != '']
        word = 'English Language Arts/Literacy'
        ENG_LANG_ARTS_LITER_ = []
        for i in LST:
            try:
                SUBJECTS.remove('English Language Arts/Literacy')
            except:
                pass
            if word in i and 'Yes' in i:
              ENG_LANG_ARTS_LITER_.append(word)
              st_ = i.replace('Yes', '')
              st_ = st_.replace(' 0', '')
              st_ = st_.replace(' .0', '')
              st_ = st_.replace('%', '')
              ENG_LANG_ARTS_LITER_.append(" ".join((st_.split(word)[1]).split()))
              new_lst = LST[LST.index(i)+1:]
              for j in new_lst:
                if any(s in j for s in SUBJECTS) == False:
                    ENG_LANG_ARTS_LITER_.append(j)
                else:
                    break
              break
        
        try:
            ENG_LANG_ARTS_LITER = TEXT_CLEANER([i for i in ENG_LANG_ARTS_LITER_[1:] if i != ''])
        except:
            ENG_LANG_ARTS_LITER = [i for i in ENG_LANG_ARTS_LITER_[1:] if i != '']
        if ENG_LANG_ARTS_LITER_ != []:
            DICT.update({ENG_LANG_ARTS_LITER_[0]:ENG_LANG_ARTS_LITER})
    
        word = 'Reading/Language Arts'
        READ_LANG_ARTS = []
        for i in LST:
            try:
                SUBJECTS.remove('Reading/Language Arts')
            except:
                pass
            if word in i and 'Yes' in i:
              READ_LANG_ARTS.append(word)
              st_ = i.replace('Yes', '')
              st_ = st_.replace(' 0', '')
              st_ = st_.replace(' .0', '')
              st_ = st_.replace('%', '')
              READ_LANG_ARTS.append(" ".join((st_.split(word)[1]).split()))
              new_lst = LST[LST.index(i)+1:]
              for j in new_lst:
                if any(s in j for s in SUBJECTS) == False:
                    READ_LANG_ARTS.append(j)
                else:
                    break
              break
        try:
            READ_LANG_ARTS_ = TEXT_CLEANER([i for i in READ_LANG_ARTS[1:] if i != ''])
        except:
            READ_LANG_ARTS_ = [i for i in READ_LANG_ARTS[1:] if i != '']
        if READ_LANG_ARTS != []:
            DICT.update({READ_LANG_ARTS[0]:READ_LANG_ARTS_})
    
        word = 'Mathematics'
        MATH = []
        for i in LST:
            try:
                SUBJECTS.remove('Mathematics')
            except:
                pass
            if word in i and 'Yes' in i:
              MATH.append(word)
              st_ = i.replace('Yes', '')
              st_ = st_.replace(' 0', '')
              st_ = st_.replace(' .0', '')
              st_ = st_.replace('%', '')
              st_ = " ".join(st_.split())
              try:
                  MATH.append(st_.split(' ', 1)[1])
              except:
                  MATH.append('')
              new_lst = LST[LST.index(i)+1:]
              for j in new_lst:
                if any(s in j for s in SUBJECTS) == False:
                    MATH.append(j)
                else:
                    break
              break
        try:
            MATH_ = TEXT_CLEANER([i for i in MATH[1:] if i != ''])
        except:
            MATH_ = [i for i in MATH[1:] if i != '']
        if MATH != []:
            DICT.update({MATH[0]:MATH_})
    
        word = 'Science'
        SCIENCE = []
        for i in LST:
            try:
                SUBJECTS.remove('Science')
            except:
                pass
            if word in i and 'Yes' in i:
              SCIENCE.append(word)
              st_ = i.replace('Yes', '')
              st_ = st_.replace(' 0', '')
              st_ = st_.replace(' .0', '')
              st_ = st_.replace('%', '')
              st_ = " ".join(st_.split())
              try:
                  SCIENCE.append(st_.split(' ', 1)[1])
              except:
                  SCIENCE.append('')
              new_lst = LST[LST.index(i)+1:]
              for j in new_lst:
                if any(s in j for s in SUBJECTS) == False:
                    SCIENCE.append(j)
                else:
                    break
              break
        try:
            SCIENCE_ = TEXT_CLEANER([i for i in SCIENCE[1:] if i != ''])
        except:
            SCIENCE_ = [i for i in SCIENCE[1:] if i != '']
        if SCIENCE != []:
            DICT.update({SCIENCE[0]:SCIENCE_})
    
        word = 'History-Social Science'
        HIST_SOCIAL_SC = []
        for i in LST:
            try:
                SUBJECTS.remove('History-Social Science')
            except:
                pass
            if word in i and 'Yes' in i:
              HIST_SOCIAL_SC.append(word)
              st_ = i.replace('Yes', '')
              st_ = st_.replace(' 0', '')
              st_ = st_.replace(' .0', '')
              st_ = st_.replace('%', '')
              HIST_SOCIAL_SC.append(" ".join((st_.split(word)[1]).split()))
              new_lst = LST[LST.index(i)+1:]
              for j in new_lst:
                if any(s in j for s in SUBJECTS) == False:
                    HIST_SOCIAL_SC.append(j)
                else:
                    break
              break    
        try:
            HIST_SOCIAL_SC_ = TEXT_CLEANER([i for i in HIST_SOCIAL_SC[1:] if i != ''])
        except:
            HIST_SOCIAL_SC_ = [i for i in HIST_SOCIAL_SC[1:] if i != '']   
        if HIST_SOCIAL_SC != []:
            DICT.update({HIST_SOCIAL_SC[0]:HIST_SOCIAL_SC_})
    
        return DATA['SCHOOL'], DATA['DISTRICT'], DATA['CDS_CODE'], DATA['COLLECTED_DATE'], DICT
    
    #-----------------------GET ROWS FOR SUBJECTS------------------------#
    def GET_ROWS(self, path):
        Data = self.SENT_RET(path)
        OUT = []
        for k, v in zip(Data[4].keys(), Data[4].values()):
            if v != []:
                for s in v:
                    s = re.sub('[()*.;:]', '', s)
                    s = s.replace('Grades', '')
                    s = s.replace('Grade', '')
                    s = s.replace('Adopted', '')
                    GRADE = []
                    DATE  = []
                    hype_num = re.findall(r'\d{1,2}-\d{1,2}', s)
                    GRADE.append(hype_num)
                    date     = re.findall('\d[0-9]\d\d', s)
                    DATE.append(date)
                    hype_date= re.findall(r'\s\d{4}-\d{4}\s', s)
                    DATE.append(hype_date)
                    K_num    = re.findall(r'\sK-\d{1,2}', s)
                    GRADE.append(K_num)
                    TK_num   = re.findall(r'\sTK-\d{1,2}', s)
                    GRADE.append(TK_num)
                    TK   = re.findall(r'\sTK', s)
                    GRADE.append(TK)
                    Dub_num  = re.findall(r'\s\d[0-9][^\d):]', s)
                    GRADE.append(Dub_num)
                    sing_num = re.findall(r'\s\d{1}[^\d-]', s)
                    GRADE.append(sing_num)                
                    words_eng = ['First', 'Second', 'Third', 'Fourth', 'Fifth', 'Sixth', 'Seventh', 'Eighth', 'Ninth', 'Tenth']
                    Eng_num  = [e for e in words_eng if e in s]
                    GRADE.append(Eng_num)
                    if hype_num != [] or K_num != [] or TK_num != [] or Dub_num != [] or sing_num != [] or Eng_num != [] or TK != []:
                        grade = [e for e in GRADE if e != []]
                        if date != [] or hype_date != []:
                            Date= [e for e in DATE if e != []]
                            s = s.replace(grade[0][0], '')
                            s = s.replace(Date[0][0], '')
                            s = re.sub('[-]', '', s)
                            row = [Data[0], Data[1], Data[2], Data[3], k, s, grade[0][0], Date[0][0]]
                            OUT.append(row)
                        else:
                            s = s.replace(grade[0][0], '')
                            row = [Data[0], Data[1], Data[2], Data[3], k, s, grade[0][0], '']
                            OUT.append(row)
                    elif date != [] or hype_date != []:
                        Date= [e for e in DATE if e != []]
                        s = s.replace(Date[0][0], '')
                        if len(s.split()) > 1:
                            row = [Data[0], Data[1], Data[2], Data[3], k, s, '', Date[0][0]]
                            OUT.append(row)
                                
        return OUT      
    #---------------MAIN FUNCTION TO COLLECT ALL FUNCTIONS-------------#
    def main(self):
        path = self.path
        hdr = ['School', 'District', 'CDS Code', 'Collected Date', 'Subject', 'Curriculum', 'Grades', 'Adoption Year']
        pth = self.load_pdfs(path)
        try:
            with open('Output.csv', 'w', newline = '') as output_csv:
                # initialize rows writer
                csv_writer = csv.writer(output_csv)
                # write headers to the file
                csv_writer.writerow(hdr)
                for p in tqdm(pth):
                    Pth = path+'/'+p
                    nest_lst = self.GET_ROWS(Pth)
                    if nest_lst != []:
                        csv_writer.writerows(nest_lst)
                    else:
                        print('\nThe PDF that is skipped is: ', p)
        except:
            pass
        return          
