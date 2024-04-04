import requests
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import get_template
import sys
import random

from django.views.decorators.clickjacking import xframe_options_exempt

sys.path.append("..")
import nltk

nltk.download('stopwords')
nltk.download('punkt')
import sqlite3
import os
import re
import string
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import TweetTokenizer
import itertools
import logging
import time
from typing import Optional, Dict, Union

from nltk import sent_tokenize, TweetTokenizer

import torch
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizer,
)

# Create your views here.
from transformers import pipeline
from transformers.pipelines import SUPPORTED_TASKS
from .pipelines import pipeline

nlp = pipeline("multitask-qa-qg")
glo = {}
glo['new'] = []
glo['system_num'] = 10
stu = {}
stulist = []


#############################################################################################            教師端
def go_home(request):  ##首頁
    glo['now_account'] = ''
    return render(request, 'home.html')


def teacher_login(request):  ##教師端登入頁面
    return render(request, 'teacher_login.html')


def teacher_login_(request):  ##教師登入後台
    conn = sqlite3.connect(os.path.dirname(__file__) + "\database02.db")  # 建立資料庫連線
    data = request.POST
    if data.get("submit") == "註冊":
        return render(request, 'teacher_register.html')
    elif data.get("submit") == "登入":
        account = request.POST['account']
        if '0' <= account[0] <= '9':
            account = 'account_' + account
        cursor = conn.cursor()
        sqlstr = "select account,password,job from account"
        cursor = cursor.execute(sqlstr)
        for row in cursor:
            if account == row[0] and request.POST['password'] == row[1]:
                if row[2] == 'teacher':
                    return render(request, 'teacher_choice.html')
        return render(request, 'teacher_login.html')
    else:
        return render(request, 'home.html')


def teacher_register(request):  ##教師註冊後台
    if request.POST["verify"] != '0000':
        return render(request, 'teacher_register.html')
    account = request.POST['account']
    if '0' <= account[0] <= '9':
        account = 'account_' + account
    conn = sqlite3.connect(os.path.dirname(__file__) + "\database02.db")  # 建立資料庫連線
    cursor = conn.cursor()
    sqlstr = "CREATE TABLE IF NOT EXISTS account ('account' TEXT ,'password' TEXT ,'job' TEXT )"
    cursor.execute(sqlstr)
    sqlstr = "select account from account"
    cursor = cursor.execute(sqlstr)
    for row in cursor:
        if account == row[0]:
            return render(request, 'teacher_register.html')
    sqlstr = "insert into account values ('" + account + "','" + request.POST["password"] + "','teacher')"
    cursor.execute(sqlstr)
    conn.commit()
    return render(request, 'teacher_login.html')


def teacher_create(request):  ##教師端產生頁面
    return render(request, 'teacher_create.html')


def teacher_create_(request):  ##教師端產生後台
    title = request.POST['title'].strip()
    system_num = glo['system_num']
    if title == '':
        glo['system_num'] = glo['system_num'] + 1
        title = 'title_' + str(system_num) + '_system'
    if '0' <= title[0] <= '9':
        title = 'title_' + title
    title = title.replace(' ', '_')
    type_ = request.POST["type"]
    text = request.POST["passage"]
    text = re.sub(r"\[\d*[a-z]*\]", "", text)  # 刪掉類似[1]
    context = {}
    if type_ == 'exam':
        type = '考試'
    elif type_ == 'test':
        type = '自我練習'
    context['type'] = type

    glo['now_type'] = type

    if title.startswith('title_'):
        context['title'] = title[6:]
    else:
        context['title'] = title
    context['text'] = text
    glo['now_title'] = title
    glo['text'] = text

    conn = sqlite3.connect(os.path.dirname(__file__) + "\database01.db")  # 建立資料庫連線
    cursor = conn.cursor()  # 建立 cursor 物件

    sqlstr = "CREATE TABLE IF NOT EXISTS title ('title' TEXT, 'passage' TEXT, 'type' TEXT)"
    cursor.execute(sqlstr)

    sqlstr = "select title from title"
    cursor = cursor.execute(sqlstr)
    for row in cursor:
        if title == row[0]:
            return render(request, 'teacher_create.html', context)

    sqlstr = "CREATE TABLE IF NOT EXISTS " + title + " ('id' TEXT,'A' TEXT ,'B' TEXT,'C' TEXT)"  ## A question, B answer, C mark answer in string
    cursor.execute(sqlstr)

    text = text.replace("'", "''")  ##### 將 ' 改成 '' ###########################################
    results = nlp(text)
    num = len(results)
    ans = []
    qu = []
    n = 0

    sqlstr = "insert into title (title, passage, type)" \
             "values('" + title + "','" + text + "','" + type_ + "')"
    cursor.execute(sqlstr)
    conn.commit()

    for r in results:
        if r['answer'].startswith('<pad>'):  # 若開頭是<pad>
            r['answer'] = r['answer'][6:]
        str_list = text.split('.')
        # strr = ''
        # for s in str_list:
        #     if s.find(r['answer']) >= 0:
        #         strr = s
        #         break
        # context['strr'] = strr
        ans.append(r['answer'])
        qu.append(r['question'])
        # sqlstr = "insert into " + title + " (id, A, B, C)" \
        #                                   "values ('" + str(n) + "','" + r['question'] + "','" + r[
        #              'answer'] + "','" + strr + "')"
        # cursor.execute(sqlstr)
        # conn.commit()
        n = n + 1

    glo["qu"] = qu
    glo["ans"] = ans

    context['results'] = zip(range(n), qu, ans)
    context['num'] = num
    glo['total_num'] = num
    conn.close()
    return render(request, 'teacher_topic_number.html', context)

