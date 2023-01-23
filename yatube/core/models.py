from django.db import models


class CreateModel(models.Model):
    """
    Абстрактная модель.
    Добавляет поле дата создания
    """
    pub_date = models.DateTimeField(
        'Дата создания',
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        abstract = True
