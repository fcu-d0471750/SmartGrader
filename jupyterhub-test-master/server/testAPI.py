from flask import Flask, request
from nltk.metrics.distance import jaccard_distance
from nbgrader.api import Gradebook, MissingEntry
from Levenshtein import distance
from flask import jsonify
import pandas as pd
import datetime
import difflib
import json
import os
import re

def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = "Content-Type"
    return response
    
app = Flask(__name__)
app.after_request(after_request)

# Done
@app.route('/GetCode/<nid>', methods=['POST'])
def GetCode(nid):
    # POST data receive
    data = request.json

    # save path
    base_url = "D:/workspace/user/"
    if not os.path.exists(base_url + nid):
        os.makedirs(base_url + nid)
    data['code'] = data['code'].replace('\u00a0\n', '')
    # get compile time
    data["time"] = str(datetime.datetime.now())

    # write to log
    fp = open(base_url + nid + "/jupyterhub-" + str(datetime.date.today()) + ".log", "a")
    fp.writelines(json.dumps(data) + "\n")
    fp.close()
    return data

# Done
@app.route('/ErrorMsg/<nid>', methods=['POST'])
def ErrorMsg(nid):
    # POST data receive
    data = request.json

    # save path
    base_url = "D:/workspace/user/"

    # clean traceback data
    reaesc = re.compile(r'\x1b[^m]*m')
    new_text = []
    for i in data["traceback"]:
        new_text.append(reaesc.sub('', i))
    data["traceback"] = new_text

    # write to log
    fname = base_url + nid + "/jupyterhub-" + str(datetime.date.today()) + ".log"
    lines = []
    log = {}
    with open(fname, 'r') as f:
        lines = f.readlines()
        for line_count in range(0, len(lines)):
            log = json.loads(lines[line_count])
            if log['msg_id'] == data['msg_id']:
                for key in data:
                    if key != 'msg_id':
                        log[key] = data[key]
                lines[line_count] = json.dumps(log) + "\n"
                break
    with open(fname, 'w') as f:
        for line in lines:
            f.writelines(line)

    error_line_split = re.compile(r' \(<\S+-\S+-\S+-\S+>, \S+ ')
    error_pair = error_line_split.split(str(log['evalue']))
    replace = re.sub(r"\'\S+\'", "VAR", error_pair[0])
    replace = re.sub(r"\'[\S ]+\'", "VAR", replace)
    replace = re.sub(r"[0-9]+", "NUMBER", replace)
    replace = re.sub(r"can't assign to [\S ]*", "can't assign to", replace)
    try:
        temp = replace.split('.')
        error_pair[0] = temp[0]
    except:
        pass

    error_pair[0] = replace

    try:
        error_pair[1] = int(error_pair[1].replace(")", ""))
    except:
        if len(error_pair) == 1:
            error_pair.append(-1)
        else:
            error_pair[1] = -1
        pass

    print()
    print(error_pair)
    print(log['code'].split('\n')[error_pair[1]])

    keyword = []
    # error_line = []
    if error_pair[1] != -1:
        try:
            error_code = log['code'].split('\n')[error_pair[1]]
            tk = tokenlize(error_code)
            #error_line.append(error_code)
            for tk_count in range(0, len(tk)):
                if tk[tk_count][0] == 'FUNCTION' or tk[tk_count][0] == 'KEYWORD':
                    keyword.append(tk[tk_count][1])
        except:
            pass

    print(keyword)

    knowledgebase = pd.read_excel("D:/workspace/data/test_data/knowledgebase.xlsx", encoding='utf-8')

    knowledgebase = knowledgebase[knowledgebase.ename == log['ename']]
    knowledgebase = knowledgebase.reset_index(drop=True)

    guide = {'guide':'', 'link_name':[], 'link':[]}
    
    for knowledgebase_count in range(0, len(knowledgebase)):
        if distance(error_pair[0], knowledgebase.iloc[knowledgebase_count].evalue) == 0:
            if log['ename'] == 'SyntaxError' and error_pair[0] == 'invalid syntax':
                guide['guide'] = knowledgebase.iloc[knowledgebase_count].guide

                tutorial_candidate = {'difference':[], 'count':[]}
                knowledgebase_tutorial = pd.read_excel("D:/workspace/data/test_data/knowledgebase_tutorial.xlsx", encoding='utf-8')
                
                for tutorial_count in range(0, len(knowledgebase_tutorial)):
                    difference = jaccard(set(keyword), set(eval(knowledgebase_tutorial.iloc[tutorial_count].keyword)))
                    tutorial_candidate['difference'].append(difference)
                    tutorial_candidate['count'].append(tutorial_count)
                
                max_difference = max(tutorial_candidate['difference'])

                if max_difference != 0:
                    for diff_count in range(0, len(tutorial_candidate['difference'])):
                        if tutorial_candidate['difference'][diff_count] == max_difference:
                            if knowledgebase_tutorial.iloc[diff_count].link_name in guide['link_name'] and knowledgebase_tutorial.iloc[diff_count].link in guide['link']:
                                pass
                            else:
                                guide['link_name'].append(knowledgebase_tutorial.iloc[diff_count].link_name)
                                guide['link'].append(knowledgebase_tutorial.iloc[diff_count].link)
                else:
                    pass
            else:
                guide['guide'] = knowledgebase.iloc[knowledgebase_count].guide
                guide['link_name'].append(knowledgebase.iloc[knowledgebase_count].link_name)
                guide['link'].append(knowledgebase.iloc[knowledgebase_count].link)

    return guide

