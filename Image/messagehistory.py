from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.chat_history import BaseChatMessageHistory


class LastNMessageHistory(BaseChatMessageHistory):
    
    def __init__(self, mongo_history, max_messages=2):
        self.mongo_history = mongo_history
        self.max_messages = max_messages
        self._load_messages()

    def _load_messages(self):
        self._messages = self.mongo_history.messages[-self.max_messages:] if len(self.mongo_history.messages) > self.max_messages else self.mongo_history.messages
    
    @property
    def messages(self):
        return self._messages

    def add_message(self, message):
        if isinstance(message, HumanMessage):
            self.mongo_history.add_user_message(message.content)
        elif isinstance(message, AIMessage):
            self.mongo_history.add_ai_message(message.content)

        self._messages.append(message)
        
        if len(self._messages) > self.max_messages:
            self._messages = self._messages[-self.max_messages:]
    
    def add_user_message(self, message: str):
        self.add_message(HumanMessage(content=message))
    
    def add_ai_message(self, message: str):
        self.add_message(AIMessage(content=message))
    
    def clear(self):
        self._messages = []
        self.mongo_history.clear()