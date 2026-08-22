from app.models.notification import Notification


async def create_notification(db, user_id: int, title: str, content: str,
                               ntype: str, related_type: str = None, related_id: int = None):
    n = Notification(user_id=user_id, title=title, content=content, type=ntype,
                     related_type=related_type, related_id=related_id)
    db.add(n)
    await db.flush()
    return n
