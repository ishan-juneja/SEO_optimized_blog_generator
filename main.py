import praw
import time
import torch
import re
import google.generativeai as genai
from transformers import pipeline
from prawcore.exceptions import NotFound
from pytrends.request import TrendReq

# things to work on

# specific prompts
# list of key words
# city, sport, specific key words

# pick up game

# Configure the Gemini API
api_key = "" # Enter your api key
genai.configure(api_key=api_key)


def load_model():
	start_time = time.time()

	# Check if GPU is available and use it
	device = 0 if torch.cuda.is_available() else -1
	print(f"Using device: {'GPU' if device == 0 else 'CPU'}")
	# Load a pre-trained sentiment analysis pipeline with GPU support if available
	print("Loading model...")
	sentiment_analysis = pipeline(
		'sentiment-analysis',
		model='cardiffnlp/twitter-roberta-base-sentiment-latest',
		device=device
	)
	print("Model loaded in {:.2f} seconds.".format(time.time() - start_time))

	return sentiment_analysis


def retrieve_sentiment_score(model, sentence):
	result = model(sentence)
	print("Sentiment analysis result:", result)
	if result[0]["label"] == "neutral":  # if neutral do nothing
		return 0
	if result[0]["label"] == "negative":
		return float(result[0]["score"] * -1)
	return float(result[0]["score"])


def retrieve_reddit_posts(subreddit, query, max_posts=25, max_comments=10):
	# Set up the Reddit client
	reddit = praw.Reddit(
		client_id="uC-9qQ36XuReiwCOZ5_i-A",
		client_secret="kQNKUX9M7g8M8hEmj_36HiciR63GZA",
		user_agent="SquadzBot/0.1 by Ishgan"
	)

	# Define the subreddit (e.g., r/sports)
	subreddit = reddit.subreddit(subreddit)

	# Base URL for Reddit posts
	reddit_base_url = "https://www.reddit.com"

	# Create our list of posts from the reddit
	list_of_posts = []

	# Search for posts related to the query in the subreddit
	count = 0
	for post in subreddit.search(query, sort="hot", limit=max_posts):  # ADJUST LIMIT LATER
		count += 1
		print(f"Title: {post.title}")
		print(f"Score: {post.score}")
		print(f"URL: {post.url}\n")  # this is like any videos or attachmentes
		reddit_post_url = f"{reddit_base_url}{post.permalink}"  # Construct the Reddit post URL
		print(f"Reddit URL: {reddit_post_url}\n")

		# Create a dictionary with 5 keys --> this is an entry of all of our posts
		list_of_posts_entry = {"Title": post.title, "Score": post.score, "Attachments": post.url,
		                       "URL": reddit_post_url, "Comments": [], "Title_Score": 0, "Comment_Score": 0}

		# Specify the post you want to fetch comments from
		list_of_comments = []
		try:
			submission = reddit.submission(url=reddit_post_url)
			# Fetch the top 10 comments if available
			submission.comments.replace_more(limit=0)  # Ensure that all top-level comments are retrieved
			for comment in submission.comments.list()[
			               2:max_comments + 2]:  # Limiting to top 10 comments by default, skipping ad/mod comments
				list_of_comments.append(comment.body)
		except NotFound:
			print("Post not found or not accessible.")

		# Update our dictionary entry
		list_of_posts_entry["Comments"] = list_of_comments

		# Add our dictionary entry to our broader list
		list_of_posts.append(list_of_posts_entry)

	return list_of_posts


def update_sentiment_of_posts(posts):
	sentiment_model = load_model()

	# # these are the weights for our sentiment analysis
	# title_multiplier = 0.75
	# comment_multiplier = 0.25

	for post in posts:
		comment_score = 0
		title_score = retrieve_sentiment_score(model=sentiment_model, sentence=post["Title"])
		comments = post["Comments"]
		for comment in comments:
			score = retrieve_sentiment_score(model=sentiment_model, sentence=comment)
			comment_score += score
		post["Comment_Score"] = comment_score
		post["Title_Score"] = title_score


def generate_blog_topics(posts, filename, number_of_topics=5):
	# Assuming posts is a list of dictionaries containing post titles and comments
	combined_text = "\nTitle: ".join(
		[post["Title"] + " " + "Reddit URL".join(post["URL"]) + " " + "Comments: ".join(post["Comments"]) for post in
		 posts])

	# Use the model to generate blog post topics with max_new_tokens
	prompt = f"Imaging you are a blog writer for a sports facility company. Generate {number_of_topics} blog post topics based on the following Reddit posts that would also be SEO optimized (give " \
	         f"reasoning for the SEO optimization, use some of the comments as a testimonal to the post if possible, " \
	         f"include some key points to cover)." \
	         f" Be as specific as possible, please. Also give me all {number_of_topics} of the blog titles right at the" \
	         f" top and then the rest of the info after.: \n {combined_text}"

	model = genai.GenerativeModel("gemini-1.5-flash")
	response = model.generate_content(prompt)

	# Open the file in write mode
	with open(filename, 'w') as file:
		file.write(response.text)

	# Returning the generated topics
	return response.text


