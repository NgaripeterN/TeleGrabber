from sqlalchemy import Column, Integer, String, DateTime, Boolean
from .database import Base
import datetime


class GroupSubscription(Base):
    __tablename__ = "group_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, unique=True, index=True)
    subscribed = Column(Boolean, default=False)
    expiry_date = Column(DateTime, nullable=True)
    subscriber_id = Column(Integer, nullable=True)
    custom_caption = Column(String, nullable=True)

    def is_active(self):
        if not self.subscribed:
            return False
        if self.expiry_date and self.expiry_date < datetime.datetime.utcnow():
            return False
        return True
