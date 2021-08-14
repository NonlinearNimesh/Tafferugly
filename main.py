from flask import *
import nltk
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')
nltk.download('wordnet')
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
from nltk.stem import WordNetLemmatizer
import numpy as np
from textblob import TextBlob
import re
#from wordcloud import WordCloud
from flask import *
import sqlite3
import json
import sys
import tweepy

app = Flask(__name__)

@app.route('/')
def index():
    return "Homepage"

@app.route('/livetweet', methods=['GET', 'POST'])
def livetweet():
    if request.method == "POST":

        SEP = ';'
        csv = open('OutputStreaming.csv', 'a')
        csv.write('User_created' + SEP + 'Date' + SEP + 'Text' + SEP + 'Location' + SEP + 'Number_Follower' + SEP + 'User_Name' + SEP + "Source" + SEP + 'Friends_count\n')

        class MyStreamListener(tweepy.StreamListener):
            def __init__(self):
                super().__init__()
                self.max_tweets = 200
                self.tweet_count = 0

            def on_status(self, status):
                try:
                    status
                except TypeError:
                    print("completed")
                else:
                    self.tweet_count += 1
                    if (self.tweet_count == self.max_tweets):
                        print("completed")
                        return (False)
                    else:
                        Created = status.created_at.strftime("%Y-%m-%d-%H:%M:%S")
                        Text = status.text.replace('\n', ' ').replace('\r', '').replace(SEP, ' ')
                        # full_Text = status.extended_tweet['full_text']
                        Location = ''
                        if status.coordinates is not None:
                            lon = status.coordinates['coordinates'][0]
                            lat = status.coordinates['coordinates'][1]
                            Location = lat + ',' + lon
                        Follower = str(status.user.followers_count)
                        User_created = str(status.user.created_at)
                        Name = status.user.screen_name
                        Friend = str(status.user.friends_count)
                        Source = str(status.source)
                        csv.write(User_created + SEP + Created + SEP + Text + SEP + Location + SEP + Follower + SEP + Name + SEP + Source + SEP + Friend + '\n')

            def on_error(self, status_code):
                print(status_code)

        consumer_key = "AxOyrvs5TfCwW4zMC6FiQVijO"
        consumer_secret = "68LVeWzJJOHxIYHZ0BZnKKvlvyLlgEVWoJzxQRPgiTgi2oKMEk"
        access_token = "1292791929810423810-uf31LSiTTMMtLThOM12nZXZ1sMXXYT"
        access_token_secret = "n0cOgdGm1PslPx9I4IsfpiyY0yLWS6ZwXHNXdKrqLgP0S"

        # stream
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        myStream = tweepy.Stream(auth, MyStreamListener())
        key = request.form["livetweet"]
        myStream.filter(track=[key])

        import pandas as pd
        df = pd.read_csv("OutputStreaming.csv", sep=';')
        df = df.replace(r'RT', ' ', regex=True)
        df = df.replace(r'Retweet', ' ', regex=True)
        df = df.replace(r'#', ' ', regex=True)
        df = df.replace(r'@\w+', ' ', regex=True)
        df = df.replace(r'http\S+', ' ', regex=True)
        #df = df["Text"].replace(':','', regex=True)
        #df = df.replace(r':', '', regex=True)
        #df = df.astype(str).apply(lambda x: x.str.encode('ascii', 'ignore').str.decode('ascii'))
        print(df)

############################################### Source ################################################################

        Source = df["Source"].value_counts()
        eighth = Source.plot.pie(autopct="%.1f%%", textprops={'fontsize': 20}, figsize=(15, 15));
        eighth.figure.savefig('static/images/Source.png')
        plt.clf()
        plt.cla()
        plt.close()

############################################## Valid - Invalid #######################################################

        df["Count"] = df.User_Name.str.extract('(\d+)')
        df['count_numbers'] = df['Count'].str.count('\d')
        df.loc[df['count_numbers'] > 7.0, 'ValidAccount?'] = 'Invalid'
        df.loc[df['count_numbers'] < 8.0, 'ValidAccount?'] = 'Valid'
        df = df.drop(['Count', 'count_numbers'], axis=1)
        df["ValidAccount?"].fillna("Valid", inplace=True)
        countValInval = df["ValidAccount?"].value_counts()
        mylabels = ["invalid", "valid"]
        first = countValInval.plot.pie(autopct="%.1f%%", textprops={'fontsize': 20}, labels=mylabels, figsize=(15, 15));
        first.figure.savefig('static/images/val_inval.png')
        plt.clf()
        plt.cla()
        plt.close()

