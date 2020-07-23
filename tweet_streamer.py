from tweepy import API
from tweepy import Cursor
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import twitter_credentials
import pandas as pd
import numpy as np
from textblob import TextBlob
import re

class Authenticate():
	def authenticate_app(self):
		auth = OAuthHandler(twitter_credentials.CONSUMER_KEY, twitter_credentials.CONSUMER_SECRET)
		auth.set_access_token(twitter_credentials.ACCESS_TOKEN, twitter_credentials.ACCESS_TOKEN_SECRET)
		return auth


class TwitterStreamer():
	def __init__(self):
		self.twitter_authenticator = Authenticate()
	
	def stream_tweets(self, filename, hashtag_list):
		listener = TwitterListener(filename)
		auth = self.twitter_authenticator.authenticate_app()
		stream = Stream(auth, listener)

		stream.filter(track=hashtag_list)


class TwitterListener(StreamListener):
	def __init__(self, filename):
		self.filename = filename

	def on_data(self, data):
		try:
			print(data)

			with open(self.filename, 'a') as f:
				f.write(data)
			return True
		except BaseException as e:
			print(f'Error on_data {e}')

		return True

	def on_error(self, status):
		if status == 420:
			return False
		print(status)


class TwitterClient():
	def __init__(self, twitter_user=None):
		self.auth = Authenticate().authenticate_app()
		self.twitter_client = API(self.auth)
		self.twitter_user = twitter_user

	def get_twitter_client_api(self):
		return self.twitter_client

	def get_user_timeline_tweets(self, num_tweets):
		tweets = []
		for tweet in Cursor(self.twitter_client.user_timeline, id=self.twitter_user).items(num_tweets):
			tweets.append(tweet)

		return tweets

	def get_friend_list(self, num_friends):
		friend_list = []
		for friend in Cursor(self.twitter_client.friends, id=self.twitter_user).items(num_friends):
			friend_list.append(friend)

		return friend_list

	def get_home_timeline_tweets(self, num_tweets):
		home_timeline_tweets = []
		for tweet in Cursor(self.twitter_client.home_timeline, id=self.twitter_user).items(num_tweets):
			home_timeline_tweets.append(tweet)

		return home_timeline_tweets


class AnalyzeTweets():
	def clean_tweet(self, tweet):
		return ' '.join(re.sub('(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)', ' ', tweet).split())
	
	def predict_sentiment(self, tweet):
		analysis = TextBlob(self.clean_tweet(tweet))

		if analysis.sentiment.polarity > 0:
			return 1
		elif analysis.sentiment.polarity == 0:
			return 0
		else:
			return -1

	def tweets_to_dataframe(self, tweets):
		df = pd.DataFrame(data=[tweet.text for tweet in tweets], columns=['tweets'])
		df['id'] = np.array([tweet.id for tweet in tweets])
		df['length'] = np.array([len(tweet.text) for tweet in tweets])
		df['date'] = np.array([tweet.created_at for tweet in tweets])
		df['source'] = np.array([tweet.source for tweet in tweets])
		df['likes'] = np.array([tweet.favorite_count for tweet in tweets])
		df['retweets'] = np.array([tweet.retweet_count for tweet in tweets])
		return df


if __name__ == "__main__":
	twitter_client = TwitterClient()
	tweets_analyzer = AnalyzeTweets()

	api = twitter_client.get_twitter_client_api()

	tweets = api.user_timeline(screen_name='narendramodi', count=2000)

	df = tweets_analyzer.tweets_to_dataframe(tweets)
	df['sentiment'] = np.array([tweets_analyzer.predict_sentiment(tweet) for tweet in df['tweets']])
	print(df.head(10))
