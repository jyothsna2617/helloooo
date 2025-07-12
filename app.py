from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import random
import time
from textblob import TextBlob
import os

app = Flask(__name__)
CORS(app)

# Use environment variable for API key (more secure)
GOOGLE_PLACES_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY', 'YOUR_API_KEY_HERE')


class HospitalReviewAnalyzer:
    def __init__(self):
        self.reviews_cache = {}
        self.user_reviews = []  # Store user reviews

    def get_google_places_reviews(self, hospital_name, location=""):
        """Fetch reviews from Google Places API"""
        try:
            # Search for the hospital
            search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            search_params = {
                'query': f"{hospital_name} {location}",
                'key': GOOGLE_PLACES_API_KEY,
                'type': 'hospital'
            }

            search_response = requests.get(search_url, params=search_params, timeout=10)
            search_data = search_response.json()

            if not search_data.get('results'):
                return []

            place_id = search_data['results'][0]['place_id']

            # Get place details with reviews
            details_url = "https://maps.googleapis.com/maps/api/place/details/json"
            details_params = {
                'place_id': place_id,
                'fields': 'reviews,rating,user_ratings_total',
                'key': GOOGLE_PLACES_API_KEY
            }

            details_response = requests.get(details_url, params=details_params, timeout=10)
            details_data = details_response.json()

            reviews = []
            if 'result' in details_data and 'reviews' in details_data['result']:
                for review in details_data['result']['reviews']:
                    reviews.append({
                        'text': review.get('text', ''),
                        'author': review.get('author_name', 'Anonymous'),
                        'rating': review.get('rating', 0),
                        'time': review.get('time', 0)
                    })

            return reviews

        except Exception as e:
            print(f"Error fetching Google Places reviews: {e}")
            return []

    def get_mock_reviews(self, hospital_name, location):
        """Generate mock reviews for demonstration"""
        mock_reviews = [
            {
                'text': "Excellent service and very caring staff. The doctors were professional and the facilities were clean.",
                'author': 'John Smith',
                'rating': 5
            },
            {
                'text': "Had to wait for a long time but the treatment was good. Staff could be more friendly.",
                'author': 'Sarah Johnson',
                'rating': 3
            },
            {
                'text': "Poor service, long waiting times, and unprofessional behavior from some staff members.",
                'author': 'Mike Brown',
                'rating': 2
            },
            {
                'text': "Outstanding care! The nurses were amazing and the doctor explained everything clearly.",
                'author': 'Emily Davis',
                'rating': 5
            },
            {
                'text': "Average experience. Nothing special but got the job done. Could improve cleanliness.",
                'author': 'David Wilson',
                'rating': 3
            },
            {
                'text': "Terrible experience. Rude staff, dirty facilities, and very poor communication.",
                'author': 'Lisa Anderson',
                'rating': 1
            },
            {
                'text': "Good medical care but the administration process was confusing and time-consuming.",
                'author': 'Robert Taylor',
                'rating': 4
            },
            {
                'text': "Highly recommend this hospital. Professional staff, modern equipment, and great patient care.",
                'author': 'Jennifer Martinez',
                'rating': 5
            }
        ]

        # Return a random subset of reviews
        return random.sample(mock_reviews, min(len(mock_reviews), random.randint(5, 8)))

    def analyze_sentiment(self, text):
        """Analyze sentiment of text using TextBlob"""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity

            if polarity > 0.1:
                return 'positive'
            elif polarity < -0.1:
                return 'negative'
            else:
                return 'neutral'
        except Exception as e:
            print(f"Error analyzing sentiment: {e}")
            return 'neutral'

    def fetch_all_reviews(self, hospital_name, location=""):
        """Fetch reviews from all sources"""
        cache_key = f"{hospital_name}_{location}".lower()

        # Check cache first
        if cache_key in self.reviews_cache:
            cached_data = self.reviews_cache[cache_key]
            if time.time() - cached_data['timestamp'] < 300:  # 5 minutes cache
                return cached_data['reviews']

        # Try Google Places API first
        reviews = self.get_google_places_reviews(hospital_name, location)

        # If no reviews from API, use mock data
        if not reviews:
            reviews = self.get_mock_reviews(hospital_name, location)

        # Analyze sentiment for each review
        for review in reviews:
            review['sentiment'] = self.analyze_sentiment(review['text'])

        # Cache the results
        self.reviews_cache[cache_key] = {
            'reviews': reviews,
            'timestamp': time.time()
        }

        return reviews

    def analyze_user_review(self, review_text, author_name="Anonymous", rating=0):
        """Analyze a single user review"""
        sentiment = self.analyze_sentiment(review_text)

        user_review = {
            'text': review_text,
            'author': author_name or "Anonymous",
            'rating': rating,
            'sentiment': sentiment,
            'is_user_review': True
        }

        self.user_reviews.append(user_review)

        return user_review


