from django_q.tasks import schedule


def schedule_append_price_history():

    schedule('main.utils.run_append_price_history', name='Append Price History', cron='30 21 * * *')





