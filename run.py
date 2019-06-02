import os
from flask import Flask, redirect, url_for, render_template, request, g, flash
import json
import requests
import datetime


#変数の初期化
app = Flask(__name__)
app.config.from_object(__name__)

jsonDict = 0
jsonDictPart = 0
page = 0



# 以下、画面ごとの関数

#イベント一覧を全件表示する
@app.route('/')
def index():  
    return render_template('index.html', jsonDict=jsonDict)


#イベント一覧を10件ずつ表示する
@app.route('/ten/<page>')
def ten(page):
    global jsonDictPart
    jsonDictPart = list(split_list(jsonDict, 10))
    pageInt = int(page)
    maxPage = int(len(jsonDict)/10)
    return render_template('ten.html', jsonDictPart=jsonDictPart[pageInt], page=pageInt, maxPage=maxPage)


#イベント一覧を30件ずつ表示する
@app.route('/thirty/<page>')
def thirty(page):
    global jsonDictPart
    jsonDictPart = list(split_list(jsonDict, 30))
    pageInt = int(page)
    maxPage = int(len(jsonDict)/30)
    return render_template('thirty.html', jsonDictPart=jsonDictPart[pageInt], page=pageInt, maxPage=maxPage)


#キーワード検索の処理を行う
@app.route('/search', methods=['POST'])
def search():
    keyword = request.form['keyword'] #入力されたキーワードを受け取る
    jsonSearch = [] #キーワードが当てはまるイベントのデータを保存する配列の宣言

    #キーワードが、イベント名,概要,連絡先,場所,備考に含まれているかどうかを調べる
    for keywordCmp in jsonDict:
        eventName = keyword in keywordCmp["event_name"]
        description = keyword in keywordCmp["description"]
        contact = keyword in keywordCmp["contact"]
        eventPlace = keyword in keywordCmp["event_place"]
        remarks = keyword in keywordCmp["remarks"]
        #キーワードが当てはまれば、先ほど宣言した配列にデータを追加する
        if eventName or description or contact or eventPlace or remarks:
            jsonSearch.append(keywordCmp)

    hit = len(jsonSearch)
    #キーワードが当てはまるイベントがあれば、そのイベントの一覧を表示する
    if hit > 0:
        return render_template('search.html', jsonSearch=jsonSearch, keyword=keyword, hit=hit)
    #キーワードが当てはまるイベントがなければ、見つからなかったと表示する
    else:
        return render_template('nothing.html', keyword=keyword, hit=hit)


#カテゴリー検索の処理を行う
@app.route('/category', methods=['POST'])
def category():
    category = request.form['category'] #検索するカテゴリーを受け取る
    jsonCategory = [] #入力されたカテゴリーのイベントデータを保存する配列の宣言

    #入力されたカテゴリーのデータを抽出する
    for categoryCmp in jsonDict:
        #入力されたカテゴリーのデータは、先ほど宣言した配列に追加する
        if category == categoryCmp["category"]:
            jsonCategory.append(categoryCmp)

    hit = len(jsonCategory)
    #入力されたカテゴリーのイベント一覧を表示する
    return render_template('search.html', jsonSearch=jsonCategory, keyword=category, hit=hit)


#イベントの詳細な情報を表示する 
@app.route('/details/<key>')
def details(key):
    global jsonDict
    keyInt = int(key)
    return render_template('details.html', jsonPart=jsonDict[keyInt])