def teacher_topic_number_(request):             ##教師選擇題目數
    get_num = int(request.POST['number'].strip())
    num = glo['total_num']
    title = glo['now_title']
    text = glo['text']
    qu = glo["qu"]
    ans = glo["ans"]
    get_list = []
    for i in range(get_num):
        n = random.randrange(num)
        if n not in get_list:
            get_list.append(n)
        else:
            c = 1
            while(c):
                n = n + 1
                n = n % num
                if n not in get_list:
                    get_list.append(n)
                    c = 0
    conn = sqlite3.connect(os.path.dirname(__file__) + "\database01.db")  # 建立資料庫連線
    cursor = conn.cursor()  # 建立 cursor 物件
    n = 0
    q = []
    a = []
    for i in get_list:
        str_list = text.split('.')
        strr = ''
        for s in str_list:
            if s.find(ans[i]) >= 0:
                strr = s
                break
        q.append(qu[i])
        a.append(ans[i])
        strr = strr.replace("'", "''")   ##### 將 ' 改成 '' ###########################################
        qu[i] = qu[i].replace("'", "''")
        ans[i] = ans[i].replace("'", "''")
        sqlstr = "insert into " + title + " (id, A, B, C)" \
             "values ('" + str(n) + "','" + qu[i] + "','" + ans[i] + "','" + strr + "')"
        cursor.execute(sqlstr)
        conn.commit()
        # q.append(qu[i])
        # a.append(ans[i])
        n = n + 1
    context = {}
    context['num'] = get_num
    context['title'] = title
    context['type'] = glo['now_type']
    context['results'] = zip(range(n), q, a)
    conn.close()
    return render(request, 'teacher_check_qa.html', context)

@xframe_options_exempt
def go_passage(request):  ##查看文章
    title = glo['now_title']
    context = {}
    conn = sqlite3.connect(os.path.dirname(__file__) + "\database01.db")  # 建立資料庫連線
    cursor = conn.cursor()  # 建立 cursor 物件

    sqlstr = "select passage from title WHERE title = '" + title + "'"
    cursor = cursor.execute(sqlstr)
    for row in cursor:
        text = row[0]
    context['text'] = text
    conn.close()
    return render(request, 'passage.html', context)


@xframe_options_exempt
def go_passage_explain(request):  ##查看文章
    title = glo['now_title']
    context = {}
    conn = sqlite3.connect(os.path.dirname(__file__) + "\database01.db")  # 建立資料庫連線
    cursor = conn.cursor()  # 建立 cursor 物件
    ctext = glo['currenttext']
    sqlstr = "select passage from title WHERE title = '" + title + "'"
    cursor = cursor.execute(sqlstr)
    context['first_text'] = ""
    context['medium'] = ""
    context['later_text'] = ""
    check = False
    for row in cursor:
        text = row[0]

    # context['text'] = text
    # return HttpResponse(ctext)
    str_list = text.split('.')
    for r in str_list:
        if (r == ""):
            continue
        if (ctext == r):
            context['medium'] = r + ". "
            check = True
        else:
            if (check):
                context['later_text'] = context['later_text'] + r + ". "
            else:
                context['first_text'] = context['first_text'] + r + ". "
    conn.close()
    return render(request, 'passage_explain.html', context)


def teacher_check_qa_(request):  ##teacher_check_qa網頁的後端
    data = request.POST
    title = glo['now_title']
    # num = glo['total_num']
    selected = []  # 被勾選到的題目

    checked = request.POST.getlist('id')
    for ch in checked:
        selected.append(ch[3:])

    if data.get("button") == "編輯":
        context = {}
        id = []
        q = []
        a = []
        conn = sqlite3.connect(os.path.dirname(__file__) + "\database01.db")  # 建立資料庫連線
        cursor = conn.cursor()
        sqlstr = "select id,A,B from " + title
        cursor = cursor.execute(sqlstr)
        for row in cursor:
            if row[0] in selected:
                id.append(row[0])
                q.append(row[1])
                a.append(row[2])
        context['results'] = zip(id, q, a)
        glo['selected'] = selected
        sqlstr = "select passage from title WHERE title = '" + title + "'"
        cursor = cursor.execute(sqlstr)
        for row in cursor:
            text = row[0]
        context['text'] = text
        cursor.close()
        return render(request, 'teacher_edit.html', context)
    elif data.get("button") == "刪除":
        conn = sqlite3.connect(os.path.dirname(__file__) + "\database01.db")  # 建立資料庫連線
        cursor = conn.cursor()
        for id in selected:
            sqlstr = "delete from " + title + " where id like " + id
            cursor.execute(sqlstr)
            conn.commit()
        conn.close()
        return open_teacher_check_qa(request)
    elif data.get("button") == "完成":
        return render(request, 'teacher_choice.html')


