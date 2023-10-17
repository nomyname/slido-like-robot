# 導入函式庫
import tkinter as tk
import os
import sys
import requests
from tkinter import messagebox
from tkinter.constants import *
from PIL import ImageTk
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
# import pickle
# import namelist
# from namelist import getName,getID
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
# https://youtu.be/gC7Hm_7l27M?t=471


# window.configure(background='white')
# window.geometry('numxnum')

# head_label = tk.Label(window, text = 'Slido 推推小幫手')
# head_label.grid(row=1, columnspan=2)
def get_event_tag(id):
    my_option = Options()
    my_option.add_argument("--headless")
    driver = webdriver.Chrome(options=my_option)  # 在背景運作
    driver.get("https://app.sli.do/")
    event_num_input = driver.find_element(By.ID, "sp__form-input")
    event_num_input.send_keys(id)
    event_num_input.submit()
    time.sleep(1)
    event_tag = driver.current_url.split('event/')[1].split('?')[0]
    return event_tag

def get_uuid(event_tag):
    # endpoint = f"https://app.sli.do/api/v0.5/events?hash={event_tag}"
    endpoint = f"https://app.sli.do/eu1/api/v0.5/app/events?hash={event_tag}"
    res = requests.get(endpoint)
    if res.status_code==200:
        res = res.json()
        # return res[0]['uuid']
        return res['uuid']
    else:
        return False
    
def get_auth(uuid):
    # endpoint = f"https://app.sli.do/api/v0.5/events/{uuid}/auth?attempt=1"
    endpoint = f"https://app.sli.do/eu1/api/v0.5/events/{uuid}/auth"
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    res = requests.post(endpoint, headers=headers)
    #logger.info(f'{res.status_code}, {res.text}')
    if res.status_code==200:
        res = res.json()
        return res['access_token']
    else:
        return False

def getquestion():
    uuid = get_uuid(event_tag)
    bearer = get_auth(uuid)
    url=f'https://app.sli.do/api/v0.5/events/{uuid}/questions'
    headers = {"Content-Type": "application/json;charset=UTF-8","Authorization":f"Bearer {bearer}"}
    res = requests.get(url,headers=headers)
    res=res.json()
    questions, like = [], []
    for i in range(0,len(res)):
        questions.append(res[i]['text'].translate(non_bmp_map))
        like.append(res[i]['score'])
    return questions, like, res

def likes(questionID,event_tag):
    dum1, dum2, res = getquestion()
    event_question_id = res[questionID]['event_question_id'] 
    uuid = get_uuid(event_tag)
    Bearer = get_auth(uuid)
    endpoint = f'https://app.sli.do/eu1/api/v0.5/events/{uuid}/questions/{event_question_id})/like'
    headers = {"Authorization":f'Bearer {Bearer}','X-Client-Id':'fHqw1k2cG1pfEGm','X-Slidoapp-Version':'SlidoParticipantApp/50.56.1 (web)'}
    data = {'score': '1'}
    res = requests.post(endpoint,headers=headers,data=data)

# 打開點讚視窗
def open_vote_window():
    global push_window
    push_button.config(state='disabled')
    push_window = tk.Toplevel(window)
    push_window.title('為當前問題點讚！')
    frame = tk.Frame(push_window)
    frame.pack()

    tk.Label(frame, text = '請選擇欲點讚之問題：').grid(row=0, columnspan=2)
    scrollbar = tk.Scrollbar(frame)
    scrollbar.grid(row=1, column=1, sticky='ns')
    pre_questions = tk.Listbox(frame, selectmode=MULTIPLE, yscrollcommand=scrollbar.set)
    # 有幾個問題跳幾個按鈕選項
    question, like, res = getquestion()
    for i in range(len(question)):
        pre_questions.insert(tk.END, f"{like[i]} {question[i]}")
    pre_questions.grid(row=1, column=0)
    
    scrollbar.config(command=pre_questions.yview)

    tk.Label(frame, text = '請輸入點讚次數(1-20)：').grid(row=2, columnspan=2)
    vote_count = tk.Spinbox(frame, from_=0, to=100)
    vote_count.grid(row=3, columnspan=2)

    def confirm():
        result = messagebox.askokcancel('請確認資訊', '請確認問題及點讚次數正確無誤！\n如需修正請取消並重新輸入。')
        if result == True:
            try:
                like_times = int(vote_count.get())
                if like_times > 20: 
                    messagebox.showerror('', '請輸入1-20的數字')
                    return
            except:
                messagebox.showerror('', '請輸入1-20的數字')
                return
            selected_listbox = [pre_questions.get(i) for i in pre_questions.curselection()]
            for q in selected_listbox:
                # get selection
                try:
                    q = q.split(' ', 1)
                    q_id = question.index(q[1])
                except:
                    messagebox.showerror('', '請選取問題')
                    return
                # like
                processes = []
                with ThreadPoolExecutor(max_workers=20) as executor:
                    for i in range(like_times):
                        processes.append(executor.submit(likes,q_id,event_tag))
            restart()
    # my tag cDjA9R8MDkshkM2BWhGrk7
    cnfrm_btn = tk.Button(frame, text = '確認', command = confirm)
    cnfrm_btn.grid(row=4, columnspan=2)
