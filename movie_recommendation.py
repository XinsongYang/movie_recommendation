#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import csv
import random
import math

# load data
movies_file = 'data/movies.csv'
movies = {}
with open(movies_file, newline='') as csvfile:
	reader = csv.reader(csvfile)
	for row in reader:
		if reader.line_num == 1:	#ignore the first line
			continue
		movie_id, movie_name, movie_genres = row[0], row[1], row[2]
		movies[movie_id] = (movie_name, movie_genres)

ratings_file='data/ratings.csv'
user_ratings = {}
movie_ratings = {}
with open(ratings_file, newline='') as csvfile:
	reader = csv.reader(csvfile)
	for row in reader:
		if reader.line_num == 1:	#ignore the first line
			continue
		user_id, movie_id, rating = row[0], row[1], row[2]
		user_ratings.setdefault(user_id, {})
		user_ratings[user_id][movie_id] = float(rating)
		movie_ratings.setdefault(movie_id, {})
		movie_ratings[movie_id][user_id] = float(rating)


def sim_distance(ratings, id1, id2, threshold=0, isAdjust=False):
	si = {}	#common between 1 and 2
	for id3 in ratings[id1]:
		if id3 in ratings[id2]:
			si[id3] = 1
	# if common things is below the threshold, we ignore their similarity
	if len(si) < threshold:
		 return 0
	sum_of_squares = sum([pow(ratings[id1][id3] - ratings[id2][id3], 2) for id3 in ratings[id1] if id3 in ratings[id2]])
	# we set an adjustment: the larger the common part is, the higher the similarity is
	adjust = pow(len(si) / len(ratings[id1]) * len(si) / len(ratings[id2]), 0.05) if isAdjust else 1
	return 1 / (1 + sum_of_squares) * adjust


def sim_pearson(ratings, id1, id2, threshold=0, isAdjust=False):
	si = {}	#common between 1 and 2
	for id3 in ratings[id1]:
		if id3 in ratings[id2]:
			si[id3] = 1
	n = len(si)
	# if common things is below the threshold, we ignore their similarity
	if n <= threshold:
		 return 0
	sum1 = sum([ratings[id1][id3] for id3 in si])
	sum2 = sum([ratings[id2][id3] for id3 in si])
	sum1Sq = sum([pow(ratings[id1][id3],2) for id3 in si])
	sum2Sq = sum([pow(ratings[id2][id3],2) for id3 in si])
	pSum = sum([ratings[id1][id3] * ratings[id2][id3] for id3 in si])
	num = pSum - (sum1 * sum2 / n)
	den = math.sqrt((sum1Sq - pow(sum1, 2) / n) * (sum2Sq - pow(sum2, 2) / n))
	if den == 0: 
		return 0
	r = num / den
	# we set an adjustment: the larger the common part is, the higher the similarity is
	adjust = pow(len(si) / len(ratings[id1]) * len(si) / len(ratings[id2]), 0.05) if isAdjust else 1
	return r * adjust


def user_based_recommendations(user_ratings, user_id, sim_fun=sim_distance, n=10, isAdjust=True):
	totals = {}
	total_sim = {}
	for other in user_ratings:	#similar users
		if other == user_id:
			continue
		sim = sim_fun(user_ratings, user_id, other, isAdjust=isAdjust)
		if sim <= 0:
			continue
		for item in user_ratings[other]:	#the items of similar users
			if item not in user_ratings[user_id]:
				totals.setdefault(item, 0)
				totals[item] += user_ratings[other][item] * sim
				total_sim.setdefault(item, 0)
				total_sim[item] += sim
	#adjustment: the larger of total_sim is, the higher the score is
	rankings = [(total / total_sim[item] * (pow(total_sim[item], 1.1) / total_sim[item]), movies[item][0]) for item, total in totals.items()]
	rankings.sort()
	rankings.reverse()
	return rankings[0:n]
	

def item_based_recommendations(user_ratings, item_ratings, user_id, sim_fun=sim_distance, n=10, isAdjust=True):
	scores = {}
	total_sim = {}
	for (item, rating) in user_ratings[user_id].items():	#all items of the user
		similar_items = [(sim_fun(item_ratings, item, other_item, isAdjust=isAdjust), other_item) for other_item in item_ratings if other_item != item]
		similar_items.sort()
		similar_items.reverse()
		similar_items = similar_items[0:n]
		for (similarity, item2) in similar_items:	#similar items
			if item2 in user_ratings[user_id]: 
				continue
			scores.setdefault(item2, 0)
			scores[item2] += similarity * rating
			total_sim.setdefault(item2, 0)
			total_sim[item2] += similarity
	#adjustment: the larger of total_sim is, the higher the score is
	rankings = [(score / total_sim[item] * (pow(total_sim[item], 1.1) / total_sim[item]) , movies[item][0]) for item,score in scores.items() if total_sim[item] != 0]
	rankings.sort()
	rankings.reverse()
	return rankings[0:n]


