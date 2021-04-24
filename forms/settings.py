from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired


class SettingsForm(FlaskForm):
    point_name = StringField('Название баллов', validators=[DataRequired()],
                             render_kw={"placeholder": "Название баллов"})
    tempban_len = IntegerField('Время блокировки (в секундах)', validators=[DataRequired()],
                               render_kw={"placeholder": "Время блокировки (в секундах)"})
    banwords = TextAreaField('Заблокированные слова (Разделять символом ";")', validators=[],
                             render_kw={"placeholder": "Заблокированные слова",
                                        "style": "resize: none; height: 200px"})
    is_activated = BooleanField('Подключить бота')
    submit = SubmitField('Сохранить')