def open_teacher_check_qa(request):  ##打開teacher_check_qa的網頁
    title = glo['now_title']
    conn = sqlite3.connect(os.path.dirname(__file__) + "\database01.db")  # 建立資料庫連線
    cursor = conn.cursor()
    sqlstr = "select id,A,B from " + title
    cursor = cursor.execute(sqlstr)
    # S = "ID, 問題, 答案<br>"
    context = {}
    if title.startswith('title_'):
        context['title'] = title[6:]
    else:
        context['title'] = title
    id = []
    q = []
    a = []
    count = 0
    for row in cursor:
        # S += row[0]+", "+row[1]+", "+row[2]+"<br>"
        id.append(row[0])
        q.append(row[1])
        a.append(row[2])
        count += 1
    context['results'] = zip(id, q, a)
    context['num'] = count
    glo['total_num'] = count
    if count == 0:
        sqlstr = "drop table " + title
        cursor.execute(sqlstr)
        conn.commit()
        sqlstr = "delete from title where title like '" + title + "'"
        cursor.execute(sqlstr)
        conn.commit()
        conn.close()
        return render(request, 'teacher_choice.html')
    sqlstr = "select passage from title WHERE title = '" + title + "'"
    cursor = cursor.execute(sqlstr)
    for row in cursor:
        text = row[0]
    context['text'] = text
    sqlstr = "select type from title WHERE title = '" + title + "'"
    cursor = cursor.execute(sqlstr)
    for row in cursor:
        type = row[0]
    if type == 'exam':
        type = '考試'
    elif type == 'test':
        type = '自我練習'
    context['type'] = type
    cursor.close()
    return render(request, 'teacher_check_qa.html', context)


def teacher_edit_(request):  ##修改題目的後台
    title = glo['now_title']
    selected = glo['selected']
    new = glo['new']
    text = ''
    context = {}
    id = []
    q = []
    a = []
    for n in selected:
        s = 'id_' + str(n)
        lit = request.POST.getlist(s)
        id.append(str(n))
        q.append(lit[0])
        a.append(lit[1])
    if len(new) != 0:
        for n in new:
            s = 'id_' + str(n)
            lit = request.POST.getlist(s)
            id.append(str(n))
            q.append(lit[0])
            a.append(lit[1])
    data = request.POST
    conn = sqlite3.connect(os.path.dirname(__file__) + "\database01.db")  # 建立資料庫連線
    cursor = conn.cursor()

    last_id = 0
    sqlstr = "select id from " + title
    cursor = cursor.execute(sqlstr)
    for row in cursor:
        last_id = row[0]
    add_id = int(last_id) + 1

    if data.get("submit") == "新增題目":
        sqlstr = "insert into " + title + " (id, A, B)" \
                                          "values ('" + str(add_id) + "','','')"
        cursor.execute(sqlstr)
        conn.commit()
        id.append(str(add_id))
        q.append('')
        a.append('')
        glo['new'].append(str(add_id))
        glo['total_num'] = glo['total_num'] + 1
        context['results'] = zip(id, q, a)

        sqlstr = "select passage from title WHERE title = '" + title + "'"
        cursor = cursor.execute(sqlstr)
        for row in cursor:
            text = row[0]
        context['text'] = text

        return render(request, 'teacher_edit.html', context)
    elif data.get("submit") == "生成問答":
        det = []  ##要移除的問題id
        for n in selected:
            s = "id_" + str(n)
            lit = request.POST.getlist(s)
            lit[0] = lit[0].replace("'", "''")
            lit[1] = lit[1].replace("'", "''")
            if lit[0] == '':
                sqlstr = "delete from " + title + " where id like " + str(n)
                cursor.execute(sqlstr)
                conn.commit()
                det.append(n)
                continue
            sqlstr = "update " + title + " set A='" + lit[0] + "'where id like '" + str(n) + "'"
            cursor.execute(sqlstr)
            conn.commit()
            if lit[1] == '':
                dt = dict()
                dt['question'] = lit[0]
                sqlstr = "select passage from title WHERE title = '" + title + "'"
                cursor = cursor.execute(sqlstr)
                for row in cursor:
                    text = row[0]
                dt['context'] = text

                ans = nlp(dt)
                sqlstr = "update " + title + " set B='" + ans + "'where id like '" + str(n) + "'"
                cursor.execute(sqlstr)
                conn.commit()
            else:
                sqlstr = "update " + title + " set B='" + lit[1] + "'where id like '" + str(n) + "'"
                cursor.execute(sqlstr)
                conn.commit()
        for n in new:
            s = "id_" + str(n)
            lit = request.POST.getlist(s)
            lit[0] = lit[0].replace("'", "''")
            lit[1] = lit[1].replace("'", "''")
            if lit[0] == '':
                sqlstr = "delete from " + title + " where id like " + str(n)
                cursor.execute(sqlstr)
                conn.commit()
                det.append(n)
                continue
            sqlstr = "update " + title + " set A='" + lit[0] + "'where id like '" + str(n) + "'"
            cursor.execute(sqlstr)
            conn.commit()
            if lit[1] == '':
                dt = dict()
                dt['question'] = lit[0]
                sqlstr = "select passage from title WHERE title = '" + title + "'"
                cursor = cursor.execute(sqlstr)
                for row in cursor:
                    text = row[0]
                dt['context'] = text

                ans = nlp(dt)
                sqlstr = "update " + title + " set B='" + ans + "'where id like '" + str(n) + "'"
                cursor.execute(sqlstr)
                conn.commit()
            else:
                sqlstr = "update " + title + " set B='" + lit[1] + "'where id like '" + str(n) + "'"
                cursor.execute(sqlstr)
                conn.commit()
        for n in det:
            if n in selected:
                selected.remove(n)
            if n in new:
                new.remove(n)
        id = []
        q = []
        a = []
        sqlstr = "select id,A,B from " + title
        cursor = cursor.execute(sqlstr)
        for row in cursor:
            if row[0] in selected:
                id.append(row[0])
                q.append(row[1])
                a.append(row[2])
            if row[0] in new:
                id.append(row[0])
                q.append(row[1])
                a.append(row[2])
        context['results'] = zip(id, q, a)

        sqlstr = "select passage from title WHERE title = '" + title + "'"
        cursor = cursor.execute(sqlstr)
        for row in cursor:
            text = row[0]
        context['text'] = text
        return render(request, 'teacher_edit.html', context)
        # return HttpResponse("完成編輯!!")

    elif data.get("submit") == "完成編輯":
        sqlstr = "select passage from title WHERE title = '" + title + "'"
        cursor = cursor.execute(sqlstr)
        for row in cursor:
            text = row[0]
        for n in selected:
            s = "id_" + str(n)
            lit = request.POST.getlist(s)
            lit[0] = lit[0].replace("'", "''")
            lit[1] = lit[1].replace("'", "''")
            if lit[0] == '':
                sqlstr = "delete from " + title + " where id like " + str(n)
                cursor.execute(sqlstr)
                conn.commit()
                continue
            sqlstr = "update " + title + " set A='" + lit[0] + "'where id like '" + str(n) + "'"
            cursor.execute(sqlstr)
            conn.commit()
            if lit[1] == '':
                dt = dict()
                dt['question'] = lit[0]
                sqlstr = "select passage from title WHERE title = '" + title + "'"
                cursor = cursor.execute(sqlstr)
                for row in cursor:
                    text = row[0]
                dt['context'] = text

                ans = nlp(dt)
                sqlstr = "update " + title + " set B='" + ans + "'where id like '" + str(n) + "'"
                cursor.execute(sqlstr)
                conn.commit()
                str_list = text.split('.')  ######找來源句子
                strr = ''
                for s in str_list:
                    if s.find(ans) >= 0:
                        strr = s
                        break
                sqlstr = "update " + title + " set C='" + strr + "'where id like '" + str(n) + "'"
                cursor.execute(sqlstr)
                conn.commit()
            else:
                sqlstr = "update " + title + " set B='" + lit[1] + "'where id like '" + str(n) + "'"
                cursor.execute(sqlstr)
                conn.commit()
                str_list = text.split('.')  ######找來源句子
                strr = ''
                for s in str_list:
                    if s.find(lit[1]) >= 0:
                        strr = s
                        break
                sqlstr = "update " + title + " set C='" + strr + "'where id like '" + str(n) + "'"
                cursor.execute(sqlstr)
                conn.commit()
        for n in new:
            s = "id_" + str(n)
            lit = request.POST.getlist(s)
            lit[0] = lit[0].replace("'", "''")
            lit[1] = lit[1].replace("'", "''")
            if lit[0] == '':
                sqlstr = "delete from " + title + " where id like " + str(n)
                cursor.execute(sqlstr)
                conn.commit()
                continue
            sqlstr = "update " + title + " set A='" + lit[0] + "'where id like '" + str(n) + "'"
            cursor.execute(sqlstr)
            conn.commit()
            if lit[1] == '':
                dt = dict()
                dt['question'] = lit[0]
                sqlstr = "select passage from title WHERE title = '" + title + "'"
                cursor = cursor.execute(sqlstr)
                for row in cursor:
                    text = row[0]
                dt['context'] = text

                ans = nlp(dt)
                sqlstr = "update " + title + " set B='" + ans + "'where id like '" + str(n) + "'"
                cursor.execute(sqlstr)
                conn.commit()
                str_list = text.split('.')  ######找來源句子
                strr = ''
                for s in str_list:
                    if s.find(ans) >= 0:
                        strr = s
                        break
                sqlstr = "update " + title + " set C='" + strr + "'where id like '" + str(n) + "'"
                cursor.execute(sqlstr)
                conn.commit()
            else:
                sqlstr = "update " + title + " set B='" + lit[1] + "'where id like '" + str(n) + "'"
                cursor.execute(sqlstr)
                conn.commit()
                str_list = text.split('.')  ######找來源句子
                strr = ''
                for s in str_list:
                    if s.find(lit[1]) >= 0:
                        strr = s
                        break
                sqlstr = "update " + title + " set C='" + strr + "'where id like '" + str(n) + "'"
                cursor.execute(sqlstr)
                conn.commit()
        glo['new'] = []
        glo['selected'] = []
        return open_teacher_check_qa(request)


def go_teacher_choice_title(request):  ##進入teacher_choice_title頁面
    context = {}
    conn = sqlite3.connect(os.path.dirname(__file__) + "\database01.db")  # 建立資料庫連線
    cursor = conn.cursor()
    sqlstr = "select title from title"
    cursor = cursor.execute(sqlstr)
    title = []
    for row in cursor:
        if row[0].startswith('title_'):
            title.append(row[0][6:])
        else:
            title.append(row[0])
    context['title'] = title
    return render(request, 'teacher_choice_title.html', context)


def teacher_choice_title_(request):  ##teacher_choice_title的後端
    try:
        title = request.POST['choice']
    except:
        return render(request, 'teacher_choice.html')
    if '0' <= title[0] <= '9':
        title = 'title_' + title
    glo['now_title'] = title
    return open_teacher_check_qa(request)


##############################################################################################                  學生端
def student_login(request):  ##學生端登入頁面
    return render(request, 'student_login.html')


def student_login_(request):  ##學生登入後台
    conn = sqlite3.connect(os.path.dirname(__file__) + "\database02.db")  # 建立資料庫連線
    data = request.POST
    if data.get("submit") == "註冊":
        return render(request, 'student_register.html')
    elif data.get("submit") == "登入":
        account = request.POST['account']
        if '0' <= account[0] <= '9':
            account = 'account_' + account
        cursor = conn.cursor()
        sqlstr = "select account,password,job from account"
        cursor = cursor.execute(sqlstr)
        for row in cursor:
            if account == row[0] and request.POST['password'] == row[1]:
                if row[2] == 'student':
                    glo['now_account'] = account
                    return render(request, 'student_choice.html')
        return render(request, 'student_login.html')
    else:
        return render(request, 'home.html')


def student_register(request):  ##學生註冊後台

    conn = sqlite3.connect(os.path.dirname(__file__) + "\database02.db")  # 建立資料庫連線
    cursor = conn.cursor()
    sqlstr = "CREATE TABLE IF NOT EXISTS account ('account' TEXT ,'password' TEXT ,'job' TEXT )"
    cursor.execute(sqlstr)
    sqlstr = "select account from account"
    cursor = cursor.execute(sqlstr)
    for row in cursor:
        if request.POST["account"] == row[0]:
            return render(request, 'student_register.html')
    account = request.POST['account']
    if '0' <= account[0] <= '9':
        account = 'account_' + account
    sqlstr = "insert into account values ('" + account + "','" + request.POST["password"] + "','student')"
    cursor.execute(sqlstr)
    conn.commit()
    return render(request, 'student_login.html')


def student_choice_title(request):
    context = {}
    conn = sqlite3.connect(os.path.dirname(__file__) + "\database01.db")  # 建立資料庫連線
    cursor = conn.cursor()
    sqlstr = "CREATE TABLE IF NOT EXISTS title ('title' TEXT, 'passage' TEXT, 'type' TEXT)"
    cursor.execute(sqlstr)
    sqlstr = "select title from title"
    cursor = cursor.execute(sqlstr)
    name = []
    for row in cursor:
        if row[0].startswith('title_'):
            name.append(row[0][6:])
        else:
            name.append(row[0])
    context['title'] = name

    return render(request, 'student_choice_title.html', context)