@app.route('/GetStudents', methods=['GET'])
def GetStudents():
    with Gradebook('sqlite:///test/gradebook.db') as gb:
        print(gb.course_id)
    return {}

# Done
@app.route('/GetAssignmentList', methods=['GET'])
def GetAssignmentList():
    assignment_list = []
    with Gradebook('sqlite:///test/gradebook.db') as gb:
        for assignment in gb.assignments:
            temp_dict = {}
            temp_dict["assignment"] = assignment.name
            temp_dict["problem"] = []
            for notebook in assignment.notebooks:
                temp_dict["problem"].append(notebook.name)
            assignment_list.append(temp_dict)
    return jsonify(assignment_list)

# 缺少學生班級、學院
@app.route('/GetGrades', methods=['GET'])
def GetGrades():
    grade_dict = {"course_id":"1081Python", "data":[], "assignment_list":[]}
    with Gradebook('sqlite:///test/gradebook.db') as gb:
        for assignment in gb.assignments:
            grade_dict["assignment_list"].append(assignment.name)
        for student in gb.students:
            temp_dict = {}
            if (student.last_name != None) & (student.first_name != None):
                temp_dict['nid']= student.id
                temp_dict["name"] = student.last_name + student.first_name
                temp_dict["assignment_score"] = {}
                temp_dict["assignment_score"]["average_score"] = student.score / len(gb.assignments)
                for assignment in gb.assignments:
                    try:
                        submission = gb.find_submission(assignment.name, student.id)
                        temp_dict["assignment_score"][submission.assignment.name] = submission.score
                    except MissingEntry:
                        temp_dict["assignment_score"][assignment.name] = 0.0
                grade_dict['data'].append(temp_dict)
    return jsonify([grade_dict])

# Done
@app.route('/GetCodeDiff', methods=['POST'])
def GetCodeDiff():
    nid = request.args.get('nid', None)
    problem_name  = request.args.get('problem', None)
    count = request.args.get('count', 0)
    log_df = pd.read_csv("D:/workspace/data/csv/" + problem_name + ".csv", encoding='utf-8')
    log_df = log_df[log_df.nid == nid]
    
    if nid not in set(log_df.nid.to_list()) or problem_name == None:
        return {'error':'nid 或 problem 輸入錯誤'}
    elif int(count) < len(log_df):
        d = difflib.Differ() 
        lines_1 = log_df.iloc[int(count)].code.splitlines()
        lines_2 = log_df.iloc[int(count) + 1].code.splitlines()
        diff = list(d.compare(lines_1, lines_2))
        for i in range(0, len(diff)):
            print(diff[i], i)

        del_count = []
        for i in range(0, len(diff)):
            if len(diff[i]) != 0:
                if diff[i][0] == '?':
                    del_count.append(i)
        multipop(diff, del_count)
        return {'total_count':len(log_df), 'code1':lines_1, 'code2':lines_2, 'diff':diff}
    else:
        return {'error':"無下筆資料"}