#日付検索の処理を行う
@app.route('/date', methods=['POST'])
def date():
    #入力された年月日を受け取る
    myYear = request.form['year']
    myMonth = request.form['month']
    myDate = request.form['date']
    dateImpossible = False

    #受け取った年月日があり得る値なのか判定する
    #月が2月なら日付があり得る値がどうか調べる(閏年も考慮する)
    if int(myMonth) == 2:
        if int(myYear) == 2020:
            if int(myDate) > 29:
                dateImpossible = True
        else:
            if int(myDate) > 28:
                dateImpossible = True

    #日が31日なら、31日がある月かを判断する
    if int(myDate) == 31:
        if (int(myMonth) == 2) or (int(myMonth) == 4) or (int(myMonth) == 6) or (int(myMonth) == 9) or (int(myMonth) == 11):
            dateImpossible = True

    #入力された年月日がありえない値なら、その年月日は存在しないと出力する　
    if dateImpossible:
        return render_template('impossible.html', year=myYear, month=myMonth, date=myDate)

    #受け取った年月日の文字列からdatetime.dateクラスのインスタンスを生成
    inputDate = datetime.date(int(myYear), int(myMonth), int(myDate))
    jsonDate = [] #当てはまるデータを保存する配列の宣言

    #inputDateがイベントの期間の中にあるか調べる
    for dateCmp in jsonDict:
        #inputDateがイベントの開催期間内であれば、先ほど宣言した配列にイベントのデータを追加する
        if (dateCmp["startDate"] <= inputDate) and (inputDate <= dateCmp["endDate"]):
            jsonDate.append(dateCmp)

    hit = len(jsonDate)
    #入力された日付にイベントが開催していたら、そのイベントの一覧を表示する
    if hit > 0:
        return render_template('search.html', jsonSearch=jsonDate, keyword=inputDate, hit=hit)
    #入力された日付にイベントが開催していなかったら、見つからなかったと表示する
    else:
        return render_template('nothing.html', keyword=inputDate, hit=hit)



#イベント情報のjsonデータをURLから読み取る処理
def download():
    global jsonDict
    global jsonDictPart
    url = 'https://raw.githubusercontent.com/jigjp/intern_exam/master/fukui_event.json'
    #urlからjsonデータを受け取り、pythonの辞書型の配列に変換する
    respons = requests.get(url)
    jsonData = respons.content
    jsonString = respons.content.decode('utf-8')
    jsonDict = json.loads(jsonString) #ここで、jsonデータが辞書型の配列になる

    j = 0
    #jsonDictの内容を後の処理で扱いやすいように少し変更する
    while j<len(jsonDict):
        jsonDict[j]["key"] = j #辞書型のデータに、固有の識別番号を持たせる

        #start_dateとend_dateから、datetime.dateクラスのインスタンスを生成する
        startDate = changeDate(jsonDict[j]["start_date"])
        endDate = changeDate(jsonDict[j]["end_date"])
        #生成したインスタンスを、辞書型のjsonDictに追加する
        jsonDict[j]["startDate"] = startDate
        jsonDict[j]["endDate"] = endDate

        #概要と備考のデータで箇条書きの記号の前に改行のタグを追加する
        if ('■' in jsonDict[j]["description"]) or ('●' in jsonDict[j]["description"]):
            i = 1
            while i<len(jsonDict[j]["description"]):
                if jsonDict[j]["description"][i] == '●' or jsonDict[j]["description"][i] == '■':
                    jsonDict[j]["description"] = jsonDict[j]["description"][:i-1] + "<br>" + jsonDict[j]["description"][i:]
                    i+=4
                i+=1
        if ('■' in jsonDict[j]["remarks"]) or ('●' in jsonDict[j]["remarks"]):
            i = 1
            while i<len(jsonDict[j]["remarks"]):
                if jsonDict[j]["remarks"][i] == '●' or jsonDict[j]["remarks"][i] == '■':
                    jsonDict[j]["remarks"] = jsonDict[j]["remarks"][:i-1] + '<br>' + jsonDict[j]["remarks"][i:]
                    i+=4
                i+=1
        j+=1



#受け取った文字列からdatetime.dateクラスのインスタンスを生成して返す処理
def changeDate(dateString):
    myDatetime = datetime.datetime.strptime(dateString, '%Y/%m/%d')
    myDate = datetime.date(myDatetime.year, myDatetime.month, myDatetime.day)
    return myDate


#受け取ったリストをnこずつのリストに分割する処理
def split_list(l, n):
    """
    リストをサブリストに分割する
    :param l: リスト
    :param n: サブリストの要素数
    :return: 
    """
    for idx in range(0, len(l), n):
        yield l[idx:idx + n]
 

#プログラムを実行すると最初に呼び出される部分
if __name__ == '__main__':
    #イベント情報のデータを取得する
    download()
    app.run()