def student_answer(request):
    conn = sqlite3.connect(os.path.dirname(__file__) + "\database01.db")  # 建立資料庫連線
    cursor = conn.cursor()
    try:
        glo['now_title'] = request.POST["choice_title"]
    except:
        return render(request, 'student_choice.html')
    title = glo['now_title']
    title1 = title
    if '0' <= title[0] <= '9':
        title = 'title_' + title
    glo['now_title'] = title
    sqlstr = "select A,id from " + title
    cursor = cursor.execute(sqlstr)
    context = {}
    id = []
    q = []
    showid = []
    global showidtoid
    showidtoid = {}
    for row in enumerate(cursor, start=1):
        q.append(row[1][0])
        id.append(row[1][1])
        showid.append(row[0])
        showidtoid[str(row[0])] = str(row[1][1])
    context['results'] = zip(showid, id, q)

    sqlstr = "select title, type from title"
    cursor = cursor.execute(sqlstr)
    for row in cursor:
        if (glo['now_title'] == row[0]):
            glo['now_type'] = row[1]
            break

    glo['total_id'] = id
    global stu
    global stulist
    stu = {}
    stulist = []
    sqlstr = "select passage from title WHERE title = '" + title + "'"
    cursor = cursor.execute(sqlstr)
    for row in cursor:
        text = row[0]
    context['text'] = text
    glo['now_text'] = context['text']
    sqlstr = "select A, B, C, id from " + title
    cursor = cursor.execute(sqlstr)
    glo['total_num'] = 0
    context['title'] = title1
    check = True
    for row in cursor:
        # if (row[1] == ""):
        #     continue
        if (row[3] and check):
            context['currentQ'] = row[0]
            context['currentA'] = row[1]
            context['currentid'] = row[3]  # true id
            context['currentAS'] = " "
            check = False
        glo['total_num'] += 1
        glo['last_id'] = row[3]
        stu['id'] = row[3]
        stu['question'] = row[0]
        stu['answerC'] = row[1]
        stu['text'] = row[2]
        stu['answerS'] = " "
        stu_copy = stu.copy()
        stulist.append(stu_copy)
    glo['now_id'] = context['currentid']  ##存目前id用於接收答案(id = name)
    context['total_num'] = glo['total_num']
    context['type'] = glo['now_type']
    context['last_id'] = glo['last_id']
    conn.close()
    return render(request, 'student_answer.html', context)


def student_answer_(request):
    conn = sqlite3.connect(os.path.dirname(__file__) + "\database01.db")  # 建立資料庫連線
    cursor = conn.cursor()
    title = glo['now_title']
    title1 = title
    if title.startswith('title_'):
        title1 = title[6:]

    sqlstr = "select A,id from " + title
    cursor = cursor.execute(sqlstr)
    context = {}
    context['last_id'] = glo['last_id']
    id = []
    q = []
    showid = []
    for row in enumerate(cursor, start=1):
        q.append(row[1][0])
        id.append(row[1][1])
        showid.append(row[0])
    context['results'] = zip(showid, id, q)
    context['title'] = title1

    global stulist
    for row in stulist:  # read stu ans
        if (row['id'] == glo['now_id'] and request.POST["choice_id"] != "返回"):
            row['answerS'] = request.POST["answer"]
            break

    if request.POST["choice_id"] == "下一題":
        sqlstr = "select A, B, id from " + title
        cursor = cursor.execute(sqlstr)
        for row in cursor:
            if int(row[2]) > int(glo['now_id']):
                glo['now_id'] = row[2]
                break
    elif request.POST["choice_id"] == "確認答案" or request.POST["choice_id"] == "返回":
        glo['now_id'] = str(int(glo['now_id']))
    elif request.POST["choice_id"] == "繳交":
        conn.close()
        return answer_compared(request)
    else:

        tmp = request.POST["choice_id"]
        # return HttpResponse(showidtoid[tmp])
        glo['now_id'] = str(int(showidtoid[tmp]))  ##存目前id用於接收答案(id = name)

    sqlstr = "select passage from title WHERE title = '" + title + "'"  # get passage
    cursor = cursor.execute(sqlstr)
    for row in cursor:
        text = row[0]
    context['text'] = text
    context['currentid'] = glo['now_id']

    sqlstr = "select A, B, C, id from " + title
    cursor = cursor.execute(sqlstr)
    for row in cursor:
        if (row[3] == context['currentid']):
            context['currentQ'] = row[0]
            context['currentA'] = row[1]
            glo['currenttext'] = row[2]
            break
    # context['total_num'] = str(glo['total_num'] - 1)
    context['type'] = glo['now_type']

    for row in stulist:
        if (row['id'] == glo['now_id']):  # save stu ans
            context['currentAS'] = row['answerS']
            if request.POST["choice_id"] == "確認答案":
                conn.close()
                ansC = text_process(row['answerC'])
                ansS = text_process(row['answerS'])
                leng = len(ansC)
                for ch in ansC:
                    if ch in ansS:
                        ansS.remove(ch)
                        leng = leng - 1
                if leng == 0:
                    return render(request, 'student_answer_check_correct.html', context)
                else:
                    return render(request, 'student_answer_check_error.html', context)
    conn.close()
    return render(request, 'student_answer.html', context)


