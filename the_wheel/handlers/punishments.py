from mongoengine import Document, DateTimeField, StringField, DictField, ObjectIdField, URLField

class Punishments(Document):
    meta = {'collection': 'punishments'}
    loser = ObjectIdField()
    video = URLField()
    image = URLField()
    iframe = URLField()
    description = StringField()

def get_punishment(loser_id):
    p = Punishments.objects(loser=loser_id).first()
    return p
