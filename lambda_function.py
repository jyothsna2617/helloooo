import json
import os
from app import app
from flask import Flask
import awsgi

def lambda_handler(event, context):
    """
    Lambda handler function that wraps the Flask app
    """
    try:
        # Use awsgi to handle the WSGI interface
        return awsgi(app, event, context)
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