def answer_compared(request):
    conn = sqlite3.connect(os.path.dirname(__file__) + "\database01.db")  # 建立資料庫連線
    cursor = conn.cursor()
    title = glo['now_title']
    total = glo['total_num']
    topic_size = total
    each_score = round(100.0 / topic_size, 2)
    gain_score = 0.0
    title1 = title
    if title.startswith('title_'):
        title1 = title[6:]
    '''
    correct_ans = []

    for row in stulist:
        correct_ans.append(row['answerC'])

    answer = zip(correct_ans,id)
    '''
    correct = 0
    num = 0
    id = []
    qus = []
    check = []
    user_ans = []
    correct_ans = []
    this_ans_score = []
    ctext = []
    for row in stulist:
        ans = row['answerS']
        ans = text_process(ans)
        corr_ans = text_process(row['answerC'])
        count = len(corr_ans)

        this_score = round(each_score / count, 2)
        find = 0.0
        for c_a in corr_ans:
            if c_a in ans:
                find += 1
                ans.remove(c_a)
                count -= 1
        if count == 0:  ##答對
            check.append('1')
            correct += 1
            ans_score = round(100.0 / topic_size, 2)
        else:  ##答錯
            check.append('0')
            correct = correct
            gain_score += this_score * find
            ans_score = this_score * find

        id.append(row['id'])
        qus.append(row['question'])
        user_ans.append(row['answerS'])
        correct_ans.append(row['answerC'])
        ctext.append(row['text'])
        ans_score = str(ans_score)
        this_ans_score.append(ans_score)
        num += 1
    context = {}
    sqlstr = "select passage from title WHERE title = '" + title + "'"
    cursor = cursor.execute(sqlstr)
    for row in cursor:
        text = row[0]
    context['text'] = text
    context['correct'] = correct
    context['topic_size'] = topic_size
    context['results'] = zip(check, id, qus, user_ans, correct_ans, this_ans_score)
    context['title'] = title1
    score = round(100 * correct / topic_size, 2) + gain_score
    context['score'] = score

    account = str(glo['now_account'])  # 儲存分數
    if (request.POST["choice_id"] == "繳交"):
        conn = sqlite3.connect(os.path.dirname(__file__) + "\database03.db")  # 建立資料庫連線
        cursor = conn.cursor()
        # 建立一個資料表
        sqlstr = "CREATE TABLE IF NOT EXISTS " + account + " ('id' TEXT ,'title' TEXT ,'score' TEXT, 'TF' TEXT, 'qid' TEXT, 'qus' TEXT, 'user_ans' TEXT, 'correct_ans' TEXT, 'this_ans_score' TEXT, 'ctext' TEXT, 'datatime' TEXT)"
        cursor.execute(sqlstr)
        # 新增一筆資料
        sqlstr = "select id from " + account
        cursor = cursor.execute(sqlstr)
        lastid = 0
        for row in cursor:
            lastid = row[0]
        lastid = int(lastid) + 1
        glo['check'] = check
        check = ','.join(check)
        id = ','.join(id)
        qus = ','.join(qus)
        qus = qus.replace("'", "''")
        user_ans = ','.join(user_ans)
        user_ans = user_ans.replace("'", "''")
        correct_ans = ','.join(correct_ans)
        correct_ans = correct_ans.replace("'", "''")
        this_ans_score = ','.join(this_ans_score)
        ctext = '.'.join(ctext)
        ctext = ctext.replace("'","''")
        datatime = time.strftime("%Y-%m-%d %I:%M:%S %p", time.localtime())
        sqlstr = "insert into " + account + " values ('" + str(lastid) + "' , '" + title + "', '" + str(
            score) + "', '" + str(check) + "', '" + str(id) + "', '" + str(qus) + "', '" + str(user_ans) + "', '" + str(
            correct_ans) + "', '" + str(this_ans_score) + "', '" + str(ctext) + "', '" + str(datatime) + "')"
        cursor.execute(sqlstr)
        conn.commit()
        conn.close()

    return render(request, 'student_score.html', context)


def text_process(tweet):  ##答案前處理
    tweet = re.sub(r'^RT[\s]+', '', tweet)
    tweet = re.sub(r'https?:\/\/.*[\r\n]*', '', tweet)
    tweet = re.sub(r'#', '', tweet)
    tokenizer = TweetTokenizer()
    tweet_tokenized = tokenizer.tokenize(tweet)
    stopwords_english = stopwords.words('english')
    tweet_processsed = [word for word in tweet_tokenized
                        if word not in stopwords_english and word not in
                        string.punctuation]
    tweet_processsed_lower = []
    for word in tweet_processsed:
        word = word.lower()
        if word != 'the':
            tweet_processsed_lower.append(word)
    return tweet_processsed_lower


# def student_score(request):
#     return render(request, 'student_choice.html')