analyzer = HospitalReviewAnalyzer()


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/reviews', methods=['POST'])
def get_reviews():
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data received'}), 400

        hospital_name = data.get('hospital_name', '').strip()
        location = data.get('location', '').strip()

        if not hospital_name:
            return jsonify({'error': 'Hospital name is required'}), 400

        if not location:
            return jsonify({'error': 'Location is required'}), 400

        reviews = analyzer.fetch_all_reviews(hospital_name, location)

        if not reviews:
            statistics = {'positive': 0, 'negative': 0, 'neutral': 0}
            return jsonify({
                'statistics': statistics,
                'reviews': [],
                'total_reviews': 0,
                'hospital_name': hospital_name,
                'location': location
            })

        # Calculate statistics
        positive_count = sum(1 for r in reviews if r['sentiment'] == 'positive')
        negative_count = sum(1 for r in reviews if r['sentiment'] == 'negative')
        neutral_count = sum(1 for r in reviews if r['sentiment'] == 'neutral')

        statistics = {
            'positive': positive_count,
            'negative': negative_count,
            'neutral': neutral_count
        }

        # Format reviews for response
        review_list = []
        for r in reviews:
            review_list.append({
                'text': r['text'],
                'author': r['author'],
                'rating': r['rating'],
                'sentiment': r['sentiment']
            })

        return jsonify({
            'statistics': statistics,
            'reviews': review_list,
            'total_reviews': len(reviews),
            'hospital_name': hospital_name,
            'location': location
        })

    except Exception as e:
        print(f"Error in get_reviews: {e}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@app.route('/analyze-review', methods=['POST'])
def analyze_single_review():
    """Analyze a single user review"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data received'}), 400

        review_text = data.get('review_text', '').strip()
        author_name = data.get('author_name', '').strip()
        rating = data.get('rating', 0)

        if not review_text:
            return jsonify({'error': 'Review text is required'}), 400

        # Analyze the review
        analyzed_review = analyzer.analyze_user_review(review_text, author_name, rating)

        return jsonify({
            'review': analyzed_review,
            'sentiment': analyzed_review['sentiment'],
            'message': 'Review analyzed successfully!'
        })

    except Exception as e:
        print(f"Error in analyze_single_review: {e}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@app.route('/submit-review', methods=['POST'])
def submit_review():
    """Submit a user review to be included in hospital analysis"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data received'}), 400

        hospital_name = data.get('hospital_name', '').strip()
        location = data.get('location', '').strip()
        review_text = data.get('review_text', '').strip()
        author_name = data.get('author_name', '').strip()
        rating = data.get('rating', 0)

        if not hospital_name or not location:
            return jsonify({'error': 'Hospital name and location are required'}), 400

        if not review_text:
            return jsonify({'error': 'Review text is required'}), 400

        if rating < 1 or rating > 5:
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400

        # Analyze the review
        analyzed_review = analyzer.analyze_user_review(review_text, author_name, rating)

        # Add to cache for this hospital
        cache_key = f"{hospital_name}_{location}".lower()
        if cache_key in analyzer.reviews_cache:
            analyzer.reviews_cache[cache_key]['reviews'].append(analyzed_review)

        return jsonify({
            'review': analyzed_review,
            'sentiment': analyzed_review['sentiment'],
            'message': 'Review submitted successfully!'
        })

    except Exception as e:
        print(f"Error in submit_review: {e}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Server is running'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)