def postquestion(event_tag,que,num,name,ID,like_num):
    uuid = get_uuid(event_tag)
    bearer = get_auth(uuid)
    headers = {"Content-Type": "application/json;charset=UTF-8","Authorization":f"Bearer {bearer}"}
    if(name):
        url=f'https://app.sli.do/api/v0.5/events/{uuid}/user'
        json = {'name':f'{ID}'}
        res = requests.put(url,headers=headers,json=json)
        anony = 'false'
    else:
        anony = 'true'
    url=f'https://app.sli.do/api/v0.5/events/{uuid}/questions'
    res = requests.get(url,headers=headers)
    res=res.json()
    eventid=res[0]['event_id']
    eventsectionid=res[0]['event_section_id']
    question, like, res = getquestion()
    start_id = len(question)
    for i in range(num):
        #bearer = get_auth(uuid)
        url=f'https://app.sli.do/api/v0.5/events/{uuid}/questions'
        data = {"event_id":f"{eventid}","event_section_id":f"{eventsectionid}","is_anonymous":f"{anony}","path":"/questions","text":f"{que}"}
        headers = {"Content-Type": "application/json;charset=UTF-8","Authorization":f"Bearer {bearer}"}
        res = requests.post(url,json=data,headers=headers)
        for j in range(like_num): likes(start_id + i, event_tag)
        # 3983476
    messagebox.showinfo('', '問題已成功發送且按讚！')
    python = sys.executable
    os.execl(python, python, * sys.argv)

# 打開提問視窗
def open_post_window():
    push_button.config(state='disabled')
    post_window = tk.Toplevel(window)
    post_window.title('提出新問題！')

    tk.Label(post_window, text = '請輸入欲提出之問題：').grid(row=0, sticky=W)
    question_entry = tk.Entry(post_window)
    question_entry.grid(row=1, sticky=W+E)

    tk.Label(post_window, text = '請輸入提問者名稱（匿名提問請留空）：').grid(row=2, sticky=W)
    id_entry = tk.Entry(post_window)
    id_entry.grid(row=3, sticky=W+E)

    tk.Label(post_window, text = '請輸入提問次數：').grid(row=4, sticky=W)
    num_entry = tk.Entry(post_window)
    num_entry.grid(row=5, sticky=W+E)

    tk.Label(post_window, text = '請輸入欲為此問題點讚之次數：').grid(row=6, sticky=W)
    vote_count = tk.Spinbox(post_window, from_=0, to=100)
    vote_count.grid(row=7, sticky=W+E)
    def get_content():
        que = question_entry.get()
        name = id_entry.get()
        try:
            num = int(num_entry.get())
        except:
            messagebox.showerror('', '請輸入提問數')
            return
        if name == '': nn = False
        else: nn = True
        try:
            like_num = int(vote_count.get())
        except:
            messagebox.showerror('', '請輸入按讚數')
            return
        postquestion(event_tag, que, num, nn, name, like_num)
    btn = tk.Button(post_window, text = '確認', command = get_content)
    btn.grid(row=8)

# 顯示選擇按鈕
def show_button():
    global event_tag, show_btn, push_button, push_button
    show_btn = False
    event_id = tag_entry.get()
    try:
        event_tag = get_event_tag(event_id)
    except:
        messagebox.showerror('', '請輸入合法Event ID')
        return
    tag_btn.config(state='disabled')
    # 點讚按鈕
    push_button = tk.Button(window, text = '為當前問題點讚！', width=13, bg='#38AC36', command = open_vote_window)
    push_button.pack(side='left')

    # 提問按鈕
    post_button = tk.Button(window, text = '詢問新問題！', width=13, bg='#38AC36', command = open_post_window)
    post_button.pack(side='right')

# 重新啟動程式
def restart():
    result = messagebox.askyesno('', '問題已推送！\n(Yes)選擇其他問題(No)選擇其他Event')
    if result == True:
        push_window.destroy()
        open_vote_window()
    else:
        python = sys.executable
        os.execl(python, python, * sys.argv)

def main():
    global non_bmp_map, logger, vote_count, ques_count, window, tag_entry, tag_btn
    non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)

    logger = logging.getLogger(__name__)

    vote_count = 0
    ques_count = 0
    # 主視窗
    window = tk.Tk()
    window.title('Slido 推推小幫手')
    logo_img = ImageTk.PhotoImage(file = "slido assistant.png")
    logo = tk.Label(window, image = logo_img)
    logo.pack()
    # get event tag
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    tag = tk.Label(window, text='請輸入Event ID(#xxxxxxx):')
    tag.pack()
    tag_entry = tk.Entry()
    tag_entry.pack()
    tag_btn = tk.Button(text='確認', command=show_button)
    tag_btn.pack()
    window.mainloop()

if __name__ == '__main__':
    main()