def student_choice_score(request):
    context = {}
    account = str(glo['now_account'])
    conn = sqlite3.connect(os.path.dirname(__file__) + "\database03.db")  # 建立資料庫連線
    cursor = conn.cursor()
    sqlstr = "CREATE TABLE IF NOT EXISTS " + account + " ('id' TEXT ,'title' TEXT ,'score' TEXT, 'TF' TEXT, 'qid' TEXT, 'qus' TEXT, 'user_ans' TEXT, 'correct_ans' TEXT, 'this_ans_score' TEXT, 'ctext' TEXT, 'datatime' TEXT)"
    cursor.execute(sqlstr)
    sqlstr = "select id, title, score from " + account
    cursor = cursor.execute(sqlstr)
    realname = []
    score = []
    name = []
    id = []
    count = 0
    for row in cursor:
        if (row[1] not in realname):
            realname.append(row[1])
            score.append(row[2])
            if row[1].startswith('title_'):
                name.append(row[1][6:])
            else:
                name.append(row[1])
            # name.append(row[1])
            id.append(row[0])
            count += 1
        else:
            for i in range(0, count):
                if (row[1] == realname[i]):
                    if (row[2] > score[i]):
                        score[i] = row[2]
                    break
    context['result'] = zip(name, id, score)
    return render(request, 'student_choice_score.html', context)


def student_choice_score2(request):
    context = {}
    try:
        title = request.POST["choice_title"]
    except:
        return render(request, 'student_choice.html')
    account = str(glo['now_account'])
    conn = sqlite3.connect(os.path.dirname(__file__) + "\database03.db")  # 建立資料庫連線
    cursor = conn.cursor()
    # sqlstr = "select id, title, score from " + account
    sqlstr = "select id, title, score, datatime from " + account + " WHERE title = '" + title + "'"
    cursor = cursor.execute(sqlstr)
    score = []
    time = []
    id = []
    for row in cursor:
        score.append(row[2])
        time.append(row[3])
        # name.append(row[1])
        id.append(row[0])
    context['title'] = title
    context['result'] = zip(time, id, score)
    return render(request, 'student_choice_score2.html', context)


def student_choice_see_score(request):
    context = {}
    global stu
    stu = {}
    account = str(glo['now_account'])
    conn = sqlite3.connect(os.path.dirname(__file__) + "\database03.db")  # 建立資料庫連線
    cursor = conn.cursor()

    title = request.POST["choice_title"]
    glo['now_title_id'] = title

    sqlstr = "select id, title, score, qid, qus, user_ans, correct_ans, TF, this_ans_score, ctext from " + account
    cursor = cursor.execute(sqlstr)
    for row in cursor:
        if (title == row[0]):
            context['results'] = zip(row[7].split(','), row[3].split(','), row[4].split(','), row[5].split(','),
                                     row[6].split(','), row[8].split(','))
            stu['qid'] = row[3].split(',')
            stu['qus'] = row[4].split(',')
            stu['user_ans'] = row[5].split(',')
            stu['correct_ans'] = row[6].split(',')
            stu['TF'] = row[7].split(',')
            stu['this_ans_score'] = row[8].split(',')
            stu['ctext'] = row[9].split('.')
            context['title'] = row[1]
            context['score'] = float(row[2])
            break
    conn.close()
    glo['now_title'] = context['title']
    title1 = glo['now_title']
    if title1.startswith('title_'):
        title1 = title1[6:]
    context['title'] = title1
    conn = sqlite3.connect(os.path.dirname(__file__) + "\database01.db")  # 建立資料庫連線
    cursor = conn.cursor()
    sqlstr = "select passage from title WHERE title = '" + glo['now_title'] + "'"
    cursor = cursor.execute(sqlstr)
    for row in cursor:
        text = row[0]
    context['text'] = text
    glo['now_text'] = text
    conn.close()
    return render(request, 'student_choice_see_score.html', context)


def student_choice_see_score_check(request):
    context = {}
    account = str(glo['now_account'])
    quid = request.POST['choice_id']
    if quid == '返回':
        return render(request, 'student_choice.html')
    context['text'] = glo['now_text']
    title = glo['now_title']
    title1 = title
    if title.startswith('title_'):
        title1 = title[6:]
    context['title'] = title1
    context['now_title_id'] = glo['now_title_id']
    count = 0
    for row in stu['qid']:
        if (row == quid):
            context['TF'] = stu['TF'][count]
            context['currentQ'] = stu['qus'][count]
            context['currentAS'] = stu['user_ans'][count]
            context['currentA'] = stu['correct_ans'][count]
            glo['currenttext'] = stu['ctext'][count]
            # return HttpResponse(glo['currenttext'])
            break
        count += 1
    return render(request, 'student_choice_see_score_check.html', context)


def student_score(request):
    quid = request.POST['choice_id']
    if (quid == "返回"):
        return render(request, 'student_choice.html')
    context = {}
    account = str(glo['now_account'])
    title = glo['now_title']
    title1 = title
    if title.startswith('title_'):
        title1 = title[6:]
    context['title'] = title1
    context['text'] = glo['now_text']
    count = 0
    for row in stulist:
        if (row['id'] == quid):
            context['TF'] = glo['check'][count]
            context['currentQ'] = row['question']
            context['currentAS'] = row['answerS']
            context['currentA'] = row['answerC']
            glo['currenttext'] = row['text']

            break
        count += 1

    return render(request, 'student_score_check.html', context)


def student_score_check(request):
    return answer_compared(request);

##############################################################################################################