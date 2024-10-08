# SEO Optimized Reddit Sentiment and Blog Topic Generator

This project pulls Reddit posts from specific subreddits, performs sentiment analysis on posts and comments, and uses the Google Gemini API to generate SEO-optimized blog topics based on the data collected. It also provides related facilities and trend data for various keywords within the domain of sports.

## Table of Contents
Setup
Project Overview and Logic
Use Cases and Utility
Customization
API Rate Limits

# Setup
## Prerequisites
Python 3.8 or higher
Google Gemini API Key: Required for content generation.
Reddit API Credentials: Get these by creating an app on Reddit's Developer Platform and using the Client ID and Secret.

## ENV Variables
Set up environment variables for sensitive information:

export GOOGLE_API_KEY="your_google_api_key"
export REDDIT_CLIENT_ID="your_reddit_client_id"
export REDDIT_CLIENT_SECRET="your_reddit_client_secret"

#Project Overview and Logic
The project works through the following main steps:

Reddit Data Retrieval: Using keywords like “Pickup game,” “Gyms,” or “Tournaments,” the script retrieves posts from Reddit and associated comments within a specified subreddit.
Sentiment Analysis: Each Reddit post title and comment is scored for sentiment using a pre-trained model to differentiate positive, negative, and neutral opinions.
Topic Generation: Using Google Gemini API, SEO-optimized blog topics are generated based on the Reddit posts’ content.
Facility Extraction: Recognizes and lists specific sports facilities mentioned within Reddit posts.
Trend Analysis: Searches for keyword trends over time using Google Trends, allowing an analysis of keyword popularity.
Use Cases and Utility
SEO-Optimized Blog Content: Ideal for content marketers, providing blog ideas directly informed by real user discussions.
Sentiment-Driven Insights: Aids businesses in understanding public sentiment around sports facilities, events, or leagues.
Keyword and Facility Analysis: Quickly extracts common facilities and keyword popularity, helping locate trending facilities.
Trend Tracking: Monitors the trend over time for keywords to assist in content planning around peak periods.
Customization
The following aspects of the program can be customized:

Keywords: Adjust the list_of_keywords variable in the code to add or modify keywords of interest.
Subreddit: Change the target subreddit to match the audience or theme you want to explore.
API Limits: Modify the code to include more or fewer comments/posts by adjusting the max_posts and max_comments parameters in the retrieve_reddit_posts function.
Sentiment Weights: Fine-tune sentiment scoring for titles and comments by adjusting weights in update_sentiment_of_posts.
API Rate Limits
This program relies on several APIs that have specific rate limits:

Google Gemini API: Limited by API quota; large batches may exhaust daily quota quickly, so it’s recommended to handle exceptions for quota errors and include delays between requests.
Reddit API: Rate-limited; avoid exceeding the default request limit by spreading out calls, especially when retrieving comments.
