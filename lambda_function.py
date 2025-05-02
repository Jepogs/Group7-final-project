import json
import pymysql
import openai
import os

# Set your OpenAI API key (ensure you securely store this as an environment variable)
openai.api_key = os.environ['OPENAI_API_KEY']

# RDS credentials from environment variables
RDS_HOST = os.environ['RDS_HOST']
RDS_USER = os.environ['RDS_USER']
RDS_PASSWORD = os.environ['RDS_PASSWORD']
RDS_DB = os.environ['RDS_DB']

def lambda_handler(event, context):
    try:
        # Connect to the RDS MySQL database
        connection = pymysql.connect(
            host=RDS_HOST,
            user=RDS_USER,
            password=RDS_PASSWORD,
            database=RDS_DB
        )
        cursor = connection.cursor()

        # Fetch new/unprocessed rows
        cursor.execute("SELECT id, input_text FROM user_requests WHERE processed = FALSE")
        rows = cursor.fetchall()

        responses = []

        for row in rows:
            id, input_text = row

            # Send input_text to ChatGPT
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": input_text}]
            )
            gpt_response = response['choices'][0]['message']['content']

            # Update database with the response
            cursor.execute(
                "UPDATE user_requests SET gpt_response = %s, processed = TRUE WHERE id = %s",
                (gpt_response, id)
            )
            connection.commit()

            responses.append({'id': id, 'input_text': input_text, 'gpt_response': gpt_response})

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Processed successfully!',
                'responses': responses
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Failed to process', 'error': str(e)})
        }

    finally:
        if connection:
            cursor.close()
            connection.close()
