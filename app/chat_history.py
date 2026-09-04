class ChatHistory:

    def __init__(self):
        self.messages = []

    def add_user_message(self, message):

        self.messages.append({
            "role": "user",
            "content": message
        })

    def add_ai_message(self, message):

        self.messages.append({
            "role": "assistant",
            "content": message
        })

    def get_history(self):

        return self.messages

    def clear(self):

        self.messages = []