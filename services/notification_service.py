from extensions import db
from models import Notification, User, Role


class NotificationService:

    @staticmethod
    def send(user_ids, title, message, ntype="info", link=None):
        for uid in user_ids:
            n = Notification(
                user_id=uid,
                title=title,
                message=message,
                notification_type=ntype,
                link=link
            )
            db.session.add(n)
        db.session.commit()

    @staticmethod
    def send_to_officers_admins(title, message, ntype="info", link=None):
        users = User.query.filter(User.role.in_([Role.ADMIN, Role.OFFICER])).all()
        ids = [u.user_id for u in users]
        if ids:
            NotificationService.send(ids, title, message, ntype, link)

    @staticmethod
    def send_to_customer(customer_id, title, message, ntype="info", link=None):
        user = User.query.filter_by(linked_customer_id=customer_id).first()
        if user:
            NotificationService.send([user.user_id], title, message, ntype, link)

    @staticmethod
    def get_unread(user_id):
        return Notification.query.filter_by(
            user_id=user_id, is_read=False
        ).order_by(Notification.created_at.desc()).all()

    @staticmethod
    def get_all(user_id):
        return Notification.query.filter_by(
            user_id=user_id
        ).order_by(Notification.created_at.desc()).all()

    @staticmethod
    def get_unread_count(user_id):
        return Notification.query.filter_by(
            user_id=user_id, is_read=False
        ).count()

    @staticmethod
    def mark_read(notification_id):
        n = Notification.query.get_or_404(notification_id)
        n.is_read = True
        db.session.commit()

    @staticmethod
    def mark_all_read(user_id):
        Notification.query.filter_by(
            user_id=user_id, is_read=False
        ).update({"is_read": True})
        db.session.commit()
