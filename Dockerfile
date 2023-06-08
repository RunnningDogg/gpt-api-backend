# 测试Flask的Dockerfile
FROM python:3.11.3
# set a directory for the app
WORKDIR /usr/src/app

# copy all the files to the container
COPY . .

# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# expose port
EXPOSE 5001

# Exec
CMD ["flask", "run" , "--host=0.0.0.0", "-p", "5001"]