SELECT tw.id, tw.tweet_data, COUNT(tw.id) as likes
FROM tweets as tw
RIGHT JOIN likes as l ON tw.id = l.tweet_id
WHERE tw.author_id in
      (SELECT fr.following_user_id
       FROM followers as fr
       WHERE fr.follower_user_id = 12)
GROUP BY tw.id
ORDER BY likes DESC;