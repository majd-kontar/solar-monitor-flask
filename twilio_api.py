from twilio.rest import Client


class TwilioApi:
    def __init__(self):
        self.account_sid = 'AC3761bf367fbbe45b797c7bb15b5553c7'
        self.auth_token = 'ec2fe1dfc6aa0e4f149427d64999bd8c'
        self.client = Client(self.account_sid, self.auth_token)

    def send_message(self, body):
        msg = self.client.messages.create(
            from_='whatsapp:+14155238886',
            body=body,
            to='whatsapp:+96171705620'
        )
        return msg


if __name__ == '__main__':
    twilio = TwilioApi()
    message = twilio.send_message('test')
    print(message.body)
