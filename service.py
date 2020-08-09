import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import email
import base64

class Service:
    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(self):
        self.service = self.get_service()
        self.query = 'subject: ' +input('What subject do you want to look up? ')
        self.message_ids = self.search_messages('me', self.query)
        self.store(self.message_ids)

    def get_service(self):
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('gmail', 'v1', credentials=creds)

        return service

    def search_messages(self, user_id, search_string):

        try:
            search_id = self.service.users().messages().list(userId = user_id, q = search_string).execute()

            number_results = search_id['resultSizeEstimate']

            results = []
            if number_results > 0:
                message_ids = search_id['messages']

                for ids in message_ids:
                    results.append(ids['id'])
                return results
            else:
                print("There were no results for your query.  Returning EMPTY String")
                return ""


        except (errors.HttpError, error):
            print("An error occured {}".format(error))

    def get_message(self, user_id, msg_id):
        
        try:
            subject = "This message has no Subject"

            msg = self.service.users().messages().get(userId = user_id, id = msg_id, format = "full").execute()

            headers= msg["payload"]["headers"]
            
            for item in headers:
                if item['name'] == 'Subject':
                    subject = item['value']


            message = msg['payload']['parts'][0]['body']['data']

            msg_str = base64.urlsafe_b64decode(message.encode("utf-8"))

            msg_email = email.message_from_bytes(msg_str).get_payload()

            #This is intended for a specific daily email I recieve where the important message and the ads are
            #separated by a dashed line.  Since this divides the message into a list and I only want the important
            #message, which precedes the dashed lines, I use [0] to to retrieve that important message from the list
            msg_email = msg_email.split('-------------------------------------')[0].replace('\r', '')
            #Adding a separator at the end of the message
            msg_email += '--------------------------------------------------------------------------------\n\n'

            return msg_email, subject

        except Exception as error:
            print("An error occured {}".format(error))
        
    def store(self, message_ids):

        indx = len(message_ids)-1
        non_printable = []

        with open("problems.txt", "a") as problems:
            while indx >= 0:
                message, subject = self.get_message("me", message_ids[indx])
                try:
                    problems.write(subject +'\n\n')
                    problems.write(message)
                    message_ids.pop(indx)
                    indx -= 1
                except:
                    non_printable.append(subject)
                    problems.write('\n\n--------------------------------------------------------------------------------\n\n')
                    indx -= 1

            problems.write(str(non_printable))

