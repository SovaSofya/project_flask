from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import func, update, desc
from models import User, Poems, db, get_comvect, cos_comparison, lemmatize
import matplotlib.pyplot as plt
import pathlib
from wordcloud import WordCloud


app = Flask(__name__)
#  change path to database if you want the code to work on your computer
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/Users/user/Desktop/проект по проге/flask/datapoems.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.app = app
db.init_app(app)


@app.route('/')
def index():
    return render_template('index.html')

#  page for processing user's answer
@app.route('/process', methods=['get'])
def answer_process():
    # если нет ответов, то отсылаем обратно
    if not request.args:
        return redirect(url_for('/'))

    # getting params
    ask = request.args.get('userask')
    vectoruser = get_comvect(ask)
    # now we need to compare vector of user's query to vectors at the database
    data = Poems.query.all()
    vectors = []
    for x in data:
        vectors.append(x.vector)
    try:
        check = cos_comparison(vectoruser, vectors)  # comparing, if error (vector = NaN) then leading to error page
    except:
        return render_template("error.html")
    needed = Poems.query.filter_by(vector=check).first()
    answer = needed.poem.split("\n")
    answer_id = needed.id

    # сreating user's profile
    user = User(
        ask=ask,
        vector=" ".join(list(map(str, list(vectoruser)))),
        answer_id=answer_id
    )
    # adding to the base
    db.session.add(user)
    # save
    db.session.commit()
    # receiving user's id
    db.session.refresh(user)

    return render_template("results.html", answer=answer)

@app.route('/work_statistics', methods=['get'])  # if user wants to see statistics immediately after rating poem that was given to him
def work_statistics():
    rated = request.args.get('rated')
    # getting user's rating of the poem that was given to him
    popular_up = int(rated)
    user_id = db.session.query(
        func.max(User.id)
    ).one()
    num = user_id[0]
    user = User.query.get(num)  # getting the last user (the one who rated the poem)
    needed = Poems.query.filter_by(id=user.answer_id).first()  # getting the poem that he got
    needed_id = int(needed.id)
    needed_popul = needed.popularity
    # now we can update this poem's popularity by adding user's rating to its current rating
    db.session.execute(update(Poems).where(Poems.id == needed_id).values(popularity=needed_popul + popular_up))
    db.session.commit()  # aaand getting new rating to the database
    # FROM HERE EVERYTHING IN DEF STATISTICS IS THE SAME.
    all_info = {}
    data = Poems.query.order_by(desc(Poems.popularity)).limit(10)  # showing the user 10 most popular poems
    # and they will change with how the popularity changes!
    all_info['data_popular'] = []
    for x in data:
        all_info['data_popular'].append(x.poem.split('\n'))  # also I want the poems to look nice: these are its strings
    all_info['total_people'] = User.query.count()  # how many users have visited the app
    return render_template("statistics.html", all_info=all_info)

@app.route('/statistics')
def statistics():
    all_info = {}
    data = Poems.query.order_by(desc(Poems.popularity)).limit(10)  # showing the user 10 most popular poems
    # and they will change with how the popularity changes!
    all_info['data_popular'] = []
    for x in data:
        all_info['data_popular'].append(x.poem.split('\n'))  # also I want the poems to look nice: these are its strings
    all_info['total_people'] = User.query.count()  # how many users have visited the app
    # now let's make some plots. I dont want them to run every time the program starts, so I commentate them
    # you can just download the pics altogether with the project
    # or uncommentate strings from "now let's make some plots" up to the end of DEF STATISTICS and when running the app click on "Статистика"
    # so the "savefig" would work again. I recommend to comment everything back after that
    # data = Poems.query.all()
    # moods = ["любовь", "жизнь", "женщина", "дружба", "смерть", "люди", "предательство",
    #          "счастье", "вино", "Бог", "деньги"]
    # nummoods = [0,0,0,0,0,0,0,0,0,0,0]
    # for x in data:
    #     if type(x.theme_id) is int:
    #         nummoods[x.theme_id - 1] += 1
    # plt.figure(figsize=(4, 7))
    # plt.xticks(fontsize=6, rotation=90)
    # plt.title('Количество стихов, относящихся к к-л. теме')
    # plt.xlabel('Темы')
    # plt.ylabel('Кол-во')
    # path1 = pathlib.Path("static/images/imgplot1.png")
    # plt.bar(moods, nummoods)  # plot of how many poems there is in each particular theme
    # plt.savefig(path1)
    # texts = []
    # for x in data:
    #     texts.append(lemmatize(x.poem))
    # dataforwc = " ".join(texts)
    # wordcloud = WordCloud(
    #     background_color='white',
    #     width=800,
    #     height=800,
    # ).generate(dataforwc)
    # plt.figure(figsize=(4, 4), facecolor=None)
    # plt.imshow(wordcloud)
    # plt.axis("off")
    # plt.title('Облако слов стихотворений (без стоп-слов)')
    # path2 = pathlib.Path("static/images/imgplot2.png")
    # plt.savefig(path2)
    return render_template("statistics.html", all_info=all_info)

if __name__ == '__main__':
    app.run(debug=True)
