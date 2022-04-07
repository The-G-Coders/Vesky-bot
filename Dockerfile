FROM python:3.9-alpine3.15

# set time-zone
ENV TZ="Europe/Bratislava"

# setup the workdir
WORKDIR /app

# instal dependencies
COPY requirements.txt /app
RUN pip install -r requirements.txt

# copy all files to the workdir
COPY . /app

#run the bot.py file
CMD ["python", "bot.py"]