def reverse_blog_idea_to_reddit_posts(blog_ideas, reddit_posts, number_of_topics=5):
	"""
    This function takes a list of blog post ideas and a list of Reddit posts (with titles and comments)
    and uses Google Gemini to identify which Reddit posts contributed to generating each blog post idea.

    Parameters:
        blog_ideas (list): A list of blog post ideas.
        reddit_posts (list): A list of dictionaries containing Reddit post titles and comments.

    Returns:
        dict: A dictionary mapping each blog idea to the most relevant Reddit posts.
    """

	prompt = f"Out of the following text, list in numbered format with a new line after, all {number_of_topics} " \
	         f"blog ideas: {blog_ideas}"

	# Use Google Gemini to generate a response
	model = genai.GenerativeModel("gemini-1.5-flash")
	list_of_posts_text = model.generate_content(prompt).text

	print(list_of_posts_text)
	# Split the paragraph into lines
	list_of_posts = re.findall(r'^\d+\.\s.*', list_of_posts_text, re.MULTILINE)
	print(list_of_posts_text)
	reverse_mapping = {}

	# Number off the Reddit posts and store them in the list
	numbered_reddit_posts = []

	for i, post in enumerate(reddit_posts):
		numbered_post = {
			"Number": i + 1,
			"Title": post["Title"],
			"Comments": post["Comments"],
			"URL": post["URL"]
		}
		numbered_reddit_posts.append(numbered_post)

	# Create a combined string of numbered Reddit posts (titles and comments) for matching with blog ideas
	combined_reddit_posts_text = [
		f"{post['Number']}. Title: {post['Title']} Comments: {' | '.join(post['Comments'])}" + "\n"
		for post in numbered_reddit_posts
	]

	reverse_mapping_text = ""

	for idea in list_of_posts:
		# Create a prompt to match blog post idea back to Reddit posts
		prompt = f"Given the blog post idea: '{idea}', which of the following Reddit posts is most likely to have inspired it? Return one corresponding number only:\n" \
		         f"Reddit Posts:\n" + "\n".join(combined_reddit_posts_text)

		# Use Google Gemini to generate a response
		model = genai.GenerativeModel("gemini-1.5-flash")
		response = model.generate_content(prompt)

		# Store the response in the reverse mapping dictionary
		reverse_mapping[idea] = response.text

		print("DEBUG")
		print(response.text)

		# Use a regular expression to find the integer
		match = re.search(r'\d+', response.text)

		# Extract the integer if found
		if match:
			number = int(match.group()) - 1
			reverse_mapping_text += f"Idea: {idea} Link: {numbered_reddit_posts[number]['URL']}"
		else:
			print("No integer found")
			reverse_mapping_text += f"Idea: {idea} Link: Not found as no matching blog post exists"
		print(reverse_mapping_text)
		reverse_mapping_text += "\n"

		#subtract 1 because it isn't numbered off correctly otherwise / indexes start from 0
	return reverse_mapping_text


def search_for_sports_facilities(posts, filename):
	# Assuming posts is a list of dictionaries containing post titles and comments
	combined_text = "\nTitle: ".join([post["Title"] + " " + "Comments: ".join(post["Comments"]) for post in posts])

	# Use the model to generate blog post topics with max_new_tokens
	prompt = f"From the following reddit posts and comments, can you search for any sport facilities that are mentioned and return a list of them, GIVE THE SPECIFIC NAMES: \n {combined_text}"

	model = genai.GenerativeModel("gemini-1.5-flash")
	response = model.generate_content(prompt)

	# Open the file in write mode
	with open('list_of_possible_facilities.txt', 'w') as file:
		file.write(response.text)

	# Returning the generated topics
	return response.text


def get_keyword_trend(keyword):
	pytrends = TrendReq(hl='en-US', tz=360)
	pytrends.build_payload([keyword], cat=0, timeframe='today 12-m', geo='', gprop='')
	data = pytrends.interest_over_time()
	return data


def perform_keyword_search_in_reddit(subreddit, filename, number_of_topics=5):
	print("starting! \n")
	list_of_keywords = ["League", "Pickup game", "Open gym", "Drop in", "Tournaments", "Facilities", "Gyms", "Courts", \
	                    "Fields", "Rec league", "Adult league", "Church league"]
	my_big_paragraph = "Generating various blog posts from the following subreddit. \n\n\n\n"
	for keyword in list_of_keywords:
		print(f"\n\nOnto keyword: {keyword} \n\n")
		my_current_posts = retrieve_reddit_posts(subreddit, keyword)

		if my_current_posts:
			my_current_blogs = generate_blog_topics(my_current_posts, filename, number_of_topics)
			reverse_text = reverse_blog_idea_to_reddit_posts(my_current_blogs, my_current_posts)
			my_current_sports_facilities = search_for_sports_facilities(my_current_posts, filename)
			print(my_current_blogs)
			print("\n\n\n")
			print(reverse_text)
			my_big_paragraph += f'For the following keyword {keyword}, we generated these blog posts: \n\n'
			my_big_paragraph += my_current_blogs
			my_big_paragraph += f'We also found these reddit posts relate most to the posts: {reverse_text} \n\n'
			my_big_paragraph += f'\n\nFor the following keyword {keyword}, we found these potential facilities: \n\n'
			my_big_paragraph += my_current_sports_facilities + '\n\n\n\n'

			time.sleep(5)
		else:
			my_big_paragraph += f'There were no posts found regarding the keyword: {keyword}\n\n\n\n'

	with open(filename, 'w') as file:
		file.write(my_big_paragraph)

	print("We are done!")


# Run the Program Here
if __name__ == "__main__":
	perform_keyword_search_in_reddit("newyork", filename="second_test.txt")