@app.route('/GetStudentData', methods=['POST'])
def GetStudentData():
    # POST data receive
    nid  = request.args.get('nid', None)
    assignment_name  = request.args.get('assignment', None)
    problem_name  = request.args.get('problem', None)
    if nid != None or problem_name != None:
        student_data = get_student_data(nid, assignment_name, problem_name)
        return student_data
    else:
        return {"error":"未傳入學號、作業名稱以及問題名稱"}

# Partial Done, 缺少學生班級、學院
@app.route('/GetAssignmentGrade', methods=['POST'])
def GetAssignmentGrade():
    assignment_name  = request.args.get('assignment', None)
    if assignment_name != None:
        try:
            grade_dict = {}
            with Gradebook('sqlite:///test/gradebook.db') as gb:
                assignment = gb.find_assignment(assignment_name)
                for student in gb.students:
                    if (student.last_name != None) & (student.first_name != None):
                        grade_dict[student.id]= {}
                        grade_dict[student.id]["name"] = student.last_name + student.first_name
                    else:
                        grade_dict[student.id]= {}
                        grade_dict[student.id]['name'] = ""
                    grade_dict[student.id]['duedate'] = assignment.duedate
                    try:
                        submission = gb.find_submission(assignment.name, student.id)
                    except MissingEntry:
                        grade_dict[student.id]['timestamp'] = None
                        grade_dict[student.id]['score'] = 0.0
                    else:
                        grade_dict[student.id]['timestamp'] = submission.timestamp
                        grade_dict[student.id]['score'] = submission.score
                    
                    grade_dict[student.id]['max_score'] = assignment.max_score
                    
                    for notebook in submission.notebooks:
                        try:
                            grade_dict[student.id][notebook.name + '_score'] = notebook.score
                        except:
                            grade_dict[student.id][notebook.name + '_score'] = 0.0
            return grade_dict
        except:
           return {"error":"作業名稱錯誤"}
    else:
        return {"error":"未輸入作業名稱"}

# Done
@app.route('/GetErrorTypeMsg', methods=['POST'])
def GetErrorTypeMsg():
    # POST data receive
    nid  = request.args.get('nid', None)
    problem_name  = request.args.get('problem', None)

    if nid != None and problem_name != None:
        error_log_df = pd.read_excel("D:/workspace/data/test_data/error_log.xlsx", encoding='utf-8')
        if nid.lower() not in set(error_log_df.username.to_list()):
            return {"error":"學號輸入錯誤"}
        else:
            error_log_df = error_log_df[(error_log_df.username == nid.lower()) & (error_log_df.file_name == problem_name)]

            if len(error_log_df) == 0:
                return {}
            else:
                ename_dummies = pd.get_dummies(error_log_df['ename']).sum()
                response = {'ename':[], 'count':[]}
                for ename, count in ename_dummies.items():
                    response['ename'].append(ename)
                    response['count'].append(count)
                return jsonify([response])
    elif nid == None and problem_name != None:
        error_log_df = pd.read_excel("D:/workspace/data/test_data/error_log.xlsx", encoding='utf-8')
        error_log_df = error_log_df[error_log_df.file_name == problem_name]

        if len(error_log_df) == 0:
            return {}
        else:
            ename_dummies = pd.get_dummies(error_log_df['ename']).sum()
            response = {'ename':[], 'count':[]}
            for ename, count in ename_dummies.items():
                response['ename'].append(ename)
                response['count'].append(count)
            return jsonify([response])
    else:
        return {"error":"未傳入學號及問題名稱"}

# Done
def jaccard(a, b):
    c = a.intersection(b)
    return float(len(c)) / (len(a) + len(b) - len(c))