def test():
	# make train and test data
	test_user_percent = 0.2
	users = list(user_ratings.keys())
	test_user_num = int(len(users) * test_user_percent)
	test_users = random.sample(users, test_user_num)
	test_movies = {}
	for uid in test_users:
		best_mid = ''
		max_score = 0
		for mid in user_ratings[uid]:
			if user_ratings[uid][mid] > max_score:
				max_score = user_ratings[uid][mid]
				best_mid = mid
		test_movies[uid] = (best_mid, max_score)
		del user_ratings[uid][best_mid]
		del movie_ratings[best_mid][uid]

	# test
	success = 0
	count = 0
	for user in test_users:
		count += 1
		print(count, "/", test_user_num)
		recommendations = item_based_recommendations(user_ratings, movie_ratings, user, sim_fun=sim_pearson, n=10, isAdjust=True)
		#print(recommendations)
		#print(test_movies[user])
		for r in recommendations:
			if test_movies[user][0] == r[1]:
				success += 1
				print("success:", success)
				break
	print(success)

print(sim_distance(user_ratings,'fengliang','xinsong',isAdjust=False))
print(sim_pearson(user_ratings,'fengliang','xinsong',isAdjust=False))
print(sim_distance(user_ratings,'fengliang','xinsong',isAdjust=True))
print(sim_pearson(user_ratings,'fengliang','xinsong',isAdjust=True))

# print(user_based_recommendations(user_ratings, 'xinsong', sim_fun=sim_distance, n=10, isAdjust=False))
# print('\n')
# print(user_based_recommendations(user_ratings, 'xinsong', sim_fun=sim_distance, n=10, isAdjust=True))
# print('\n')
# print(user_based_recommendations(user_ratings, 'xinsong', sim_fun=sim_pearson, n=10, isAdjust=False))
# print('\n')
# print(user_based_recommendations(user_ratings, 'xinsong', sim_fun=sim_pearson, n=10, isAdjust=True))
# print('\n')
# print(item_based_recommendations(user_ratings, movie_ratings, 'xinsong', sim_fun=sim_distance, n=10, isAdjust=False))
# print('\n')
# print(item_based_recommendations(user_ratings, movie_ratings, 'xinsong', sim_fun=sim_distance, n=10, isAdjust=True))
# print('\n')
# print(item_based_recommendations(user_ratings, movie_ratings, 'xinsong', sim_fun=sim_pearson, n=10, isAdjust=False))
# print('\n')
# print(item_based_recommendations(user_ratings, movie_ratings, 'xinsong', sim_fun=sim_pearson, n=10, isAdjust=True))
# print('\n')

# print(user_based_recommendations(user_ratings, 'fengliang', sim_fun=sim_distance, n=10, isAdjust=False))
# print('\n')
# print(user_based_recommendations(user_ratings, 'fengliang', sim_fun=sim_distance, n=10, isAdjust=True))
# print('\n')
# print(user_based_recommendations(user_ratings, 'fengliang', sim_fun=sim_pearson, n=10, isAdjust=False))
# print('\n')
# print(user_based_recommendations(user_ratings, 'fengliang', sim_fun=sim_pearson, n=10, isAdjust=True))
# print('\n')
# print(item_based_recommendations(user_ratings, movie_ratings, 'fengliang', sim_fun=sim_distance, n=10, isAdjust=False))
# print('\n')
# print(item_based_recommendations(user_ratings, movie_ratings, 'fengliang', sim_fun=sim_distance, n=10, isAdjust=True))
# print('\n')
# print(item_based_recommendations(user_ratings, movie_ratings, 'fengliang', sim_fun=sim_pearson, n=10, isAdjust=False))
# print('\n')
# print(item_based_recommendations(user_ratings, movie_ratings, 'fengliang', sim_fun=sim_pearson, n=10, isAdjust=True))
# print('\n')


# def items_similarities(item_ratings, similarity=sim_distance, n=5):
# 	similarities = {}
# 	count = 0
# 	for item in item_ratings:
# 		count += 1
# 		if count % 100 == 0: print(count, '/', len(item_ratings) )
# 		scores = [(similarity(item_ratings, item, other_item), other_item) for other_item in item_ratings if other_item != item]
# 		scores.sort()
# 		scores.reverse()
# 		similarities[item] = scores[0:n]
# 	return similarities