################################################## Influencer ##########################################################

        df[["Number_Follower", "Friends_count"]] = df[["Number_Follower", "Friends_count"]].apply(pd.to_numeric)
        for index, row in df.iterrows():
            if row.Number_Follower > 0:
                df.loc[index, 'ImpactNo'] = row.Friends_count / row.Number_Follower
            else:
                df.loc[index, 'ImpactNo'] = 0

        df.loc[df['ImpactNo'] > 0.5, 'Impact'] = 'Amateur'
        df.loc[df['ImpactNo'] < 0.5, 'Impact'] = 'Influencer'
        df = df.drop(['ImpactNo'], axis=1)
        countImpact = df["Impact"].value_counts()
        second_label = ["amateur", "influencer"]
        second = countImpact.plot.pie(autopct="%.1f%%", textprops={'fontsize': 20}, labels=second_label,
                                      figsize=(15, 15));
        second.figure.savefig('static/images/eff.png')
        plt.clf()
        plt.cla()
        plt.close()

############################################ Account Created On #######################################################

        df['Account_created_on'] = pd.DatetimeIndex(df['User_created']).date
        df = df.drop(['User_created'], axis=1)

########################################### Which user tweeted the most with against a given Hashtag ##################

        countUser = df.groupby("User_Name").filter(lambda x: len(x) > 1)
        countUser.head()
        countUser = countUser["User_Name"].value_counts()
        third = countUser.plot.pie(autopct="%.1f%%", textprops={'fontsize': 20}, figsize=(15, 15));
        third.figure.savefig('static/images/label_twt_partculr_hasht.png')
        plt.clf()
        plt.cla()
        plt.close()

########################################### Sentiment #################################################################

        # Sentiment analysis using Textblob
        def sentiment(tweet):
            analysis = TextBlob(tweet)
            if analysis.sentiment.polarity > 0:
                return 1
            elif analysis.sentiment.polarity == 0:
                return 0
            else:
                return -1

        df['Sentiment'] = df['Text'].apply(sentiment)

        Sentiment = df["Sentiment"].value_counts()
        Fourth = Sentiment.plot.pie(autopct="%.1f%%", textprops={'fontsize': 20}, figsize=(15, 15));
        Fourth.figure.savefig('static/images/Sentiment.png')
        plt.clf()
        plt.cla()
        plt.close()

#################################### # Users posting max negative tweet ################################################

        neg = df.loc[df['Sentiment'] == -1]
        neg_user_name = neg["User_Name"].value_counts()
        Fifth = neg_user_name.plot.pie(autopct="%.1f%%", textprops={'fontsize': 20}, figsize=(15, 15));
        Fifth.figure.savefig('static/images/neg_user_name_Sentiment.png')
        plt.clf()
        plt.cla()
        plt.close()

#################################### Date on which Negative sentiment tweet is posted ##################################

        neg_sentiment_date = neg["Date"].value_counts()
        sixth = neg_sentiment_date.plot.pie(autopct="%.1f%%", textprops={'fontsize': 20}, figsize=(15, 15));
        sixth.figure.savefig('static/images/neg_sentiment_date.png')
        plt.clf()
        plt.cla()
        plt.close()

##################### Time of the day when max tweet were posted against a given hashtag ###############################

        df['Time'] = pd.to_datetime(df['Date']).dt.time
        df['hour'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.hour
        df = df.drop(['Time'], axis=1)
        cat = []
        for i in df["hour"]:
            if i in range(4, 12):
                # print("morning")
                cat.append("morning")
            elif i in range(12, 17):
                # print("Afternoon")
                cat.append("Afternoon")
            elif i in range(17, 21):
                # print("Evening")
                cat.append("Evening")
            else:
                # print("Night")
                cat.append("Night")
        cat = pd.DataFrame(cat)
        final_df = pd.concat([df, cat], axis=1)
        final_df = final_df.rename(columns={0: 'Time of the day'})
        TimeofTheDay = final_df["Time of the day"].value_counts()
        seventh = TimeofTheDay.plot.pie(autopct="%.1f%%", textprops={'fontsize': 20}, figsize=(15, 15));
        seventh.figure.savefig('static/images/TimeOfTheDay.png')
        final_df = final_df.drop(['Location'], axis=1)
        final_df.head()
        plt.clf()
        plt.cla()
        plt.close()
        return render_template("table.html",  tables=[final_df.to_html(classes='data')], titles=final_df.columns.values)
    else:
        return render_template("LiveTweet.html")

@app.route('/display')
def display():
    return render_template("displayimages.html")



if __name__ == '__main__':
    app.run(debug=False)