def get_student_data(nid, assignment_name, problem_name):
    log_df = pd.read_csv("D:/workspace/data/test_data/log.csv", encoding='utf-8')

    if nid not in set(log_df.username.to_list()):
        return {}
    else:
        student_log_df = log_df[((log_df.username == nid) & (log_df.file_name == problem_name))]
        
        student_df = pd.read_excel("D:/workspace/data/test_data/1081Python_name.xlsx", encoding='utf-8')
        student_df = student_df.drop(['grade', 'dept_detail'], axis=1)
        
        student_index = student_df[student_df.nid == nid.upper()].index
        student_dict = student_df.iloc[student_index].to_dict('index')[0]
        student_dict["exec_counts"] = len(student_log_df)
        assignment_df = pd.read_csv("D:/workspace/data/test_data/course_data/problem_grade/" + assignment_name + "_grades.csv")
        assignment_df = assignment_df[assignment_df["學號"] == nid]
        print(assignment_df)
        student_dict["problem_grade"] = int(assignment_df[problem_name + " 成績"])
        print(student_dict)
        
        return student_dict

# Done
def tokenlize(code):
    keywords = ['False', 'await', 'else', 'import', 'pass', 'None', 'break', 'except', 'in', 'raise', 'True', 'class', 'finally', 
                'is', 'return', 'and', 'continue', 'for', 'lambda', 'try', 'as', 'def', 'from', 'nonlocal', 'while', 'assert', 
                'del', 'global', 'not', 'with', 'async', 'elif', 'if', 'or', 'yield']

    built_in_function = ['abs', 'delattr', 'hash', 'memoryview', 'set', 'all', 'dict', 'help', 'min', 'setattr', 'any', 'dir',
                         'hex', 'next', 'slice', 'ascii', 'divmod', 'id', 'object', 'sorted', 'bin', 'enumerate', 'input', 'oct',
                         'staticmethod', 'bool', 'eval', 'int', 'open', 'str', 'breakpoint', 'exec', 'isinstance', 'ord', 'sum',
                         'bytearray', 'filter', 'issubclass', 'pow', 'super', 'bytes', 'float', 'iter', 'print', 'tuple', 'callable',
                         'format', 'len', 'property', 'type', 'chr',  'frozenset', 'list', 'range', 'vars', 'classmethod', 'getattr',
                         'locals', 'repr', 'zip', 'compile', 'globals', 'map', 'reversed', '__import__', 'complex', 'hasattr', 'max',
                         'round']

    tokens = []                               # for string tokens
    code_unit_list = re.findall("\s*(\d+|\w+|.)", code)
    # Loop through each source code word
    for unit_count in range(0, len(code_unit_list)):

        # This will check if a token has keyword
        if code_unit_list[unit_count] in keywords: 
            tokens.append(['KEYWORD', code_unit_list[unit_count]])
            continue
        
        # This will check if a token has built-in fuction
        if code_unit_list[unit_count] in built_in_function: 
            tokens.append(['FUNCTION', code_unit_list[unit_count]])
            continue
        
        # This will look for an identifier which would be just a word
        elif re.match("[a-z]", code_unit_list[unit_count]) or re.match("[A-Z]", code_unit_list[unit_count]):
            tokens.append(['IDENTIFIER', code_unit_list[unit_count]])
            continue

        # This will look for an operator
        elif code_unit_list[unit_count] in '*-/+%=':
            tokens.append(['OPERATOR', code_unit_list[unit_count]])
            continue

        # This will look for integer items and cast them as a number
        elif re.match("[0-9]+", code_unit_list[unit_count]):
            tokens.append(["INTEGER", code_unit_list[unit_count]])
            continue
            
        elif re.match("[.\'\"()]", code_unit_list[unit_count]):
            tokens.append(["SEPARATOR", code_unit_list[unit_count]])
            continue

    return tokens

def multipop(yourlist, itemstopop):
    result = []
    itemstopop.sort()
    itemstopop = itemstopop[::-1]
    for x in itemstopop:
        result.append(yourlist.pop(x))
    return result

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10002, debug=True)
