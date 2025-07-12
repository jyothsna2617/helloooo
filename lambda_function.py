from textblob import TextBlob
import json

def lambda_handler(event, context):
    body = json.loads(event['body'])
    review = body.get('review', '')
    analysis = TextBlob(review)
    polarity = analysis.sentiment.polarity

    sentiment = "Neutral"
    if polarity > 0:
        sentiment = "Positive"
    elif polarity < 0:
        sentiment = "Negative"

    return {
        'statusCode': 200,
        'headers': {"Content-Type": "application/json"},
        'body': json.dumps({'sentiment': sentiment})
    }
