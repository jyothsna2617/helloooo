import json
import os
from app import app
from flask import Flask
from mangum import Mangum

from asgiref.wsgi import WsgiToAsgi  # ✅ add this line

# ✅ Wrap the Flask app using WsgiToAsgi
asgi_app = WsgiToAsgi(app)

# Create Mangum handler
handler = Mangum(asgi_app)

def lambda_handler(event, context):
    """
    Lambda handler function that wraps the Flask app
    """
    try:
        # Use awsgi to handle the WSGI interface
        return handler(event, context)
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error detected',
                'message': str(e)
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }